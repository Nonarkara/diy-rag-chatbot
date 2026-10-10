# AGENTS.md — entry contract for any AI agent

You are an agent working in this repo. The owner cloned
[Nonarkara/diy-rag-chatbot](https://github.com/Nonarkara/diy-rag-chatbot)
— it is the **Vibecoding Kit (OTBPPS)**, not a chatbot tutorial.

## Read order — do not skip

1. **`README.md`** — what this kit is, what it ships, the four use cases.
2. **`knowledge/principles.md`** — the design rules you must follow.
3. **`knowledge/tools.md`** — what tools you have access to (and which you don't).
4. **`knowledge/patterns/`** — read the pattern(s) relevant to the current task before writing code.
5. **`bin/scaffold`** — run this when the owner asks you to build something new.
6. **`bin/council`** — run this when the owner has a decision that needs multi-perspective deliberation.

If the owner has already scaffolded a project folder, read the
project's own `AGENTS.md` first — that file is the contract for
THAT project, and it overrides the kit-level defaults where they
conflict.

## Your job, in three shapes

### Shape 1 · The owner asks you to build something new

> "Build me a chatbot that answers questions about X."
> "Scaffold me a dashboard for tracking Y."
> "Give me a webpage that does Z."

Your job:

1. Ask **one** clarifying question if the request is ambiguous. Ask about the *domain*, not the *tech stack* — the kit decides the tech stack.
2. Run `./bin/scaffold --type <chatbot|dashboard|webpage|file-system> --name <their-project>` from the repo root.
3. `cd` into the generated project folder.
4. Read the project's `AGENTS.md` and the matching `knowledge/patterns/*.md`.
5. Build. Run `./bin/start` to verify it boots.
6. Tell the owner what to do next.

Do NOT skip the scaffold step. Do NOT write project code in the kit
root — the kit stays clean. Do NOT require the owner to set up
cloud accounts, API keys, or databases for the first run.

### Shape 2 · The owner asks you to extend an existing project

> "Add a /reset command to the bot."
> "Add a new chart to the dashboard."
> "Add a CSV export to the file-system tool."

Your job:

1. Read the project's own `AGENTS.md`, `README.md`, and any
   `knowledge/` it has.
2. Read the matching `knowledge/patterns/*.md` for the change.
3. Make the change in the project folder.
4. Run the project's tests + start script.
5. Summarize the diff in plain language.

### Shape 3 · The owner asks a hard question

> "Should we add streaming responses?"
> "Should we drop the standards section?"
> "What's the right model to pick?"

Your job:

1. Do NOT answer from one perspective if the question has real
   downside. The user picked this kit specifically because the
   council is here.
2. Run `./bin/council "the question"` (or
   `./bin/council --duo --members torvalds,feynman "..."` for a
   faster 2-persona pass).
3. Summarize the verdict in plain Thai or English, with the
   concrete next step.

## What you MUST do

- **Read before you write.** The patterns in `knowledge/` are the source of truth. If you find yourself writing code that contradicts them, the pattern is right and you are wrong.
- **Local-first by default.** Use Ollama. The user opted into "no internet required" by cloning this kit. Don't ask for an OpenAI key unless they explicitly ask for it.
- **Stay in the project folder.** The kit root is read-only infrastructure. Generated projects live in sibling directories (`./my-assistant/`, `./my-dashboard/`, etc.).
- **Cite your evidence.** When you reference a file, name the file. When you make a claim, point at the code that supports it.
- **Test before you say done.** Run the project's test suite and the start script. Confirm it boots.

## What you MUST NOT do

- **Do NOT** rewrite `AGENTS.md` or `CLAUDE.md` without telling the owner. They are the contract.
- **Do NOT** add new packages to `requirements.txt` without flagging it. The kit is intentionally minimal.
- **Do NOT** edit `bin/scaffold` to add a new template silently. Add it via `templates/<new-type>/` and tell the owner to run `bin/scaffold --list` to see the new option.
- **Do NOT** push to a remote. The owner pushes.
- **Do NOT** claim something is in `knowledge/` if it isn't. If the pattern isn't there, write it and tell the owner.

## Tone

- Plain language. Short sentences. One screen per idea.
- If the owner is non-technical (they don't write code), assume that and explain what you're doing in plain terms.
- If the owner is technical, drop the explanation and show the diff.
- Thai or English, whatever they wrote.

## When you don't know

Read `knowledge/` first. If the answer isn't there, **say so
plainly** and propose writing the answer into `knowledge/` so the
next agent has it. Don't invent.

The kit is intentionally small. It grows by being fed real
patterns from real projects.
