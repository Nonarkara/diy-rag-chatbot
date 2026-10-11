# Dashboard template

A small FastAPI + static HTML dashboard. Reads data from
`data/` (CSV or JSON), renders charts in vanilla JS — no
frontend build step, no npm. Local-first.

## What's inside the generated project

```
my-dashboard/
├── README.md
├── AGENTS.md
├── app.py              # FastAPI server + JSON API
├── data/               # CSV / JSON files the dashboard reads
│   └── sample.csv
├── templates/          # Jinja2 HTML templates
│   └── index.html
├── static/             # CSS + vanilla JS for charts
│   ├── style.css
│   └── charts.js
├── requirements.txt
├── .env.example
└── bin/start
```

## How it works

1. `app.py` exposes:
   - `GET /` — the dashboard page (Jinja2-rendered HTML)
   - `GET /api/data` — JSON of the latest data from `data/`
   - `POST /api/refresh` — re-read the data folder
   - `GET /health` — health check
2. The page fetches `/api/data` on load and every 30 seconds.
3. `charts.js` plots the data in vanilla JS — no D3, no Chart.js
   dependency. Replace with whatever you want.

## Run

```bash
./bin/start
# open http://127.0.0.1:8000
```

## Extend

| Owner says... | You do |
|---|---|
| "Add a new chart for column Y" | Add a `<canvas>` in `index.html`, draw in `charts.js`. |
| "Read from PostgreSQL" | Add a `db.py` + SQLAlchemy, replace the CSV reader with a query. |
| "Add auth" | Add a session cookie or HTTP Basic in `app.py`. |
| "Filter by date" | Add a `?from=` / `?to=` query param to `/api/data`. |

## Don't

- Don't pull in npm/Vite/React unless the owner asks. Vanilla JS + Jinja2 is enough for most dashboards.
- Don't add a frontend build step. The `static/` folder is served as-is.
- Don't read secrets from `.env` into the HTML. Pass them via API.
