"""Modes and the local-only RAM check.

The primary provider is an OpenAI-compatible API. It loads no weights,
so RAM is not consulted. Ollama is optional: only then do we compare
available memory with the model's weight budget.

Environment variables override ``workshop.yaml``.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml


# Approximate weight RAM in gigabytes. Keep this table boring and honest.
KNOWN_MODELS_GB: dict[str, float] = {
    "qwen2.5:1.5b": 1.2,
    "qwen2.5:3b": 2.2,
    "qwen2.5:7b": 4.7,
    "qwen2.5:14b": 9.0,
    "qwen2.5:32b": 20.0,
    "llama3.2:1b": 0.8,
    "llama3.2:3b": 2.0,
    "llama3.1:8b": 4.9,
    "gemma2:2b": 1.6,
    "gemma3:1b": 0.8,
    "gemma3:4b": 3.3,
    "gemma4:e2b": 3.0,
    "gemma4:e4b": 5.0,
    "mistral:7b": 4.4,
}

REMOTE_PROVIDERS = frozenset({"openai", "scripted"})
LOCAL_PROVIDERS = frozenset({"ollama"})

# lite / full is how many agents may run at once. On an API that is a
# concurrency cap, not a memory requirement.
MODE_CONCURRENCY = {"lite": 1, "full": 4}

# Headroom when a local model is actually loaded. One weight footprint,
# plus a little extra per in-flight request. Not used for API providers.
LOCAL_HEADROOM_GB = 1.5
KV_GB_PER_EXTRA = 0.5

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_YAML = REPO_ROOT / "workshop.yaml"


class WorkshopConfigError(ValueError):
    """The config cannot be run as written. Fix it before starting."""


class InsufficientResources(RuntimeError):
    """RAM or model size cannot support this mode. Refused on purpose."""


@dataclass(frozen=True)
class WorkshopConfig:
    mode: str
    provider: str
    model: str
    knowledge_dir: Path
    max_concurrent: int
    max_turns: int
    max_revisions: int
    max_invalid_per_task: int
    accept_risk: bool
    ram_total_gb: float | None
    ram_available_gb: float | None
    model_gb: float | None
    out_dir: Path | None = None


@dataclass(frozen=True)
class ResourcePlan:
    mode: str
    provider: str
    model: str
    model_gb: float
    concurrent: int
    required_gb: float
    floor_gb: float
    total_gb: float | None
    available_gb: float | None
    summary: str


def repo_root() -> Path:
    return REPO_ROOT


def _yaml_defaults() -> dict:
    if not DEFAULT_YAML.exists():
        return {}
    data = yaml.safe_load(DEFAULT_YAML.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise WorkshopConfigError("workshop.yaml must be a mapping")
    return data


def _env_float(name: str) -> float | None:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return None
    try:
        return float(raw)
    except ValueError as exc:
        raise WorkshopConfigError(f"{name} must be a number of gigabytes, got {raw!r}") from exc


def detect_ram() -> tuple[float | None, float | None]:
    """Return ``(total_gb, available_gb)``.

    ``WORKSHOP_RAM_GB`` is available RAM. ``WORKSHOP_RAM_TOTAL_GB`` is
    installed RAM. When only one is set, it is used for both so a test
    or a manual override stays a single number.
    """
    override_avail = _env_float("WORKSHOP_RAM_GB")
    override_total = _env_float("WORKSHOP_RAM_TOTAL_GB")
    if override_avail is not None or override_total is not None:
        avail = override_avail if override_avail is not None else override_total
        total = override_total if override_total is not None else override_avail
        return total, avail

    total_kb = None
    avail_kb = None
    try:
        text = Path("/proc/meminfo").read_text(encoding="utf-8")
    except OSError:
        text = ""
    for line in text.splitlines():
        if line.startswith("MemTotal:"):
            total_kb = int(line.split()[1])
        elif line.startswith("MemAvailable:"):
            avail_kb = int(line.split()[1])
    if total_kb and avail_kb:
        return total_kb / (1024 * 1024), avail_kb / (1024 * 1024)

    try:
        out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True, timeout=2).strip()
        total = int(out) / (1024 ** 3)
        # Available is unknown; assume 60% is free enough to plan against.
        return total, total * 0.6
    except (OSError, subprocess.SubprocessError, ValueError):
        return None, None


def resolve_model_gb(model: str) -> float:
    override = _env_float("WORKSHOP_MODEL_GB")
    if override is not None:
        if override < 0:
            raise WorkshopConfigError("WORKSHOP_MODEL_GB cannot be negative")
        return override
    if model not in KNOWN_MODELS_GB:
        known = ", ".join(sorted(KNOWN_MODELS_GB))
        raise WorkshopConfigError(
            f"No RAM estimate for local model {model!r}. "
            f"Set WORKSHOP_MODEL_GB to its weight size in gigabytes, "
            f"or pick a known model ({known})."
        )
    return KNOWN_MODELS_GB[model]


def load_config(
    *,
    mode: str | None = None,
    provider: str | None = None,
    model: str | None = None,
    knowledge_dir: Path | None = None,
    live: bool = False,
) -> WorkshopConfig:
    defaults = _yaml_defaults()
    mode = (mode or os.environ.get("WORKSHOP_MODE") or defaults.get("mode") or "lite").strip().lower()
    if mode not in MODE_CONCURRENCY:
        raise WorkshopConfigError(f"WORKSHOP_MODE must be lite or full, got {mode!r}")

    provider = (
        provider
        or os.environ.get("WORKSHOP_PROVIDER")
        or defaults.get("provider")
        or "openai"
    ).strip().lower()
    # `--live` means the API path. The offline rehearsal is `--offline`.
    if live and provider == "scripted":
        provider = "openai"
    if provider not in REMOTE_PROVIDERS | LOCAL_PROVIDERS:
        raise WorkshopConfigError(
            f"WORKSHOP_PROVIDER must be scripted, ollama, or openai, got {provider!r}"
        )

    model = (
        model
        or os.environ.get("WORKSHOP_MODEL")
        or defaults.get("model")
        or os.environ.get("LLM_MODEL")
        or ("qwen2.5:3b" if provider == "ollama" else "gpt-4o-mini")
    ).strip()

    knowledge = knowledge_dir or Path(
        os.environ.get("WORKSHOP_KNOWLEDGE")
        or defaults.get("knowledge_dir")
        or "knowledge"
    )
    if not knowledge.is_absolute():
        knowledge = REPO_ROOT / knowledge

    total, avail = detect_ram()
    accept = os.environ.get("WORKSHOP_I_ACCEPT_RISK", "").strip() in {"1", "true", "yes"}
    model_gb = None if provider in REMOTE_PROVIDERS else resolve_model_gb(model)

    return WorkshopConfig(
        mode=mode,
        provider=provider,
        model=model,
        knowledge_dir=knowledge,
        max_concurrent=MODE_CONCURRENCY[mode],
        max_turns=int(os.environ.get("WORKSHOP_MAX_TURNS") or defaults.get("max_turns") or 8),
        max_revisions=int(os.environ.get("WORKSHOP_MAX_REVISIONS") or defaults.get("max_revisions") or 1),
        max_invalid_per_task=2,
        accept_risk=accept,
        ram_total_gb=total,
        ram_available_gb=avail,
        model_gb=model_gb,
    )


def plan_resources(cfg: WorkshopConfig) -> ResourcePlan:
    if cfg.provider in REMOTE_PROVIDERS:
        summary = (
            f"provider={cfg.provider} model={cfg.model}: API path, no local weights, "
            f"RAM check skipped. Concurrency cap is {cfg.max_concurrent}."
        )
        return ResourcePlan(
            mode=cfg.mode,
            provider=cfg.provider,
            model=cfg.model,
            model_gb=0.0,
            concurrent=cfg.max_concurrent,
            required_gb=0.0,
            floor_gb=0.0,
            total_gb=cfg.ram_total_gb,
            available_gb=cfg.ram_available_gb,
            summary=summary,
        )

    assert cfg.model_gb is not None
    extra = max(0, cfg.max_concurrent - 1)
    required = cfg.model_gb + LOCAL_HEADROOM_GB + KV_GB_PER_EXTRA * extra
    summary = (
        f"local model {cfg.model} needs about {required:.1f} GB free "
        f"({cfg.model_gb:.1f} GB weights + {LOCAL_HEADROOM_GB:.1f} GB headroom"
        + (f" + {KV_GB_PER_EXTRA:.1f} GB × {extra} extra in-flight" if extra else "")
        + "). This check runs only for Ollama."
    )
    return ResourcePlan(
        mode=cfg.mode,
        provider=cfg.provider,
        model=cfg.model,
        model_gb=cfg.model_gb,
        concurrent=cfg.max_concurrent,
        required_gb=required,
        floor_gb=0.0,
        total_gb=cfg.ram_total_gb,
        available_gb=cfg.ram_available_gb,
        summary=summary,
    )


def assert_resources(cfg: WorkshopConfig) -> ResourcePlan:
    """Skip RAM entirely for API providers. Check it only for local weights.

    ``WORKSHOP_I_ACCEPT_RISK=1`` skips the local refusal.
    """
    plan = plan_resources(cfg)
    if cfg.provider in REMOTE_PROVIDERS:
        return plan

    problems: list[str] = []
    if plan.available_gb is None:
        problems.append(
            "Could not read available RAM. Set WORKSHOP_RAM_GB in gigabytes, "
            "or switch to WORKSHOP_PROVIDER=openai."
        )
    elif plan.available_gb + 1e-6 < plan.required_gb:
        problems.append(
            f"Available RAM is {plan.available_gb:.1f} GB, under the "
            f"{plan.required_gb:.1f} GB estimate for local model {cfg.model}."
        )

    if not problems:
        return plan
    if cfg.accept_risk:
        return ResourcePlan(
            **{
                **plan.__dict__,
                "summary": plan.summary + " WORKSHOP_I_ACCEPT_RISK=1 so the local refusal was skipped.",
            }
        )

    message = (
        f"Refusing to load local model {cfg.model}.\n"
        f"{plan.summary}\n"
        + "\n".join(f"- {p}" for p in problems)
        + "\n"
        "This check applies only when WORKSHOP_PROVIDER=ollama.\n"
        "An ordinary laptop can run the workshop on a cheap API with tool calls:\n"
        "  WORKSHOP_PROVIDER=openai\n"
        "  LLM_API_KEY=replace-me\n"
        "  # optional LLM_BASE_URL=https://openrouter.ai/api/v1\n"
        "Put the real key in .env yourself. Do not paste it into chat.\n"
        "Or pick a smaller local model from KNOWN_MODELS_GB in workshop/config.py.\n"
        "Set WORKSHOP_I_ACCEPT_RISK=1 only after you have measured this machine."
    )
    raise InsufficientResources(message)
