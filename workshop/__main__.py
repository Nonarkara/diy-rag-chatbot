"""Command line.

    python -m workshop demo            # OpenAI-compatible API + tools
    python -m workshop demo --offline  # same tools, no key, scripted worker
    python -m workshop demo --local    # optional Ollama weights
    python -m workshop check
    python -m workshop room "write a brief on …"
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from workshop import __version__
from workshop.config import (
    DEFAULT_YAML,
    InsufficientResources,
    KNOWN_MODELS_GB,
    MODE_CONCURRENCY,
    WorkshopConfigError,
    assert_resources,
    load_config,
    repo_root,
)
from workshop.demo import run_demo, run_room_message
from workshop.llm import MissingAPIKey, OllamaLLM, OpenAICompatibleLLM, ScriptedLLM, api_key


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    parser = argparse.ArgumentParser(prog="workshop", description="DIY multi-agent workshop")
    parser.add_argument("--version", action="version", version=f"workshop {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="research → brief → review, then stop")
    demo.add_argument("--offline", action="store_true", help="scripted worker, real tools, no API key")
    demo.add_argument("--local", action="store_true", help="Ollama on this machine (optional)")
    demo.add_argument("--mode", choices=("lite", "full"))
    demo.add_argument("--model", default=None)
    demo.add_argument("--goal", default=None)
    demo.add_argument("--out", default=None, help="directory for brief.md, room.md, trace.json")

    check = sub.add_parser("check", help="print the plan; RAM is checked only for Ollama")
    check.add_argument("--mode", choices=("lite", "full"))
    check.add_argument("--provider", choices=("scripted", "ollama", "openai"))
    check.add_argument("--model", default=None)

    sub.add_parser("models", help="print approximate local model sizes (optional path)")

    room = sub.add_parser("room", help="one user message; agents work or stay silent")
    room.add_argument("message", nargs="*", help="the message to post")
    room.add_argument("--offline", action="store_true")
    room.add_argument("--local", action="store_true")
    room.add_argument("--mode", choices=("lite", "full"))
    room.add_argument("--model", default=None)
    room.add_argument("--out", default=None)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "models":
            return _models()
        if args.cmd == "check":
            return _check(args)
        if args.cmd == "demo":
            return _demo(args)
        if args.cmd == "room":
            return _room(args)
    except (InsufficientResources, WorkshopConfigError, MissingAPIKey, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2


def _models() -> int:
    print("Optional local models only. The default path is an API and does not load these.")
    print("Approximate Q4 weight RAM. Not a benchmark of your machine.")
    print(f"{'model':<18} {'GB':>6}")
    for name, size in sorted(KNOWN_MODELS_GB.items()):
        print(f"{name:<18} {size:6.1f}")
    print()
    print("lite  concurrency", MODE_CONCURRENCY["lite"], "(API or local, one agent at a time)")
    print("full  concurrency", MODE_CONCURRENCY["full"], "(API or local, several agents in flight)")
    print("RAM is checked only for WORKSHOP_PROVIDER=ollama.")
    print(f"Defaults file: {DEFAULT_YAML}")
    return 0


def _check(args) -> int:
    cfg = load_config(mode=args.mode, provider=args.provider, model=args.model)
    plan = assert_resources(cfg)
    print(plan.summary)
    if plan.total_gb is not None:
        print(f"installed RAM: {plan.total_gb:.1f} GB")
        print(f"available RAM: {plan.available_gb:.1f} GB")
    print("ok")
    return 0


def _demo(args) -> int:
    cfg = _cfg_from_args(args)
    llm = _llm(cfg)
    out = Path(args.out) if args.out else _default_out()
    print(f"workshop {__version__}  mode={cfg.mode}  provider={cfg.provider}  model={cfg.model}")
    report = run_demo(cfg, llm, goal=args.goal, run_dir=out)
    if report.tool_calls:
        print(f"tools: {report.tool_calls}")
    print(f"status: {report.status}")
    print(f"reason: {report.reason}")
    print(f"waves: {report.waves}")
    print(f"llm turns: {report.llm_turns}")
    print(f"wrote {out / 'brief.md'}")
    if report.status != "done":
        return 1
    print()
    print(report.brief)
    return 0


def _room(args) -> int:
    text = " ".join(args.message).strip()
    if not text:
        print("Give one message, for example:\n  python -m workshop room \"write a brief on the refusal rules\"", file=sys.stderr)
        return 2
    cfg = _cfg_from_args(args)
    llm = _llm(cfg)
    out = Path(args.out) if args.out else _default_out()
    report = run_room_message(cfg, llm, text, run_dir=out)
    print(f"status: {report.status}")
    print(f"reason: {report.reason}")
    print(report.room.render())
    print(f"wrote {out}")
    return 0 if report.status in {"done", "yielded", "blocked"} else 1


def _cfg_from_args(args):
    if getattr(args, "offline", False):
        return load_config(mode=args.mode, provider="scripted", model=args.model)
    if getattr(args, "local", False):
        return load_config(mode=args.mode, provider="ollama", model=_local_model(args.model))
    return load_config(mode=args.mode, provider=None, model=args.model)


def _local_model(explicit: str | None) -> str:
    import os

    if explicit:
        return explicit
    env_model = (os.environ.get("WORKSHOP_MODEL") or "").strip()
    if env_model in KNOWN_MODELS_GB:
        return env_model
    return "qwen2.5:3b"


def _llm(cfg):
    if cfg.provider == "scripted":
        return ScriptedLLM()
    if cfg.provider == "ollama":
        return OllamaLLM(model=cfg.model)
    if cfg.provider == "openai":
        if not api_key():
            raise MissingAPIKey(
                "No API key is set. Put LLM_API_KEY in .env (see .env.example), "
                "or run python -m workshop demo --offline to rehearse the same tools."
            )
        return OpenAICompatibleLLM(model=cfg.model, api_key=api_key())
    raise WorkshopConfigError(f"unknown provider {cfg.provider}")


def _default_out() -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = repo_root() / "workshop-runs" / stamp
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(repo_root() / ".env")


if __name__ == "__main__":
    raise SystemExit(main())
