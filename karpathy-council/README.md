# karpathy-council — 3-stage LLM Council (design pattern)

This folder documents the **3-stage LLM Council** pattern from
[karpathy/llm-council](https://github.com/karpathy/llm-council)
(commit `92e1fcc`, "Vibe Code Alert — 99% vibe coded as a fun Saturday
hack" by Andrej Karpathy).

It is **NOT a vendored copy of the source code**. The upstream repo
ships a FastAPI + React + OpenRouter web app; bringing all of that in
would bloat `diy-rag-chatbot` for a tool the user does not need to
run in this repo. Instead, this folder ships:

1. **[`prompts.md`](prompts.md)** — the three stage-prompts as plain
   text, so anyone can run a 3-stage council with their existing
   Claude Code / OpenCode / Codex / Gemini CLI.
2. **[`BIN-LLM-COUNCIL.md`](BIN-LLM-COUNCIL.md)** — how `bin/llm-council`
   in this repo integrates with the upstream karpathy app if it is
   running on `localhost:8001`.
3. **Provenance notes** — what is upstream, what is local, what is
   deliberately NOT vendored.

## What is the 3-stage pattern?

The karpathy council is a 3-stage deliberation. It uses **different
LLM models in parallel** (via OpenRouter), not personas on one model.

| Stage | What happens |
|---|---|
| 1. First opinions | All council models answer the question independently, in parallel. |
| 2. Review | Each model is given the other models' answers, **anonymized** as "Response A, B, C, …" so it can't play favorites. Each model produces a `FINAL RANKING:` of the responses. |
| 3. Final response | A designated "Chairman" model reads the Stage 1 answers + Stage 2 rankings and produces a single synthesized answer. |

## How it differs from the 0xNyk council (vendored in `council/`)

| | 0xNyk council (`council/`) | karpathy council (`karpathy-council/`) |
|---|---|---|
| Engine | Prompt-only, runs inside a host CLI (Claude Code, etc.) | Web app (FastAPI + React) + OpenRouter API |
| Models used | One LLM, many **personas** (system prompts) | Many LLMs, one **persona** per model |
| Stages | 5 (parse → independent analysis → cross-examination → final stance → synthesis) | 3 (first opinions → review → final) |
| Cost | Whatever the host charges per call | OpenRouter tokens × 3 stages |
| Latency | ~2–12 min for full 18-persona round | ~30–90 s for 3-stage round |
| Output | Long structured verdict with sections | Synthesized prose + the Stage 1/2 transcripts |
| Local-only | Yes — no API keys beyond the host CLI | No — needs OpenRouter API key + the web app running |
| Setup time | One `bin/council` install | `git clone` upstream + `uv sync` + frontend `npm install` + `OPENROUTER_API_KEY` |

The two systems are **complementary**:

- 0xNyk is for *hard, slow decisions* where you want 18 analytical
  lenses and a structured verdict with dissent, kill criteria, and
  unresolved questions. Use it before committing to a big refactor.
- Karpathy is for *fast "what do these models actually think"* runs
  where the cross-pollination of different model families is the
  value. Use it for design discussions, option enumeration, "should
  I be worried about X".

The user can run both. The wrapper `bin/llm-council` (in the parent
`bin/`) tries the karpathy app first, then falls back to the 0xNyk
council if the app is not running.

## What is deliberately NOT vendored

- The FastAPI backend (`backend/*.py`) — license is unclear (no
  LICENSE file upstream). The 3-stage *prompt text* in
  `prompts.md` is the design pattern, not the source code.
- The React + Vite frontend (`frontend/`) — heavy dependency tree
  (240K+ source, plus `node_modules` would be 100s of MB) for a UI
  the user does not need inside `diy-rag-chatbot`. Use the upstream
  if you want the chat UI.
- `header.jpg` (163K) — Karpathy's brand image for the upstream
  README. Not used here.
- `main.py`, `pyproject.toml`, `uv.lock` — the upstream runs the
  backend as a Python module. Not needed if you are not running the
  upstream app.

If you want the full upstream app, clone it separately:

```bash
git clone https://github.com/karpathy/llm-council.git ~/work/llm-council
cd ~/work/llm-council
# follow the upstream README
```

## When to use which (a one-page decision rule)

```
Question is about the bot's behavior / corpus / RAG?
  └── yes → bin/council  (0xNyk with rag-curator)
Question is about design / strategy / market / "what do others think"?
  └── yes → bin/llm-council --karpathy  (3-stage multi-model)
Question is about a quick yes/no on a code change?
  └── yes → ask the host directly, no council
```

## Provenance

- Upstream: <https://github.com/karpathy/llm-council>
- Upstream commit: `92e1fccb1bdcf1bab7221aa9ed90f9dc72529131`
- Upstream author: Andrej Karpathy
- Upstream license: **None declared** (no LICENSE file in the
  repository as of `92e1fcc`). Treat as "all rights reserved" by
  default; this folder ships the design pattern (text) and the
  integration shim (new code), NOT the upstream source.
- This folder is part of `diy-rag-chatbot`, MIT-licensed by
  Non Arkaraprasertkul.
