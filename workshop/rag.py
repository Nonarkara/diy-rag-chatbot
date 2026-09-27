"""Lexical retrieval over a local folder.

No LangChain, LlamaIndex, or Chroma. The librarian agent calls this
function; it does not invent passages. Embeddings stay optional and
are not required for the demo.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


_TOKEN = re.compile(r"[a-z0-9\u0e00-\u0e7f]{3,}", re.IGNORECASE)
_STOP = frozenset(
    """
    the and for with that this from are was were you your not but have has
    will into over only about what how who when where which than then them
    """.split()
)


@dataclass(frozen=True)
class Passage:
    path: str
    heading: str
    text: str
    score: int

    def cite(self) -> str:
        return f"knowledge/{self.path}" if not self.path.startswith("knowledge/") else self.path


def search(root: Path, query: str, k: int = 4) -> list[Passage]:
    if not root.is_dir():
        raise FileNotFoundError(f"knowledge folder not found: {root}")
    terms = _terms(query)
    found: list[Passage] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".md", ".txt"}:
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith("."):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for heading, body in _chunks(text):
            score = _score(terms, f"{heading}\n{body}\n{rel}")
            if score <= 0:
                continue
            found.append(
                Passage(path=rel, heading=heading.strip() or rel, text=body.strip(), score=score)
            )
    found.sort(key=lambda p: (-p.score, p.path))
    # Keep the best chunk per file first, then fill.
    picked: list[Passage] = []
    seen: set[str] = set()
    for passage in found:
        if passage.path in seen:
            continue
        picked.append(passage)
        seen.add(passage.path)
        if len(picked) >= k:
            break
    return picked


def format_passages(passages: list[Passage]) -> str:
    if not passages:
        return "NO_PASSAGES"
    blocks = []
    for passage in passages:
        excerpt = passage.text[:900].strip()
        blocks.append(
            f"SOURCE: {passage.cite()}\nHEADING: {passage.heading}\n{excerpt}"
        )
    return "\n\n".join(blocks)


def _chunks(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    heading = ""
    buf: list[str] = []
    chunks: list[tuple[str, str]] = []
    for line in lines:
        if line.startswith("#"):
            if buf:
                chunks.append((heading, "\n".join(buf)))
            heading = line.lstrip("#").strip()
            buf = []
        else:
            buf.append(line)
    if buf:
        chunks.append((heading, "\n".join(buf)))
    if not chunks:
        chunks.append(("", text))
    return chunks


def _terms(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN.findall(text) if t.lower() not in _STOP}


def _score(terms: set[str], text: str) -> int:
    if not terms:
        return 0
    hay = _terms(text)
    return len(terms & hay)
