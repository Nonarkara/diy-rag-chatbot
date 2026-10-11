# Pattern: RAG (Retrieval-Augmented Generation)

RAG is the *only* knowledge architecture this kit supports. It is
the right tool for "answer questions from a folder of files" and
the wrong tool for everything else. Don't reach for it if the user
isn't asking about content from a folder.

## The shape

```
knowledge/                  ← the source of truth (markdown files)
    ↓ load
retrieval                   ← pick the top-K most relevant files
    ↓
prompt = system + question + retrieved context
    ↓
LLM                         ← answer only from the retrieved context
    ↓
refusal-or-answer
```

The hard part is the *refusal-or-answer* part. The bot must say "I
do not have that in this folder" when nothing relevant is
retrieved. Without that, the LLM will confabulate from training
data and the user will not know.

## File format (canonical)

See `templates/chatbot/starter/knowledge/HOW-WE-FILE.md` for the
full format. The short version:

```markdown
## Q: <question in user's language>
## Q: <other-language variant>

## A: <answer sourced only from this file>

## Source: <optional provenance>
```

Bilingual Q/A is encouraged. The bot answers in the language of the
user's question.

## Retrieval

Three options, in increasing quality:

1. **Keyword heuristic** (the default in `templates/chatbot/starter/app.py`):
   pick files whose body or name contains a word from the question.
   Free, no model, fast. Quality is mediocre.
2. **Embedding cosine similarity** (recommended for real use):
   embed each file once with `bge-m3` or `nomic-embed-text`, embed
   the question at query time, pick top-K by cosine. Quality is
   good. Latency: 1–2s per query on CPU.
3. **Cross-encoder re-ranking** (best, slowest):
   after top-K, re-rank with a cross-encoder. Quality is best.
   Latency: 200–500ms per re-rank. Overkill for most bot use.

The `templates/chatbot/starter/app.py` uses option 1. Replace
`simple_retrieve()` with an embedding-based version when you
outgrow it. The signature stays the same.

## Prompting

The system prompt must enforce three rules:

1. Answer only from the retrieved context.
2. Refuse when the context is empty or irrelevant.
3. Cite the file you used.

Example (from the starter):

```
You are a careful assistant. You answer ONLY using the files the
operator gave you. If the files do not contain the answer, reply
exactly: 'I do not have that in this folder.' Do not draw on
outside knowledge. Match the user's language. Be concise. Cite
the file you used.
```

## Common mistakes

- **No refusal message** — the LLM will confabulate. Always have
  the bot say "I do not have that in this folder" when retrieval
  is empty.
- **Windowing the answer but not the question** — if the
  retrieved context is longer than the model's context, the bot
  silently drops the question. Use a model with enough context
  (`qwen3:4b` has 32K, plenty for RAG).
- **Not citing the file** — the user can't audit the answer. Add
  the filename to the system prompt.
- **Embedding + answering in two steps** — you'll double the
  latency. Batch them when possible.

## The rag-curator persona

The kit ships a RAG-specific persona in `council/agents/council-rag-curator.md`.
Use it (via `bin/council` or the `bot/` Telegram bot) when
debugging a RAG pipeline: "why is the bot hallucinating on this
question?"
