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
    brief="Run the folder search and hand passages to the next agent. Do not paraphrase from memory.",
)

RESEARCHER = Agent(
    name="researcher",
    role="research",
    skills=("read retrieved passages", "note what the files actually say", "cite paths"),
    brief="Write research notes grounded only in the passages you were given.",
)

SCOUT = Agent(
    name="scout",
    role="research",
    skills=("read retrieved passages", "extract limits and refusals", "cite paths"),
    brief="Write notes on what the files refuse, and the handoff when they have no answer.",
)

WRITER = Agent(
    name="writer",
    role="draft",
    skills=("turn notes into a short brief", "honor @mentions", "cite paths"),
    brief="Write the operator brief from the research notes. Do not add facts that are not in those notes.",
)

REVIEWER = Agent(
    name="reviewer",
    role="review",
    skills=("check citations", "check the refusal boundary", "approve or request one revision"),
    brief="Review the brief against the acceptance criteria. Approve only when they hold.",
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
