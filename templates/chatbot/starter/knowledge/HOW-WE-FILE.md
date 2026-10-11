# How we file — knowledge format

Knowledge files are markdown. Each file is one topic.

## Format

```
## Q: <question in the user's language>

## A: <answer sourced only from the file body>

## Source: <where this info came from>
```

## Rules

1. **Bilingual Q/A is encouraged** — the bot answers in the language
   of the user's question, but the file can carry multiple Q lines
   in different languages for the same A.
2. **Keep `Q:` and `A:` lines in the same language** so the
   retrieval hits work.
3. **No website chrome** — strip headers, footers, sidebars from
   any pasted content. The bot will quote them otherwise.
4. **Refusals go in `examples/02-fallback.md`** so all bots from
   this template share the same refusal style.
5. **One topic per file.** If a file has more than ~5 questions,
   split it.

## Examples

See `examples/01-greeting.md` and `examples/02-fallback.md`.
