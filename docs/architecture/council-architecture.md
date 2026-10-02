# Council architecture

![hero](hero.svg)

This repo ships a host-CLI council skill, an adapter for a separately installed multi-model app, and a Python Telegram council. It does not ship the LINE RAG runtime. The two documented council patterns below share the same goal —
multi-perspective deliberation on hard questions — but they use
different machinery. Pick the right one per question.

| | 0xNyk council (vendored) | karpathy council (adapted) |
|---|---|---|
| Path in this repo | `council/` | `karpathy-council/` |
| Wrapper | `bin/council` | `bin/llm-council` |
| Engine | Prompt-only skill | Web app + OpenRouter API |
| Models | 1 LLM × 18 personas | N LLMs × 1 default persona each |
| Stages | 5 | 3 |
| Latency | 2–12 min (full) | 30–90 s (3 stages) |
| Cost | LLM tokens for the host | 3× OpenRouter tokens |
| Setup | One shell command | `git clone` upstream + `uv sync` + OpenRouter key |
| Output | Structured verdict with required sections | Synthesized prose + per-model transcripts |

## When to use which

```
RAG / bot / corpus / prompt question?
  └── yes → bin/council  (0xNyk with rag-curator)

Design / strategy / "what would other models think" question?
  └── yes → bin/llm-council  (karpathy, when its app is running)

Quick yes/no on a code change?
  └── yes → ask the host directly, no council

End user wants a verdict from a Telegram bot?
  └── yes → python -m bot  (single-orchestrator pattern, see below)
```

The shell wrappers use `council-sessions/`; the Python Telegram adapter does not write that session archive. `bin/council` creates a template where the operator must paste the verdict, not an automatic transcript capture.

---

## Why a single orchestrator (and not multiple bots)

A previous attempt to build an "AI council" on Telegram used
**multiple bots**, one per persona. That failed because Telegram
bots cannot initiate messages to other bots — they are user-like
accounts that can only respond to messages users send to them.
The "council" became N parallel siloed answers, not a deliberation.

The right architecture: **one bot, one process, N personas as
in-process LLM calls**. The channel is the mouth; the bot is the
brain; the personas are subagent calls within the brain.

![wrong-vs-right](wrong-vs-right.svg)

> See [`bot/README.md`](../../bot/README.md) for the deployable
> Telegram bot that ships this pattern out of the box.

---

## The 0xNyk 5-stage protocol

![the-five-stages](the-five-stages.svg)

The vendored skill at `council/` defines a fixed 5-round protocol
that runs inside a host CLI (Claude Code, OpenCode, Codex, or
Gemini CLI). One LLM, many personas (system prompts).

| Stage | What happens | Where it runs |
|---|---|---|
| **00 — parse + select panel** | Read `.council.yaml`, honor explicit CLI flags, pick a triad or full membership. | Host CLI, single call to coordinator |
| **01 — independent analysis** | Each persona writes its first analysis blind, 300 words, no reference to peers. | Parallel: N calls |
| **02 — cross-examination** | Each persona reads the others' positions and produces `Disagree:` + `Strengthened by:`. This is where dissent surfaces. | Parallel: N calls (anonymised peers) |
| **03 — final stance** | Each persona restates its position and labels its evidence + confidence. | Parallel: N calls |
| **04 — synthesis (the verdict)** | The coordinator produces the verdict with all required sections. The weighted tally is preserved — if the council is split, the verdict returns the split instead of manufacturing consensus. | Serial: 1 chairman call |

The RAG-specific persona `council-rag-curator` (this repo's local
addition) is auto-included on any question whose keywords match
`retrieval | knowledge | rag | embedding | faithfulness`. The host skill instructs it to inspect cited files and label evidence. The Python bot has no file-reading tools or retrieval step, so that instruction is not proof of grounding.

## The karpathy 3-stage protocol

The adapted pattern at `karpathy-council/` is a 3-stage multi-model
deliberation. Each stage runs in parallel across multiple LLM models
via OpenRouter. The two key tricks are *anonymization* (Stage 2) and
*chairman synthesis* (Stage 3).

- **Stage 01 — First opinions.** All council models answer
  independently. Their responses are tagged `Response A`, `B`, `C`,
  `…` so the next stage cannot play favorites.
- **Stage 02 — Review.** Each model receives all of the Stage 1
  responses (still anonymized) and produces a `FINAL RANKING:`
  block listing the responses from best to worst. The orchestrator
  parses these and computes the average rank per model.
- **Stage 03 — Chairman synthesis.** A designated Chairman model
  reads the Stage 1 answers + Stage 2 rankings and produces a
  single, well-reasoned final answer. This is the only serial step.

The full upstream app is a React + FastAPI web app you can run
locally on `:5173` (frontend) and `:8001` (backend). The wrapper
`bin/llm-council` in this repo probes `:8001` and either uses the
running app or falls back to the 0xNyk skill.

---

## Why this design wins

![why-this-wins](why-this-wins.svg)

The orchestrator pattern wins on four axes at once — and only on the
orchestrator pattern. The illustration is a conceptual comparison, not a benchmark. For the shipped Python bot:

| Approach | Breadth | Grounding | Synthesis | Cost | Deploys |
|---|---|---|---|---|---|
| Single LLM | 1 perspective | no evidence check | just the prose | $ per call | API only |
| Multi-bot Telegram | N bots in parallel | none — bots don't see each other | zero — no shared verdict | N × per-call | yes, no synthesis |
| RAG alone | 1 perspective on a corpus | folder-grounded | still one answer | 1× per call + retrieval | yes |
| **DIY Python council** | **N personas · staged calls** | **prompt + peer review; no folder retrieval** | **chairman synthesis** | **3N + 1 model calls** | **Telegram adapter only** |

