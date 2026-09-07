# เริ่มที่นี่ — จับมือทำทีละเว็บ

ชุดนี้ชื่อ **Dr Non's DIY RAG / Chatbot-as-a-Self-Service**

ทางลัดที่ถูก:

1. โคลน repo นี้
2. เปิด Cursor / Claude Code / เอเจนต์ใดก็ได้ในโฟลเดอร์นี้
3. พิมพ์ประโยคนี้:

> อ่าน AGENTS.md กับ START-HERE.md แล้วพาฉันทำทีละขั้น จนกว่า LINE Official Account จะตอบจากโฟลเดอร์ knowledge ได้ อย่าข้ามขั้น อย่าให้ฉันวางคีย์ลงในแชต

เอเจนต์จะเปิดเว็บให้ทีละหน้า บอกปุ่มที่ต้องกด แล้วรอให้คุณพิมพ์ **เสร็จแล้ว**

ถ้าไม่มีเอเจนต์ อ่านไฟล์นี้จากบนลงล่างเองก็ได้ — ลิงก์ทุกอันเปิดได้จริง

ไม่ใช่ผลิตภัณฑ์ทางการของ depa, สำนักงานเมืองอัจฉริยะ, หรือ LINE

---

## สิ่งที่จะได้เมื่อจบ

คนทัก LINE Official Account ของคุณ → ระบบค้นไฟล์ในโฟลเดอร์ `knowledge/` → ตอบจากไฟล์นั้นเท่านั้น → ถ้าไม่มีในไฟล์ จะพูดว่าไม่มี ไม่เดา

คอมพิวเตอร์เครื่องนี้ต้องเปิดอยู่ ปิดเครื่อง = บอทตาย

---

## สถานี 0 · โคลนชุดนี้

บนแม็ค เปิด Terminal แล้ววาง:

```bash
git clone https://github.com/Nonarkara/diy-rag-chatbot.git
cd diy-rag-chatbot
```

