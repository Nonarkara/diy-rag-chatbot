# Claude Code

Read `AGENTS.md` first — that is the canonical entry contract for
any agent. This file is the Claude Code–specific pointer.

## What to do in this folder

1. Open this folder in Claude Code (or any compatible agent).
2. Read `AGENTS.md`.
3. Tell the owner what the kit can do, then run `./bin/scaffold
   --help` to see the scaffolder's options.
4. When the owner says "build me X", follow AGENTS.md Shape 1.

## If the owner points you at a project folder (not this kit)

Read the project's own `AGENTS.md`. It overrides this file.

## Don't

- Don't edit `AGENTS.md`, `CLAUDE.md`, or the `bin/scaffold`
  script silently. Tell the owner first.
- Don't add new packages to `requirements.txt` without flagging it.
- Don't push to a remote.

## TL;DR

`./bin/scaffold --type chatbot --name my-assistant && cd my-assistant && ./bin/start`

That's the magic.
