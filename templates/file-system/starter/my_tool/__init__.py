"""my_tool — the actual package. Put logic here, not in cli.py."""
from __future__ import annotations

from importlib.metadata import version as _v

__all__ = ["hello", "version_info"]


def hello(name: str = "world") -> str:
    """Return a greeting. Replace with real logic."""
    return f"hello, {name} 👋"


def version_info() -> str:
    """Return the package version. Used by --version."""
    try:
        return _v("my-tool")
    except Exception:  # noqa: BLE001
        return "0.1.0"
