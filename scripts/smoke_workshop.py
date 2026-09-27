#!/usr/bin/env python3
"""Prove the orchestrator assigns work and the demo finishes.

Run from the repo root:

    python scripts/smoke_workshop.py

Uses the scripted workers, so it does not download a model and does not
need an API key. Exit 0 means the brief was approved inside the turn cap.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_workshop")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    from workshop.config import load_config
    from workshop.demo import run_demo
    from workshop.llm import ScriptedLLM

    out = Path(tempfile.mkdtemp(prefix="workshop-smoke-"))
    cfg = load_config(mode="lite", provider="scripted", knowledge_dir=ROOT / "knowledge")
    report = run_demo(cfg, ScriptedLLM(), run_dir=out)
    print()
    print(f"demo status: {report.status}")
    print(f"waves: {report.waves}")
    print(f"brief: {out / 'brief.md'}")
    if report.status != "done":
        print(report.reason)
        return 1
    text = (out / "brief.md").read_text(encoding="utf-8")
    if "knowledge/" not in text:
        print("brief is missing a knowledge/ citation")
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
