# TrustLens Telegram Bot

A lightweight Telegram bot that verifies the credibility of any text, link, or
forwarded post using the TrustLens backend. Bangla-first, English-ready.

## Features

- **Send anything** — plain text, a news link, or a forwarded message.
- **`/analyze <text>`** — explicit analyze command.
- **Bilingual** — Bangla (default) and English, switchable per chat with `/lang`.
- **Rich results** — trust score badge, verdict, per-pillar bars, explanation,
  and a link to the full web report.
- **Resilient** — handles scrape failures, backend errors, network timeouts,
  long messages, and never crashes the polling loop.

## Commands

| Command    | Description                          |
| ---------- | ------------------------------------ |
| `/start`   | Welcome message + how to use         |
| `/analyze` | Analyze the text that follows        |
| `/lang`    | Toggle language (`/lang en`, `/lang bn`) |
| `/help`    | Usage help                           |
| `/about`   | About TrustLens                      |

You can also just send (or forward) any message and it will be analyzed.

## Configuration

Set via environment variables (e.g. an `.env` file or the host environment):

| Variable             | Required | Default                  | Description                          |
| -------------------- | -------- | ------------------------ | ------------------------------------ |
| `TELEGRAM_BOT_TOKEN` | ✅       | —                        | Token from [@BotFather](https://t.me/BotFather) |
| `API_URL`            | —        | `http://localhost:8000`  | TrustLens backend base URL           |
| `APP_URL`            | —        | `https://trustlens.app`  | Public web app URL (for report links)|

## Run locally

```bash
cd bot
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN="123456:ABC..."
export API_URL="http://localhost:8000"
python bot.py
```

## Run with Docker

```bash
# From the repo root, with TELEGRAM_BOT_TOKEN + API_URL in your .env:
docker compose up -d bot
docker compose logs -f bot
```

## How it works

The bot uses Telegram **long polling** (no public webhook required), so it runs
anywhere with outbound internet — including behind NAT. Each incoming message is
routed to the right command handler, or treated as content to analyze. Analysis
is delegated to the backend's `POST /api/analyze` endpoint, and the JSON
response is rendered into a clean, HTML-formatted Telegram message.

No database is required: the only per-chat state is the language preference,
held in memory and re-defaulting to Bangla on restart.
