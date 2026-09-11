# bot/ — in-process council + Telegram adapter

This package is the **deployable council**: one Telegram bot, one
Python process, the deliberation happens **inside** the process. End
users who message the bot get the same multi-perspective verdict that
the repo owner gets from the vendored 0xNyk skill — but they don't
need Claude Code, OpenCode, or any subagent-capable host CLI.

## Why this exists

A previous attempt to build an "AI council" on Telegram used
**multiple bots**, one per persona. That failed because Telegram
bots cannot initiate messages to other bots — they are user-like
accounts that only respond to messages users send to them. The
"council" became N parallel siloed answers, not a deliberation.

The right architecture: **one bot, one process, N personas as
in-process LLM calls**. The channel is the mouth; the bot is the
brain; the personas are subagent calls within the brain.

## How it runs

```
┌─────────────────────────────────────────────────────┐
│  Telegram user                                      │
│     │  /council <question>                          │
│     ▼                                               │
│  python-telegram-bot                                │
│     │                                               │
│     ▼                                               │
│  bot.telegram  ──►  bot.core.run_council()          │
│                       │                             │
│                       ├──► bot.personas  (19 loaded)│
│                       ├──► bot.llm      (Ollama…)   │
│                       └──► bot.verdict  (chunked)   │
│     │                                               │
│     ▼                                               │
│  Telegram reply  (verdict, 1-N messages)            │
└─────────────────────────────────────────────────────┘
```

All 5 stages run inside the bot's process. Total wall time on a
warm Ollama `qwen3:4b`: ~2–4 minutes for a 5-persona panel.

## Install & run

```bash
# 1. Add python-telegram-bot to your env (already in requirements.txt)
pip install -r requirements.txt

# 2. Create a Telegram bot via @BotFather, copy the token
#    See: https://core.telegram.org/bots#how-do-i-create-a-bot

# 3. Set environment variables
export TELEGRAM_BOT_TOKEN=123456:ABC-DEF...
export LLM_PROVIDER=ollama         # default
export LLM_MODEL=qwen3:4b          # or gemma4:e4b, etc.

# 4. Start the bot
python -m bot
```

That's it. Message the bot on Telegram. `/council <your question>`
or just send a question in a DM.

## Environment variables

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | yes | — | The bot token from @BotFather |
| `TELEGRAM_ALLOWED_USERS` | no | (empty = everyone) | Comma-separated Telegram user IDs. If set, the bot ignores messages from other users. Useful for keeping the bot private during testing. |
| `LLM_PROVIDER` | no | `ollama` | `ollama` or `openai` (covers OpenAI, Groq, Together, OpenRouter, LM Studio) |
| `LLM_MODEL` | no | `gemma4:e4b` (ollama) / `gpt-4o-mini` (openai) | Model name |
| `LLM_API_KEY` | yes for `openai` | — | Bearer token |
| `LLM_BASE_URL` | no | provider default | Override for non-OpenAI OpenAI-compatible endpoints (e.g. `https://api.groq.com/openai`) |
| `LLM_TEMPERATURE` | no | `0.4` | |
| `LLM_MAX_TOKENS` | no | `1200` | Per LLM call |

## LLM provider notes

- **Ollama (default)** — local, free. Must be running at
  `http://localhost:11434`. Pull a model first: `ollama pull qwen3:4b`.
  Cold-load latency: 5–30 seconds on first call.
- **OpenAI** — `https://api.openai.com/v1`. Requires an API key.
- **Groq** — OpenAI-compatible. Set `LLM_BASE_URL=https://api.groq.com/openai`
  and `LLM_MODEL=llama-3.1-8b-instant`. Free tier available.
- **OpenRouter / Together / LM Studio** — same shape as OpenAI;
  set `LLM_BASE_URL` and `LLM_API_KEY`.

Gemini and Anthropic providers are stubbed (`TODO` in `llm.py`) —
the shape is straightforward to add when needed.

## What the bot returns

The bot's reply has three parts:

1. A status message that edits in place as the council progresses
   (`🔵 Stage 01/04 …`, `🔵 Stage 02/04 …`, etc.)
2. The verdict markdown, split into ≤ 3800-char messages (Telegram's
   4096-char limit with a margin). The first message replaces the
   status; follow-up messages continue the verdict.
3. A short `✅ Council done in N.Ns · N personas · M message(s)`
   footer with hints.

The verdict itself has all the upstream 0xNyk sections:

- Header (question, panel, engine, elapsed)
- Per-persona Stage 01 / 02 / 03 records
- Stage 04 chairman synthesis (Verdict, Acceptable compromises,
  Kill criteria, Concrete next step, Unresolved questions)
- Points of disagreement (extracted from Stage 02)

## Default panel

For a typical question, the orchestrator picks:

- **profile:** `execution-lean` (5 personas)
- **triad:** `ship-now` (3 of the 5: torvalds, feynman, aurelius)
- **+ rag-curator** auto-added when the question's keywords match
  `retrieval | knowledge | rag | embedding | faithfulness`

To see the active panel: send `/panel` to the bot.

## Run the orchestrator without the bot

```bash
python -m bot --core-smoke "your question here"
```

Useful for sanity-checking the LLM wiring before involving Telegram.

## Adding more channels

The orchestrator (`bot/core.py`) is channel-agnostic. To add Discord,
Slack, or a web `/council` endpoint:

1. Copy `bot/telegram.py` → `bot/discord.py` (or whatever)
2. Replace the Telegram-specific calls (`update.message.reply_text`,
   `chat.send_message`, etc.) with the new platform's calls
3. Keep `core.py`, `llm.py`, `personas.py`, `verdict.py` untouched
4. Wire the new entry point into `__main__.py` if you want it
   reachable via `python -m bot --discord`

The verdict markdown is the canonical form. `chunk_for_telegram()`
becomes `chunk_for_slack()` etc. with a different character limit.

## Files in this folder

| File | What |
|---|---|
| `__init__.py` | Package marker + design-rationale docstring |
| `__main__.py` | Entry point (`python -m bot`); also `python -m bot --core-smoke` |
| `llm.py` | Multi-provider LLM client (Ollama + OpenAI-compatible) |
| `personas.py` | Load 19 personas from `council/agents/` + panel selection |
| `verdict.py` | Verdict assembly + Telegram-safe chunking |
| `core.py` | The 5-stage orchestrator (channel-agnostic) |
| `telegram.py` | The python-telegram-bot adapter |
| `README.md` | This file |

## Provenance

- Vendored at: `bot/` in `diy-rag-chatbot`
- Depends on: `council/` (vendored, MIT), `python-telegram-bot` (LGPLv3+),
  `httpx` (BSD-3), `PyYAML` (MIT)
- License of `bot/`: MIT (Non Arkaraprasertkul)
