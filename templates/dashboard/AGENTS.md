# AGENTS.md — for THIS dashboard project

You are an agent working inside a project generated from the
`dashboard` template. The kit's entry contract is in
`<kit-root>/AGENTS.md`. **This file overrides it where they conflict.**

## Read order

1. **This file.**
2. `app.py` — the server. Understand it before extending.
3. `templates/index.html` — the page.
4. `static/charts.js` — the rendering.
5. `data/sample.csv` — the shape of the data.

## The dashboard's contract

1. **Reads from `data/`.** Don't hardcode data in the page. Add a
   new CSV/JSON file in `data/` and the dashboard will see it.
2. **Vanilla JS only.** No npm install, no Vite, no React. The
   `static/` folder is served as-is.
3. **Refreshes on a timer.** Default: 30 seconds. Make it
   configurable via `.env`.
4. **JSON API is the source of truth.** The page must work even if
   someone POSTs data directly to the API.

## How to extend

| Owner says... | You do |
|---|---|
| "Add a chart for X" | Add a `<canvas id="x-chart">` in `index.html`, draw in `charts.js`. |
| "Read from a SQL DB" | Add `db.py`, replace `read_csv` with `read_db`. |
| "Filter by date" | Add `?from=` / `?to=` to `/api/data`, parse in `charts.js`. |
| "Add a refresh button" | Wire a button to `POST /api/refresh`. |
| "Deploy somewhere" | See kit-level `patterns/deployment.md`. |

## Don't

- Don't add React/Vue/Svelte/npm unless asked.
- Don't put secrets in the HTML.
- Don't read data outside `data/` without telling the owner.
