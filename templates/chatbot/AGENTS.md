# AGENTS.md — for THIS chatbot project

You are an agent working inside a project generated from the
`chatbot` template. The kit's entry contract is in
`<kit-root>/AGENTS.md`; that file is the global default. **This
file overrides it where they conflict.**

## Read order

1. **This file.**
2. `<kit-root>/knowledge/patterns/rag.md` — the canonical RAG
   pattern. Don't reinvent it.
3. `knowledge/HOW-WE-FILE.md` — the file format the bot expects.
4. `app.py` — the server. Understand it before extending.

## The bot's contract (do not violate)

1. **Answer only from `knowledge/`.** If a file is not present, the
   bot says so. It must NOT hallucinate, confabulate, or draw on
   training data.
2. **Match the user's language.** Thai question → Thai answer. The
   bot's default system prompt enforces this.
3. **Stay under the channel's message-length budget.** LINE is
   ~1,500 characters; Telegram is ~4,096; Discord is ~2,000; web is
   unbounded.
4. **Cite the file.** When the bot answers from a file, it should
   include the filename (or at least the section). This makes the
   answer auditable.
5. **Refuse politely.** A refusal is a feature, not a bug.

## How to extend this project

| Owner says... | You do |
|---|---|
| "Add LINE support" | Add a `/webhook/line` handler that verifies the LINE signature, then calls the same internal `answer(question, user_lang)` function. |
| "Add Telegram support" | Same shape with the python-telegram-bot webhook helper. |
| "Switch to OpenAI" | Edit `.env` — `LLM_PROVIDER=openai`, add `LLM_API_KEY`. The LLM client code is provider-agnostic. |
| "Add a /reset command" | Add a state store + `/reset` endpoint that wipes the user's session. |
| "Add streaming responses" | Switch to the LLM client's streaming mode + an SSE endpoint. |

## Knowledge file format

See `knowledge/HOW-WE-FILE.md`. Bilingual Q/A is encouraged:

```
## Q: <question>
## Q: <question in another language>

## A: <answer sourced only from the file body>

## Source: <optional provenance>
```

## Don't

- **Don't** add a second LLM client. The one in `app.py` is provider-agnostic.
- **Don't** add a database. Session state goes in memory or in a tiny JSON file.
- **Don't** rewrite `HOW-WE-FILE.md` to "improve" it — the kit owns it.
- **Don't** push to a remote. The owner pushes.

## Tone

The bot is a guide, not a chatter. Short sentences. Name the file it cited. Refuse when uncertain.
