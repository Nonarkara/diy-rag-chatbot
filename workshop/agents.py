"""Named agents. Skills are job descriptions, not chat personalities."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Agent:
    name: str
    role: str
    skills: tuple[str, ...]
    brief: str


LIBRARIAN = Agent(
    name="librarian",
    role="retrieval",
    skills=("search local knowledge files", "cite paths", "stay silent when nothing matches"),
    brief="Call search_knowledge, then write_artifact with the paths and excerpts. Do not answer from memory.",
)

RESEARCHER = Agent(
    name="researcher",
    role="research",
    skills=("read retrieved passages", "note what the files actually say", "cite paths"),
    brief="Call search_knowledge, then write_artifact with notes that cite the paths the tool returned.",
)

SCOUT = Agent(
    name="scout",
    role="research",
    skills=("read retrieved passages", "extract limits and refusals", "cite paths"),
    brief="Call search_knowledge, then write_artifact with what the files refuse and the handoff when they have no answer.",
)

WRITER = Agent(
    name="writer",
    role="draft",
    skills=("turn notes into a short brief", "honor @mentions", "cite paths"),
    brief="Call read_artifact on the research notes, then write_artifact the brief. Do not add facts that are not in those notes.",
)

REVIEWER = Agent(
    name="reviewer",
    role="review",
    skills=("check citations", "check the refusal boundary", "approve or request one revision"),
    brief="Call read_artifact on the brief. Approve only when the acceptance checks hold.",
)


LITE_AGENTS = (LIBRARIAN, RESEARCHER, WRITER, REVIEWER)
FULL_AGENTS = (LIBRARIAN, RESEARCHER, SCOUT, WRITER, REVIEWER)


def roster(mode: str) -> tuple[Agent, ...]:
    if mode == "full":
        return FULL_AGENTS
    return LITE_AGENTS


def get_agent(mode: str, name: str) -> Agent:
    for agent in roster(mode):
        if agent.name == name:
            return agent
    raise KeyError(name)
