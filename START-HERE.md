# Start here — 30-second quickstart

## Step 1 · Clone the kit

```bash
git clone https://github.com/Nonarkara/diy-rag-chatbot.git vibecoding-kit
cd vibecoding-kit
```

## Step 2 · Make sure a local LLM is running (optional but recommended)

The kit works with any OpenAI-compatible endpoint. Default is Ollama
on `http://localhost:11434` — free, offline.

```bash
# Install Ollama: https://ollama.com/download
ollama serve                       # background
ollama pull qwen3:4b               # or gemma4:e4b, llama3.2:3b, etc.
```

If you don't want a local LLM, set `LLM_PROVIDER=openai` and a key
in `.env`. The kit never requires this for the first run.

## Step 3 · Scaffold a project

```bash
./bin/scaffold --type chatbot --name my-assistant
cd my-assistant
```

Available scaffold types: `chatbot`, `dashboard`, `webpage`, `file-system`.

The scaffolder will:
1. Copy the right template into `./my-assistant/`
2. Drop a starter `knowledge/` folder (chatbot, dashboard)
3. Print what to do next

Run `./bin/scaffold --help` for all options.

## Step 4 · Open an agent in the new project

```bash
cd my-assistant
claude             # or: opencode, codex, gemini
```

Tell the agent what you want. The project's own `AGENTS.md` will
guide it. Examples:

> "Add a /reset command that clears the conversation history."
>
> "Wire the dashboard to my reading-list.csv at /Users/me/reading.csv."
>
> "Add a search bar to the webpage."

## Step 5 · Run it

```bash
./bin/start
```

That's it. Iterate.

## Need a council for a hard question?

```bash
# From the kit root
./bin/council "Should we add streaming responses to the chatbot?"
./bin/council --quick --triad ship-now "Ship today with the flaky test?"
./bin/council --duo --members torvalds,rams "Is the prompt under 1,500 chars?"
```

The council runs 5 stages (independent → cross-examine → final →
synthesis) with 19 personas. See `council/SKILL.md` for the full
protocol.

## Want to add a new project template?

1. Create `templates/<your-type>/` with the same shape as the
   existing ones (`README.md`, `AGENTS.md`, `starter/`).
2. The scaffolder will discover it automatically.
3. Tell the owner to run `./bin/scaffold --list` to see the new option.

## Want to add a knowledge pattern?

1. Write it as `knowledge/patterns/<topic>.md`.
2. Reference it from `AGENTS.md` "Read order" if it's hot path.
3. The next agent will pick it up.
