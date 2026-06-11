# TrustLens — AI-Powered Trust Scoring for Bengali Social Media

> **"গুজব চিনুন, সত্য জানুন।"** — _See through the noise. Trust what matters._

TrustLens takes any social media post, news article, claim, or URL and returns a
**Trust Score (0–100)** with a fully explainable, bilingual (বাংলা / English)
breakdown. It is purpose-built for Bangladesh's information ecosystem — where
misinformation spreads fastest on Facebook to 50M+ users in Bengali.

Use it three ways:

- 🌐 **Web app** — paste text or a link, get a verdict in ~10–15s.
- 🧩 **Chrome extension** — right-click any post/selection to check it in place.
- 🤖 **Telegram bot** — [@TrustLensAI_bot](https://t.me/TrustLensAI_bot) — forward or paste a message, get a score in chat.

---

## ✨ What it does

- **Claim verification, not vibes.** A two-pass, verifier-first pipeline runs
  live web searches to cross-check the actual claims before scoring — so the
  verdict reflects today's facts, not an LLM's stale training memory.
- **Explainable by design.** Every score is broken down into 6 weighted pillars,
  each with its own evidence list and a plain-language explanation in both Bengali
  and English.
- **Bengali-first.** Native handling of Bengali text, transliteration, and
  Bangladesh-specific political/cultural context.
- **Graceful on locked content.** Social posts behind login walls can't be
  fetched by an AI — instead of fabricating a verdict, TrustLens detects this and
  asks the user to paste the text or upload a screenshot.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  Clients                                                         │
│  • Next.js web app (Vercel)   • Chrome extension   • Telegram bot│
└───────────────┬──────────────────────────────────────────────-─┘
                │  POST /api/analyze
                ▼
┌────────────────────────────────────────────────────────────────┐
│  FastAPI backend                                                 │
│  1. Redis cache check (daily-keyed, v3 namespace)                │
│  2. URL → scrape (Jina Reader → OG fallback) or login-wall guard │
│  3. 2-pass scoring pipeline (see below)                          │
│  4. Cache successful results 24h                                 │
└───────────────┬──────────────────────────────────────────────-─┘
                ▼
   Pollinations AI (OpenAI-compatible)  •  Redis  •  (Neo4j / Postgres optional)
```

- **Backend:** Python 3.12 + FastAPI, rate-limited with SlowAPI.
- **Frontend:** Next.js 14 (App Router) + Tailwind, dark-first design, BN/EN i18n.
- **AI:** [Pollinations](https://pollinations.ai) API (OpenAI-compatible) with
  multiple specialized models.
- **Cache:** Redis (24h result cache, keyed per-day so recency-sensitive claims
  re-verify).
- **Optional storage:** PostgreSQL + pgvector and Neo4j for the RAG / author-network
  experiments.
- **Clients:** Chrome Extension (Manifest V3) and a live Telegram bot.

### Trust Score engine — two-pass, verifier-first

The old "one mega-prompt" approach caused role-conflict: a single model asked to
both browse the web *and* fill a giant scoring rubric tended to fall back on stale
training data. TrustLens splits the job:

1. **Pass 1 — VERIFY.** Two independent models run live web searches in parallel
   (`gemini-search-fast` + `perplexity-fast`, with fallbacks) to extract and
   cross-check the claims. High recall, current facts.
2. **Pass 2 — SCORE.** A reasoning model (`openai-large`) receives the
   pre-verified evidence and does one job: score the 6 pillars and write the
   bilingual summary. No web search at this stage → no role-conflict.

Total ≈ 10–15s, ~3 API calls, dramatically higher accuracy.

### The 6 pillars

| Pillar | Weight | What it measures |
|--------|:------:|------------------|
| Content Consistency | **40%** | Are the claims factually accurate / internally consistent vs. verified evidence? |
| Source Reputation | 20% | Credibility/track-record of the source domain or page |
| Language Analysis | 15% | Manipulative, sensational, or emotionally-loaded language |
| Bengali Context | 10% | Bangladesh-specific political/cultural plausibility |
| Author / Network | 10% | Author/page history and amplification patterns |
| Image Authenticity | 5% | Signs of manipulation / out-of-context media |

**Score interpretation**

| Range | Verdict |
|-------|---------|
| 85–100 | True / Verified ✅ |
| 70–84 | Mostly True ✅ |
| 50–69 | Mixed / Unverified ⚠️ |
| 30–49 | Misleading ❌ |
| 0–29 | False / High Risk 🚨 |

---

## 🚀 Quick start

### Prerequisites
- Node.js 22+
- Python 3.12+
- Docker & Docker Compose (only needed for the optional Postgres/Neo4j/Redis stack)
- A Pollinations API key

### 1. Clone & configure

```bash
git clone https://github.com/mahdiebene/TrustLensAI.git
cd TrustLensAI
cp .env.example .env       # then fill in POLLINATIONS_API_KEY etc.
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000` — interactive docs at `/docs`.

> Redis is recommended for caching but optional in dev. Start it with
> `docker compose up -d redis` if you want caching locally.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev                  # http://localhost:3000
```

The frontend talks to the backend via `NEXT_PUBLIC_API_URL` (defaults to the
hosted API; set to `http://localhost:8000` for local backend dev).

### 4. (Optional) Full stack with Docker

```bash
docker compose up -d
```

---

## 🌐 Web app pages

| Route | Purpose |
|-------|---------|
| `/` | Home — input box (text / URL), language toggle, tool cards |
| `/results` | Trust gauge, radar chart, per-pillar breakdown with evidence |
| `/docs` | How it works / methodology |
| `/get-extension` | Install + usage guide for the Chrome extension |
| `/get-bot` | Guide for the live Telegram bot ([@TrustLensAI_bot](https://t.me/TrustLensAI_bot)) |

---

## 🧩 Chrome extension

Manifest V3 extension that lets you check posts and selections without leaving the
page (right-click → analyze, or via the popup).

```bash
cd extension
node package-extension.js     # produces frontend/public/trustlens-extension.zip
```

Load unpacked from the `extension/` folder via `chrome://extensions` (Developer
mode), or download the packaged zip from the `/get-extension` page.

---

## 🤖 Telegram bot

Live at **[@TrustLensAI_bot](https://t.me/TrustLensAI_bot)**. Commands:

| Command | Action |
|---------|--------|
| `/start` | Welcome + quick guide |
| `/analyze <text or URL>` | Score a message (you can also just paste text) |
| `/lang` | Toggle Bengali / English |
| `/help` | Command reference |
| `/about` | About TrustLens |

```bash
cd bot
pip install -r requirements.txt
# set TELEGRAM_BOT_TOKEN in .env
python bot.py
```

---

## 🔗 API

```http
POST /api/analyze
Content-Type: application/json

{ "content": "text or URL", "image_url": "optional screenshot URL" }
```

**Response (abridged):**

```json
{
  "trust_score": 72,
  "verdict": "Mostly True",
  "verdict_bn": "অধিকাংশ সত্য",
  "explanation_en": "...",
  "explanation_bn": "...",
  "confidence": 0.86,
  "cached": false,
  "processing_time_ms": 12840,
  "pillars": [
    { "name": "Content Consistency", "name_bn": "বিষয়বস্তু সামঞ্জস্য",
      "score": 80, "weight": 0.40, "evidence": ["..."],
      "explanation_en": "...", "explanation_bn": "..." }
  ]
}
```

When a social URL can't be fetched, the response sets `scrape_failed: true` and
`needs_user_input: true` so the client can prompt for pasted text / a screenshot
instead of showing a fabricated score.

Other endpoints: `GET /api/health` (liveness). Rate limit: `10/minute` per IP on
`/api/analyze`.

---

## ⚙️ Environment variables

Copy `.env.example` → `.env`. Key values:

| Variable | Purpose |
|----------|---------|
| `POLLINATIONS_API_KEY` | **Required** — auth for the AI models |
| `POLLINATIONS_BASE_URL` | Pollinations endpoint (default provided) |
| `REDIS_URL` | Result cache (recommended) |
| `APP_URL` / `API_URL` | Public URLs, used for CORS |
| `TELEGRAM_BOT_TOKEN` | Required only to run the bot |
| `POSTGRES_*`, `NEO4J_*` | Optional — RAG / author-network experiments |

Frontend (Vercel) env:

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | Backend base URL |
| `NEXT_PUBLIC_TELEGRAM_BOT_HANDLE` / `NEXT_PUBLIC_TELEGRAM_BOT_URL` | Override the bot link on `/get-bot` |

---

## 📁 Project structure

```
.
├── backend/            # FastAPI app
│   └── app/
│       ├── api/        # analyze, health, sources routers
│       ├── core/       # scoring engine, pillars, RAG
│       ├── models/     # Pydantic schemas + DB models
│       └── services/   # Pollinations, scraper, Redis, Neo4j clients
├── frontend/           # Next.js 14 web app (App Router)
│   ├── app/            # /, /results, /docs, /get-bot, /get-extension, /api
│   ├── components/     # gauge, radar, pillar cards, i18n toggles
│   └── lib/            # api client, store, i18n
├── extension/          # Chrome extension (Manifest V3) + packager
├── bot/                # Telegram bot
├── nginx/              # Reverse-proxy config
├── n8n/                # Workflow automation notes
├── plans/              # Specs, deploy scripts, demo guide
└── docker-compose.yml
```

---

## 🏆 Hackathon

Built for **The Infinity AI BuildFest 2026** (CloudCamp Bangladesh).

**Key differentiator:** Bengali-first misinformation detection with live claim
verification — purpose-built for Bangladesh's 50M+ Facebook users, delivered across
web, browser extension, and Telegram.

## 📄 License

MIT
