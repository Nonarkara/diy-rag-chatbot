# Pattern: API integration (LINE / Telegram / Discord / web)

The `templates/chatbot/` ships a FastAPI app that implements two
endpoints: `GET /health` and `POST /ask`. Adding a channel means
adding one more webhook handler. Each handler has the same shape:

```python
@app.post("/webhook/<channel>")
async def webhook_<channel>(req: Request) -> Response:
    # 1. Verify the channel's signature
    # 2. Extract the user's question
    # 3. Call `answer(question)` to get the reply
    # 4. Send the reply back through the channel
    return Response(status_code=200)
```

## LINE

LINE Messaging API uses HMAC-SHA256 on the request body, with the
secret in the `x-line-signature` header.

```python
import hashlib, hmac, base64
from fastapi import Request, HTTPException

LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"].encode()

@app.post("/webhook/line")
async def webhook_line(req: Request) -> dict:
    body = await req.body()
    sig = req.headers.get("x-line-signature", "")
    digest = hmac.new(LINE_CHANNEL_SECRET, body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    if not hmac.compare_digest(sig, expected):
        raise HTTPException(status_code=401, detail="bad signature")
    payload = await req.json()
    for ev in payload.get("events", []):
        if ev["type"] != "message":
            continue
        user_msg = ev["message"]["text"]
        reply = answer(user_msg)
        # Send reply via LINE's /v2/bot/message/push endpoint
        await send_line_reply(ev["replyToken"], reply)
    return {"ok": True}
```

Tunnels: `cloudflared tunnel --url http://127.0.0.1:8000` exposes
the local server; paste the URL into the LINE Developers Console
as the webhook URL. **Origin is `http://127.0.0.1:8000`, never
`localhost`** — LINE rejects `localhost`.

LINE uses **Push** (POST to `/v2/bot/message/push`), not Reply. The
`replyToken` expires after a few seconds.

## Telegram

Telegram has two ways: polling (long-running) or webhooks (server-side).
For the OOTBPAP use case, use webhooks. The kit's `bot/` package
is the polling variant — re-implement with webhooks when the user
wants to deploy.

```python
import hashlib, hmac

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

@app.post("/webhook/telegram")
async def webhook_telegram(req: Request) -> dict:
    body = await req.body()
    # Telegram signs with the bot token in the X-Telegram-Bot-Api-Secret-Token
    # header if you set it. Otherwise just process the body.
    payload = await req.json()
    msg = payload.get("message") or {}
    text = msg.get("text", "")
    if text:
        reply = answer(text)
        await send_telegram_reply(msg["chat"]["id"], reply)
    return {"ok": True}
```

## Discord

Discord uses Ed25519 signatures in the `X-Signature-Ed25519` header
on Interactions.

```python
import nacl.signing  # pip install pynacl

DISCORD_PUBLIC_KEY = bytes.fromhex(os.environ["DISCORD_PUBLIC_KEY"])

@app.post("/webhook/discord")
async def webhook_discord(req: Request) -> dict:
    body = await req.body()
    sig = req.headers.get("X-Signature-Ed25519", "")
    timestamp = req.headers.get("X-Signature-Timestamp", "")
    verify = nacl.signing.VerifyKey(DISCORD_PUBLIC_KEY)
    try:
        verify.verify(timestamp.encode() + body, bytes.fromhex(sig))
    except nacl.exceptions.BadSignatureError:
        raise HTTPException(status_code=401, detail="bad signature")
    payload = await req.json()
    if payload.get("type") == 1:
        # PING
        return {"type": 1}
    # PING done; handle the command
    ...
```

## Web (generic)

`POST /ask` with `{"q": "..."}` is the lowest common denominator.
The starter already implements it. A simple HTML form:

```html
<form method="post" action="/ask" onsubmit="return submitAsk(event)">
  <input name="q" placeholder="Ask a question…">
  <button>Send</button>
</form>
```

with a `fetch` overlay for SPA-style UX.

## Common mistakes

- **Skipping signature verification** — without it, anyone can
  send messages to the bot. Always verify.
- **Hardcoding secrets** — read from `.env`, never paste tokens
  into source files.
- **Re-asking the user for tokens** — if `.env` is missing, tell
  the user to fill it in and only say 「ใส่แล้ว」, never paste
  the token into chat.
- **Logging the full request body** — secrets leak. Log only the
  event type and the user ID.
