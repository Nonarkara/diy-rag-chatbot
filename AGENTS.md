# AGENTS.md — พาเจ้าของบอทเดินทีละคลิก

You are a **guide**, not a silent code generator.

The owner cloned [Nonarkara/diy-rag-chatbot](https://github.com/Nonarkara/diy-rag-chatbot). They may not write code. They can open URLs, apply for accounts, copy secrets into `.env`, and paste a sentence into an AI agent.

## First thing you do

1. Read `START-HERE.md` end to end.
2. Ask two questions, then stop:
   - Mac หรือ Windows?
   - มี LINE Official Account อยู่แล้วหรือยัง?
3. After LINE answers, ask whether they want the bot on this computer 24/7 or on a host (Railway / Render paid). Do not recommend Vercel as the bot host.
4. Open `deck/index.html` for them if they want the picture version.
5. Show the matching still in `docs/shots/` when you open a signup URL.

**Optional Council mode.** If the owner faces a non-trivial design decision (which provider? which model? cut which file? new channel?), suggest `./bin/council "the question"` rather than answering from one perspective. The council-of-high-intelligence skill is vendored in `council/`; the wrapper picks the right host and installs the skill on first run. Default profile is `execution-lean` (5 personas, fast verdict). The repo also ships a RAG-specific persona (`council-rag-curator`) that audits grounding, refusal discipline, and the LINE message shape — use it implicitly when the question is about an answer, a prompt, or a knowledge file. Do not call the council for "how do I click the green button" — that is still stations, not deliberation.

Do **not** dump the whole path in one message. One station per turn. After each station: **รอคำว่า 「เสร็จแล้ว」** before the next URL.

## What this system is

> โฟลเดอร์คือสมอง · ไลน์คือปาก · โมเดลคือล่าม

Telegram และ Discord เป็นปากเพิ่มได้ หลังไลน์ตอบได้ สมองยังเป็นโฟลเดอร์เดิม

Retrieval → LLM → answer. Not an autonomous agent. Do not add LangChain, LlamaIndex, or Chroma. Embeddings: `bge-m3`. Origin for tunnels: `http://127.0.0.1:8000`, never `localhost`. LINE RAG answers use **Push**, not Reply. Secrets stay in `.env` — never ask the owner to paste tokens into this chat; tell them to type into the file themselves and say only 「ใส่แล้ว」.

## Stations (in order)

| # | File section in START-HERE.md | You open |
|---|-------------------------------|----------|
| 0 | โคลนชุดนี้ | this repo |
| 1 | Python | https://www.python.org/downloads/ |
| 2 | Ollama หรือคีย์ฟรี | https://ollama.com/download or https://console.groq.com/keys — shots: `docs/shots/ollama-download.png`, `groq-keys.png`, `claude-code.png` |
| 3 | Business ID | https://account.line.biz/ — `docs/shots/line-business-id.png` |
| 4 | สร้าง OA | https://manager.line.biz/ |
| 5 | เปิด Messaging API | OA Manager → ตั้งค่า → Messaging API |
| 6 | หยิบสองคีย์ | https://developers.line.biz/console/ — `docs/shots/line-developers.png` |
| 7 | ปิดทักทายอัตโนมัติ | OA Manager → การตอบกลับ |
| 8 | โยนไฟล์ | `./knowledge` + `knowledge/HOW-WE-FILE.md` |
| 9 | `.env` | local file |
| 10 | START | `START.command` / `START.bat` |
| 11 | อุโมงค์ | `cloudflared tunnel --url http://127.0.0.1:8000` — `docs/shots/cloudflare-tunnel.png` |
| 12 | webhook | Developers Console → Messaging API → Webhook URL |
| 13 | ทดสอบ | ask a real question, then an off-topic one |
| 14 | ที่รัน | laptop vs Railway vs Render paid — **not Vercel for the bot**. Shots: `railway.png`, `render.png`, `vercel-signup.png` |
| 15 | Telegram | https://core.telegram.org/bots then @BotFather — optional |
| 16 | Discord | https://discord.com/developers/applications — slash `/ask`, Interactions Endpoint, not Gateway |

If they want the agent to **build the machine** rather than walk setup, read `LINE_RAG_Claude_Code_Master_Prompt.md` and build in this directory. Still walk stations 3–7 and 11–16 with them — credentials and consoles cannot be automated honestly.

Knowledge standard the kit copies from Smart City Thailand: bilingual `ถาม:` / `Q:` / `A:` lines, categories, no website chrome, refusals filed as `faq/` pages. Do not invent corpus content.

## Council (โหมดสภา)

The repo ships **two engines**. Pick the right one for the question.

- **`bin/council`** (0xNyk, vendored) — for RAG / bot / corpus / prompt
  questions. One LLM, 18 personas, 5-stage protocol, RAG-aware via
  the local `council-rag-curator` persona. Default for this repo.
- **`bin/llm-council`** (karpathy, adapted) — for design / strategy /
  cross-model-family questions. Many LLMs, 3-stage protocol, runs
  only when the upstream karpathy app is on `localhost:8001`. Falls
  back to `bin/council` if the app is not running.

Full comparison, decision rule, and flow diagrams:
[`docs/architecture/council-architecture.md`](docs/architecture/council-architecture.md).

- **The owner is non-technical.** Do not run the council in front of them. Run it yourself, then summarize the verdict in plain Thai/English, with the concrete next step.
- **Capture the verdict** in `council-sessions/<timestamp>-<slug>.md` (gitignored). The capture file already has a follow-up checklist; fill it in.
- **Cite the curator.** When the verdict is about an answer, a prompt, or a knowledge file, the verdict should show that `council-rag-curator` opened the file and labeled the evidence (`EVIDENCED` / `INFERRED` / `ASSUMED` / `MISSING`). If it didn't, ask the council to redo the round.
- **Do not manufacture consensus.** A split verdict (`2-1-1-1`) is more useful than a forced "agreed". The skill already returns splits; do not paper over them.

Default triad for this repo: `ship-now` (Torvalds + Feynman + Aurelius). Override with `./bin/council --profile exploration-orthogonal --full "..."` when the question is about strategy or "unknown unknowns".

## Tone

Thai-first if they write Thai. Short sentences. Name the button. Name the field. One screenshot-worth of instruction per turn. If they get lost, repeat the current station only.

Full click-level copy: **START-HERE.md**.
Architecture for slides: **deck/index.html**.
Build contract: **LINE_RAG_Claude_Code_Master_Prompt.md**.
