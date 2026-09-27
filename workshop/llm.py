"""LLM backends.

``ScriptedLLM`` completes the demo with no model process, so the
orchestrator can be proven on any machine. ``LiveLLM`` talks to Ollama
or an OpenAI-compatible endpoint. The workshop never invents an API key.
"""

from __future__ import annotations

import json
import threading
from typing import Protocol

from workshop.protocol import Turn


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str: ...


def _field(user: str, name: str) -> str:
    prefix = name + ":"
    for line in user.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


_GOOD_NOTES_FACTS = """\
# Research notes — what the kit answers and how to file

The kit answers only from files in the knowledge folder. A page should be markdown with one H1, a ถาม: line, a Q: line, and an A: line, filed in a short English category such as faq/ or briefings/. Source: knowledge/HOW-WE-FILE.md.

Example filing in the folder: knowledge/briefings/example-bilingual-qa.md defines a smart city as a platform for local problems, and says to replace the sample with the organisation's own definition.
"""

_GOOD_NOTES_LIMITS = """\
# Research notes — refusals

The kit will not answer questions absent from the documents, including weather, politics, other agencies, medical, legal, or investment advice, and it will not ignore its rules. If the files do not cover the question, say so and hand off. Sources: knowledge/GUARDRAILS.md and knowledge/faq/example-ask-someone-else.md.
"""

_GOOD_BRIEF = """\
# What this kit will answer

This kit answers only from files in knowledge/. A page should be markdown with one heading, a Thai question line, an English question line, and an answer, filed under a short category such as faq/ or briefings/. See knowledge/HOW-WE-FILE.md and knowledge/briefings/example-bilingual-qa.md.

It will not answer questions missing from the documents. That includes weather, politics, other agencies, medical, legal, and investment advice, and it will not drop these rules on request. If a file does not cover the question, say so and hand the person to a named owner. See knowledge/GUARDRAILS.md and knowledge/faq/example-ask-someone-else.md.

Kept under 180 words as requested.
"""

_BAD_BRIEF = """\
This note describes a helpful assistant that can talk about many civic topics and gadgets in general terms for an operator who wants a friendly overview of the project and its goals today and tomorrow.
"""


def _turn(action: str, artifact: str, note: str, decision: str | None = None) -> str:
    payload = Turn(
        action=action,
        note=note,
        artifact=artifact,
        decision=decision,
    )
    return payload.to_json()


class ScriptedLLM:
    """Deterministic worker used by the offline demo and the smoke test."""

    def __init__(self, *, bad_first_draft: bool = False):
        self.bad_first_draft = bad_first_draft
        self.calls = 0
        self.drafts = 0
        self.prompts: list[str] = []
        self._lock = threading.Lock()

    def complete(self, system: str, user: str) -> str:
        del system
        with self._lock:
            self.calls += 1
            self.prompts.append(user)
            kind = _field(user, "TASK_KIND")
            task_id = _field(user, "TASK_ID")
            if kind == "draft":
                self.drafts += 1
                draft_n = self.drafts
            else:
                draft_n = 0
        if kind == "research":
            if task_id == "research_limits":
                artifact = _GOOD_NOTES_LIMITS
            elif task_id == "research":
                artifact = _GOOD_NOTES_FACTS + "\n" + _GOOD_NOTES_LIMITS
            else:
                artifact = _GOOD_NOTES_FACTS
            return _turn("done", artifact, "notes cite the local files")
        if kind == "draft":
            revise = "REVISE:" in user
            if self.bad_first_draft and draft_n == 1 and not revise:
                return _turn("done", _BAD_BRIEF, "draft without sources")
            return _turn("done", _GOOD_BRIEF, "brief cites files and states refusals")
        if kind == "review":
            return json.dumps(
                {
                    "action": "done",
                    "decision": "approve",
                    "note": "Checked citations, refusal boundary, and length.",
                    "artifact": "APPROVED. The brief cites knowledge/ paths and states what the kit will not answer.",
                    "question": None,
                    "handoff_to": None,
                },
                ensure_ascii=False,
            )
        return _turn("yield", "", "no task kind matched")


class LiveLLM:
    """Ollama or an OpenAI-compatible endpoint. Requires a running server or a key in the environment."""

    def __init__(self, *, provider: str, model: str, temperature: float = 0.2, max_tokens: int = 900):
        import os

        from bot.llm import LLMClient, LLMConfig

        if provider == "ollama":
            base = os.environ.get("LLM_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
            key = None
        elif provider == "openai":
            base = os.environ.get("LLM_BASE_URL", "https://api.openai.com").rstrip("/")
            key = os.environ.get("LLM_API_KEY") or None
            if not key:
                raise RuntimeError(
                    "WORKSHOP_PROVIDER=openai requires LLM_API_KEY in the environment or .env. "
                    "Leave the value out of chat; put it in .env yourself."
                )
        else:
            raise RuntimeError(f"LiveLLM does not serve provider {provider!r}")
        self.client = LLMClient(
            LLMConfig(
                provider=provider,
                model=model,
                api_key=key,
                base_url=base,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=180.0,
            )
        )

    def complete(self, system: str, user: str) -> str:
        return self.client.complete(system, user)
