# Vendored From

This `council/` directory is a vendored copy of
[council-of-high-intelligence](https://github.com/0xnyk/council-of-high-intelligence)
(MIT © 2026 [0xNyk](https://github.com/0xnyk)).

| Field | Value |
|---|---|
| Upstream version | 1.2.0 (2026-07-04) + Unreleased |
| Upstream SHA | `aacf75a7f21344ad2f3db821ff94e257e83a6fc0` |
| Vendored on | 2026-09-11 |
| Vendored by | Dr Non Arkaraprasertkul · [nonarkara.org](https://nonarkara.org) |
| Vendored for | `diy-rag-chatbot` — Thai LINE RAG chatbot |

## Why vendored (not submodule, not plugin)

- Anyone who clones `diy-rag-chatbot` immediately gets the full council protocol
  — no separate install step, no extra `git submodule update` to forget.
- The `agents/council-rag-curator.md` persona is a local addition that is
  useless outside a RAG project, so a submodule would not carry it.
- The user is **Dr Non**, the project is **diy-rag-chatbot**, and the
  sales motion is "working prototype as the contract" — every consumer
  of this repo gets a real demo of the council capability, not a
  deferred install.

## What was added on top of upstream

| Path | What | Why |
|---|---|---|
| `agents/council-rag-curator.md` | RAG-specific persona — "The Knowledge Curator" | Forces the council to reason about grounding, retrieval, refusal discipline, and the LINE message shape. The 18 upstream personas are general-purpose; this one is for *this* domain. |

## What was kept from upstream

Everything except:

- `.git/`
- `.github/` (upstream CI)
- `.markdownlint.json` (upstream lint)
- `.gitattributes`

Including assets/ (~5.5MB of jpegs and svgs that document the protocol).
If you want to slim it, delete `assets/header.jpeg`, `assets/social-preview.jpeg`,
and `assets/star-history-*.svg` — they are README visuals, not protocol.

## Hosts wired up

This repo currently has:

- **Claude Code** (`claude` on PATH) — primary host
- **OpenCode** (`opencode` on PATH) — secondary host

Not installed:

- Codex CLI
- Gemini CLI

To run a council in Claude Code, the `agents/council-*.md` and `council/SKILL.md`
files are still referenced from the upstream install paths (`~/.claude/`).
To wire them up locally:

```bash
# From the repo root
./council/install.sh
# or, dry-run first:
./council/install.sh --dry-run
```

To wire them up for OpenCode only:

```bash
./council/install.sh --opencode
```

## How to update this vendored copy

1. `cd` to a temp directory and `git clone https://github.com/0xnyk/council-of-high-intelligence.git`
2. Check the new SHA and version (`git rev-parse HEAD`, `head CHANGELOG.md`)
3. Diff the new contents against `council/` here; resolve any conflicts with `agents/council-rag-curator.md`
4. Replace `council/` with the new copy (preserving `council-rag-curator.md` and `VENDORED-FROM.md`)
5. Bump the version table at the top of this file
6. Commit

## License

The vendored content is MIT-licensed by 0xNyk.
See [`council/LICENSE`](./LICENSE) for the full text.
The local additions in this repo (e.g. `agents/council-rag-curator.md`,
this file) are MIT-licensed by Non Arkaraprasertkul and the
original diy-rag-chatbot authors.
