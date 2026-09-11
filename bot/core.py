"""
core.py — the 5-stage council orchestrator.

This is the channel-agnostic brain. Telegram calls it, a future Discord
adapter will call it, the web demo can call it, even a cron job can
call it. The orchestrator knows nothing about messaging; it just runs
the protocol and returns a `CouncilResult`.

Stages
------

  00  Parse + select panel
        Read defaults (env-supplied profile + triad), pick the panel,
        auto-include rag-curator if the question matches.

  01  Independent analysis
        Each persona analyses the question blind. No reference to
        peers. ~300 words each. Run in parallel.

  02  Cross-examination
        Each persona reads the other personas' Stage 01 outputs and
        writes Disagree / Strengthened. Run in parallel.

  03  Final stance
        Each persona restates its position after seeing the cross-
        examination, with an evidence label and confidence. Run in
        parallel.

  04  Synthesis (the chairman)
        One designated persona (default: first in panel, or whoever
        has 'chairman' polarity in the panel — currently none) reads
        everything and produces the final synthesis, including a
        concrete next step and the unresolved questions.

All persona calls run via the same `LLMClient.complete(system, user)`
interface — see `bot.llm`. Parallelism uses `concurrent.futures.
ThreadPoolExecutor` because the LLM calls are network-bound and the
GIL is not the bottleneck.
"""

from __future__ import annotations

import concurrent.futures
import re
import time
from dataclasses import dataclass

from .llm import LLMClient
from .personas import Persona, load_all_personas, select_panel
from .verdict import CouncilResult, _extract_bullets, _evidence_and_confidence


# ---------- knobs ----------

DEFAULT_PROFILE = "execution-lean"
DEFAULT_TRIAD = "ship-now"
MAX_WORKERS = 6               # parallel persona calls per stage
STAGE_WORD_LIMITS = {         # soft caps the personas are told about
    "01": 280,
    "02": 220,
    "03": 200,
    "04": 500,
}


# ---------- stage prompts ----------

def _stage01_prompt(question: str, word_limit: int) -> str:
    return f"""A council has been convened to answer this question. You are one
member. Analyse it INDEPENDENTLY — do not reference other members,
you have not seen their answers.

QUESTION:
{question}

Your response is your independent first analysis. Stay under
{word_limit} words. Use the "Output Format (Council Round 1)" from
your Identity section: restate the problem in your own terms, give
your analysis, and end with a one-sentence position.

Do not preamble. Do not sign your name. Speak as your character."""


def _stage02_prompt(question: str, stage01_block: str, word_limit: int) -> str:
    return f"""Cross-examination. You will now see what the other council members
wrote in Stage 1 (anonymised — they are "Member A", "Member B", etc.
to keep the cross-examination honest). Respond to them.

QUESTION:
{question}

STAGE 1 — OTHER MEMBERS' POSITIONS:
{stage01_block}

Required format (under {word_limit} words):

### Disagree: <member label>
<the strongest disagreement you have with that position>

### Strengthened by: <member label>
<where another member's argument supports or sharpens yours>

### Open question
<one thing you want another member to clarify>

You may name multiple "Disagree:" lines if you disagree with more than
one member. Speak as your character."""


def _stage03_prompt(question: str, stage02_block: str, word_limit: int) -> str:
    return f"""Final stance. You have seen the Stage 2 cross-examination.
Restate your position now that you have heard your peers.

QUESTION:
{question}

STAGE 2 — CROSS-EXAMINATION:
{stage02_block}

Required format (under {word_limit} words):

### Position Update
<your restated position. Note any changes from Stage 1.>

### Evidence Label
<one of: empirical | mechanistic | strategic | ethical | heuristic
(plus EVIDENCED / INFERRED / ASSUMED / MISSING if your identity uses
those labels)>

### Confidence
<High | Medium | Low — with a one-line reason>

Speak as your character."""


