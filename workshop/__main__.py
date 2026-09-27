"""Command line.

    python -m workshop demo          # offline, finishes a brief
    python -m workshop demo --live   # Ollama or WORKSHOP_PROVIDER
    python -m workshop check
    python -m workshop models
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
    MODE_FLOOR_GB,
    WorkshopConfigError,
    assert_resources,
    load_config,
    repo_root,
)
from workshop.demo import run_demo, run_room_message
from workshop.llm import LiveLLM, ScriptedLLM


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    parser = argparse.ArgumentParser(prog="workshop", description="DIY multi-agent workshop")
    parser.add_argument("--version", action="version", version=f"workshop {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    demo = sub.add_parser("demo", help="research → brief → review, then stop")
    demo.add_argument("--live", action="store_true", help="call a real model instead of the scripted workers")
    demo.add_argument("--mode", choices=("lite", "full"))
    demo.add_argument("--goal", default=None)
    demo.add_argument("--out", default=None, help="directory for brief.md, room.md, trace.json")

    check = sub.add_parser("check", help="print the RAM plan and refuse if it does not fit")
    check.add_argument("--mode", choices=("lite", "full"))
    check.add_argument("--provider", choices=("scripted", "ollama", "openai"))
    check.add_argument("--model", default=None)

    sub.add_parser("models", help="print approximate local model sizes")

    room = sub.add_parser("room", help="one user message; agents work or stay silent")
    room.add_argument("message", nargs="*", help="the message to post")
    room.add_argument("--live", action="store_true")
    room.add_argument("--mode", choices=("lite", "full"))
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
    except (InsufficientResources, WorkshopConfigError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2


def _models() -> int:
    print("Approximate Q4 weight RAM. Not a benchmark of your machine.")
    print(f"{'model':<18} {'GB':>6}")
    for name, size in sorted(KNOWN_MODELS_GB.items()):
        print(f"{name:<18} {size:6.1f}")
    print()
    print("lite  concurrency", MODE_CONCURRENCY["lite"], " installed floor", f"{MODE_FLOOR_GB['lite']:.0f} GB")
    print("full  concurrency", MODE_CONCURRENCY["full"], " installed floor", f"{MODE_FLOOR_GB['full']:.0f} GB")
    print("Remote provider openai uses 0 GB of local weights.")
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
    cfg = load_config(mode=args.mode, live=args.live)
    llm = _llm(cfg, live=args.live)
    out = Path(args.out) if args.out else _default_out()
    print(f"workshop {__version__}  mode={cfg.mode}  provider={cfg.provider}  model={cfg.model}")
    report = run_demo(cfg, llm, goal=args.goal, run_dir=out)
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
    cfg = load_config(mode=args.mode, live=args.live)
    llm = _llm(cfg, live=args.live)
    out = Path(args.out) if args.out else _default_out()
    report = run_room_message(cfg, llm, text, run_dir=out)
    print(f"status: {report.status}")
    print(f"reason: {report.reason}")
    print(report.room.render())
    print(f"wrote {out}")
    return 0 if report.status in {"done", "yielded", "blocked"} else 1


def _llm(cfg, *, live: bool):
    if live or cfg.provider in {"ollama", "openai"}:
        return LiveLLM(provider=cfg.provider if cfg.provider != "scripted" else "ollama", model=cfg.model)
    return ScriptedLLM()


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
