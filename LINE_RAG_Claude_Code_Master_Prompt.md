# LINE RAG Bot — Claude Code Master Prompt

**Repo:** [Nonarkara/diy-rag-chatbot](https://github.com/Nonarkara/diy-rag-chatbot)  
**Product name:** Dr Non's DIY RAG / Chatbot-as-a-Self-Service

If this file is sitting inside that repo, **build here**. Do not create a sibling `line-rag-bot/` folder. If the owner pasted this into an empty directory, create the project in the current directory.

The intended owner is nontechnical. After setup their loop is: **drop files into `./knowledge` and keep the computer on**. You build the machine. You are not the machine.

Claude Code / Cursor / any agent: also read `AGENTS.md` and `START-HERE.md`. Credentials and LINE consoles are walked with the owner, one URL per turn. Never ask them to paste secrets into chat.

---

## Product goal

A LINE user sends a text question to the Official Account. The service retrieves evidence from `./knowledge`, asks an LLM to answer from that evidence, and replies through LINE. It must not invent an answer when the knowledge base does not support one.

Mental model — do not violate:

> โฟลเดอร์คือสมอง · ไลน์คือปาก · โมเดลคือล่าม

Do not call this an “AI agent” unless it actually needs tools. Retrieval → LLM → answer is the whole system.

---

## 1. Project structure

```text
diy-rag-chatbot/
├── knowledge/
├── rag_database/          # gitignored SQLite, not Chroma
├── app/
│   ├── ingest.py
│   ├── parsers.py
│   ├── chunk.py
│   ├── embeddings.py
│   ├── retrieve.py
│   ├── rag.py
│   ├── llm.py
│   ├── line_webhook.py
│   ├── server.py
│   └── settings.py
├── templates/             # /admin
├── tests/
├── deck/                  # keep the Thai briefing if it already exists
├── START-HERE.md
├── AGENTS.md
├── .env.example
├── .gitignore
├── requirements.txt
├── START.command
├── START.bat
└── README.md
```

Python 3.11+ and FastAPI. No LangChain. No LlamaIndex. No Chroma.

---

## 2. Knowledge-folder behavior

`./knowledge` is the source of truth. Recursively support PDF, DOCX, XLSX, PPTX, TXT, Markdown.

For each chunk keep: file path, file name, page when available, sheet/row for spreadsheets, slide number for decks, heading, last-modified, SHA-256 of file bytes.

Detect scanned / image-only PDFs. Do not silently pretend they contain text. Mark them on `/admin` as requiring OCR. Optional OCR path is allowed; do not block the rest of the index.

On startup and on folder change:

- index new files;
- re-index changed files only (hash mismatch);
- remove chunks of deleted files;
- do not rebuild the whole corpus.

Thai chunking: split on blank lines, keep a heading with the following block, break oversized blocks on sentence punctuation (`. ! ? 。 ฯ`), never on spaces.

Filing standard the kit copies from Smart City Thailand (`knowledge/HOW-WE-FILE.md`):

- Categories as lowercase folders: `faq/` `briefings/` `policies/` `program/` `institutional/` `general/`.
- Distilled pages use one H1 and bilingual `ถาม:` / `Q:` / `A:` lines so Thai and English retrieve the same chunk. Treat `ถาม:` as a heading in the chunker, same as `Q:`.
- Never index website chrome (nav, footer, cookie banner, generic titles like "Digital service View"). If a fetch is menu soup, replace it with three honest sentences pointing at the source URL.
- File refusals as short `faq/` pages ("ask someone else"). A refusal only in the system prompt vanishes when the model is swapped.
- Hand-edited files are not live until the watcher reindexes.

---

## 3. RAG

Embeddings: **bge-m3 via Ollama**. Do not default to MiniLM, MPNet, or `nomic-embed-text`. With mixed Thai/English, nomic’s on-topic and off-topic scores overlap — no honest refusal threshold exists. Record the embedder name in the index; refuse to search a mismatched corpus.

Store chunks in **one SQLite file** under `./rag_database` (FTS5 trigram + float32 blobs). Not Chroma, not Pinecone, not Postgres.

Retrieval:

1. normalize the query;
2. dense cosine over all chunks (brute force is fine under ~50k);
3. FTS5 trigram lexical search (Thai has no spaces);
4. Reciprocal Rank Fusion, K=20, lexical weight 0.6;
5. rarity ceiling = min(25% of chunks, 40);
6. `minScore` default **0.46** (measured on bge-m3: on-topic 0.50–0.61, off-topic ≤ 0.42);
7. pass only the evidence to the LLM.

There is **no** LLM “is this on topic?” classifier. Retrieval already answers that.

Do not expose raw scores to LINE users.

---

## 4. Answer policy

- Answer from retrieved evidence, not general model memory.
- Never manufacture policy, numbers, names, dates, or procedures.
- If evidence is insufficient, conflicting, or below threshold with no rare-term hit, refuse in the user’s language and include a human handoff.
- Language is decided **in code** from the question script (Thai characters → Thai). Do not leave it to the model.
- Strip Markdown and `[#n]` markers before LINE. LINE renders a chat bubble, not Markdown.
- Append an AI disclaimer on every generated answer.
- Distinguish answer from caveat. Cite filename and page/section when available.

Thai fallback:

> ยังไม่พบข้อมูลที่เพียงพอในเอกสารที่มี กรุณาระบุคำถามให้แคบลง หรือให้เจ้าหน้าที่ตรวจสอบข้อมูลต้นทาง

---

## 5. LLM provider abstraction

`ANSWER_PROVIDER=auto` tries, in order, whichever keys exist:

Groq (`openai/gpt-oss-20b`) → Gemini → OpenAI → Anthropic → OpenRouter → local Ollama (`gemma4:e4b`, or `gemma4:e2b` on 8 GB RAM).

Embeddings always local (`bge-m3`). Never hard-code keys.

Reasoning models (gpt-oss, deepseek-r1, qwen3): extra completion budget so thinking does not eat the answer.

---

## 6. LINE Messaging API

- `POST /webhook`
- `GET /health`
- `GET /admin`

For every webhook:

- verify `X-Line-Signature` (HMAC-SHA256 of **raw body**) with `LINE_CHANNEL_SECRET` before parsing;
- reject invalid signatures with 401;
- return **200 immediately**, process in the background;
- **Push** for RAG answers (reply tokens die in ~30 seconds; RAG is often slower). Reply is allowed only for instant commands (`/about`, `/privacy`, `/forget`) and the follow disclosure;
- handle text; ignore or politely decline stickers/images unless you implement them;
- `webhookEventId` idempotency so redeliveries do not double-reply;
- on any exception, Push a bilingual apology — never go silent;
- on `follow`, disclose that the responder is automated;
- log failures without leaking secrets.

Do not require the official LINE SDK if `httpx` + HMAC is clearer. Either is fine if tests pass.

---

## 7. Environment configuration

`.env.example`:

```dotenv
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=

ANSWER_PROVIDER=auto
GROQ_API_KEY=
GEMINI_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=

OLLAMA_URL=http://127.0.0.1:11434
OLLAMA_CHAT_MODEL=gemma4:e4b
OLLAMA_EMBED_MODEL=bge-m3

KNOWLEDGE_FOLDER=./knowledge
RAG_DB=./rag_database/index.sqlite
RAG_MIN_SCORE=0.46
TOP_K=6

HOST=127.0.0.1
PORT=8000
BOT_NAME=Knowledge Bot
BOT_LANGUAGE=th
HANDOFF=ติดต่อผู้ดูแลเพจ
ADMIN_ENABLED=true

TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
DISCORD_APP_ID=
DISCORD_PUBLIC_KEY=
DISCORD_BOT_TOKEN=
PUBLIC_URL=
```

Add `.env` and `rag_database/` to `.gitignore`.

---

## 8. Admin page

`/admin` on localhost only. Show: service state; LINE keys present/missing (never values); LLM present/missing; file count; chunk count; files skipped / needing OCR; last index time; last scan; recent latency; recent source filenames; recent errors. Not decorative.

---

## 9. Start scripts

`START.command` (macOS) and `START.bat` (Windows):

1. verify Python;
2. create/install venv;
3. copy `.env.example` → `.env` if missing;
4. scan/index `knowledge/`;
5. start folder watcher;
6. start FastAPI on `127.0.0.1:8000`;
7. print local URL and health.

The owner must not type five commands every morning.

---

## 10. Cloudflare Tunnel

Do not hard-wire Cloudflare into the app. Document:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Never use `localhost` as the origin. Quick Tunnels are for testing. Named tunnel or a VPS for a bot that must stay up. **If the computer is off, the bot is dead.**

Walk the owner through `START-HERE.md` stations 11–12 for the webhook URL.

---

## 10b. Where it runs (compute)

Do not default to Vercel. Walk station 14.

- **This computer 24/7** + Cloudflare Tunnel: zero extra host bill; lid-close = dead bot; keep-awake.
- **Railway**: always-on containers, trial credits then usage billing, persistent volume for SQLite. Best cloud fit for a LINE webhook.
- **Render free**: spins down after ~15 minutes idle; LINE webhooks fail on cold start. Paid always-on (~USD 7/mo) if they insist on Render.
- **Vercel Hobby**: serverless, no persistent FastAPI, no folder watcher, no local SQLite/Ollama. Host the **slide deck** there if they want. Do **not** host this bot there.

On a cloud host: no local Ollama unless they run a custom image; `ANSWER_PROVIDER=groq` (or Gemini); `HOST=0.0.0.0`; knowledge arrives by git push or upload, not drag-and-drop.

---

## 10c. Telegram (optional)

After LINE works. `POST /webhook/telegram`.

- Token from @BotFather into `TELEGRAM_BOT_TOKEN` (owner types into `.env`).
- `setWebhook` only when `PUBLIC_URL` is public HTTPS (not 127.0.0.1).
- Verify `X-Telegram-Bot-Api-Secret-Token` against `TELEGRAM_WEBHOOK_SECRET`; 403 on mismatch.
- Reply with Bot API `sendMessage`, 4000-character cap.
- Same RAG pipeline as LINE. Same refuse-don't-invent. Strip Markdown.

---

## 10d. Discord (optional)

After LINE works. `POST /webhook/discord`.

- Discord Developer Portal → New Application → Public Key + Application ID + bot token.
- **Interactions Endpoint**, not a Gateway websocket. Slash command `/ask`.
- Verify Ed25519 over `timestamp + rawBody`. Respond to PING (type 1) with `{"type":1}`.
- RAG exceeds Discord's 3-second window: respond type 5 (deferred) then follow up.
- Do not require Message Content Intent if `/ask` is the only surface.

---

## 11. Security and privacy

- secrets only in env;
- signature verification first;
- send only retrieved chunks to a cloud LLM, never the whole folder;
- minimum logs; no PII by default;
- no debug traces to LINE;
- `/about` `/privacy` `/forget` without a model call;
- document token rotation;
- knowledge files are the backup; the SQLite index is rebuildable.

Even with a local LLM, chat text still travels through LINE. “Local” means embeddings and (optionally) generation on this computer, not that LINE becomes offline.

---

## 12. Tests / acceptance

Automated tests must not need the network.

A. Known answer — test doc in `./knowledge`, answer matches evidence and cites source.  
B. Unknown answer — refuse, do not hallucinate.  
C. File update — only that file re-indexed; retrieval changes.  
D. Deleted file — chunks gone.  
E. Invalid LINE signature — 401.  
F. Duplicate webhookEventId — no second reply.  
G. Restart — index loads without full rebuild.  
H. Thai retrieval — Thai question hits the right passage.  
I. Markdown stripped from a fake model output that contains `**bold**`.

Then a manual smoke: add the OA, ask an in-corpus question, ask an off-topic question. If B/off-topic does not refuse, it is not done.

---

## 13. Definition of done

Run the tests. Fix. Re-run. Leave a working tree, `.env.example`, start scripts, tests, Thai+English README pointing at `START-HERE.md`, and `TECHNICAL_NOTES.md` for decisions.

Owner experience:

> Clone this repo → tell the agent to read AGENTS.md → drop files in `knowledge` → paste LINE/LLM credentials once into `.env` → START → Cloudflare → Verify webhook → ask → grounded answers.

Do not stop until acceptance tests pass.
