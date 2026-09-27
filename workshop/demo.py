"""The happy-path mission: retrieve → research → brief → review.

Lite runs one agent at a time.
Full adds a second researcher and may run both research tasks together.
A single revision handoff is allowed. Then the queue stops.
"""

from __future__ import annotations

from pathlib import Path

from workshop.config import WorkshopConfig
from workshop.orchestrator import Mission, RunReport, Task, run_mission, write_run
from workshop.room import Room, looks_like_work


DEMO_GOAL = (
    "From the local knowledge folder only, write a short brief an operator can trust: "
    "what this kit will answer, what it refuses, and how a page should be filed. "
    "Cite the file paths you used."
)

_DRAFT_ACCEPTANCE = (
    "cites_knowledge",
    "min_words_40",
    "max_words_220",
    "states_refusal",
    "mentions_180",
)


def build_mission(mode: str, goal: str, *, max_turns: int, max_revisions: int) -> Mission:
    retrieve = Task(
        id="retrieve",
        title="Search the knowledge folder",
        owner="librarian",
        kind="retrieve",
        brief="Find passages that answer the goal. Return paths and excerpts.",
        acceptance=("cites_knowledge",),
    )
    if mode == "full":
        research = [
            Task(
                id="research_facts",
                title="Notes on filing and what the kit answers",
                owner="researcher",
                kind="research",
                brief="From the passages only, note how a page is filed and what the kit will answer.",
                acceptance=("cites_knowledge", "min_words_25"),
                depends_on=("retrieve",),
            ),
            Task(
                id="research_limits",
                title="Notes on refusals",
                owner="scout",
                kind="research",
                brief="From the passages only, note what the kit will not answer and what to do instead.",
                acceptance=("cites_knowledge", "min_words_25", "states_refusal"),
                depends_on=("retrieve",),
            ),
        ]
        draft_deps = ("research_facts", "research_limits")
    else:
        research = [
            Task(
                id="research",
                title="Notes from the knowledge folder",
                owner="researcher",
                kind="research",
                brief="From the passages only, note filing rules, what the kit answers, and what it refuses.",
                acceptance=("cites_knowledge", "min_words_25", "states_refusal"),
                depends_on=("retrieve",),
            )
        ]
        draft_deps = ("research",)
    draft = Task(
        id="draft",
        title="Write the operator brief",
        owner="writer",
        kind="draft",
        brief=(
            "Write the brief from the research notes. "
            "Honor every @writer message in the room. Cite knowledge/ paths."
        ),
        acceptance=_DRAFT_ACCEPTANCE,
        depends_on=draft_deps,
    )
    review = Task(
        id="review",
        title="Review the brief",
        owner="reviewer",
        kind="review",
        brief="Approve only if the brief cites files, states a refusal, and stays inside the word cap.",
        acceptance=("cites_knowledge",),
        depends_on=("draft",),
    )
    return Mission(
        goal=goal,
        tasks=[retrieve, *research, draft, review],
        max_turns=max_turns,
        max_revisions=max_revisions,
    )


def run_demo(
    cfg: WorkshopConfig,
    llm,
    *,
    goal: str | None = None,
    run_dir: Path | None = None,
    user_message: str | None = None,
) -> RunReport:
    goal = goal or DEMO_GOAL
    room = Room()
    room.post(
        "user",
        "user",
        user_message
        or "@writer Keep the brief under 180 words and cite knowledge/ paths.",
    )
    mission = build_mission(
        cfg.mode,
        goal,
        max_turns=cfg.max_turns,
        max_revisions=cfg.max_revisions,
    )
    report = run_mission(mission, cfg, llm, room)
    if run_dir is not None:
        write_run(report, run_dir)
    return report


def run_room_message(cfg: WorkshopConfig, llm, text: str, *, run_dir: Path | None = None) -> RunReport:
    """One user message. A greeting gets silence. A job runs the bounded pipeline."""
    room = Room()
    room.post("user", "user", text)
    if not looks_like_work(text):
        room.post(
            "orchestrator",
            "status",
            "No task in that message. Agents stayed silent. "
            "Send a job, or mention an agent with a concrete ask.",
        )
        report = RunReport(
            status="yielded",
            reason="no task in the user message; agents stayed silent",
            mode=cfg.mode,
            provider=cfg.provider,
            model=cfg.model,
            goal=text,
            room=room,
        )
        if run_dir is not None:
            write_run(report, run_dir)
        return report
    mission = build_mission(
        cfg.mode,
        text,
        max_turns=cfg.max_turns,
        max_revisions=cfg.max_revisions,
    )
    report = run_mission(mission, cfg, llm, room)
    if run_dir is not None:
        write_run(report, run_dir)
    return report
