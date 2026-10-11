# Pattern: Deployment

The OOTBPAP promise is *local-first*. Deployment is opt-in. The
right deployment depends on what the user actually needs: a
personal tool, a small team's bot, a public website, a webhook
for a channel that needs to be reachable from the public internet.

## Decision tree

```
What does the user need?
├── Personal / single-machine / "I run it"
│   └── ./bin/start on the user's laptop. Document the OS-specific
│       how-to-start-on-boot (launchd on macOS, systemd on Linux).
│
├── Public static site
│   ├── GitHub Pages     (zero config, free)
│   ├── Netlify          (zero config, free tier, forms)
│   ├── Cloudflare Pages (zero config, free tier, fastest)
│   └── S3 + CloudFront  (when you outgrow the above)
│
├── Public webhook (LINE / Telegram / Discord)
│   ├── Railway          (recommended, free tier, ~$5/mo paid)
│   ├── Render           (similar to Railway)
│   ├── Fly.io           (free tier, edge deploys)
│   ├── Cloudflare Worker (best for low-latency, but Python → Pyodide)
│   └── DO NOT USE Vercel for webhooks (10s timeout, cold starts)
│
└── Internal tool (small team, not public)
    └── A small VM (Hetzner, DigitalOcean) or a Raspberry Pi
        with `cloudflared tunnel` exposing it.
```

## Railway (the recommended default)

```bash
# 1. Install the CLI
npm i -g @railway/cli
railway login

# 2. From the project root
railway init
railway up

# 3. Set env vars in the Railway dashboard, or:
railway variables set LLM_PROVIDER=ollama TELEGRAM_BOT_TOKEN=...
```

Railway reads `Procfile` or `railway.toml` for the start command.
The starter has neither. Add a `Procfile`:

```
web: uvicorn app:app --host 0.0.0.0 --port $PORT
```

Or `railway.toml`:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uvicorn app:app --host 0.0.0.0 --port $PORT"
```

## Render

Same shape as Railway, slightly different config:

```yaml
# render.yaml
services:
  - type: web
    name: my-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: LLM_PROVIDER
        value: ollama
      - key: LLM_BASE_URL
        value: http://localhost:11434
```

## Cloudflare Pages (for static sites only)

```bash
# Install wrangler
npm i -g wrangler

# From the webpage template project root
wrangler pages deploy .
```

Cloudflare Pages auto-detects static HTML, serves over their CDN,
free. The OOTBPAP's `webpage` template is shaped for this — no
build step, just drag-and-drop the folder.

## GitHub Pages (for static sites)

```bash
# Add to the project root
echo "mysite.com" > docs/CNAME   # optional

# In the repo settings → Pages:
#   Source: main / docs (or main / root, depending on your layout)
#   Branch: main
#   Save
```

## Cloudflare Tunnel (for a personal machine exposing a webhook)

This is the right move for "I want my bot running 24/7 on my
laptop without paying for a server."

```bash
brew install cloudflared
cloudflared tunnel login
cloudflared tunnel create my-bot
cloudflared tunnel route dns my-bot bot.example.com
cloudflared tunnel run my-bot --url http://127.0.0.1:8000
```

Then point the channel's webhook URL at `https://bot.example.com`.

## Things to NOT do

- **Vercel for webhooks** — 10s timeout, cold starts. The LINE
  webhook will silently drop messages.
- **Heroku free tier** — gone. Paid tier is $7/mo minimum, no
  advantage over Railway.
- **AWS Lambda for the bot** — cold starts break the webhook
  flow. Use Railway/Render/Fly instead.
- **Kubernetes** — overkill for any OOTBPAP project. Don't.

## Cost

| Tier | Cost | What you get |
|---|---|---|
| Local only | $0 | The user's laptop, no internet, Ollama |
| GitHub Pages / Netlify / CF Pages | $0 | Static sites |
| Railway free tier | $0 (with limits) | Webhooks, sleep after idle |
| Railway paid | $5/mo | Webhooks, no sleep, custom domain |
| Render paid | $7/mo | Webhooks, no sleep |
| Hetzner VM | €4/mo | Always-on VM, full control |

For a single bot with a few hundred users, the local-only or
free-tier options are fine. The user only needs to pay when they
have a real reason — don't push them to Railway on day one.
