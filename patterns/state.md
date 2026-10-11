# Pattern: State

Most OOTBPAP projects don't need a database. They need a
**JSON file in the project root** or **in-memory state**. Reach
for a database only when the user asks for one or when the
in-memory option breaks.

## The decision tree

```
Need to remember user X's session between requests?
├── no  → no state at all, function calls are enough
└── yes
    ├── How many concurrent users?
    │   ├── 1 (single owner)    → in-memory dict
    │   ├── < 100               → JSON file in the project root
    │   └── > 100 or persistent → SQLite, Postgres, or a hosted KV
    └── Does the user ask for it specifically?
        └── "use a database" → SQLite (file) is the right default
```

The `templates/chatbot/starter/app.py` has no state. The `bot/`
package has in-memory session state (per chat_id). Anything
heavier is opt-in.

## In-memory (per-process)

```python
SESSIONS: dict[str, dict] = {}

@app.post("/ask")
def ask(req: AskRequest) -> AskResponse:
    state = SESSIONS.setdefault(req.user_id, {"history": []})
    state["history"].append({"q": req.q, "a": answer(req.q)})
    return AskResponse(answer=state["history"][-1]["a"], state=state)
```

Caveats:

- **Lost on restart** — fine for a bot, terrible for a dashboard
- **Not shared across processes** — fine for a single uvicorn
  worker, broken with `--workers 2`

## JSON file

```python
import json
from pathlib import Path

STATE_FILE = Path(os.environ.get("STATE_FILE", "./.state.json"))

def load_state() -> dict:
    if STATE_FILE.is_file():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))

@app.post("/ask")
def ask(req: AskRequest) -> AskResponse:
    state = load_state()
    user_state = state.setdefault(req.user_id, {"history": []})
    user_state["history"].append({"q": req.q, "a": answer(req.q)})
    save_state(state)
    return AskResponse(answer=user_state["history"][-1]["a"])
```

Caveats:

- **Write contention** — multiple concurrent requests can corrupt the file
- **Slow at scale** — JSON-encoding 10K entries takes a few hundred ms
- **Single-process** — fine for SQLite/Postgres, broken if you scale out

## SQLite (file)

```python
import sqlite3

DB = Path(os.environ.get("DB_FILE", "./.state.db"))

def init_db() -> None:
    with sqlite3.connect(DB) as c:
        c.execute("CREATE TABLE IF NOT EXISTS sessions (user_id TEXT, key TEXT, value TEXT, PRIMARY KEY (user_id, key))")

def get_value(user_id: str, key: str) -> str | None:
    with sqlite3.connect(DB) as c:
        row = c.execute("SELECT value FROM sessions WHERE user_id=? AND key=?", (user_id, key)).fetchone()
        return row[0] if row else None
```

This is the right default for a stateful bot with > 100 users.
SQLite is in the stdlib, supports concurrent reads, and the file
copies with the project.

## Don't

- Don't add Redis. It adds an external service. The OOTBPAP
  promise is *no internet*. SQLite is local, JSON is local,
  in-memory is local.
- Don't add a database because the user said "I have a lot of
  data" — most of the time a CSV file is the right answer.
- Don't use a global `dict` for state if you ever run with
  `--workers > 1`. SQLite, not Redis.

## When the user asks for a database

If they say "let's use Postgres" or "set up a Redis", do it. But
ask first: "is this for the chatbot, the dashboard, or both?"
because the answer changes the schema.