For N personas, stages 01–03 each call the model N times, followed by one
chairman call: **3N + 1**. The default three-person panel therefore makes ten
calls; adding the curator makes thirteen. Running those calls in one Python
process does not combine their tokens into one request or make a hosted provider
free. Ollama avoids a hosted per-token bill but still uses memory and compute.

Cross-examination is not document retrieval. The current helper labels peers
“Member A” etc. while also including their figure names, so it is not a blinded
review. These are useful deliberation mechanics, not guarantees of evidence,
independence or correctness.

---

## How a question travels

For an `0xNyk` question:

```
your shell
  └─ bin/council "the question"
       └─ /council slash command  (host CLI resolves to ~/.claude/skills/council/SKILL.md)
            └─ 5-stage protocol runs inside the host LLM
                 └─ verdict printed to your terminal
                      └─ capture template written to council-sessions/<timestamp>-<slug>.md
```

For a `karpathy` question:

```
your shell
  └─ bin/llm-council "the question"
       ├─ probe http://localhost:8001/
       │    └─ 200 OK → POST to /api/query
       │                  └─ FastAPI runs the 3-stage orchestration
       │                       └─ OpenRouter calls 4+ models in parallel
       │                            └─ JSON response back to your terminal
       │                                 └─ capture written to council-sessions/<timestamp>-<slug>-karpathy.md
       └─ not reachable → fall back to bin/council (the 0xNyk path)
```

For a Telegram bot user:

```
a Telegram user
  └─ /council <question>  (or a plain DM)
       └─ python-telegram-bot  (single process, one orchestrator)
            └─ bot.telegram using shared bot.core stage helpers
                 ├─ Stage 01: N parallel LLM calls
                 ├─ Stage 02: N parallel LLM calls (peer-labelled, figures visible)
                 ├─ Stage 03: N parallel LLM calls
                 └─ Stage 04: 1 chairman synthesis call
                      └─ verdict markdown → 3800-char splits + part labels
                           └─ one or more Telegram replies
```

The fallback in `bin/llm-council` is the safety net. The in-process
orchestrator in `bot/` is the deployment that doesn't need a host
CLI at all — it's just Python and Ollama.

---

## Files in this folder

### Illustrations (manga + MoMA)

| File | What |
|---|---|
| `hero.svg` | The orchestrator as a manga-passionate figure with persona echoes + amber verdict beam |
| `wrong-vs-right.svg` | Multi-bot Telegram chaos vs single-orchestrator harmony |
| `the-five-stages.svg` | 5-panel manga page for the 0xNyk protocol |
| `why-this-wins.svg` | 4-row comparison: single-LLM / multi-bot / RAG / orchestrator |
| `flow-0xnyk-council.svg` | Clean editorial flow diagram for the 0xNyk protocol |
| `flow-karpathy-council.svg` | Clean editorial flow diagram for the karpathy protocol |
| `flow-comparison.svg` | Side-by-side flow comparison |
| `ILLUSTRATIONS.md` | Index page with rendering notes |

### The explainer

| File | What |
|---|---|
| `council-architecture.md` | This document |

### Where the engine actually lives

| Engine | Path |
|---|---|
| 0xNyk council skill | `../../council/` (vendored) |
| karpathy council pattern | `../../karpathy-council/` (adapted) |
| In-process orchestrator | `../../bot/` (Telegram adapter + core) |
| Project defaults | `../../.council.yaml` |

## Why this is on par with top AI-council repos

There are three projects the rest of the world calls "AI council":

- **[0xNyk/council-of-high-intelligence](https://github.com/0xnyk/council-of-high-intelligence)** — 4.2k stars. 18 personas, 5-stage protocol, runs in a host CLI.
- **[karpathy/llm-council](https://github.com/karpathy/llm-council)** — 24.8k stars. Multi-model parallel + review + chairman, web app + OpenRouter.
- **This repo, `Nonarkara/diy-rag-chatbot`** — the orchestrator pattern as a deployable Telegram bot. The single-process, multi-persona architecture.

What we add that the other two do not:

- **A RAG-specific 19th persona** (`council-rag-curator`) that asks a capable host agent to inspect evidence. The Python bot has no retrieval/file tools. The 0xNyk personas are general-purpose; this one is for *this* domain.
- **A `bin/llm-council` shim** that auto-detects whether the karpathy app is up and falls back to 0xNyk otherwise. Neither of the upstream projects have a fallback path.
- **A Telegram deployable bot** (`bot/`) that runs the same 0xNyk protocol in-process. 0xNyk requires a host CLI; karpathy requires a separate web app. This repo provides the `python -m bot` entry point; dependencies, model/channel configuration and access-control review remain required.
- **The single-orchestrator pattern as a documented anti-pattern fix** for the multi-bot Telegram failure mode. Anyone who has tried the multi-bot approach has hit the same wall.

What we share:

- The same 5-stage 0xNyk protocol (vendored, MIT).
- The same 3-stage karpathy pattern (vendored as text, MIT-style upstream).
- The same 18 personas (vendored, MIT).
- The same verdict discipline (kill criteria, dissent preserved, concrete next step).

This repo is not a fork of either. It is a third project that
**adopts both patterns** and ships them in a deployable form for
end users, with the lessons of trying (and failing) the multi-bot
approach documented as a guard against the same failure repeating.
