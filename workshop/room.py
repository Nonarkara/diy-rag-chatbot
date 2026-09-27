"""A room is a transcript with a silence default.

Agents appear only when the orchestrator accepts a work turn.
@mentions are delivered to that agent. Everyone else stays quiet.
"""

from __future__ import annotations

from dataclasses import dataclass, field


VISIBLE_KINDS = frozenset({"user", "artifact", "question", "status"})


@dataclass
class RoomMessage:
    speaker: str
    kind: str
    text: str
    task_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "speaker": self.speaker,
            "kind": self.kind,
            "text": self.text,
            "task_id": self.task_id,
        }


@dataclass
class Room:
    messages: list[RoomMessage] = field(default_factory=list)

    def post(
        self,
        speaker: str,
        kind: str,
        text: str,
        task_id: str | None = None,
    ) -> RoomMessage:
        message = RoomMessage(speaker=speaker, kind=kind, text=text.strip(), task_id=task_id)
        self.messages.append(message)
        return message

    def mentions_for(self, agent: str) -> str:
        lines: list[str] = []
        needle = f"@{agent}"
        for message in self.messages:
            if message.kind != "user":
                continue
            if needle in message.text or "@everyone" in message.text:
                lines.append(message.text)
        return "\n".join(lines).strip()

    def visible(self) -> list[RoomMessage]:
        return [m for m in self.messages if m.kind in VISIBLE_KINDS and m.text]

    def render(self) -> str:
        blocks: list[str] = []
        for message in self.visible():
            blocks.append(f"## {message.speaker} ({message.kind})\n\n{message.text}")
        return "\n\n".join(blocks).strip() + ("\n" if blocks else "")


def looks_like_work(text: str) -> bool:
    """A greeting is not a job. Silence is the right response."""
    raw = text.strip()
    if not raw:
        return False
    lowered = raw.lower()
    if "@" in raw and len(raw.split()) >= 4:
        return True
    keywords = (
        "write",
        "research",
        "brief",
        "summar",
        "review",
        "draft",
        "file",
        "refus",
        "เขียน",
        "สรุป",
        "ค้น",
        "ตรวจ",
    )
    if any(word in lowered for word in keywords):
        return True
    return len(raw.split()) >= 8
