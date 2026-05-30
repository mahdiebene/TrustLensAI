# 3-Min Demo (Slides + Live Demo Mix) — 30 Min Plan

## Setup (5 min)
- OBS: Display + Mic.
- Tabs ready: live site + cached URL pre-loaded.
- Warm cache: hit demo URL once now.
- Open Google Slides — fastest, 6 slides.

---

## Build slides (5 min) — dark theme, big text, one idea per slide

| # | Slide | Content |
|---|---|---|
| 1 | **Title** | TrustLens — Live Trust Check for Bengali Social Media · Team Potato Crackers · trust-lens-ai-beta.vercel.app |
| 2 | **Problem** | 65% of Bengali FB users have shared fake content · Spreads in hours · No AI tool speaks Bengali well |
| 3 | **Solution** | Paste URL / text / image → 0–100 score in <2s · 6 explainable signals · Bengali-native, web-cited |
| 4 | **Architecture** | 3-stage AI cascade: Perplexity → Mistral → OpenAI · Graph-RAG on Neo4j · Redis-cached embeddings |
| 5 | **Roadmap** | ✅ Web app (live) · 🔜 Telegram bot for family group chats · 🔜 Chrome extension overlay · 🔜 Image deepfake detector · 🔜 Newsroom partner API (Rumor Scanner BD) · 🔜 WhatsApp integration |
| 6 | **End** | Built. Live. trust-lens-ai-beta.vercel.app · github.com/mahdiebene/TrustLensAI |

---

## Record 6 segments (15 min) — each as separate take, redo only broken ones

**0:00–0:20 · Slide 1 + 2 (Title → Problem)**
> "TrustLens — a live trust check for Bengali social media. The problem: 65% of Bangladeshi Facebook users have shared something fake. Bengali misinformation spreads in hours, and no AI tool speaks Bengali well enough to stop it."

**0:20–0:40 · Slide 3 (Solution)**
> "Our solution: paste any Bengali post, URL, or image — get a 0 to 100 trust score in under 2 seconds, across 6 explainable signals. Bilingual, web-cited, fast."

**0:40–1:50 · 🎥 LIVE DEMO (switch to browser, this is the heart)**
- Paste cached URL → score appears → narrate radar + one pillar.
- Paste a private URL → show manual-paste fallback.
> "Most tools just fail on private posts — we fall back so users never hit a dead end."

**1:50–2:20 · Slide 4 (Architecture)**
> "Under the hood: a 3-stage AI cascade — Perplexity for live web search, Mistral for Bengali language, OpenAI for the explainable verdict. Graph-RAG on Neo4j tracks author reputation. Redis caches repeat checks to under a second."

**2:20–2:50 · Slide 5 (Roadmap — what's next)**
> "Today: the web app is live. Coming next: a Telegram bot so families can /check forwarded messages in their group chats, a Chrome extension that overlays trust scores directly on Facebook, an image deepfake detector, a partner API for newsrooms like Rumor Scanner BD, and WhatsApp integration."

**2:50–3:00 · Slide 6 (End)**
> "TrustLens is built, it's live, and it's the trust layer Bengali social media has been missing. Try it now."

---

## Edit (8 min) — Clipchamp or CapCut
- Drop 6 clips in order. Trim silences.
- Each slide visible 5–25 sec depending on clip length.
- Live demo segment plays as full-screen browser recording.
- **Auto-captions** (mandatory — evaluators watch muted).
- Skip music, transitions.

## Upload (2 min)
- Export 1080p MP4 → YouTube **Unlisted**
- Title: `TrustLens — BuildFest Submission`
- Description:
  ```
  TrustLens — AI trust scoring for Bengali social media.
  Live: https://trust-lens-ai-beta.vercel.app/
  GitHub: https://github.com/mahdiebene/TrustLensAI
  Team: Potato Crackers
  ```
- Paste link in submission form.

---

## Don't
- Don't read monotone — speak naturally, even if you stumble.
- Don't show 6 features for 5 sec each — show 2 deeply (success + scrape-fail).
- Don't skip captions.

## If broken
- Backend slow? → use the cached URL, say "previously analyzed."
- Mic dies? → phone voice memo, sync after.

---

**Closing line to memorize**: *"Built. Live. Trust layer for Bengali social media."*
