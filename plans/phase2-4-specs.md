# TrustLens — Phase 2-4 Implementation Specs

---

## Phase 2: Full Engine

### 2A — Pillar 1: Source Reputation (20%)

**File:** `backend/app/core/pillars/source_reputation.py`  
**Model:** `gemini`

**Logic:**
1. Extract domain/source from URL or content mentions
2. Query Neo4j for existing source node and reliability_score
3. If not in graph: call gemini to assess domain reputation
4. Factors: domain age, HTTPS, known news outlet, bias rating
5. Store new source node in Neo4j for future lookups

---

### 2B — Pillar 4: Bengali Context (15%)

**File:** `backend/app/core/pillars/bengali_context.py`  
**Model:** `qwen-large`

**Detects Bangladesh-specific patterns:**
- Communal tension narratives
- Political misinformation (election-related)
- Disaster/crisis rumor patterns
- Celebrity death hoaxes
- Price manipulation rumors
- Anti-minority narratives

---

### 2C — Pillar 5: Image Authenticity (15%)

**File:** `backend/app/core/pillars/image_authenticity.py`  
**Model:** `qwen-vision-pro`

**Checks:**
- AI-generated image detection
- Manipulated/doctored photo indicators
- Reverse image context (is this image from a different event?)
- Metadata inconsistencies
- If no image provided: return neutral score (50) with note

---

### 2D — Pillar 6: Author/Network (10%)

**File:** `backend/app/core/pillars/author_network.py`  
**Model:** `gemini`

**Analyzes:**
- Account age and posting patterns
- Bot-like behavior indicators
- Network amplification signals
- Author credibility from Neo4j graph
- If no author info available: return neutral score with note

---

### 2E — Score Synthesis

**File:** `backend/app/core/scoring.py`  
**Model:** `gpt-5.5` (use sparingly — paid_only)

**Logic:**
1. Receive all 6 pillar scores + evidence
2. Calculate weighted score: sum(pillar.score * pillar.weight)
3. Call gpt-5.5 to generate human-readable explanation
4. Generate both Bengali and English explanations
5. Assign confidence level based on pillar agreement
6. Determine verdict string

**Verdict mapping:**
- 80-100: "Highly Trustworthy" / "অত্যন্ত বিশ্বাসযোগ্য"
- 60-79: "Generally Reliable" / "সাধারণত নির্ভরযোগ্য"
- 40-59: "Questionable" / "সন্দেহজনক"
- 20-39: "Likely Unreliable" / "সম্ভবত অবিশ্বাসযোগ্য"
- 0-19: "High Risk" / "উচ্চ ঝুঁকি"

---

### 2F — RAG Pipeline

**Files:** `backend/app/core/rag/chunking.py`, `contextual.py`, `embeddings.py`

**Pipeline:**
1. **Ingest:** Scrape BD news sources (Prothom Alo, Daily Star, BD News 24)
2. **Chunk:** Semantic chunking by claim boundaries (not fixed tokens)
3. **Enrich:** For each chunk, LLM generates metadata (topic, claims, source, language)
4. **Embed:** openai-3-large via Pollinations -> 3072-dim vectors
5. **Store:** pgvector for similarity search
6. **Query:** User content -> embed -> search pgvector -> feed context to pillars

---

### 2G — Neo4j Graph RAG

**File:** `backend/app/core/rag/graph_rag.py`

**Node types:** Source, Claim, Author, Topic, FactCheck  
**Relationships:** PUBLISHED_BY, MADE_BY, ABOUT, VERIFIES, COVERS, WRITES_FOR

**Query patterns:**
- Find related claims by topic traversal
- Check if source has history of misinformation
- Find fact-checks that verify/debunk similar claims
- Author credibility from network connections

---

### 2H — RadarChart Component

**File:** `frontend/components/RadarChart.tsx`

**Specs:**
- Hexagonal SVG with 6 axes (one per pillar)
- Draws clockwise over 800ms
- Gradient fill fades in during last 200ms
- Axis labels in current language (bn/en)
- Interactive: hover axis to highlight pillar card

---

### 2I — LanguageToggle + i18n

**File:** `frontend/components/LanguageToggle.tsx` + `frontend/lib/i18n.ts`

**Implementation:**
- Zustand store for current language (bn/en)
- Toggle component: pill-shaped, shows বাং/EN
- All UI strings from i18n dictionary
- Bengali numerals (১২৩) when in Bengali mode
- Persisted in localStorage

---

### 2J — Full Results Page

**File:** `frontend/app/results/page.tsx`

Complete layout with all components wired together:
- Score gauge + radar chart (top row)
- 6 pillar cards (grid)
- Explanation tabs (bn/en)
- Evidence list (collapsible, with source links)
- Share button (copy link / screenshot)

---

## Phase 3: Extensions

### 3A — Telegram Bot

**Files:** `bot/bot.py`, `bot/handlers/`  
**Token:** From env var TELEGRAM_BOT_TOKEN

**Commands:**
- /start — Welcome message in Bengali + English
- /analyze <text> — Analyze forwarded message
- Forward any message — Auto-analyze

**Response format:** Score badge + verdict + top 3 findings

---

### 3B — Chrome Extension

**Files:** `extension/manifest.json`, `extension/popup/`, `extension/content/`

**Features:**
- Popup: paste URL or text, get score
- Content script: right-click on any text -> "Check with TrustLens"
- Badge: shows trust score color on active tab (if analyzed)

---

### 3C — n8n Workflows

**Directory:** `n8n/`

**Workflows:**
- Daily news ingestion from BD sources (RSS feeds)
- Fact-check database sync
- Source reputation updates

---

## Phase 4: Deploy & Submit

### 4A — VPS Setup

Run setup commands from CLAUDE.md on VPS (107.161.168.216):
- System update, swap increase, firewall
- Docker + Docker Compose
- Node.js 22, Nginx, Certbot

### 4B — Nginx + SSL

**File:** `nginx/trustlens.conf`
- Reverse proxy: / -> frontend (port 3000)
- Reverse proxy: /api -> backend (port 8000)
- SSL via Certbot (Let's Encrypt)

### 4C — Final Testing + Submission

- End-to-end test with real Bengali content
- Record YouTube demo video
- Write submission documentation
- Install Ollama + pull models for bonus points
- Submit to hackathon platform
