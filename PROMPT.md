# PROMPT.md — วางไฟล์นี้ในโฟลเดอร์ว่าง แล้วให้เอเจนต์สร้างเครื่อง

Claude Code ควรสร้างเครื่อง ไม่ควร *เป็น* เครื่อง

คัดลอกทั้งหมดด้านล่างไปให้เอเจนต์ (Claude Code, Cursor, อื่น ๆ)

---

Build a LINE Official Account RAG chatbot in this directory.

The product is:

> Put documents in a folder → connect a LINE Official Account → run one command → you have a RAG chatbot.

Mental model, do not violate:

- The folder is the brain.
- LINE is the mouth.
- The LLM is the interpreter, not the boss.
- Do not call this an "AI agent" unless it actually needs tools. Retrieval → LLM → answer is the whole system.

REQUIREMENTS

1. Everything inside ./knowledge is the knowledge base. Recursively scan all folders.

2. Support PDF, DOCX, XLSX, PPTX, TXT, Markdown.

3. Maintain an index of file hashes (SHA-256 of bytes).
   Only re-index changed or new files.
   Remove deleted files from the index.

4. Use bge-m3 via Ollama for embeddings. Do not use nomic-embed-text if the corpus may contain Thai: its on-topic and off-topic score ranges overlap, so honest refusal is impossible. Record the embedder name in the index and refuse to search a mismatched corpus.

5. Store chunks locally in one SQLite file next to the project (not Chroma, not Pinecone, not Postgres).
   Hybrid retrieval:
   - dense cosine over all chunks (brute force is fine under 50k chunks)
   - FTS5 trigram lexical search (Thai has no spaces)
   - Reciprocal Rank Fusion, K=20, lexical weight 0.6
   - rarity ceiling = min(25% of chunks, 40)
   - minScore 0.46 for bge-m3 (measured: on-topic 0.50–0.61, off-topic ≤ 0.42)
   There is NO LLM "is this on topic?" classifier. Retrieval already answers that.

6. Thai chunking: split on blank lines, keep headings with the following block, break oversized blocks on sentence punctuation (. ! ? 。 ฯ), never on spaces.

7. FastAPI (or equivalent) on 127.0.0.1:8000.

8. POST /webhook for LINE Messaging API.
   Verify HMAC-SHA256 of the raw body against header x-line-signature and LINE_CHANNEL_SECRET before doing anything.
   Return 200 immediately; process the question in the background.
   Answer with Push, not Reply — LINE reply tokens die in ~30 seconds and RAG is often slower.
   Instant commands (/about /privacy /forget) may use Reply.
   On any exception, Push a bilingual apology. Never go silent.
   On follow, disclose that the responder is automated.

9. The LLM must not invent. If retrieval is empty or below minScore with no rare-term hit, refuse in the user's language and include a human handoff contact.
   Language is decided in code from the question script (Thai characters → Thai), not left to the model.
   Strip Markdown and [#n] citation markers before sending to LINE. LINE renders a chat bubble, not Markdown.
   Append an AI disclaimer on every generated answer.

10. Secrets only in .env. Never in source. Provide .env.example.

11. START.command (Mac) and START.bat (Windows) that:
    - create a venv
    - install requirements
    - copy .env.example → .env if missing
    - update the knowledge index
    - start the server
    - start the folder watcher
    - print status

12. Localhost admin page: files indexed, chunk count, last indexed, LINE connection, LLM connection, recent questions, retrieval preview, errors.

13. Answer providers, tried in order when ANSWER_PROVIDER=auto:
    Groq (openai/gpt-oss-20b), Gemini, OpenAI, Anthropic, OpenRouter, then local Ollama (gemma4:e4b, or gemma4:e2b on 8 GB RAM).
    Embeddings always local.

14. Automated tests that do not need the network:
    - bad LINE signature → 401
    - file hash skip
    - off-topic question refused
    - Markdown stripped
    - Thai chunker does not split inside a syllable when punctuation exists

15. Do not add LangChain, LlamaIndex, or Chroma.
16. Do not expose API keys.
17. README in Thai and English for a non-technical owner.
18. Cloudflare: document `cloudflared tunnel --url http://127.0.0.1:8000` and the rule "if the computer is off, the bot is dead." Never bind the origin as localhost — use 127.0.0.1.

Build it, run the tests, fix errors, and leave the complete working project in this directory.
