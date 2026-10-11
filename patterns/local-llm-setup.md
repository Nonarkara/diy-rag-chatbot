# Pattern: Local LLM setup

Default: Ollama on `http://localhost:11434`. Free, offline,
fast enough for prototyping. The agent defaults to this and the
user never has to set up an API key.

## Why Ollama first

- **Free** — no per-token cost, no usage limit
- **Offline** — works on a plane, on a train, with no Wi-Fi
- **Open weights** — `gemma4:e4b` (3B), `qwen3:4b` (4B), `llama3.2:3b`,
  `bge-m3` (embeddings) all pull from the same place
- **Same shape as OpenAI** — many providers speak `/v1/chat/completions`,
  so an Ollama-shaped client switches with a single env var

## Installation (macOS, Linux, WSL)

```bash
# macOS
brew install ollama
# or
curl -fsSL https://ollama.com/install.sh | sh

# start the daemon
ollama serve &

# pull a model
ollama pull qwen3:4b          # 4B params, ~2.5 GB on disk
ollama pull gemma4:e4b        # 3B params
ollama pull bge-m3             # embeddings
```

## Choosing a model

| Model | Size | When to use |
|---|---|---|
| `qwen3:4b` | 2.5 GB | Default. Best balance of speed and quality for English/Thai/Chinese. |
| `gemma4:e4b` | ~2 GB | Lower memory, slightly weaker Chinese. |
| `llama3.2:3b` | 2 GB | Multilingual. Slower on Thai. |
| `bge-m3` | 0.7 GB | Embeddings. Pair with any chat model. |
| `nomic-embed-text` | 0.3 GB | Alternative embeddings. |

The kit's `.env.example` and templates' `.env.example` use
`qwen3:4b` as the default. Switch by editing `.env`.

## Switching to OpenAI / Groq / OpenRouter

Edit `.env`:

```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com      # or api.groq.com/openai, openrouter.ai/api, etc.
LLM_MODEL=gpt-4o-mini                   # or llama-3.1-8b-instant, etc.
```

The same `complete(system, user)` call works for both providers;
the `bot/llm.py` and `templates/chatbot/starter/app.py` clients
branch on `LLM_PROVIDER`.

## Verifying

```bash
# Ollama: hit the tags endpoint
curl http://localhost:11434/api/tags

# OpenAI-compatible: hit the models endpoint
curl -H "Authorization: Bearer $LLM_API_KEY" \
     $LLM_BASE_URL/v1/models
```

Both should return a list of available models. If not:

- Ollama: `ollama serve` is not running, or the model hasn't been pulled
- OpenAI-compatible: the API key is missing or wrong, or the base URL is wrong

## Cold-load latency

The first call to a freshly-pulled model takes 5–30 seconds (model
load into VRAM). After that, calls are fast. If the user is on a
machine with limited RAM, the agent will be slow on the first
turn — flag it.

## When to ask the user to switch to a cloud LLM

- The model quality is too low for the task (small models hallucinate on long RAG contexts)
- The user wants a specific model (GPT-5, Claude, etc.) for a workflow
- Latency matters more than cost

Always ask **before** adding a cloud dependency. The user cloned
this kit *because* it works offline.
