"""
verdict.py — verdict assembly + Telegram-safe chunking.

The orchestrator produces a `CouncilResult` dataclass with everything
that happened: the question, the panel composition, every persona's
contribution at every stage, the chairman synthesis, the disagreements.

This module turns that into:
  - a single Markdown `verdict_md` string (the canonical form, what
    `bin/council` would also produce on the host CLI side)
  - a list of Telegram-safe `chunks`, each ≤ 4000 chars (Telegram's
    limit is 4096, we leave a margin for the bot's header text and
    for any entity markers Telegram adds).

The chunking rule: split at section boundaries first (`---\\n` or
`\\n## `), then by character if a section is still too long. The
order of sections is stable so a follow-up message always continues
where the previous one left off.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .personas import Persona


# ---------- result data ----------

@dataclass
class StageRecord:
    persona_name: str
    figure: str
    stage: str        # "01" | "02" | "03"
    label: str        # "Independent Analysis" | "Cross-Examination" | "Final Stance"
    content: str
    evidence_label: str = ""
    confidence: str = ""


@dataclass
class CouncilResult:
    question: str
    panel: list[Persona]
    records: list[StageRecord] = field(default_factory=list)
    synthesis: str = ""
    next_step: str = ""
    unresolved: list[str] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0
    provider_summary: str = ""  # e.g. "ollama:gemma4:e4b"

    def record(self, persona: Persona, stage: str, label: str, content: str,
               evidence_label: str = "", confidence: str = "") -> None:
        self.records.append(StageRecord(
            persona_name=persona.name,
            figure=persona.figure,
            stage=stage,
            label=label,
            content=content.strip(),
            evidence_label=evidence_label,
            confidence=confidence,
        ))


# ---------- markdown assembly ----------

def _extract_bullets(text: str, header_prefix: str) -> list[str]:
    """Pull lines starting with `header_prefix` (e.g. 'Disagree:' or '###')."""
    out: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(header_prefix):
            out.append(s)
    return out


def _evidence_and_confidence(content: str) -> tuple[str, str]:
    """Best-effort extraction of evidence label + confidence from a Stage 3 stance."""
    ev, conf = "", ""
    for line in content.splitlines():
        s = line.strip()
        if s.lower().startswith("evidence label:"):
            ev = s.split(":", 1)[1].strip()
        elif s.lower().startswith("evidence:"):
            ev = s.split(":", 1)[1].strip()
        elif s.lower().startswith("confidence:"):
            conf = s.split(":", 1)[1].strip()
    return ev, conf


def render_markdown(result: CouncilResult) -> str:
    """Build the canonical verdict markdown."""
    sections: list[str] = []

    # Header
    header_lines = [
        f"# Council verdict",
        f"",
        f"**Question:** {result.question}",
        f"",
        f"**Panel:** {', '.join(p.figure for p in result.panel)}",
        f"**Engine:** {result.provider_summary}",
        f"**Elapsed:** {result.elapsed_seconds:.1f}s",
        f"",
        "---",
        "",
    ]
    sections.append("\n".join(header_lines))

    # Per-persona, per-stage records (Stages 1, 2, 3)
    for persona in result.panel:
        persona_section = [f"## {persona.figure}  ·  `{persona.name}`", ""]
        any_record = False
        for rec in result.records:
            if rec.persona_name != persona.name:
                continue
            any_record = True
            persona_section.extend([
                f"### Stage {rec.stage} · {rec.label}",
                "",
                rec.content,
                "",
            ])
            if rec.evidence_label or rec.confidence:
                bits = []
                if rec.evidence_label:
                    bits.append(f"**Evidence:** `{rec.evidence_label}`")
                if rec.confidence:
                    bits.append(f"**Confidence:** {rec.confidence}")
                persona_section.append("  \n".join(bits) + "  \n")
                persona_section.append("")
        if any_record:
            persona_section.append("---")
            persona_section.append("")
            sections.append("\n".join(persona_section))

    # Stage 4: synthesis
    if result.synthesis:
        sections.append("## Stage 04 · Synthesis (the chairman)\n")
        sections.append(result.synthesis.strip() + "\n")
        sections.append("---")
        sections.append("")

    # Concrete next step
    if result.next_step:
        sections.append(f"## Concrete next step\n\n{result.next_step.strip()}\n")
        sections.append("---")
        sections.append("")

    # Disagreements (extracted from Stage 2 records)
    if result.disagreements:
        sections.append("## Points of disagreement\n")
        for d in result.disagreements:
            sections.append(f"- {d}")
        sections.append("")
        sections.append("---")
        sections.append("")

    # Unresolved questions
    if result.unresolved:
        sections.append("## Unresolved questions\n")
        for u in result.unresolved:
            sections.append(f"- {u}")
        sections.append("")

    return "\n".join(sections)


# ---------- telegram chunking ----------

# Telegram's hard limit is 4096 chars per text message. We use 3800 as a
# safety margin (the bot might wrap in italics/bold entities that count
# toward the limit too).
TELEGRAM_CHUNK_LIMIT = 3800


def chunk_for_telegram(md: str, limit: int = TELEGRAM_CHUNK_LIMIT) -> list[str]:
    """Split a Markdown verdict into Telegram-safe chunks.

    Order of preferences for the split point:
      1. The nearest '\\n---\\n' before the limit
      2. The nearest '\\n## ' before the limit
      3. The nearest '\\n\\n' before the limit
      4. Hard character split (last resort)

    Each chunk is annotated with `(N/M)` if there's more than one.
    """
    if len(md) <= limit:
        return [md]

    chunks: list[str] = []
    rest = md
    while len(rest) > limit:
        # Try each split rule in order
        cut = -1
        for sep in ["\n---\n", "\n## ", "\n### ", "\n\n"]:
            idx = rest.rfind(sep, 0, limit)
            if idx > cut:
                cut = idx + len(sep)
        if cut <= 0:
            cut = limit  # hard split
        chunk, rest = rest[:cut].rstrip(), rest[cut:].lstrip()
        chunks.append(chunk)

    if rest:
        chunks.append(rest)

    # Annotate with (N/M)
    total = len(chunks)
    if total > 1:
        chunks = [f"{c}\n\n_(part {i+1}/{total})_" for i, c in enumerate(chunks)]
    return chunks
