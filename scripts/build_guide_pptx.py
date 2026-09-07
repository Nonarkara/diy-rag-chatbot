"""Build the Axiom Editorial 16:9 Thai briefing PPTX."""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "LINE_RAG_OA_Guide_TH_Axiom.pptx"
LOGO = ROOT / "deck" / "logos"

PAPER = RGBColor(0xF6, 0xF5, 0xF2)
PANEL = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x19, 0x17, 0x12)
INK2 = RGBColor(0x6F, 0x6C, 0x63)
INK3 = RGBColor(0xA9, 0xA5, 0x9A)
LINE = RGBColor(0xE7, 0xE5, 0xDD)
BLUE = RGBColor(0x26, 0x24, 0x3F)
RED = RGBColor(0xA8, 0x32, 0x2B)

W = Inches(13.333)
H = Inches(7.5)


def set_run_font(run, size=14, bold=False, color=INK, italic=False, name="Sarabun"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = name
    rPr = run._r.get_or_add_rPr()
    # East Asian font so Thai actually renders
    ea = rPr.makeelement(qn("a:ea"), {"typeface": "Sarabun"})
    rPr.append(ea)
    cs = rPr.makeelement(qn("a:cs"), {"typeface": "Sarabun"})
    rPr.append(cs)


def add_textbox(slide, x, y, w, h, text, size=14, bold=False, color=INK, italic=False, align=PP_ALIGN.LEFT, name="Sarabun"):
    box = slide.shapes.add_textbox(x, y, w, h)
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    set_run_font(run, size=size, bold=bold, color=color, italic=italic, name=name)
    return box


def fill_slide(slide, color=PAPER):
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, W, H)
    bg.line.fill.background()
    bg.fill.solid()
    bg.fill.fore_color.rgb = color


def hairline(slide, x, y, w, h=Emu(12700)):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.line.fill.background()
    sh.fill.solid()
    sh.fill.fore_color.rgb = INK


def cell(slide, x, y, w, h, title, body, accent=False):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.line.color.rgb = LINE
    sh.line.width = Emu(6350)
    sh.fill.solid()
    sh.fill.fore_color.rgb = PANEL
    add_textbox(slide, x + Inches(0.16), y + Inches(0.12), w - Inches(0.28), Inches(0.28), title, size=10, bold=True, color=INK3, name="Inter")
    add_textbox(slide, x + Inches(0.16), y + Inches(0.4), w - Inches(0.28), h - Inches(0.5), body, size=13, color=INK if not accent else RED)


def chrome(slide, kicker, page, pages=18):
    fill_slide(slide)
    add_textbox(slide, Inches(0.5), Inches(0.22), Inches(8), Inches(0.28), "DR NON'S DIY RAG  ·  CHATBOT-AS-A-SELF-SERVICE", size=10, bold=True, color=INK3, name="Inter")
    add_textbox(slide, Inches(10.2), Inches(0.22), Inches(2.6), Inches(0.28), f"{page:02d} / {pages:02d}", size=10, bold=True, color=INK3, align=PP_ALIGN.RIGHT, name="Inter")
    hairline(slide, Inches(0.5), Inches(0.52), Inches(12.33))
    add_textbox(slide, Inches(0.5), Inches(0.62), Inches(12), Inches(0.28), kicker, size=11, bold=True, color=INK3, name="Inter")
    add_textbox(slide, Inches(0.5), Inches(7.18), Inches(9), Inches(0.22), "โฟลเดอร์คือสมอง  ·  ไลน์คือปาก  ·  โมเดลคือล่าม", size=10, color=INK3)
    add_textbox(slide, Inches(9.5), Inches(7.18), Inches(3.3), Inches(0.22), "Axiom Design Core  ·  Editorial", size=10, color=INK3, align=PP_ALIGN.RIGHT, name="Inter")


def bullets(slide, x, y, w, items, size=15):
    box = slide.shapes.add_textbox(x, y, w, Inches(5.2))
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(8)
        run = p.add_run()
        run.text = item
        set_run_font(run, size=size, color=INK)


