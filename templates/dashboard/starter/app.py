"""
app.py — FastAPI dashboard server (CSV/JSON → JSON API → HTML page).
Local-first. Reads from ./data/.
"""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Optional: pull Request from starlette if you want the request object
from starlette.requests import Request


# ---------- config ----------
DATA_DIR = Path(os.environ.get("DATA_DIR", "./data")).resolve()
REFRESH_SECONDS = int(os.environ.get("REFRESH_SECONDS", "30"))
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8000"))


# ---------- data ----------
def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> Any:
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def latest_dataset() -> dict[str, Any]:
    """Pick the first .csv or .json file in DATA_DIR (alphabetical)."""
    if not DATA_DIR.is_dir():
        return {"source": None, "rows": [], "columns": []}
    files = sorted(
        list(DATA_DIR.glob("*.csv")) + list(DATA_DIR.glob("*.json"))
    )
    if not files:
        return {"source": None, "rows": [], "columns": []}
    picked = files[0]
    if picked.suffix == ".csv":
        rows = read_csv(picked)
        columns = list(rows[0].keys()) if rows else []
        return {"source": picked.name, "format": "csv", "rows": rows, "columns": columns}
    data = read_json(picked)
    return {"source": picked.name, "format": "json", "rows": data or [], "columns": []}


# ---------- api ----------
app = FastAPI(title="Dashboard (vibecoding-kit template)")
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> Any:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "refresh_seconds": REFRESH_SECONDS,
            "data_dir": str(DATA_DIR),
        },
    )


@app.get("/api/data")
def api_data() -> dict[str, Any]:
    return latest_dataset()


@app.post("/api/refresh")
def api_refresh() -> dict[str, Any]:
    return {"refreshed": True, "at": latest_dataset()["source"]}


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "data_dir": str(DATA_DIR), "refresh_seconds": REFRESH_SECONDS}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
