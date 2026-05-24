# TrustLens — AI-Powered Trust Scoring Platform

> **"গুজব চিনুন, সত্য জানুন।"** / "See through the noise. Trust what matters."

TrustLens takes any social media post, news article, or URL and produces a **Trust Score (0-100)** with an explainable breakdown in Bengali and English.

---

## 🏗️ Architecture

- **Backend:** Python FastAPI with 6 AI-powered trust scoring pillars
- **Frontend:** Next.js 14 with dark-first design system
- **AI:** Pollinations API (OpenAI-compatible) with multiple specialized models
- **Storage:** PostgreSQL + pgvector, Neo4j Graph DB, Redis cache
- **Extensions:** Chrome Extension, Telegram Bot

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 22+
- Python 3.12+

### Development Setup

```bash
# Clone the repository
git clone https://github.com/mahdiebene/TrustLensAI.git
cd TrustLensAI

# Copy environment variables
cp .env.example .env
# Edit .env with your actual API keys

# Start infrastructure services
docker compose up -d postgres neo4j redis

# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Docker (Full Stack)

```bash
docker compose up -d
```

## 📊 Trust Score Engine

The trust score is calculated from 6 pillars:

| Pillar | Weight | Model |
|--------|--------|-------|
| Source Reputation | 20% | gemini |
| Content Consistency | 20% | perplexity-reasoning |
| Language Analysis | 20% | claude |
| Bengali Context | 15% | qwen-large |
| Image Authenticity | 15% | qwen-vision-pro |
| Author/Network | 10% | gemini |

**Score Interpretation:**
- 80-100: Highly Trustworthy ✅
- 60-79: Generally Reliable ⚠️
- 40-59: Questionable ⚠️⚠️
- 20-39: Likely Unreliable ❌
- 0-19: High Risk 🚨

## 🔗 API

```
POST /api/analyze
Body: { "content": "text or URL", "image_url": "optional" }

Response: { "trust_score": 72, "verdict": "Generally Reliable", "pillars": [...], ... }
```

## 📁 Project Structure

```
├── backend/          # Python FastAPI
├── frontend/         # Next.js 14
├── extension/        # Chrome Extension (Manifest V3)
├── bot/              # Telegram Bot
├── nginx/            # Reverse proxy config
├── n8n/              # Workflow automation
├── scripts/          # Setup & deployment
└── docker-compose.yml
```

## 🏆 Hackathon

Built for **The Infinity AI BuildFest 2026** (CloudCamp Bangladesh)

**Key Differentiator:** Bengali-first misinformation detection — purpose-built for Bangladesh's 50M+ Facebook users.

## 📄 License

MIT
