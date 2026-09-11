# bin/llm-council — integration with karpathy/llm-council

This document explains how [`../bin/llm-council`](../bin/llm-council)
in the parent directory talks to a running
[karpathy/llm-council](https://github.com/karpathy/llm-council) app.

## What the wrapper does

When you run `bin/llm-council "the question"`, the wrapper:

1. Probes `http://localhost:8001/` (the karpathy app's FastAPI
   backend) with a short timeout.
2. **If the app is running** → POSTs the question to the karpathy
   3-stage endpoint and prints the response.
3. **If the app is NOT running** → falls back to `bin/council` (the
   0xNyk council skill, vendored at `../council/`).

The wrapper auto-detects the running state on every call, so you
can start or stop the karpathy app without changing how you invoke
`bin/llm-council`.

## Running the karpathy app alongside this repo

```bash
# In a separate terminal
git clone https://github.com/karpathy/llm-council.git ~/work/llm-council
cd ~/work/llm-council
uv sync
cd frontend && npm install && cd ..
echo "OPENROUTER_API_KEY=sk-or-v1-..." > .env
./start.sh
```

This launches the FastAPI backend on `:8001` and the React frontend
on `:5173`. Open `http://localhost:5173/` for the chat UI.

Once it is running, from this repo:

```bash
bin/llm-council "Should we add streaming responses to the LINE bot?"
# → routes to the karpathy app, returns the 3-stage verdict
```

## Disabling the karpathy probe

If you want the wrapper to skip the karpathy probe and go straight
to the 0xNyk council:

```bash
bin/llm-council --karpathy=off "the question"
```

or via env var:

```bash
export COUNCIL_KARPATHY=off
bin/llm-council "the question"
```

The flag is sticky per-invocation (not persistent).

## API contract assumed

The wrapper probes the karpathy backend with:

```http
GET http://localhost:8001/  →  200 OK
POST http://localhost:8001/api/query
  Content-Type: application/json
  Body: { "query": "the question" }
  → 200 OK with { "stage1": [...], "stage2": [...], "stage3": {...} }
```

If the upstream API changes (Karpathy says it will change), the
wrapper's POST will fail and it will fall back to the 0xNyk council.
The fallback is the safety net — you will never see a dead-end error
from `bin/llm-council` as long as ONE of the two systems is
reachable.

## When to use the karpathy app vs the 0xNyk council

```
Is the karpathy app running AND do I have an OpenRouter key?
  └── yes → "what do multiple model families think of X?"
            → bin/llm-council --karpathy
  └── no  → "what do 18 analytical lenses think of X?"
            → bin/council
```

For most decisions in this repo, the 0Nyk council is the default.
Use karpathy when you specifically want cross-model-family
perspectives, or when you are running the chat UI to review
multiple answers side by side.

## Provenance

This shim is local to `diy-rag-chatbot`, MIT-licensed by
Non Arkaraprasertkul. The karpathy/llm-council app it talks to is
hosted by Andrej Karpathy's repo; we do not redistribute it here.
