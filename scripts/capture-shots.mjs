#!/usr/bin/env node
/**
 * Capture public welcome/signup pages into docs/shots/.
 * These are wayfinding stills so a human can match the screen in front of them.
 * Never capture a page that already shows an API key.
 */
import { mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const OUT = join(ROOT, 'docs', 'shots')
mkdirSync(OUT, { recursive: true })

const PAGES = [
  { file: 'line-business-id.png', url: 'https://manager.line.biz/' },
  { file: 'line-developers.png', url: 'https://developers.line.biz/en/' },
  { file: 'vercel-signup.png', url: 'https://vercel.com/signup' },
  { file: 'railway.png', url: 'https://railway.com/' },
  { file: 'render.png', url: 'https://render.com/' },
  { file: 'claude-code.png', url: 'https://claude.com/product/claude-code' },
  { file: 'groq-keys.png', url: 'https://console.groq.com/keys' },
  { file: 'google-ai-studio.png', url: 'https://aistudio.google.com/app/apikey' },
  { file: 'discord-developers.png', url: 'https://discord.com/developers/applications' },
  { file: 'telegram-bots.png', url: 'https://core.telegram.org/bots' },
  { file: 'ollama-download.png', url: 'https://ollama.com/download' },
  { file: 'cloudflare-tunnel.png', url: 'https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/' },
]

const browser = await chromium.launch({ headless: true })
const ctx = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  locale: 'en-US',
  userAgent:
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
})

for (const page of PAGES) {
  const tab = await ctx.newPage()
  process.stdout.write(`${page.file} … `)
  try {
    await tab.goto(page.url, { waitUntil: 'domcontentloaded', timeout: 45_000 })
    await tab.waitForTimeout(2500)
    await tab.screenshot({ path: join(OUT, page.file), type: 'png' })
    console.log('ok')
  } catch (err) {
    console.log(`fail (${err.message.split('\n')[0]})`)
  }
  await tab.close()
}

await browser.close()
console.log(`wrote ${OUT}`)
