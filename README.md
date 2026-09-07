# Dr Non's DIY RAG / Chatbot-as-a-Self-Service

**แร็กทำเองของดร.นน · แชตบอทบริการตนเอง**

> โฟลเดอร์คือสมอง · ไลน์คือปาก · โมเดลคือล่าม

คู่มือภาษาไทยทีละขั้น สำหรับคนที่ไม่เขียนโค้ด แต่ชี้ URL ได้ สมัครบัญชีได้ และวางข้อความให้เอเจนต์ได้

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

A 31-slide Thai briefing (`deck/`) and an 18-slide Axiom PowerPoint/PDF sit in the repo. The bot **answers only from those files** and **refuses when it cannot**.

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

บทเรียนมาจากระบบที่วิ่งอยู่ที่ [rag.nonarkara.org](https://rag.nonarkara.org) ไม่ใช่จากบล็อกทฤษฎี

---

## โครงสร้าง

```
START-HERE.md            จับมือทีละเว็บ (อ่านไฟล์นี้ก่อน)
AGENTS.md                สัญญาของเอเจนต์ — พาทีละสถานี
LINE_RAG_Claude_Code_Master_Prompt.md   ให้เอเจนต์สร้างเครื่อง
LINE_RAG_OA_Guide_TH_Axiom.pptx / .pdf  สำเนานำเสนอ 18 หน้า
deck/                    สไลด์ภาษาไทย 31 หน้า
PROMPT.md                ชี้ไปที่ master prompt
```

ทางลัด: โคลน repo นี้ แล้วบอกเอเจนต์ว่า

> อ่าน AGENTS.md กับ START-HERE.md แล้วพาฉันทำทีละขั้น
> จนกว่า LINE Official Account จะตอบจากโฟลเดอร์ knowledge ได้
> อย่าข้ามขั้น อย่าให้ฉันวางคีย์ลงในแชต


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
