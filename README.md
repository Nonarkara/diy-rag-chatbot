# Dr Non's DIY RAG / Chatbot-as-a-Self-Service

**แร็กทำเองของดร.นน · แชตบอทบริการตนเอง**

> โฟลเดอร์คือสมอง · ไลน์คือปาก · โมเดลคือล่าม

คู่มือภาษาไทยทีละขั้น สำหรับคนที่ไม่เขียนโค้ด แต่ชี้ URL ได้ สมัครบัญชีได้ และวางข้อความให้เอเจนต์ได้

> **โหมดสภา (Council mode) — ใหม่:** เมื่อต้องตัดสินใจเรื่องใหญ่ ๆ ของบอท เช่น เพิ่ม Telegram? เปลี่ยน prompt? ตัดไฟล์ไหนทิ้ง? — ใช้ `bin/council "คำถาม"` เพื่อเรียกสภา 18 คน (vendored จาก [council-of-high-intelligence](https://github.com/0xnyk/council-of-high-intelligence)) มาช่วยคิด โดยมีตัวเลือก `--quick`, `--duo`, `--triad architecture` เป็นต้น ดูรายละเอียดที่ [Council mode](#council-mode) ด้านล่าง

เปิดสไลด์ในเบราว์เซอร์:

- ไฟล์ท้องถิ่น: `open deck/index.html`
- ออนไลน์: [nonarkara.github.io/diy-rag-chatbot](https://nonarkara.github.io/diy-rag-chatbot/)
- ต้นทาง: [github.com/Nonarkara/diy-rag-chatbot](https://github.com/Nonarkara/diy-rag-chatbot)

หรือเสิร์ฟที่ `http://127.0.0.1:8765/deck/`

```bash
python3 -m http.server 8765
```

ลูกศรซ้ายขวาเลื่อนสไลด์ · ⌘P พิมพ์เป็น PDF แนวนอน

---

## English

Clone this repo, then tell your AI agent:

> Read AGENTS.md and START-HERE.md and walk me through each station until the LINE Official Account answers from the knowledge folder. Do not skip steps. Do not ask me to paste secrets into chat.

A 31-slide Thai briefing (`deck/`) and an 18-slide Axiom PowerPoint/PDF sit in the repo. The bot **answers only from those files** and **refuses when it cannot**. After LINE works, the same folder can speak through Telegram and Discord. Compute is a choice: this computer 24/7, Railway, or paid Render — **not Vercel for the bot**.

Designed in [Axiom Design Core](https://github.com/Nonarkara/Axiom-Design-Core) Editorial mode. This is **not** an official product of depa, the Smart City Thailand Office, or LY Corporation.

---

## สิ่งที่เด็คสอน

1. โยนไฟล์ลงโฟลเดอร์ความรู้
2. สร้าง LINE Official Account ที่ [manager.line.biz](https://manager.line.biz) แล้วเปิด Messaging API จากหน้าบัญชี — **สร้างชาแนลตรงจาก Developers Console ไม่ได้อีกแล้ว** (ตั้งแต่ 4 ก.ย. 2024)
3. วาง `LINE_CHANNEL_SECRET` และ `LINE_CHANNEL_ACCESS_TOKEN` ใน `.env`
4. เลือกสมอง: Ollama (`gemma4:e2b` / `gemma4:e4b` / DeepSeek) บนแรม 8–16 GB หรือคีย์ฟรี Groq / Gemini
5. ให้ LINE ถึงเครื่องผ่าน Cloudflare Tunnel (`cloudflared tunnel --url http://127.0.0.1:8000`)
6. ตรวจลายเซ็นเว็บฮุคทุกครั้ง
7. รั้ว: ไม่มีหลักฐานในไฟล์ = ปฏิเสธ ไม่เดา
8. เลือกที่รัน: เครื่องเปิดค้าง / Railway / Render จ่าย — อย่าใช้ Vercel เป็นที่รันบอท
9. (ไม่บังคับ) Telegram @BotFather และ Discord slash `/ask`

บทเรียนมาจากระบบที่วิ่งอยู่ที่ [rag.nonarkara.org](https://rag.nonarkara.org) ไม่ใช่จากบล็อกทฤษฎี คลัง Smart City Thailand คือมาตรฐานการจัดไฟล์ที่ชุดนี้ให้คัดลอก (`knowledge/HOW-WE-FILE.md`)

---

## โครงสร้าง

```
START-HERE.md            จับมือทีละเว็บ รวมที่รัน Telegram Discord
AGENTS.md                สัญญาของเอเจนต์ — พาทีละสถานี
LINE_RAG_Claude_Code_Master_Prompt.md   ให้เอเจนต์สร้างเครื่อง
knowledge/HOW-WE-FILE.md สัญญาจัดเก็บแบบ Smart City Thailand
docs/shots/              ภาพหน้าสมัครที่ต้องกดเอง
LINE_RAG_OA_Guide_TH_Axiom.pptx / .pdf  สำเนานำเสนอ
deck/                    สไลด์ภาษาไทย
PROMPT.md                ชี้ไปที่ master prompt
council/                 โหมดสภา (vendored) — ดูหัวข้อถัดไป
.council.yaml           ค่าตั้งต้นของสภาสำหรับ repo นี้
bin/council              ครอบคำสั่ง /council ให้รันได้ทันที
karpathy-council/        3-stage multi-model pattern (adapted) — ดู docs/architecture
bin/llm-council          ครอบ karpathy app (localhost:8001) → fall back ไป bin/council
bot/                     Telegram council bot (in-process) — deployable council-as-a-service
docs/architecture/       ผัง SVG + council-architecture.md (อธิบายสอง engine)
```

ทางลัด: โคลน repo นี้ แล้วบอกเอเจนต์ว่า

> อ่าน AGENTS.md กับ START-HERE.md แล้วพาฉันทำทีละขั้น
> จนกว่า LINE Official Account จะตอบจากโฟลเดอร์ knowledge ได้
> อย่าข้ามขั้น อย่าให้ฉันวางคีย์ลงในแชต


---

## Council mode (โหมดสภา)

เมื่อต้องตัดสินใจเรื่องใหญ่ ๆ เกี่ยวกับบอท เช่น เปลี่ยน prompt, เพิ่ม Telegram, ตัดไฟล์เก่าทิ้ง, เลือก embedding ตัวใหม่ — ใช้สภาช่วยคิด repo นี้มี **สอง engine** ให้เลือก

```bash
# Engine A — 0xNyk Council (vendored, default)
#   one LLM × 18 personas · 5-stage protocol · RAG-aware (rag-curator)
./bin/council "Should we add streaming responses to the LINE bot?"
./bin/council --quick --triad ship-now "Ship today with the flaky test?"
./bin/council --duo --members torvalds,rams "Is the prompt under 1,500 chars?"
./bin/council --triad architecture "Monorepo or polyrepo for adapters?"

# Engine B — karpathy LLM Council (adapted, when its app is on localhost:8001)
#   many LLMs × 3-stage protocol · cross-model-family review
./bin/llm-council "What do Claude, GPT, and Gemini each think of this prompt?"
./bin/llm-council --karpathy=off "Should we drop the Smart City standards section?"
```

สอง engine นี้ต่างกัน — ดู [docs/architecture/council-architecture.md](docs/architecture/council-architecture.md) สำหรับผังเปรียบเทียบและ decision rule ว่าเมื่อไหร่ใช้ตัวไหน

ตัวเลือกที่ใช้บ่อย (0xNyk):

| Flag | ความหมาย |
|---|---|
| `--quick` | โหมดเร็ว 2 รอบ ไม่มี cross-examination |
| `--duo` | สภา 2 คน เน้นดึงกัน (Torvalds vs Musashi, Rams vs Ada, …) |
| `--triad <name>` | สภา 3 คนตามโดเมน (architecture, ship-now, ai-product, …) |
| `--full` | สภาครบ 18 คน (overrides `.council.yaml`) |
| `--members a,b,c` | เลือกคนเอง (2–11 คน) |

ค่าตั้งต้นของ repo นี้อยู่ใน [`.council.yaml`](.council.yaml) — `profile: execution-lean`, `triad: ship-now`, `no_auto_route: true` เพราะเป็นโปรเจกต์ที่ต้อง ship

โฮสต์ที่รองรับ: **Claude Code** (ติดตั้งอยู่) และ **OpenCode** (ติดตั้งอยู่) — `bin/council` ตรวจให้อัตโนมัติว่าใช้ตัวไหน และติดตั้ง skill ให้เมื่อยังไม่มี (ดูตัวเลือก `--no-install` เมื่อไม่อยากให้ติดตั้ง)

เอเจนต์พิเศษที่เพิ่มเข้ามาสำหรับโปรเจกต์ RAG นี้: `council-rag-curator` — ผู้คุมคลังความรู้ ที่จะถามว่า "คำตอบนี้ยืนอยู่บนไฟล์จริงหรือเปล่า" ทุกครั้ง (ดู [council/agents/council-rag-curator.md](council/agents/council-rag-curator.md))

รายละเอียดทั้งหมดของโปรโตคอล: [council/SKILL.md](council/SKILL.md)  ·  ที่มาและใบอนุญาต: [council/VENDORED-FROM.md](council/VENDORED-FROM.md)  ·  แผนผัง: [docs/architecture/council-architecture.md](docs/architecture/council-architecture.md)

---

## แหล่งอ้างอิงที่ใช้ทำเด็ค

- [Get started with the Messaging API](https://developers.line.biz/en/docs/messaging-api/getting-started/)
- [Build a bot](https://developers.line.biz/en/docs/messaging-api/building-bot/)
- [Receive messages (webhook)](https://developers.line.biz/en/docs/messaging-api/receiving-messages/)
- [Cloudflare Quick Tunnels](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/)
- [Ollama · gemma4](https://ollama.com/library/gemma4)
- [Groq keys](https://console.groq.com/keys) · [Google AI Studio keys](https://aistudio.google.com/app/apikey)

---

© 2026 Non Arkaraprasertkul / Axiom X Co., Ltd. · MIT on original text and code in this repository.
LINE and Smart City Thailand marks remain their owners'.
