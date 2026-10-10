# Templates

Each template is a working starter. `bin/scaffold` copies the
`starter/` folder (and the template-level `README.md` / `AGENTS.md`)
into the new project folder.

| Type | Best for | What you get |
|---|---|---|
| [`chatbot/`](chatbot/) | LINE / Telegram / Discord bots that answer from a knowledge folder | FastAPI webhook + RAG retrieval + starter `knowledge/` |
| [`dashboard/`](dashboard/) | Web dashboards with CSV/JSON ingest | FastAPI + Jinja2 + vanilla-JS chart, 30s refresh |
| [`webpage/`](webpage/) | Static sites with no backend | HTML/CSS/JS, zero build, `python -m http.server` |
| [`file-system/`](file-system/) | CLI tools with sub-commands and tests | argparse + pytest + pyproject.toml |

## Adding a new template

1. Create `templates/<your-type>/` with:
   - `README.md` — first non-empty non-heading line becomes the
     description in `bin/scaffold --list`.
   - `AGENTS.md` — template-specific agent contract.
   - `starter/` — the actual code. Anything inside `starter/`
     gets copied to the project root.
   - `starter/bin/start` — make it executable.
2. The scaffolder will discover it automatically.
3. Tell the owner to run `./bin/scaffold --list` to see the new option.

## Don't

- Don't add a template that requires a build step without telling the owner.
- Don't add a template that requires cloud credentials for the first run.
- Don't add a template that overlaps with one of the existing four without a clear reason.
