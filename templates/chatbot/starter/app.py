"""
app.py — FastAPI webhook chatbot starter.

Answers ONLY from the files in `knowledge/`. Refuses when nothing
relevant is found. Uses Ollama by default (offline, free).

Run:
    ./bin/start

Test:
    curl -X POST http://127.0.0.1:8000/ask \
         -H 'Content-Type: application/json' \
         -d '{"q":"hi"}'
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


# ---------- config ----------
KNOWLEDGE_DIR = Path(os.environ.get("KNOWLEDGE_DIR", "./knowledge")).resolve()
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")
LLM_MODEL = os.environ.get("LLM_MODEL", "qwen3:4b")
LLM_API_KEY = os.environ.get("LLM_API_KEY") or None
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434")
TOP_K = int(os.environ.get("TOP_K", "3"))
MAX_ANSWER_CHARS = int(os.environ.get("MAX_ANSWER_CHARS", "1200"))

SYSTEM_PROMPT = (
    "You are a careful assistant. You answer ONLY using the files "
    "the operator gave you. If the files do not contain the answer, "
    "reply exactly: 'I do not have that in this folder.' Do not draw "
    "on outside knowledge. Match the user's language. Be concise. "
    "Cite the file you used."
)


# ---------- knowledge ----------
def load_knowledge() -> list[dict[str, str]]:
    """Read all .md files in KNOWLEDGE_DIR. Returns [{name, text}]."""
    if not KNOWLEDGE_DIR.is_dir():
        return []
    out: list[dict[str, str]] = []
    for p in sorted(KNOWLEDGE_DIR.rglob("*.md")):
        # Skip the format guide itself
        if p.name == "HOW-WE-FILE.md":
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        out.append({"name": str(p.relative_to(KNOWLEDGE_DIR)), "text": text})
    return out


def simple_retrieve(question: str, knowledge: list[dict[str, str]], k: int = TOP_K) -> list[dict[str, str]]:
    """Naive retrieve: pick files whose body or name contains a word from the question.

    Replace with embedding-based retrieval (bge-m3 / sentence-transformers /
    Ollama's /api/embeddings) when you outgrow the keyword heuristic.
    The point of this starter is that the bot works out of the box.
    """
    q_words = {w.lower() for w in question.split() if len(w) > 2}
    scored = []
    for item in knowledge:
        score = sum(1 for w in q_words if w in item["text"].lower())
        scored.append((score, item))
    scored.sort(key=lambda t: t[0], reverse=True)
    picked = [item for score, item in scored[:k] if score > 0]
    # Fall back to the first K if nothing matched — better than refusing
    # on the starter template (where knowledge is sparse).
    if not picked:
        picked = knowledge[:k]
    return picked


# ---------- llm ----------
def complete(system: str, user: str) -> str:
    if LLM_PROVIDER == "ollama":
        url = f"{LLM_BASE_URL}/api/chat"
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 500},
        }
        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
        return (r.json().get("message") or {}).get("content", "").strip()
    if LLM_PROVIDER == "openai":
        url = f"{LLM_BASE_URL.rstrip('/')}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"
        payload = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.3,
            "max_tokens": 500,
        }
        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, json=payload, headers=headers)
            r.raise_for_status()
        data = r.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        return (choices[0].get("message") or {}).get("content", "").strip()
    raise RuntimeError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER!r}")


def answer(question: str) -> str:
    knowledge = load_knowledge()
    if not knowledge:
        return "I do not have that in this folder. (No knowledge files yet.)"
    picked = simple_retrieve(question, knowledge)
    if not picked:
        return "I do not have that in this folder."

    context_blocks = "\n\n---\n\n".join(
        f"FILE: {item['name']}\n{item['text']}" for item in picked
    )
    user_msg = (
        f"FILES:\n{context_blocks}\n\n"
        f"USER QUESTION: {question}\n\n"
        "Answer using ONLY the files above. Cite the file you used."
    )
    reply = complete(SYSTEM_PROMPT, user_msg)
    if len(reply) > MAX_ANSWER_CHARS:
        reply = reply[: MAX_ANSWER_CHARS - 3] + "..."
    return reply


# ---------- api ----------
app = FastAPI(title="Chatbot (vibecoding-kit template)")


class AskRequest(BaseModel):
    q: str
    user: dict[str, Any] | None = None


class AskResponse(BaseModel):
    answer: str
    cited: list[str]


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "knowledge_files": len(load_knowledge())}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    if not req.q.strip():
        raise HTTPException(status_code=400, detail="q must not be empty")
    knowledge = load_knowledge()
    picked = simple_retrieve(req.q, knowledge)
    return AskResponse(answer=answer(req.q), cited=[p["name"] for p in picked])


# Hooks for channels. Add /webhook/line, /webhook/telegram,
# /webhook/discord, etc. Each should verify the channel's signature
# and then call `answer(question)` to get the reply.


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
