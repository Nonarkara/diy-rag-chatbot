"""The only legal agent turn: advance, ask, yield, or done.

Anything else — greetings, peer chatter, missing JSON — is rejected.
The orchestrator never posts rejected text into the room.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


ACTIONS = frozenset({"advance", "ask", "yield", "done"})

_CHATTER = (
    "let's chat",
    "lets chat",
    "what do you think",
    "hey team",
    "hello everyone",
    "as an ai",
    "happy to help",
)


class ProtocolError(ValueError):
    """The model did not return a work turn."""


@dataclass(frozen=True)
class Turn:
    action: str
    note: str = ""
    artifact: str = ""
    question: str | None = None
    handoff_to: str | None = None
    decision: str | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "action": self.action,
                "note": self.note,
                "artifact": self.artifact,
                "question": self.question,
                "handoff_to": self.handoff_to,
                "decision": self.decision,
            },
            ensure_ascii=False,
        )


def parse_turn(raw: str) -> Turn:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ProtocolError("no JSON work object (idle or chat output)")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ProtocolError(f"invalid JSON work object: {exc}") from exc
    if not isinstance(data, dict):
        raise ProtocolError("work object must be a JSON object")
    action = str(data.get("action") or "").strip().lower()
    if action not in ACTIONS:
        raise ProtocolError(f"action {action!r} is not advance, ask, yield, or done")
    question = data.get("question")
    handoff = data.get("handoff_to")
    decision = data.get("decision")
    artifact = str(data.get("artifact") or "")
    if _looks_like_chatter(artifact) or _looks_like_chatter(str(data.get("note") or "")):
        raise ProtocolError("idle chat phrasing inside a work turn")
    if action == "ask" and not str(question or "").strip():
        raise ProtocolError("ask requires one bounded question")
    if action in {"advance", "done"} and action != "done":
        if len(artifact.split()) < 12:
            raise ProtocolError("advance requires a real artifact, not a one-liner")
    return Turn(
        action=action,
        note=str(data.get("note") or "").strip(),
        artifact=artifact.strip(),
        question=(str(question).strip() if question else None),
        handoff_to=(str(handoff).strip() if handoff else None),
        decision=(str(decision).strip().lower() if decision else None),
    )


def _looks_like_chatter(text: str) -> bool:
    low = text.lower()
    return any(phrase in low for phrase in _CHATTER)