def _stage04_chairman_prompt(question: str, panel: list[Persona],
                             stage01_block: str, stage02_block: str,
                             stage03_block: str, word_limit: int) -> str:
    names = ", ".join(p.figure for p in panel)
    return f"""You are the Chairman of an LLM Council. You have read every
member's Stage 1 analysis, Stage 2 cross-examination, and Stage 3
final stance. Your job is to synthesise everything into the council's
verdict.

QUESTION:
{question}

COUNCIL: {names}

STAGE 1 — INDEPENDENT ANALYSES:
{stage01_block}

STAGE 2 — CROSS-EXAMINATION:
{stage02_block}

STAGE 3 — FINAL STANCES:
{stage03_block}

Required format (under {word_limit} words):

## Verdict (lead with this)
<the council's recommendation. One paragraph. State the
recommendation, then the single strongest reason, then the
single biggest risk.>

## Acceptable compromises
<what the council would accept as a fallback if the primary
recommendation is blocked. Bullets.>

## Kill criteria
<conditions under which the council reverses this verdict.
Bullets.>

## Concrete next step
<one specific action, with an owner if obvious. One or two
sentences.>

## Unresolved questions
<questions the council did NOT resolve. Be specific.>

Do not preamble. Do not sign your name."""


# ---------- helpers ----------

def _strip_label(line: str) -> str:
    """Strip the section header from a Disagree/Strengthened line."""
    return re.sub(r"^###?\s*[^:]*:\s*", "", line).strip()


def _anonymise_stage01(records: list[tuple[Persona, str]]) -> tuple[str, dict[str, Persona]]:
    """Return (block, label_map). Anonymise each persona as Member A, B, C, ..."""
    block_lines: list[str] = []
    label_map: dict[str, Persona] = {}
    for i, (persona, content) in enumerate(records):
        label = f"Member {chr(65 + i)}"
        label_map[label] = persona
        block_lines.append(f"### {label} ({persona.figure})")
        block_lines.append("")
        block_lines.append(content.strip())
        block_lines.append("")
    return "\n".join(block_lines), label_map


def _stage_records_to_block(records: list[tuple[str, str]]) -> str:
    """Combine (persona_label, content) pairs into a single block."""
    lines: list[str] = []
    for label, content in records:
        lines.append(f"### {label}")
        lines.append("")
        lines.append(content.strip())
        lines.append("")
    return "\n".join(lines)


def _run_parallel(
    work_items: list,
    runner,
    max_workers: int = MAX_WORKERS,
) -> list:
    """Run `runner(item)` for each item in parallel. Preserve input order.

    `runner` is called with one argument. Exceptions are caught and
    surfaced as an empty string + a logged error so a single failed
    persona doesn't take down the whole stage.
    """
    results: list = [None] * len(work_items)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(runner, item): i
            for i, item in enumerate(work_items)
        }
        for fut in concurrent.futures.as_completed(futures):
            i = futures[fut]
            try:
                results[i] = fut.result()
            except Exception as exc:  # noqa: BLE001
                print(f"[core] persona call {i} failed: {type(exc).__name__}: {exc}")
                results[i] = ""
    return results


# ---------- the orchestrator ----------

@dataclass
class CouncilRequest:
    question: str
    profile: str = DEFAULT_PROFILE
    triad: str | None = DEFAULT_TRIAD
    include_rag_curator: bool = True


