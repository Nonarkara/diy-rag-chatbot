"""Assign work, accept one turn, stop.

Each scheduled task is owned by one agent. A turn may advance that
task, ask one bounded question, or yield. Yielding twice, or chatting,
fails the mission. The loop is capped by ``max_turns``.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

from workshop.agents import Agent, get_agent
from workshop.config import WorkshopConfig, assert_resources
from workshop.protocol import ProtocolError, Turn, parse_turn
from workshop.rag import format_passages, search
from workshop.room import Room


CRITERIA = {
    "cites_knowledge": ("cites a knowledge/ path", lambda text: "knowledge/" in text),
    "min_words_25": ("at least 25 words", lambda text: len(text.split()) >= 25),
    "min_words_40": ("at least 40 words", lambda text: len(text.split()) >= 40),
    "max_words_220": ("at most 220 words", lambda text: len(text.split()) <= 220),
    "states_refusal": (
        "states a refusal boundary",
        lambda text: any(token in text.lower() for token in ("refus", "will not", "ไม่")),
    ),
    "mentions_180": ("honors the 180-word request", lambda text: "180" in text),
}


@dataclass
class Task:
    id: str
    title: str
    owner: str
    kind: str
    brief: str
    acceptance: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    status: str = "pending"
    artifact: str = ""
    turns: int = 0
    invalid_turns: int = 0
    max_turns: int = 2
    last_error: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "owner": self.owner,
            "kind": self.kind,
            "status": self.status,
            "turns": self.turns,
            "invalid_turns": self.invalid_turns,
            "acceptance": list(self.acceptance),
            "depends_on": list(self.depends_on),
        }


@dataclass
class Mission:
    goal: str
    tasks: list[Task]
    max_turns: int = 8
    max_revisions: int = 1
    max_invalid_per_task: int = 2
    revisions_used: int = 0
    outcome: str = "running"
    reason: str = ""


@dataclass
class RunReport:
    status: str
    reason: str
    mode: str
    provider: str
    model: str
    goal: str
    waves: list[list[str]] = field(default_factory=list)
    llm_turns: int = 0
    invalid_turns: int = 0
    tasks: list[Task] = field(default_factory=list)
    room: Room = field(default_factory=Room)
    resource_summary: str = ""
    brief: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "reason": self.reason,
            "mode": self.mode,
            "provider": self.provider,
            "model": self.model,
            "goal": self.goal,
            "waves": self.waves,
            "llm_turns": self.llm_turns,
            "invalid_turns": self.invalid_turns,
            "resource_summary": self.resource_summary,
            "brief": self.brief,
            "tasks": [task.to_dict() for task in self.tasks],
            "room": [message.to_dict() for message in self.room.messages],
        }


def evaluate(task: Task, text: str) -> tuple[bool, str]:
    for code in task.acceptance:
        label, check = CRITERIA[code]
        if not check(text):
            return False, f"{task.id} failed acceptance: {label}"
    return True, "ok"


def run_mission(
    mission: Mission,
    cfg: WorkshopConfig,
    llm,
    room: Room | None = None,
    *,
    check_resources: bool = True,
) -> RunReport:
    if check_resources:
        plan = assert_resources(cfg)
        resource_summary = plan.summary
    else:
        resource_summary = "resource check skipped"
    room = room or Room()
    room.post("orchestrator", "status", f"Mission started in {cfg.mode} mode. {resource_summary}")

    waves: list[list[str]] = []
    llm_turns = 0
    invalid_turns = 0

    while mission.outcome == "running":
        if any(task.status == "failed" for task in mission.tasks):
            mission.outcome = "failed"
            if not mission.reason:
                mission.reason = "a task failed"
            break
        if any(task.status == "blocked" for task in mission.tasks):
            mission.outcome = "blocked"
            if not mission.reason:
                mission.reason = "an agent asked one question and stopped"
            break
        ready = _ready(mission)
        if not ready:
            mission.outcome = _finish_status(mission)
            if not mission.reason:
                mission.reason = _finish_reason(mission)
            break
        if llm_turns >= mission.max_turns:
            mission.outcome = "failed"
            mission.reason = (
                f"stopped at the turn cap ({mission.max_turns}) "
                "so agents could not keep talking"
            )
            break

        wave = ready[: cfg.max_concurrent]
        waves.append([task.id for task in wave])
        results = _run_wave(wave, mission, cfg, llm, room)
        for task, outcome in results:
            if task.kind != "retrieve":
                llm_turns += 1
            if outcome[0] == "invalid":
                invalid_turns += 1
            _apply(task, outcome, mission, cfg, room)

    brief = _latest_done(mission, "draft")
    return RunReport(
        status=mission.outcome,
        reason=mission.reason,
        mode=cfg.mode,
        provider=cfg.provider,
        model=cfg.model,
        goal=mission.goal,
        waves=waves,
        llm_turns=llm_turns,
        invalid_turns=invalid_turns,
        tasks=mission.tasks,
        room=room,
        resource_summary=resource_summary,
        brief=brief,
    )


def _ready(mission: Mission) -> list[Task]:
    done = {task.id for task in mission.tasks if task.status == "done"}
    return [
        task
        for task in mission.tasks
        if task.status == "pending" and all(dep in done for dep in task.depends_on)
    ]


def _run_wave(wave, mission, cfg, llm, room):
    def one(task: Task):
        try:
            turn = _execute(task, mission, cfg, llm, room)
            return task, ("ok", turn)
        except ProtocolError as exc:
            return task, ("invalid", str(exc))

    if len(wave) == 1:
        return [one(wave[0])]
    results = []
    with ThreadPoolExecutor(max_workers=len(wave)) as pool:
        futures = {pool.submit(one, task): task for task in wave}
        for future in as_completed(futures):
            results.append(future.result())
    order = {task.id: index for index, task in enumerate(wave)}
    results.sort(key=lambda item: order[item[0].id])
    return results


def _execute(task: Task, mission: Mission, cfg: WorkshopConfig, llm, room: Room) -> Turn:
    if task.kind == "retrieve":
        passages = search(cfg.knowledge_dir, mission.goal, k=4)
        artifact = format_passages(passages)
        if artifact == "NO_PASSAGES":
            raise ProtocolError(f"librarian found nothing in {cfg.knowledge_dir}")
        return Turn(action="done", artifact=artifact, note=f"{len(passages)} passages")
    agent = get_agent(cfg.mode, task.owner)
    system, user = _prompt(agent, task, mission, room)
    raw = llm.complete(system, user)
    return parse_turn(raw)


def _prompt(agent: Agent, task: Task, mission: Mission, room: Room) -> tuple[str, str]:
    system = (
        f"You are {agent.name}, the {agent.role}. {agent.brief}\n"
        "You do a job. You do not greet, banter, or address other agents socially.\n"
        "Reply with ONE JSON object and nothing else. Keys:\n"
        'action: "advance" | "ask" | "yield" | "done"\n'
        "note: one sentence on what changed\n"
        "artifact: the work product (required for advance and done)\n"
        "question: one bounded question, or null\n"
        "handoff_to: agent name, or null\n"
        'decision: "approve" or "revise" when you are the reviewer, else null\n'
        "Use done when this task's acceptance criteria are met.\n"
        "Use ask only if you cannot proceed without one fact.\n"
        "Use yield only when you have nothing useful to add — then leave artifact empty.\n"
        "Cite paths as knowledge/<file>. Do not invent files."
    )
    mentions = room.mentions_for(agent.name)
    context = _context(mission)
    criteria = (
        "\n".join(f"- {code}: {CRITERIA[code][0]}" for code in task.acceptance)
        or "- produce the artifact"
    )
    repair = ""
    if task.last_error:
        repair = (
            f"\nPREVIOUS_TURN_REJECTED: {task.last_error}\n"
            "Reply with one JSON work object that fixes that. Do not chat.\n"
        )
    user = (
        f"TASK_ID: {task.id}\n"
        f"TASK_KIND: {task.kind}\n"
        f"OWNER: {agent.name}\n"
        f"GOAL: {mission.goal}\n"
        f"BRIEF: {task.brief}\n"
        f"ACCEPTANCE:\n{criteria}\n"
        f"{repair}\n"
        f"ROOM_FOR_YOU:\n{mentions or '(no messages addressed to you)'}\n\n"
        f"CONTEXT:\n{context or '(none yet)'}\n"
    )
    return system, user


def _context(mission: Mission) -> str:
    blocks = []
    for task in mission.tasks:
        if task.status == "done" and task.artifact:
            blocks.append(f"## {task.id} by {task.owner}\n{task.artifact}")
    return "\n\n".join(blocks)


def _apply(task: Task, outcome: tuple, mission: Mission, cfg: WorkshopConfig, room: Room) -> None:
    kind, payload = outcome
    if kind == "invalid":
        _reject(task, mission, room, str(payload))
        return
    turn: Turn = payload
    if task.kind == "retrieve":
        task.artifact = turn.artifact
        task.status = "done"
        task.turns += 1
        room.post("librarian", "artifact", _clip(turn.artifact, 1200), task.id)
        room.post("orchestrator", "status", f"Assigned next work after {task.id}.", task.id)
        return
    if turn.action == "yield":
        task.invalid_turns += 1
        task.last_error = "yield is silence; the assigned artifact is still missing"
        room.post(
            "orchestrator",
            "status",
            f"{task.owner} yielded on {task.id}; no message was posted.",
            task.id,
        )
        if task.invalid_turns >= mission.max_invalid_per_task:
            _fail_task(task, mission, f"{task.owner} yielded on {task.id} without doing the work")
        return
    if turn.action == "ask":
        room.post(task.owner, "question", turn.question or "", task.id)
        task.status = "blocked"
        mission.reason = f"{task.owner} asked one question and stopped: {turn.question}"
        return
    if turn.action in {"advance", "done"}:
        if task.artifact and turn.artifact.strip() == task.artifact.strip():
            _reject(task, mission, room, "artifact did not change")
            return
        task.artifact = turn.artifact
        task.turns += 1
        room.post(task.owner, "artifact", turn.artifact, task.id)
        if task.kind == "review":
            _apply_review(task, turn, mission, room)
            return
        ok, reason = evaluate(task, task.artifact)
        # The draft closes when the writer delivers it. The reviewer is the
        # completion gate, so a weak draft becomes one handoff, not a chat.
        if task.kind == "draft":
            task.status = "done"
            if ok:
                room.post("orchestrator", "status", f"{task.id} meets the brief checks.", task.id)
            else:
                room.post("orchestrator", "status", f"{task.id} handed to review with a gap: {reason}", task.id)
            return
        if ok:
            task.status = "done"
            room.post("orchestrator", "status", f"{task.id} accepted.", task.id)
            return
        if task.turns >= task.max_turns:
            _fail_task(task, mission, reason)
            return
        room.post("orchestrator", "status", f"{task.id} needs another work turn: {reason}", task.id)
        return
    _reject(task, mission, room, f"unhandled action {turn.action}")


def _apply_review(task: Task, turn: Turn, mission: Mission, room: Room) -> None:
    draft = _draft_under_review(mission, task)
    ok, reason = evaluate(_draft_task(mission, task), draft)
    decision = turn.decision or ("approve" if turn.action == "done" else "revise")
    task.status = "done"
    if decision == "approve" and ok:
        mission.outcome = "done"
        mission.reason = "reviewer approved the brief and the acceptance checks passed"
        room.post("orchestrator", "status", mission.reason, task.id)
        return
    critique = reason if decision == "approve" else (turn.note or reason)
    if decision == "approve" and not ok:
        critique = (
            "Reviewer said approve, but the brief missed an acceptance check. " + reason
        )
    if mission.revisions_used >= mission.max_revisions:
        mission.outcome = "failed"
        mission.reason = f"brief still fails after the revision budget: {critique}"
        room.post("orchestrator", "status", mission.reason, task.id)
        return
    mission.revisions_used += 1
    draft_id = f"draft_r{mission.revisions_used}"
    review_id = f"review_r{mission.revisions_used}"
    mission.tasks.append(
        Task(
            id=draft_id,
            title="Revise the brief",
            owner="writer",
            kind="draft",
            brief=f"REVISE: {critique}",
            acceptance=_draft_task(mission, task).acceptance,
            depends_on=(task.id,),
        )
    )
    mission.tasks.append(
        Task(
            id=review_id,
            title="Review the revision",
            owner="reviewer",
            kind="review",
            brief="Check the revised brief. Approve only if every acceptance line holds.",
            acceptance=("cites_knowledge",),
            depends_on=(draft_id,),
        )
    )
    room.post(
        "orchestrator",
        "status",
        f"Handoff: reviewer → writer for one revision ({draft_id}). {critique}",
        task.id,
    )


def _draft_under_review(mission: Mission, review: Task) -> str:
    for dep in review.depends_on:
        task = _by_id(mission, dep)
        if task and task.kind == "draft":
            return task.artifact
    return _latest_done(mission, "draft")


def _draft_task(mission: Mission, review: Task) -> Task:
    for dep in review.depends_on:
        task = _by_id(mission, dep)
        if task and task.kind == "draft":
            return task
    for task in reversed(mission.tasks):
        if task.kind == "draft":
            return task
    return review


def _reject(task: Task, mission: Mission, room: Room, detail: str) -> None:
    task.invalid_turns += 1
    task.last_error = detail
    room.post(
        "orchestrator",
        "trace",
        f"Rejected non-work turn on {task.id}: {detail}",
        task.id,
    )
    if task.invalid_turns >= mission.max_invalid_per_task:
        _fail_task(
            task,
            mission,
            f"idle or non-work output from {task.owner} on {task.id}: {detail}",
        )


def _fail_task(task: Task, mission: Mission, reason: str) -> None:
    task.status = "failed"
    mission.outcome = "failed"
    mission.reason = reason


def _by_id(mission: Mission, task_id: str) -> Task | None:
    for task in mission.tasks:
        if task.id == task_id:
            return task
    return None


def _latest_done(mission: Mission, kind: str) -> str:
    found = ""
    for task in mission.tasks:
        if task.kind == kind and task.status == "done" and task.artifact:
            found = task.artifact
    return found


def _finish_status(mission: Mission) -> str:
    if mission.outcome == "done":
        return "done"
    if any(task.kind == "review" and task.status == "done" for task in mission.tasks):
        # A review that already set outcome to done returns earlier.
        if mission.outcome == "running":
            return "failed"
    if all(task.status == "done" for task in mission.tasks) and mission.tasks:
        return "done" if _latest_done(mission, "draft") else "failed"
    return "failed"


def _finish_reason(mission: Mission) -> str:
    if mission.outcome == "done":
        return mission.reason or "mission complete"
    return mission.reason or "queue empty before the brief was approved"


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n…"


def write_run(report: RunReport, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    brief = directory / "brief.md"
    body = report.brief.strip()
    if report.status != "done":
        body = f"STATUS: {report.status}\n\n{report.reason}\n\n{body}".strip()
    brief.write_text(body + "\n", encoding="utf-8")
    (directory / "room.md").write_text(report.room.render(), encoding="utf-8")
    (directory / "trace.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return brief