def build():
    prs = Presentation()
    prs.slide_width = W
    prs.slide_height = H
    blank = prs.slide_layouts[6]

    # 1 cover
    s = prs.slides.add_slide(blank)
    fill_slide(s)
    add_textbox(s, Inches(0.7), Inches(0.7), Inches(12), Inches(0.3), "PRACTICAL BUILD GUIDE  ·  2026  ·  TH / EN", size=12, bold=True, color=INK3, name="Inter")
    add_textbox(s, Inches(0.7), Inches(1.5), Inches(12), Inches(1.1), "แร็กทำเองของดร.นน", size=40, color=INK)
    add_textbox(s, Inches(0.7), Inches(2.55), Inches(12), Inches(0.45), "DIY RAG / Chatbot-as-a-Self-Service", size=22, italic=True, color=INK, name="Spectral")
    add_textbox(s, Inches(0.7), Inches(3.3), Inches(12), Inches(1.4), "โฟลเดอร์คือสมอง\nไลน์คือปาก\nโมเดลคือล่าม — ไม่ใช่เจ้านาย", size=26, italic=True, color=RED)
    add_textbox(s, Inches(0.7), Inches(5.1), Inches(11), Inches(0.8), "โคลน repo นี้ → บอกเอเจนต์ให้อ่าน AGENTS.md → เอเจนต์พาไปทีละเว็บจน LINE OA ตอบจากไฟล์ได้", size=16, color=INK2)
    add_textbox(s, Inches(0.7), Inches(6.5), Inches(12), Inches(0.4), "ไม่ใช่ผลิตภัณฑ์ทางการของ depa / สำนักงานเมืองอัจฉริยะ / LINE", size=12, color=INK3)
    for i, name in enumerate(["axiom-mark.svg", "dr-non.svg"]):
        p = LOGO / name
        # svg may not embed; skip if pptx cannot
        if p.suffix == ".png" and p.exists():
            s.shapes.add_picture(str(p), Inches(10.6), Inches(0.55), Inches(0.42), Inches(0.42))
    png = LOGO / "axiom-logo.png"
    if png.exists():
        s.shapes.add_picture(str(png), Inches(12.15), Inches(0.45), Inches(0.7), Inches(0.7))

    # 2 idea
    s = prs.slides.add_slide(blank)
    chrome(s, "02  ·  THE IDEA", 2)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.5), "คิดให้ง่ายก่อน: ค้นก่อน แล้วค่อยตอบ", size=26)
    cell(s, Inches(0.5), Inches(1.7), Inches(2.3), Inches(3.6), "01  คนใช้", "ถามเป็นภาษาไทยใน LINE OA")
    cell(s, Inches(2.95), Inches(1.7), Inches(2.3), Inches(3.6), "02  WEBHOOK", "LINE ส่ง HTTPS POST\nตรวจลายเซ็นก่อนทำอะไร")
    cell(s, Inches(5.4), Inches(1.7), Inches(2.3), Inches(3.6), "03  ค้นในโฟลเดอร์", "เวกเตอร์ + คำตรงตัว\nbge-m3 · SQLite ไม่ใช่ Chroma")
    cell(s, Inches(7.85), Inches(1.7), Inches(2.3), Inches(3.6), "04  ล่าม", "โมเดลเรียบเรียงจากชิ้นที่ค้นได้เท่านั้น")
    cell(s, Inches(10.3), Inches(1.7), Inches(2.5), Inches(3.6), "05  กลับไลน์", "Push ไม่ใช่ Reply\nถอดมาร์กดาวน์ + คำเตือน AI", accent=True)
    add_textbox(s, Inches(0.5), Inches(5.5), Inches(12.3), Inches(1.3), "กฎทอง: ถ้าหลักฐานไม่พอ ต้องตอบว่าไม่พบในเอกสารที่มี — แทนการเดา\nอย่าเรียกสิ่งนี้ว่าเอเจนต์ จนกว่ามันจะต้องลงมือ (จองคิว รับเรื่อง ออกเอกสาร)", size=15, color=INK2)

    # 3 who does what
    s = prs.slides.add_slide(blank)
    chrome(s, "03  ·  WHO DOES WHAT", 3)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.55), "คนทำบัญชี — เอเจนต์ทำเครื่อง — คู่มือจับมือทีละเว็บ", size=24)
    cell(s, Inches(0.5), Inches(1.7), Inches(6.0), Inches(4.7), "คุณ (ไม่ต้องเขียนโค้ด)", "1. โคลน github.com/Nonarkara/diy-rag-chatbot\n2. เปิด Cursor / Claude Code ในโฟลเดอร์นี้\n3. พิมพ์: อ่าน AGENTS.md กับ START-HERE.md แล้วพาฉันทำทีละขั้น\n4. สมัคร LINE OA + เปิด Messaging API ตามที่เอเจนต์ชี้\n5. วางคีย์ลง .env เอง ห้ามวางในแชต\n6. โยนไฟล์ลง knowledge/\n7. กด START แล้ววาง webhook")
    cell(s, Inches(6.7), Inches(1.7), Inches(6.1), Inches(4.7), "เอเจนต์", "อ่าน START-HERE.md แล้วเปิด URL ทีละสถานี\nรอคำว่า เสร็จแล้ว ก่อนหน้าถัดไป\nสร้างโค้ดตาม LINE_RAG_Claude_Code_Master_Prompt.md\nห้าม Chroma / LangChain / LlamaIndex\nห้าม localhost ใน cloudflared — ใช้ 127.0.0.1")

    # 4 knowledge
    s = prs.slides.add_slide(blank)
    chrome(s, "04  ·  STEP 1  KNOWLEDGE FOLDER", 4)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.5), "เริ่มจากโฟลเดอร์เดียวที่เป็นแหล่งความจริง", size=24)
    cell(s, Inches(0.5), Inches(1.65), Inches(6.1), Inches(4.8), "โครงสร้าง", "knowledge/\n├── คู่มือพนักงาน.pdf\n├── ระเบียบ.docx\n├── FAQ.xlsx\n└── โครงการ/\n    └── รายงาน.md\n\nรองรับ PDF DOCX XLSX PPTX TXT MD\nจำแฮช — อ่านเฉพาะไฟล์ที่เปลี่ยนหรือใหม่\nลบไฟล์ = ลบออกจากดัชนี")
    cell(s, Inches(6.8), Inches(1.65), Inches(6.0), Inches(4.8), "กฎ", "โฟลเดอร์คือ source of truth\nดัชนี SQLite สร้างใหม่ได้เสมอ\nPDF สแกนไม่มีชั้นข้อความ ต้องทำเครื่องหมายบน /admin ห้ามแกล้งว่ามีข้อความ\nตัดชิ้นภาษาไทยตามประโยค ไม่ตัดตามช่องว่าง")

    # 5 rag stack
    s = prs.slides.add_slide(blank)
    chrome(s, "05  ·  STEP 2  LOCAL RAG", 5)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.5), "สแตกที่วัดแล้ว — ไม่ใช่สแตกที่บล็อกแนะนำ", size=24)
    labels = [
        ("READ", "ถอดข้อความ"),
        ("CHUNK", "ตัดเป็นชิ้น"),
        ("EMBED", "bge-m3"),
        ("STORE", "SQLite + FTS5"),
        ("SEARCH", "ลูกผสม RRF"),
        ("ANSWER", "ล่ามจากหลักฐาน"),
    ]
    for i, (a, b) in enumerate(labels):
        x = Inches(0.5) + i * Inches(2.1)
        cell(s, x, Inches(1.7), Inches(1.95), Inches(2.4), a, b)
    add_textbox(s, Inches(0.5), Inches(4.4), Inches(12.3), Inches(2.2), "ทำไมไม่ใช้ Chroma: เครื่องเดียว ไฟล์เดียวพอ วัดแล้ว cosine ทั้งคลังที่ 50,000 ชิ้นใช้ 52ms — ถูกกว่าการเรียกโมเดลร้อยเท่า และได้ FTS5 ไตรแกรมสำหรับไทยที่ไม่มีวรรค\nทำไมไม่ใช้ MiniLM: คลังไทย+อังกฤษต้อง bge-m3 — nomic-embed-text คะแนนเรื่องตรงกับเรื่องมั่วทับกัน ตั้งเกณฑ์ปฏิเสธไม่ได้\nminScore = 0.46 (วัดแล้ว)  ·  K=20  ·  lexical weight 0.6  ·  ไม่มีเกตหัวข้อด้วยโมเดลเล็ก", size=14, color=INK2)

    # 6 answer policy
    s = prs.slides.add_slide(blank)
    chrome(s, "06  ·  RAG LOGIC", 6)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.5), "คำตอบที่ดีต้องมีหลักฐาน ไม่ใช่แค่ฟังดูฉลาด", size=24)
    cell(s, Inches(0.5), Inches(1.65), Inches(4.0), Inches(4.8), "คำถาม", "「เบิกค่าเดินทางต่างจังหวัดได้วันละเท่าไร」")
    cell(s, Inches(4.7), Inches(1.65), Inches(4.0), Inches(4.8), "หลักฐาน", "ระเบียบค่าเดินทาง_2569.pdf หน้า 14\nFAQ_การเงิน.xlsx แถว 27\nถ้าคะแนนต่ำกว่า 0.46 และไม่มีคำตรงตัวที่หายาก → หยุด ไม่ส่งให้โมเดล")
    cell(s, Inches(8.9), Inches(1.65), Inches(3.9), Inches(4.8), "คำตอบ", "ตอบเฉพาะสิ่งที่หลักฐานรองรับ\nแนบชื่อไฟล์/หน้า\nถอด **มาร์กดาวน์**\nท้ายข้อความ: สร้างโดย AI อาจมีข้อผิดพลาด", accent=True)

    # 7 LINE OA
    s = prs.slides.add_slide(blank)
    chrome(s, "07  ·  STEP 3  LINE OFFICIAL ACCOUNT", 7)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.55), "สร้าง OA จากหน้าบัญชี — ไม่ใช่จาก Developers Console", size=22)
    bullets(s, Inches(0.5), Inches(1.7), Inches(12.2), [
        "1  Business ID  —  account.line.biz",
        "2  สร้าง Official Account  —  manager.line.biz",
        "3  ตั้งค่า → Messaging API → Enable Messaging API",
        "4  เลือก Provider ให้ถูก  ย้ายทีหลังไม่ได้",
        "5  ไป developers.line.biz/console ตรวจว่าชาแนลถูกสร้างแล้ว",
        "ตั้งแต่วันที่ 4 ก.ย. 2024 สร้าง Messaging API channel ตรงใน Console ไม่ได้อีกแล้ว",
        "รายละเอียดปุ่มทีละคลิก: START-HERE.md สถานี 3–7",
    ])

    # 8 keys
    s = prs.slides.add_slide(blank)
    chrome(s, "08  ·  LINE SETTINGS", 8)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.45), "สองคีย์ คนละหน้าที่ — เก็บใน .env ห้ามขึ้น Git", size=24)
    cell(s, Inches(0.5), Inches(1.6), Inches(6.1), Inches(2.2), "LINE_CHANNEL_SECRET", "ตรวจหัวข้อ x-line-signature ด้วย HMAC-SHA256 ของ raw body\nลายเซ็นผิด = 401 ไม่ประมวลผล")
    cell(s, Inches(6.8), Inches(1.6), Inches(6.0), Inches(2.2), "LINE_CHANNEL_ACCESS_TOKEN", "ให้เครื่องเรียก Messaging API\nLINE แนะนำ token แบบกำหนดวันหมดอายุ (v2.1)")
    cell(s, Inches(0.5), Inches(4.0), Inches(6.1), Inches(2.4), "Webhook", "ต้องเป็น HTTPS ใบรับรองที่เบราว์เซอร์เชื่อถือ\nUse webhook เปิดหลัง Verify สำเร็จ\nเอเจนต์ห้ามขอให้วางคีย์ลงแชต")
    cell(s, Inches(6.8), Inches(4.0), Inches(6.0), Inches(2.4), "OA Manager", "ปิดข้อความทักทาย\nปิดตอบกลับอัตโนมัติ\nไม่งั้นลูกค้าได้คำตอบซ้ำสองรอบ")

    # 9 agent builds machine
    s = prs.slides.add_slide(blank)
    chrome(s, "09  ·  STEP 4  THE AGENT BUILDS THE MACHINE", 9)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.5), "เอเจนต์สร้างเครื่อง — ไม่ได้เป็นเครื่อง", size=26)
    cell(s, Inches(0.5), Inches(1.65), Inches(6.1), Inches(4.8), "ทางลัด", "git clone https://github.com/Nonarkara/diy-rag-chatbot.git\ncd diy-rag-chatbot\n\nแล้วบอกเอเจนต์:\n「อ่าน AGENTS.md กับ START-HERE.md แล้วพาฉันทำทีละขั้น」\n\nอย่า mkdir โฟลเดอร์ว่างถ้าชุดนี้มีอยู่แล้ว")
    cell(s, Inches(6.8), Inches(1.65), Inches(6.0), Inches(4.8), "เส้นแบ่ง", "Claude Code / Cursor = สร้างและซ่อมโค้ด\nPython บนเครื่องคุณ = สิ่งที่ออนไลน์ 24/7 และคุยกับ LINE\n\nถ้ายังไม่มีเครื่องในโฟลเดอร์นี้ ให้เอเจนต์อ่าน LINE_RAG_Claude_Code_Master_Prompt.md แล้ว build → test → fix")

    # 10 must require
    s = prs.slides.add_slide(blank)
    chrome(s, "10  ·  AGENT BRIEF", 10)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.45), "บอกเอเจนต์ด้วยเกณฑ์ผ่าน ไม่ใช่แค่ว่าอยากได้บอท", size=22)
    bullets(s, Inches(0.5), Inches(1.6), Inches(12.2), [
        "01  สแกน ./knowledge แบบซ้อนโฟลเดอร์ + แฮชไฟล์",
        "02  bge-m3 + SQLite ลูกผสม  ไม่ใช่ Chroma / MiniLM",
        "03  POST /webhook ตรวจลายเซ็นก่อน  ตอบ 200 แล้วค่อยค้นพื้นหลัง",
        "04  คำตอบ RAG ส่งด้วย Push  Reply ใช้ได้แค่คำสั่งทันที",
        "05  ไม่มีหลักฐาน = ปฏิเสธภาษาคนใช้ + ช่องทางคน",
        "06  ถอดมาร์กดาวน์  คำเตือน AI  /privacy /forget /about",
        "07  หน้า /admin + START.command/START.bat + เทสอัตโนมัติ",
        "08  cloudflared ชี้ http://127.0.0.1:8000",
    ])

    # 11 tunnel
    s = prs.slides.add_slide(blank)
    chrome(s, "11  ·  STEP 5  HTTPS FOR LINE", 11)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.5), "ให้ localhost กลายเป็น HTTPS โดยไม่เปิดพอร์ทเราเตอร์", size=22)
    cell(s, Inches(0.5), Inches(1.65), Inches(3.9), Inches(3.3), "เครื่องคุณ", "127.0.0.1:8000\nห้ามพิมพ์ localhost")
    cell(s, Inches(4.7), Inches(1.65), Inches(3.9), Inches(3.3), "Cloudflare Tunnel", "https://xxxxx.trycloudflare.com\nเชื่อมออกจากเครื่อง")
    cell(s, Inches(8.9), Inches(1.65), Inches(3.9), Inches(3.3), "LINE webhook", "POST /webhook\nVerify แล้วค่อยเปิด Use webhook")
    add_textbox(s, Inches(0.5), Inches(5.2), Inches(12.3), Inches(1.4), "cloudflared tunnel --url http://127.0.0.1:8000\n\nQuick Tunnel = ทดลอง  ชื่อสุ่มตายเมื่อปิด   Named Tunnel / VPS = งานจริง\nคอมพิวเตอร์ปิด = บอทตาย  นี่คือสถาปัตยกรรม ไม่ใช่บั๊ก", size=15, color=RED)

    # 12 message path
    s = prs.slides.add_slide(blank)
    chrome(s, "12  ·  STEP 6  THE PATH OF ONE QUESTION", 12)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.45), "ทุกขั้นต้องมีเจ้าของ — โมเดลห้ามเดาเอง", size=22)
    bullets(s, Inches(0.5), Inches(1.55), Inches(12.2), [
        "1  LINE ส่ง POST + ลายเซ็น  (replyToken มีอายุสั้น)",
        "2  ตรวจลายเซ็น  ไม่ผ่าน → 401",
        "3  ตอบ 200 ทันที  ไปค้นพื้นหลัง",
        "4  ฝังคำถามด้วย bge-m3  ค้นลูกผสม",
        "5  ไม่มีหลักฐาน → ปฏิเสธในภาษาคนใช้ + มืออาชีพ",
        "6  มีหลักฐาน → โมเดลสรุป  ถอดมาร์กดาวน์  คำเตือน AI",
        "7  ส่งกลับด้วย Push  ไม่ใช้ replyToken ของงานที่ช้า",
        "8  ผิดพลาด → คำขอโทษสองภาษา  ห้ามเงียบ",
    ])

    # 13 tests
    s = prs.slides.add_slide(blank)
    chrome(s, "13  ·  ACCEPTANCE TESTS", 13)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.45), "ก่อนบอกว่าออนไลน์ ต้องผ่านชุดนี้", size=24)
    bullets(s, Inches(0.5), Inches(1.55), Inches(12.2), [
        "01  KNOWN ANSWER — ถามเรื่องใน PDF ได้คำตอบ + ชื่อไฟล์/หน้า",
        "02  UNKNOWN ANSWER — ปฏิเสธสุภาพ ไม่แต่ง",
        "03  FILE UPDATE — แกไฟล์แล้วดัชนีเฉพาะไฟล์นั้น คำตอบเปลี่ยนตาม",
        "04  BAD SIGNATURE — webhook ปลอมถูกปฏิเสธ",
        "05  DUPLICATE — webhookEventId ซ้ำไม่ตอบซ้ำ",
        "06  RESTART — เปิดใหม่แล้วดัชนีเดิมยังอยู่",
        "07  THAI — คำถามไทยไปถึงชิ้นภาษาไทยที่ถูก",
        "คนใหม่เพิ่มเพื่อน → พิมพ์คำถามได้คำตอบจากเอกสารโดยไม่ต้องเปิดเทอร์มินัล",
    ])

    # 14 security
    s = prs.slides.add_slide(blank)
    chrome(s, "14  ·  SECURITY & PRIVACY", 14)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.45), "ของง่ายไม่ควรเป็นของหลวม", size=24)
    items = [
        ("SECRETS", ".env + .gitignore  ห้ามคีย์ในซอร์สหรือประวัติ Git"),
        ("WEBHOOK", "ทุก POST จากเน็ตไม่น่าเชื่อถือจนกว่าจะตรวจลายเซ็น"),
        ("RAG DATA", "ส่งเฉพาะชิ้นที่ค้นได้  ไม่เคยอัปโหลดทั้งโฟลเดอร์"),
        ("DISCLOSE", "/about ตอนเพิ่มเพื่อน   /privacy  /forget ทันที"),
        ("BACKUP", "เอกสารต้นทางคือความจริง  ดัชนีพังแล้วสร้างใหม่ได้"),
        ("LOCAL ≠ OFFLINE", "แชตยังเดินทางผ่าน LINE  แม้โมเดลอยู่บนเครื่องนี้"),
    ]
    for i, (t, b) in enumerate(items):
        col = i % 3
        row = i // 3
        cell(s, Inches(0.5) + col * Inches(4.2), Inches(1.6) + row * Inches(2.4), Inches(4.0), Inches(2.2), t, b)

    # 15 deploy
    s = prs.slides.add_slide(blank)
    chrome(s, "15  ·  DEPLOYMENT", 15)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.45), "เริ่มบนแล็ปท็อปได้ แต่รู้ว่าเมื่อไรควรย้าย", size=22)
    cell(s, Inches(0.5), Inches(1.6), Inches(4.0), Inches(4.8), "A  เดโม", "แล็ปท็อป + Quick Tunnel\nเริ่มเร็วที่สุด\nเครื่องปิด = บอทหยุด\nเหมาะเวิร์กช็อป / นำร่อง")
    cell(s, Inches(4.7), Inches(1.6), Inches(4.0), Inches(4.8), "B  ทีมเล็ก", "แม็คมินิ / พีซีออฟฟิศ + Named Tunnel\nโดเมนคงที่  เปิด 24/7\nสำรองเอกสาร + auto restart")
    cell(s, Inches(8.9), Inches(1.6), Inches(3.9), Inches(4.8), "C  งานจริง", "วีพีเอส + โปรแกรมชุดเดียวกัน\nเฝ้าดู  หมุนคีย์  สำรอง\nอย่าเปิดพอร์ท 8000 สู่โลก")

    # 16 end state
    s = prs.slides.add_slide(blank)
    chrome(s, "16  ·  THE END STATE", 16)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.5), "ประสบการณ์ที่ควรได้: วางไฟล์ + ใส่ token + กด Start", size=22)
    cell(s, Inches(0.5), Inches(1.65), Inches(6.1), Inches(4.8), "SETUP", "Knowledge Folder  ./knowledge\nLINE Secret  ••••••\nLINE Token  ••••••\nAI  Groq / Gemini / Ollama gemma4:e4b\n\nBUILD KNOWLEDGE BASE\nSTART BOT")
    cell(s, Inches(6.8), Inches(1.65), Inches(6.0), Inches(4.8), "STATUS", "FILES INDEXED\nCHUNKS\nLINE CONNECTED\nWEBHOOK VERIFIED\nRAG READY\n\nBOT ONLINE\n\nถ้าคำถามมั่วยังไม่ถูกปฏิเสธ — ยังห้ามเปิดให้ลูกค้า", accent=True)

    # 17 copy paste
    s = prs.slides.add_slide(blank)
    chrome(s, "17  ·  COPY / PASTE", 17)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.45), "ห้าคำสั่ง — ที่เหลือคือการจับมือบนเว็บ", size=22)
    bullets(s, Inches(0.5), Inches(1.5), Inches(12.2), [
        "git clone https://github.com/Nonarkara/diy-rag-chatbot.git && cd diy-rag-chatbot",
        "เปิดเอเจนต์ในโฟลเดอร์นี้  แล้ววาง: อ่าน AGENTS.md กับ START-HERE.md แล้วพาฉันทำทีละขั้น",
        "เมื่อมี START.command แล้ว:  ./START.command",
        "cloudflared tunnel --url http://127.0.0.1:8000",
        "วาง https://….trycloudflare.com/webhook ใน Console แล้วกด Verify",
        "สไลด์ภาษาไทยเต็ม 31 หน้า:  deck/index.html   หรือ  nonarkara.github.io/diy-rag-chatbot",
    ])

    # 18 go live
    s = prs.slides.add_slide(blank)
    chrome(s, "18  ·  GO LIVE", 18)
    add_textbox(s, Inches(0.5), Inches(0.95), Inches(12), Inches(0.45), "เมื่อแปดช่องนี้เป็น — บอทพร้อมให้คนอื่นใช้", size=22)
    bullets(s, Inches(0.5), Inches(1.5), Inches(12.2), [
        "ไฟล์ทั้งหมดอยู่ใน ./knowledge และอ่านได้จริง",
        "ดัชนีพร้อม  เปลี่ยนไฟล์แล้ว re-index เฉพาะไฟล์นั้น",
        "LINE OA เปิด Messaging API แล้ว  ทักทายอัตโนมัติปิด",
        "Channel Secret / Access Token อยู่ใน .env ไม่ได้อยู่ใน Git",
        "Webhook เป็น HTTPS และ Verify ผ่าน  ลายเซ็นถูกตรวจทุกครั้ง",
        "คำถามที่ไม่มีหลักฐานไม่ถูกแต่งคำตอบ",
        "เครื่อง/เซิร์ฟเวอร์เปิดต่อเนื่อง มี restart และสำรองเอกสาร",
        "นี่ไม่ใช่ผลิตภัณฑ์ทางการของ depa หรือ LINE  — ชุดสอนของดร.นน / Axiom X",
    ])

    prs.save(OUT)
    print("wrote", OUT, "slides", len(prs.slides))


if __name__ == "__main__":
    build()
