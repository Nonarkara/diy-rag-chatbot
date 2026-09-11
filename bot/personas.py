"""
personas.py — load the 19 persona contracts from council/agents/.

The vendored `council/` ships 18 upstream personas (council-aristotle
through council-watts). This repo adds one more, council-rag-curator,
which is domain-specific to RAG/chatbot decisions and is
auto-included when the question matches its duo_keywords.

Each persona is a markdown file with a YAML frontmatter (model,
color, tools, council metadata) and a body that has four sections:

    ## Identity
    ## Grounding Protocol
    ## Analytical Method
    ## Output Format (Council Round 2)
    ## Output Format (Standalone)

For the bot, we extract:
  - The name (from frontmatter or filename)
  - The figure / domain / polarity (from frontmatter `council:` block)
  - The full body text as the `system_prompt` (all four sections
    concatenated). The orchestrator doesn't need to parse them; the
    LLM does.

Each persona is small (~2-7 KB), so loading all 19 is cheap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ---------- the dataclass ----------

@dataclass
class Persona:
    name: str
    figure: str
    domain: str
    polarity: str
    triads: list[str] = field(default_factory=list)
    duo_keywords: list[str] = field(default_factory=list)
    profiles: list[str] = field(default_factory=list)
    color: str = "gray"
    default_model: str = "sonnet"
    system_prompt: str = ""
    raw_frontmatter: dict[str, Any] = field(default_factory=dict)
    source_path: Path | None = None

    @property
    def is_rag_curator(self) -> bool:
        return self.name == "council-rag-curator"

    def matches_question(self, question: str) -> bool:
        """True if any of this persona's duo_keywords appears in the question."""
        if not self.duo_keywords:
            return False
        q = question.lower()
        return any(kw.lower() in q for kw in self.duo_keywords)


# ---------- the loader ----------

_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<yaml>.*?)\n---\s*\n(?P<body>.*)\Z",
    re.DOTALL,
)


def _parse_persona_file(path: Path) -> Persona:
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(
            f"{path.name} has no YAML frontmatter. "
            f"Expected `---\\n...\\n---` at the top."
        )
    try:
        fm = yaml.safe_load(m.group("yaml")) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"{path.name} frontmatter is not valid YAML: {exc}") from exc
    council = fm.get("council") or {}
    name = fm.get("name") or path.stem
    return Persona(
        name=name,
        figure=str(council.get("figure", name)),
        domain=str(council.get("domain", "")),
        polarity=str(council.get("polarity", "")),
        triads=list(council.get("triads", [])),
        duo_keywords=list(council.get("duo_keywords", [])),
        profiles=list(council.get("profiles", [])),
        color=str(fm.get("color", "gray")),
        default_model=str(fm.get("model", "sonnet")),
        system_prompt=m.group("body").strip(),
        raw_frontmatter=fm,
        source_path=path,
    )


def load_all_personas(agents_dir: Path | None = None) -> list[Persona]:
    """Load every council-*.md under council/agents/."""
    if agents_dir is None:
        # Default to <repo>/council/agents/
        repo_root = Path(__file__).resolve().parent.parent
        agents_dir = repo_root / "council" / "agents"
    if not agents_dir.is_dir():
        raise FileNotFoundError(
            f"council/agents/ directory not found at {agents_dir}. "
            f"Is the council skill vendored?"
        )
    personas: list[Persona] = []
    for path in sorted(agents_dir.glob("council-*.md")):
        try:
            personas.append(_parse_persona_file(path))
        except ValueError as exc:
            # Surface a clear error and continue with the rest.
            print(f"[personas] WARNING: {exc}")
    if not personas:
        raise RuntimeError(
            f"No persona files found under {agents_dir}. "
            f"Expected `council-*.md`."
        )
    return personas


# ---------- panel selection ----------

# Default triad mappings (mirror the upstream SKILL.md "Pre-defined Triads"
# but reduced to the triads the bot supports). The upstream list is in
# council/SKILL.md and is the source of truth.

EXECUTION_LEAN_MEMBERS = {"torvalds", "feynman", "sun-tzu", "aurelius", "ada"}
SHIP_NOW_TRIAD = ["torvalds", "feynman", "aurelius"]


def select_panel(
    personas: list[Persona],
    *,
    profile: str = "execution-lean",
    triad: str | None = "ship-now",
    include_rag_curator: bool = True,
    question: str | None = None,
) -> list[Persona]:
    """Pick the personas for a council session.

    Defaults to profile=execution-lean (5 personas) + triad=ship-now
    (3 of those 5) + the rag-curator if the question matches.
    The upstream `.council.yaml` is honored by `__main__.py` before
    calling this function.
    """
    by_name = {p.name.removeprefix("council-"): p for p in personas}

    if profile == "execution-lean":
        chosen_names = EXECUTION_LEAN_MEMBERS
    elif profile == "classic":
        chosen_names = {p.name.removeprefix("council-") for p in personas}
    else:
        raise ValueError(
            f"Unknown profile={profile!r}. Supported: 'execution-lean', 'classic'"
        )

    chosen = [by_name[n] for n in chosen_names if n in by_name]
    if triad:
        if triad == "ship-now":
            triad_names = SHIP_NOW_TRIAD
        else:
            # Unknown triad → fall back to all-panel; bot logs it.
            triad_names = None
        if triad_names:
            chosen = [p for p in chosen if p.name.removeprefix("council-") in triad_names]

    # Auto-include rag-curator when the question matches its duo_keywords
    if include_rag_curator and question:
        for p in personas:
            if p.is_rag_curator and p.matches_question(question):
                if p not in chosen:
                    chosen.append(p)

    if not chosen:
        raise RuntimeError("Panel selection produced an empty list. Check the profile/triad.")
    return chosen


# ---------- module self-test ----------

if __name__ == "__main__":
    personas = load_all_personas()
    print(f"[personas] loaded {len(personas)} personas:")
    for p in personas:
        kw = f" kw={','.join(p.duo_keywords)}" if p.duo_keywords else ""
        print(f"  - {p.name:30s}  figure={p.figure!r:30s}  domain={p.domain!r}{kw}")
    print()
    panel = select_panel(personas, question="Is the embedding retrieval correct?")
    print(f"[personas] execution-lean + ship-now panel for that question:")
    for p in panel:
        print(f"  * {p.name}")