def run_council(
    request: CouncilRequest,
    llm: LLMClient,
    personas: list[Persona] | None = None,
) -> CouncilResult:
    """Run the full 5-stage protocol. Returns a `CouncilResult`."""
    started = time.monotonic()
    personas = personas or load_all_personas()
    panel = select_panel(
        personas,
        profile=request.profile,
        triad=request.triad,
        include_rag_curator=request.include_rag_curator,
        question=request.question,
    )

    result = CouncilResult(
        question=request.question,
        panel=panel,
        provider_summary=llm.describe(),
    )

    # Stage 01 — independent analysis (parallel)
    print(f"[core] stage 01: {len(panel)} personas, independent analysis")
    stage01_user_messages = [_stage01_prompt(request.question, STAGE_WORD_LIMITS["01"])
                             for _ in panel]

    def stage01_runner(args):
        persona, user_msg = args
        return llm.complete(system=persona.system_prompt, user=user_msg)

    stage01_contents = _run_parallel(
        list(zip(panel, stage01_user_messages)),
        stage01_runner,
    )
    for persona, content in zip(panel, stage01_contents):
        result.record(persona, "01", "Independent Analysis", content)

    # Anonymise Stage 01 for the cross-examination prompts
    stage01_block, label_map = _anonymise_stage01(
        list(zip(panel, stage01_contents))
    )

    # Stage 02 — cross-examination (parallel)
    print(f"[core] stage 02: cross-examination")
    def stage02_runner(persona: Persona) -> str:
        user_msg = _stage02_prompt(request.question, stage01_block, STAGE_WORD_LIMITS["02"])
        return llm.complete(system=persona.system_prompt, user=user_msg)

    stage02_contents = _run_parallel(panel, stage02_runner)
    for persona, content in zip(panel, stage02_contents):
        result.record(persona, "02", "Cross-Examination", content)

    # Extract disagreements for the verdict summary
    for persona, content in zip(panel, stage02_contents):
        for line in _extract_bullets(content, "### Disagree:"):
            result.disagreements.append(f"{persona.figure}: {_strip_label(line)}")

    # Stage 03 — final stance (parallel)
    print(f"[core] stage 03: final stance")
    stage02_block_for_03 = _stage_records_to_block(
        [(p.figure, c) for p, c in zip(panel, stage02_contents)]
    )
    def stage03_runner(persona: Persona) -> str:
        user_msg = _stage03_prompt(request.question, stage02_block_for_03,
                                   STAGE_WORD_LIMITS["03"])
        return llm.complete(system=persona.system_prompt, user=user_msg)

    stage03_contents = _run_parallel(panel, stage03_runner)
    for persona, content in zip(panel, stage03_contents):
        ev, conf = _evidence_and_confidence(content)
        result.record(persona, "03", "Final Stance", content,
                      evidence_label=ev, confidence=conf)

    # Stage 04 — chairman synthesis (serial, single call)
    print(f"[core] stage 04: chairman synthesis")
    chairman = panel[0]   # default chairman = first in panel (the leanest choice)
    stage03_block = _stage_records_to_block(
        [(p.figure, c) for p, c in zip(panel, stage03_contents)]
    )
    chairman_prompt_user = _stage04_chairman_prompt(
        question=request.question,
        panel=panel,
        stage01_block=stage01_block,
        stage02_block=stage02_block_for_03,
        stage03_block=stage03_block,
        word_limit=STAGE_WORD_LIMITS["04"],
    )
    # Use a "chairman" system prompt = a short overlay on top of the persona
    chairman_system = (
        chairman.system_prompt
        + "\n\n---\n\nFor this round, you are additionally the CHAIRMAN. "
        "Your job is to synthesise, not to advocate. Lead with the verdict, "
        "not with a defence of your own position."
    )
    synthesis = llm.complete(system=chairman_system, user=chairman_prompt_user)
    result.synthesis = synthesis.strip()

    # Extract concrete next step + unresolved questions from synthesis
    next_step = _extract_section(synthesis, "Concrete next step")
    unresolved_block = _extract_section(synthesis, "Unresolved questions")
    if next_step:
        result.next_step = next_step
    if unresolved_block:
        result.unresolved = [
            line.lstrip("- ").strip()
            for line in unresolved_block.splitlines()
            if line.strip().startswith("-")
        ]

    result.elapsed_seconds = time.monotonic() - started
    print(f"[core] council done in {result.elapsed_seconds:.1f}s")
    return result


def _extract_section(text: str, header: str) -> str:
    """Pull the body under a `## Header` heading until the next `## `."""
    lines = text.splitlines()
    out: list[str] = []
    capturing = False
    for line in lines:
        s = line.strip()
        if s.startswith("## ") and header.lower() in s.lower():
            capturing = True
            continue
        if capturing and s.startswith("## "):
            break
        if capturing:
            out.append(line)
    return "\n".join(out).strip()


# ---------- module self-test ----------

if __name__ == "__main__":
    """Run a quick smoke test: 3-persona panel, one short question."""
    import sys
    question = sys.argv[1] if len(sys.argv) > 1 else (
        "Should we drop the Smart City Thailand standards section "
        "from our knowledge folder to save embedding cost?"
    )
    print(f"[core] smoke test question: {question}")
    llm = LLMClient()
    print(f"[core] llm: {llm.describe()}")
    personas = load_all_personas()
    panel = select_panel(personas, question=question)
    print(f"[core] panel ({len(panel)}): {[p.name for p in panel]}")
    req = CouncilRequest(question=question)
    result = run_council(req, llm, personas=personas)
    print()
    print("=" * 70)
    print("VERDICT (synthesis only — full markdown in result)")
    print("=" * 70)
    print(result.synthesis[:1500])
    if result.next_step:
        print()
        print(f"Next step: {result.next_step[:300]}")
