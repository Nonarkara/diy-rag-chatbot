# Vibecoding Kit

**Out-of-the-Box Plug-and-Playable System (OTBPPS) for vibecoding.**

<p align="center">
  <img src="assets/hero-banner.svg" alt="Vibecoding Kit — clone + point your agent + get a project folder" width="100%">
</p>

<p align="center">
  <em><strong>Clone. Point your agent at the folder. Say what you want to build. Walk away with a working project.</strong></em>
</p>

<p align="center">
  Works with any LLM-capable agent (Claude Code, OpenCode, Codex, Gemini CLI). Default backend: Ollama running locally — <strong>no internet required</strong> for the core build loop.
</p>

<p align="center">
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/START-HERE.md"><img src="https://img.shields.io/badge/START-30_sec_quickstart-7c3aed?style=for-the-badge" alt="start"></a>
  &nbsp;
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/AGENTS.md"><img src="https://img.shields.io/badge/AGENTS.md-entry_contract-7c3aed?style=for-the-badge" alt="agents"></a>
  &nbsp;
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/knowledge/README.md"><img src="https://img.shields.io/badge/knowledge-curated_patterns-22c55e?style=for-the-badge" alt="knowledge"></a>
  &nbsp;
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/bin/scaffold"><img src="https://img.shields.io/badge/bin/scaffold-the_magic-22c55e?style=for-the-badge" alt="scaffold"></a>
</p>

<p align="center">
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/START-HERE.md">Start</a> ·
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/AGENTS.md">AGENTS.md</a> ·
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/bin/scaffold">scaffold</a> ·
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/templates/README.md">Templates</a> ·
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/knowledge/README.md">Knowledge</a> ·
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/knowledge/principles.md">Principles</a> ·
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/council/SKILL.md">Council skill</a> ·
  <a href="https://github.com/Nonarkara/diy-rag-chatbot/blob/main/docs/architecture/council-architecture.md">Architecture</a>
</p>

<p align="center">
  <img src="assets/badges/dr-non-1.jpg" alt="Dr Non's #1 Repository Of The Day" width="49%">
  &nbsp;
  <img src="assets/badges/dr-non-2.jpg" alt="Dr Non's #2 Repository Of The Day" width="49%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/release-v1.0.0-7c3aed?style=flat-square" alt="release">
  <img src="https://img.shields.io/badge/use_cases-chatbot·dashboard·webpage·file_system-7c3aed?style=flat-square" alt="use-cases">
  <img src="https://img.shields.io/badge/default_llm-Ollama_(local_·_free)-7c3aed?style=flat-square" alt="llm">
  <img src="https://img.shields.io/badge/templates-4_starter_folders-1f2937?style=flat-square" alt="templates">
  <img src="https://img.shields.io/badge/internet-required-no-22c55e?style=flat-square" alt="offline">
  <br>
  <img src="https://img.shields.io/badge/license-MIT-2563eb?style=flat-square" alt="license">
  <img src="https://img.shields.io/badge/♡_sponsors-0-ec4899?style=flat-square" alt="sponsors">
  <img src="https://img.shields.io/badge/python-3.10%2B-3776ab?style=flat-square&logo=python&logoColor=white" alt="python">
  <img src="https://img.shields.io/badge/vendored_0xNyk-MIT-4c1?style=flat-square" alt="vendored">
</p>

---

## What this is

You clone this repo, open your AI agent (Claude Code, OpenCode, Codex,
Gemini CLI, etc.) in the folder, and say "build me a dashboard for
tracking my reading list." The agent uses `bin/scaffold` to create a
`my-project/` folder with a sophisticated sub-folder layout, pulls
relevant patterns from `knowledge/`, runs a local LLM (Ollama) on
your laptop, and you end up with working code — without ever
touching a web browser.

**No API keys needed. No cloud account. No internet.** Default backend
is Ollama running on `http://localhost:11434`. Switch to Groq /
OpenAI / Anthropic / any OpenAI-compatible endpoint by editing
`.env`.

## What you can build out of the box

| Use case | Template | What you get |
|---|---|---|
| **Chatbot** | `templates/chatbot/` | FastAPI webhook + starter knowledge folder + RAG retrieval — works with LINE, Telegram, Discord, web |
| **Dashboard** | `templates/dashboard/` | FastAPI + static HTML dashboard with chart stubs and CSV/JSON ingest |
| **Webpage** | `templates/webpage/` | Static HTML/CSS/JS site with a `python -m http.server` dev start |
| **File system** | `templates/file-system/` | CLI tool skeleton with tests + argparse sub-commands |

Each template is a working starter. The agent extends it based on
your request; the scaffold gives it a structure to extend into.

## 30-second quickstart

```bash
git clone https://github.com/Nonarkara/diy-rag-chatbot.git vibecoding-kit
cd vibecoding-kit
./bin/scaffold --type chatbot --name my-assistant
cd my-assistant
./bin/start
```

`bin/scaffold` will:
1. Copy the right template into `my-assistant/`
2. Generate a starter `knowledge/` folder (if applicable)
3. Drop a template-specific `AGENTS.md` so the next agent knows the conventions
4. Print next steps: which agent to open, what to say to it, how to run

Then open Claude Code (or your agent of choice) in `my-assistant/` and keep vibecoding.

## What this kit ships

| Layer | Path | Purpose |
|---|---|---|
| **Entry contract** | `README.md`, `AGENTS.md`, `CLAUDE.md`, `START-HERE.md` | What any agent reads first |
| **Scaffolder** | `bin/scaffold` | Creates a project folder from a template |
| **Templates** | `templates/` | 4 starter project folders — chatbot, dashboard, webpage, file-system |
| **Knowledge base** | `knowledge/` | Patterns the agent reads (RAG, API integration, state, local-LLM setup, deployment) |
| **Council (decisions)** | `council/`, `bin/council`, `bin/llm-council` | Multi-perspective deliberation for hard choices |
| **Live example** | `bot/` | A working Telegram council bot — proof the kit works end-to-end |
| **Architecture** | `docs/architecture/` | 7 SVG illustrations + explainers (manga + MoMA style) |
| **Brand** | `assets/hero-banner.svg`, `assets/badges/` | The hero + Dr Non trending badges |

## Design principles (the short version)

1. **OTBPPS** — Clone + point agent + get a project. No setup beyond `git clone` and a local LLM.
2. **Knowledge before code** — The agent reads `knowledge/` before writing anything. Patterns are first-class.
3. **Templates before generators** — Each project starts from a working starter, not a blank slate.
4. **Local-first** — Default to Ollama. Cloud is opt-in via `.env`.
5. **Council for decisions, not answers** — Use the AI council when the question is "what should we build?", not when the question is "what is X?".

Full version: [`knowledge/principles.md`](knowledge/principles.md).

## For AI agents

You are an agent. Read [`AGENTS.md`](AGENTS.md). It tells you how to
behave when the owner clones this repo. Use `bin/scaffold` when the
owner says "build me X". Use the council (`bin/council`) when the
question has multiple competing answers. Read `knowledge/` before
inventing — the patterns there are the source of truth.

---

© 2026 Non Arkaraprasertkul / Axiom X Co., Ltd. · MIT on original
text and code in this repository.
