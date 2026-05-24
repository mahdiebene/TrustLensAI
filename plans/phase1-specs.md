# TrustLens — Phase 1 Implementation Specs

---

## 1B — Backend Foundation

**`backend/app/main.py`** — FastAPI app with CORS, rate limiting, lifespan events  
**`backend/app/config.py`** — Pydantic BaseSettings from .env  
**`backend/app/models/schemas.py`** — Request/Response models  
**`backend/app/api/health.py`** — GET /api/health  
**`backend/Dockerfile`** — python:3.12-slim based  

### Pydantic Models
```python
class AnalyzeRequest(BaseModel):
    content: str
    image_url: str | None = None

class PillarScore(BaseModel):
    name: str
    score: float  # 0-100
    weight: float
    explanation_en: str
    explanation_bn: str
    evidence: list[str]

class AnalyzeResponse(BaseModel):
    trust_score: float
    verdict: str
    pillars: list[PillarScore]
    explanation_en: str
    explanation_bn: str
    confidence: float
    cached: bool
    processing_time_ms: int
```

### Dependencies
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
pydantic==2.9.0
pydantic-settings==2.5.0
httpx==0.27.0
openai==1.50.0
redis==5.1.0
slowapi==0.1.9
celery==5.4.0
sqlalchemy==2.0.35
alembic==1.13.0
asyncpg==0.29.0
pgvector==0.3.0
neo4j==5.25.0
beautifulsoup4==4.12.0
python-dotenv==1.0.1
```

---

## 1C — Pollinations API Client

**File:** `backend/app/services/pollinations.py`

```python
# Uses openai.AsyncOpenAI with base_url="https://gen.pollinations.ai"
# Methods:
#   chat(model, messages, temperature=0.3, timeout=30) -> str
#   embed(text, model="openai-3-large") -> list[float]
# Retry: 3 attempts, exponential backoff (1s, 2s, 4s)
# Logging: model, estimated tokens, latency
```

**File:** `backend/app/services/redis_client.py`

```python
# Cache key: trustlens:{pillar}:{sha256(content)[:16]}
# TTL: 24h analysis, 7d embeddings
# Methods: get_cached(key), set_cached(key, value, ttl)
```

---

## 1D — Pillar 2: Content Consistency

**File:** `backend/app/core/pillars/content_consistency.py`  
**Model:** `perplexity-reasoning`

**System prompt concept:**
- Fact-checking analyst for South Asian media
- Search web for corroborating/contradicting sources
- Return JSON: score (0-100), findings array, explanation_en, explanation_bn

**Logic flow:**
1. Check Redis cache by content hash
2. Call perplexity-reasoning with structured prompt
3. Parse JSON response (fallback: regex extraction)
4. Cache result, return PillarScore

---

## 1E — Pillar 3: Language Analysis

**File:** `backend/app/core/pillars/language_analysis.py`  
**Model:** `claude`

**Detects:**
- Emotional manipulation / sensationalism
- Clickbait patterns
- Logical fallacies
- Propaganda techniques
- Urgency/fear language
- Bengali-specific: communal tension triggers, political bias markers

**Returns:** Score 0-100 (100 = neutral/factual, 0 = heavily manipulative)

---

## 1F — POST /api/analyze Endpoint

**File:** `backend/app/api/analyze.py`

**Flow:**
1. Receive AnalyzeRequest
2. Generate content hash for caching
3. Check full-result cache first
4. If miss: run Pillar 2 + Pillar 3 in parallel (asyncio.gather)
5. Calculate weighted score: (P2 * 0.20) + (P3 * 0.20) + defaults for others
6. Determine verdict based on score ranges
7. Cache full result
8. Return AnalyzeResponse

**Note:** In Phase 1, only pillars 2 and 3 are active. Others return placeholder scores with a note.

---

## 1G — Frontend Scaffold

**Stack:** Next.js 14 (App Router), Tailwind CSS, Framer Motion, Zustand

**`frontend/package.json`** dependencies:
```json
{
  "next": "14.2.0",
  "react": "^18.3.0",
  "tailwindcss": "^3.4.0",
  "framer-motion": "^11.0.0",
  "zustand": "^4.5.0",
  "recharts": "^2.12.0",
  "@radix-ui/react-*": "latest"
}
```

**`frontend/app/layout.tsx`:**
- Dark mode default: `<html className="dark">`
- Fonts: Inter (sans), Hind Siliguri (Bengali), JetBrains Mono (mono)
- CSS variables for the color system from frontend-design-skill.md

**`frontend/app/globals.css`:**
- All CSS custom properties (surfaces, text, semantic colors, glows)
- Base styles: 8px spacing system, type scale
- Dark/light mode variables

**`frontend/tailwind.config.ts`:**
- Extended colors mapping to CSS variables
- Custom font families
- Custom animations (fadeUp, scan, scoreReveal)

---

## 1H — InputForm Component

**File:** `frontend/components/InputForm.tsx`

**Specs from frontend-design-skill.md:**
- Content-editable div (NOT textarea)
- Min height 120px
- Placeholder: "পোস্ট বা লিংক পেস্ট করুন..."
- Border: 1px --surface-3, focus: 1px --accent-blue + 3px ring
- URL detection: auto-highlight pasted URLs, show "URL detected" chip
- Language indicator pill: top-right corner, shows BN/EN/Mixed
- Submit button: full-width, label "বিশ্লেষণ করুন", bg --accent-blue
- On submit: dims input to 50%, starts scan animation

---

## 1I — TrustGauge Component

**File:** `frontend/components/TrustGauge.tsx`

**Specs:**
- 270-degree arc (open at bottom), SVG-based
- Ring thickness: 8px mobile, 12px desktop
- Background ring: --surface-3 at 30% opacity
- Active ring: gradient from red through amber to green, clipped to score %
- Soft radial glow behind ring (120% radius, 0.1 opacity)
- Center: 64px number, JetBrains Mono, weight 700, letter-spacing -0.04em
- Below: "/100" in 14px --text-secondary
- Below that: verdict badge with score color
- Animation: spring physics, slight overshoot then settle

---

## 1J — PillarCard Components

**File:** `frontend/components/PillarCard.tsx`

**Specs:**
- Background: --surface-1
- Border: 1px solid --surface-3 at 40% opacity
- Left accent: 3px solid bar, colored by pillar score
- Content: icon (16px) + name (14px) + score (24px mono) + one-line finding (13px, truncated)
- Hover: bg shifts to --surface-2, left bar brightens
- Click: expands inline (not modal) to show full explanation
- Stagger animation: 50ms delay between cards, fadeUp 12px

---

## 1K — Results Page

**File:** `frontend/app/results/page.tsx`

**Layout (desktop 1200px max):**
```
[Score Gauge] [Radar Chart placeholder]
[Pillar Cards - 6 column grid]
[Explanation - bn/en tabs]
[Evidence - collapsible list]
```

**Scan animation (loading state):**
- Input dims to 50%
- 1px horizontal line (--accent-blue, 60%) sweeps top-to-bottom
- Progress text updates: "Checking sources..." -> "Analyzing language..." -> "Generating score..."
- Pillar cards appear progressively as each completes

---

## 1L — Docker Compose

**File:** `docker-compose.yml`

Services with memory limits (7.6GB VPS total):
- postgres (pgvector/pgvector:pg16) — 1GB limit
- neo4j (neo4j:5-community) — 1.5GB limit
- redis (redis:7-alpine) — 256MB limit
- n8n (n8nio/n8n) — 512MB limit
- backend (custom Dockerfile) — 1GB limit

All with healthchecks. Backend depends_on with condition: service_healthy.

---

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python version in Docker | 3.12-slim | VPS has 3.14 but packages may lack wheels |
| API client | openai SDK | Handles retries, streaming, types |
| State management | Zustand | Lightweight, no boilerplate |
| Animations | Framer Motion | Spring physics, layout animations |
| CSS approach | Tailwind + CSS vars | Design system tokens + utility classes |
| Caching | Redis with content hash | Protect $50 Pollinations balance |
| Pillar execution | asyncio.gather | Parallel, not sequential |
| Frontend proxy | Next.js API routes | Avoids CORS entirely |