ถ้ายังไม่มี git: เปิด [github.com/Nonarkara/diy-rag-chatbot](https://github.com/Nonarkara/diy-rag-chatbot) → ปุ่มเขียว **Code** → **Download ZIP** → แตกไฟล์ → เปิดโฟลเดอร์นั้นใน Cursor

ดูภาพรวมได้ที่ `deck/index.html` (ลูกศรซ้ายขวา) หรือ https://nonarkara.github.io/diy-rag-chatbot/

พิมพ์ **เสร็จแล้ว** เมื่อโฟลเดอร์นี้เปิดอยู่ในเอเจนต์แล้ว

---

## สถานี 1 · ติดตั้ง Python

เปิด: https://www.python.org/downloads/

1. กดปุ่มเหลือง **Download Python**
2. ติดตั้ง
3. **บนวินโดวส์: ติ๊ก “Add python.exe to PATH”** ก่อนกด Install
4. ปิดหน้าต่างติดตั้ง

ตรวจว่าใช้ได้ — เปิด Terminal / PowerShell พิมพ์:

```bash
python3 --version
```

ต้องเห็น `Python 3.11` หรือใหม่กว่า (บนวินโดวส์ถ้า `python3` ไม่มี ลอง `python --version`)

พิมพ์ **เสร็จแล้ว** เมื่อเห็นเลขรุ่น

---

## สถานี 2 · เลือกสมอง

เลือกอย่างใดอย่างหนึ่งก่อน ใส่อีกอันทีหลังได้

### ทาง A — ในเครื่อง (ข้อความไม่ออกจากบ้าน)

เปิด: https://ollama.com/download

1. ดาวน์โหลด Ollama สำหรับแม็คหรือวินโดวส์
2. ติดตั้ง แล้วเปิดแอป Ollama ค้างไว้
3. ใน Terminal:

```bash
ollama pull bge-m3
ollama pull gemma4:e4b
```

แรม 8 GB ให้ใช้ `gemma4:e2b` แทน e4b  
`bge-m3` บังคับถ้าเอกสารมีภาษาไทย — อย่าใช้ nomic-embed-text

### ทาง B — คีย์ฟรีบนเน็ต (เร็ว โควตามีเพดาน)

เปิด: https://console.groq.com/keys

1. Sign up ด้วย Google / GitHub / อีเมล — **ไม่ต้องบัตร**
2. เมนูซ้าย **API Keys** → **Create API Key**
3. ตั้งชื่อ เช่น `diy-rag`
4. คัดลอกคีย์ **ทันที** (โชว์ครั้งเดียว) ไปไว้ในโน้ตบนเครื่องคุณ อย่าวางในแชต

ทางอื่น: https://aistudio.google.com/app/apikey (Gemini)

พิมพ์ **เสร็จแล้ว** เมื่อ Ollama โหลดโมเดลครบ หรือมีคีย์อยู่ในโน้ตบนเครื่อง

---

## สถานี 3 · สมัคร LINE Business ID

เปิด: https://account.line.biz/

1. เข้าสู่ระบบด้วยบัญชี LINE ของคุณ หรือสมัครด้วยอีเมล
2. ถ้าขึ้นแบบฟอร์มนักพัฒนา / ธุรกิจ ให้กรอกชื่อกับอีเมลจริง
3. จบเมื่อเข้าหน้าบัญชีได้โดยไม่มีหน้า error

แหล่งที่มา: [LINE — Get started with the Messaging API](https://developers.line.biz/en/docs/messaging-api/getting-started/)

พิมพ์ **เสร็จแล้ว** เมื่อล็อกอิน account.line.biz ได้

---

## สถานี 4 · สร้าง LINE Official Account

เปิด: https://manager.line.biz/

1. ถ้ายังไม่มี OA ให้กดสร้าง Official Account
2. กรอกชื่อบัญชีที่จะให้ลูกค้าเห็น เช่น 「บอทความรู้หน่วยงาน」
3. บันทึก
4. เข้าหน้าจัดการบัญชีนั้นได้

คุณยัง **ไม่** ไปที่ Developers Console ในขั้นนี้

พิมพ์ **เสร็จแล้ว** เมื่อเห็นชื่อบัญชีใน OA Manager

---

## สถานี 5 · เปิด Messaging API จากหน้าบัญชี

ยังอยู่ที่ https://manager.line.biz/ — เลือกบัญชีที่เพิ่งสร้าง

1. เมนู **ตั้งค่า** (Settings)
2. **Messaging API**
3. กด **Enable Messaging API** / เปิดใช้งาน Messaging API
4. ถ้าขึ้นให้สร้างบัญชีนักพัฒนา กรอกชื่อกับอีเมล
5. **เลือก Provider** — อ่านก่อนกด ย้ายชาแนลข้าม Provider ทีหลังไม่ได้
6. ตกลงจนจบ

ตั้งแต่วันที่ **4 กันยายน 2024** สร้าง Messaging API channel ตรงจาก Developers Console ไม่ได้อีกแล้ว ปุ่มนั้นไม่มีเพราะถูกปิด ไม่ใช่เพราะคุณหาไม่เจอ

พิมพ์ **เสร็จแล้ว** เมื่อหน้า Messaging API ใน OA Manager ไม่ขึ้นปุ่ม Enable แล้ว

---

## สถานี 6 · หยิบสองคีย์ จาก Developers Console

เปิด: https://developers.line.biz/console/

ล็อกอินด้วย **บัญชีเดียวกับ** ที่ใช้ใน OA Manager

1. คลิก **Provider** ที่เลือกตอนสถานี 5
2. คลิกชาแนลประเภท **Messaging API** (ชื่อเดียวกับ OA)
3. แท็บ **Basic settings**
   - คัดลอก **Channel secret** → เปิดไฟล์ `.env` ในโฟลเดอร์นี้ (ถ้ายังไม่มี ให้คัดลอกจาก `.env.example`) วางที่บรรทัด `LINE_CHANNEL_SECRET=`
4. แท็บ **Messaging API**
   - ช่อง **Channel access token** กด **Issue**
   - ใช้แบบกำหนดวันหมดอายุได้ (v2.1) ดีกว่าแบบไม่มีวันหมด
   - วางที่บรรทัด `LINE_CHANNEL_ACCESS_TOKEN=` ใน `.env`
5. อย่าแคปหน้าจอที่มีโทเคน อย่าคอมมิต `.env` อย่าวางค่าลงแชตนี้

สองคีย์คนละหน้าที่:

| ฟิลด์ใน `.env` | ทำอะไร |
|---|---|
| `LINE_CHANNEL_SECRET` | พิสูจน์ว่าเว็บฮุคมาจาก LINE จริง |
| `LINE_CHANNEL_ACCESS_TOKEN` | ให้เครื่องคุณส่งข้อความกลับ |

พิมพ์ **เสร็จแล้ว** เมื่อ `.env` มีสองบรรทัดนี้ไม่ว่าง (ไม่ต้องโชว์ค่า)

---

## สถานี 7 · ปิดทักทายและตอบอัตโนมัติ

กลับไป https://manager.line.biz/ → บัญชีคุณ

1. **การตอบกลับ** / Response
2. **ข้อความทักทาย** = ปิด
3. **ข้อความตอบกลับอัตโนมัติ** = ปิด

ค่าเริ่มต้นตอนเปิด Messaging API คือเปิดทั้งคู่ คนใช้จะได้คำตอบซ้ำสองรอบ

ยังไม่ต้องใส่ Webhook URL ในขั้นนี้ จะใส่หลังอุโมงค์ติด

พิมพ์ **เสร็จแล้ว** เมื่อสวิตช์สองตัวเป็นปิด

---

## สถานี 8 · โยนไฟล์ลงสมอง

ในโฟลเดอร์โปรเจกต์มี `knowledge/`

1. วาง PDF / Word / Excel / PowerPoint / ข้อความ / Markdown ที่บอทควรตอบได้
2. ซ้อนโฟลเดอร์ย่อยได้
3. อย่าวางรหัสผ่าน เลขบัญชี สัญญาลับ ถ้าเครื่องไม่ได้เปิด FileVault / BitLocker
4. PDF ที่เป็นภาพสแกนล้วน ยังอ่านไม่ได้ในรุ่นนี้ — ส่งออกเป็นข้อความจากเวิร์ดก่อน

เริ่มด้วยสามไฟล์ที่คุณตอบเป็นประจำก็พอ

พิมพ์ **เสร็จแล้ว** เมื่อมีไฟล์ใน `knowledge/`

---

## สถานี 9 · เติม `.env` ให้จบ

เปิด `.env` ด้วย TextEdit / Notepad (ห้ามใช้ Pages)

อย่างน้อยต้องมี:

```
LINE_CHANNEL_SECRET=...
LINE_CHANNEL_ACCESS_TOKEN=...
ANSWER_PROVIDER=auto
KNOWLEDGE_FOLDER=./knowledge
BOT_LANGUAGE=th
BOT_NAME=บอทความรู้หน่วยงาน
```

ถ้าใช้ Groq ใส่ `GROQ_API_KEY=`  
ถ้าใช้เฉพาะเครื่อง ใส่

```
ANSWER_PROVIDER=ollama
OLLAMA_CHAT_MODEL=gemma4:e4b
OLLAMA_EMBED_MODEL=bge-m3
```

พิมพ์ **เสร็จแล้ว** เมื่อบันทึกไฟล์แล้ว

---

## สถานี 10 · กด START

เมื่อมี `START.command` / `START.bat` ในโฟลเดอร์นี้:

- แม็ค: ดับเบิลคลิก `START.command` (ครั้งแรกอาจต้องคลิกขวา → เปิด)
- วินโดวส์: ดับเบิลคลิก `START.bat`

ถ้าเอเจนต์เพิ่งสร้างเครื่องตาม `LINE_RAG_Claude_Code_Master_Prompt.md` ให้รันสคริปต์นั้นหลังเทสผ่าน

หน้าต่างจะบอก URL ท้องถิ่น ปกติคือ `http://127.0.0.1:8000`  
เปิด `http://127.0.0.1:8000/admin` ต้องเห็นจำนวนไฟล์ที่อ่านแล้ว

พิมพ์ **เสร็จแล้ว** เมื่อหน้าแอดมินขึ้น

---

## สถานี 11 · ให้ LINE หาเครื่องคุณเจอ

ติดตั้ง cloudflared: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

เปิด Terminal **หน้าต่างใหม่** (หน้าต่าง START ต้องเปิดค้าง) แล้ววาง:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

ใช้ `127.0.0.1` ห้ามพิมพ์ `localhost` — cloudflared จะไป IPv6 แล้วเครื่องคุณฟัง IPv4

รอจนขึ้นบรรทัดประมาณ:

```text
https://something.trycloudflare.com
```

คัดลอก URL นั้นทั้งก้อน ต่อท้าย `/webhook`  
ได้เป็น `https://something.trycloudflare.com/webhook`

Quick Tunnel สำหรับทดสอบ ชื่อสุ่มเปลี่ยนทุกครั้งที่เปิดใหม่  
คอมพิวเตอร์หลับหรือปิด = บอทตาย

พิมพ์ **เสร็จแล้ว** เมื่อมี URL ที่ขึ้นต้นด้วย `https://` และลงท้าย `/webhook`

---

## สถานี 12 · วาง webhook แล้วกด Verify

เปิด: https://developers.line.biz/console/ → Provider → ชาแนล Messaging API → แท็บ **Messaging API**

1. ช่อง **Webhook URL** กด Edit
2. วาง URL จากสถานี 11
3. Update
4. กด **Verify** — ต้องขึ้น Success
5. เปิดสวิตช์ **Use webhook**

ถ้า Verify ไม่ผ่าน: START ยังเปิดอยู่หรือไม่ · อุโมงค์ชี้ `127.0.0.1:8000` หรือไม่ · URL มี `/webhook` หรือไม่

พิมพ์ **เสร็จแล้ว** เมื่อ Verify ขึ้น Success และ Use webhook เป็นเปิด

---

## สถานี 13 · ทดสอบสองคำถาม

ในแท็บ Messaging API มี **QR code** ของ OA

1. สแกนด้วยมือถือที่ล็อกอิน LINE ของคุณ
2. เพิ่มเพื่อน
3. ถามเรื่องที่ **มีในไฟล์** — ต้องได้คำตอบและชื่อไฟล์ ไม่มีดอกจัน `**`
4. ถามเรื่องมั่ว เช่น สีเสื้อนายกรัฐมนตรี — ต้องถูกปฏิเสธ ไม่เดา
5. ถ้าเงียบ: ดูหน้าต่าง START อย่าเดา

ถ้าข้อ 4 ไม่ปฏิเสธ **ยังห้ามเปิดให้ลูกค้า**

พิมพ์ **เสร็จแล้ว** เมื่อทั้งสองข้อเป็นไปตามนั้น

---

## หลังวันนี้

- เพิ่มไฟล์ใน `knowledge/` ได้เลย ระบบอ่านเฉพาะไฟล์ที่เปลี่ยน
- งานจริงทั้งวัน: Named Cloudflare Tunnel + เครื่องที่เปิดค้าง (แม็คมินิ) หรือวีพีเอส — โปรแกรมชุดเดียวกัน
- ถ้าคีย์ไลน์เคยโผล่ในภาพ ออกโทเคนใหม่ใน Console แล้วลบของเก่า
- `/privacy` `/forget` `/about` ต้องตอบได้โดยไม่เรียกโมเดล

เมื่อของพัง ดูตารางท้าย `deck/index.html` (สไลด์ 「เมื่อของพัง」) หรือถามเอเจนต์ว่า 「อ่าน START-HERE.md สถานีปัจจุบัน แล้วช่วยดู」

---

## ไฟล์ในชุดนี้

| ไฟล์ | สำหรับใคร |
|---|---|
| `START-HERE.md` | คุณ — จับมือทีละเว็บ |
| `AGENTS.md` | เอเจนต์ — ห้ามข้ามขั้น |
| `LINE_RAG_Claude_Code_Master_Prompt.md` | เอเจนต์ — สร้างเครื่อง |
| `deck/index.html` | สไลด์ภาษาไทย 31 หน้า |
| `LINE_RAG_OA_Guide_TH_Axiom.pptx` / `.pdf` | สำเนานำเสนอ |

แหล่งอ้างอิงปุ่มและลำดับหน้า: LINE Messaging API Getting Started, Build a bot, Receive messages; Cloudflare Quick Tunnels; Ollama gemma4; Groq Console; Google AI Studio
