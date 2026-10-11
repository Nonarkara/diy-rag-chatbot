# Chatbot template

A FastAPI webhook chatbot that answers only from the `knowledge/`
folder. Works with LINE, Telegram, Discord, or a generic web
endpoint. Uses retrieval-augmented generation (RAG) with a local
embedding model.

## What's inside the generated project

```
my-assistant/
├── README.md           # this file (template copy)
├── AGENTS.md           # agent contract for THIS project
├── app.py              # FastAPI webhook server
├── knowledge/          # the bot's brain — fill this with your content
│   ├── HOW-WE-FILE.md  # file format guide
│   └── examples/       # starter Q/A pairs
├── requirements.txt
├── .env.example
└── bin/
    └── start           # local dev launcher
```

## How it works

1. A user messages the bot through any channel (LINE, Telegram,
   Discord, web).
2. The webhook hits `POST /webhook/<channel>` on this app.
3. The app retrieves the top-K most relevant files from
   `knowledge/`.
4. The retrieved context + the user's question are sent to the
   configured LLM (default: Ollama).
5. The LLM answer is returned to the user.

If the knowledge folder has nothing relevant, the bot is wired to
say so rather than guess. You can override the refusal message in
`app.py`.

## Run

```bash
./bin/start
```

The server listens on `http://127.0.0.1:8000` by default.

## Channels

Wire any channel you want by adding a handler:

- `POST /webhook/line` — see LINE Messaging API docs
- `POST /webhook/telegram` — see Telegram Bot API docs
- `POST /webhook/discord` — see Discord Interactions docs
- `POST /ask` — generic web form

Starter implements `/ask` and `/health` only. Add the channel you need.

## Configuration

Edit `.env` (copy from `.env.example`). All defaults work offline:

```
LLM_PROVIDER=ollama
LLM_MODEL=qwen3:4b
KNOWLEDGE_DIR=./knowledge
```

## Extend

Tell your agent: "extend this chatbot to also answer on LINE."
The kit's `patterns/api-integration.md` has the relevant patterns.
