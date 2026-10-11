# patterns/ — OOTBPAP patterns the agent reads

This directory holds the patterns the agent reads **before** writing
code. They are the source of truth for "how do I do X in this kit."

If you find yourself writing code that contradicts a pattern here,
the pattern is right and you are wrong. Update the pattern
afterwards, not before.

## What's in here

| File | Covers |
|---|---|
| [`local-llm-setup.md`](local-llm-setup.md) | How to default to Ollama, switch to OpenAI-compatible, what models work |
| [`rag.md`](rag.md) | Canonical RAG pattern: knowledge folder → retrieval → answer |
| [`api-integration.md`](api-integration.md) | LINE / Telegram / Discord / web webhook plumbing |
| [`state.md`](state.md) | Session state, JSON files, when to add a database |
| [`deployment.md`](deployment.md) | Local-only, Railway, Render, Cloudflare Pages, GitHub Pages |

## Read order

The kit's `AGENTS.md` says: **read the relevant pattern before
writing code**. If you're not sure which pattern applies, read
the `local-llm-setup.md` first — most decisions in this kit
cascade from the LLM provider choice.

## Adding a new pattern

1. Write it as `patterns/<topic>.md`.
2. Reference it from the kit's `AGENTS.md` if it's hot-path.
3. The next agent will pick it up.

Keep each pattern to ~200 lines. If it grows past that, split it.
