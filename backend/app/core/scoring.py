"""TrustLens scoring engine — verifier-first 2-pass architecture.

WHY THIS REWRITE
================
The previous "single mega-prompt" approach asked one model (perplexity-reasoning)
to (a) read the post, (b) verify claims via web search, (c) score 6 pillars,
and (d) produce bilingual summaries — all inside one giant JSON-output call.

Empirically that caused **role-conflict**: when the model saw a heavyweight
structured-output rubric it slipped back into "training-data persona" and
produced confident verdicts based on stale memory (e.g., insisting Sheikh
Hasina is still PM of Bangladesh in 2026, when she is not).

Probe results from inside the production container (probe_recency.py) confirm:
  • `perplexity-reasoning` answers "Tarique Rahman, sworn in Feb 2026"
    CORRECTLY when asked directly with a small terse prompt — same model gave
    WRONG verdicts when the question was buried in a 100-line JSON rubric.
  • Fallbacks `mistral` and `openai` HAVE NO LIVE WEB ACCESS — they explicitly
    say so when asked. They cannot fact-check current events. The old cascade
    routed traffic to them when perplexity timed out, producing confidently-
    wrong verdicts.
  • `gemini-2.5-flash` (used for summary) RETURNS HTTP 400 — alias is dead.
    Current alias is `gemini-3.5-flash`. Summary step was silently failing.

NEW ARCHITECTURE
================
Pass 1 — VERIFY (parallel, web-grounded, terse output):
    Call BOTH `gemini-search-fast` (Google grounded search) and
    `perplexity-fast` in parallel with a SMALL prompt that does ONE thing:
    extract claims and run live web searches. Two independent searches →
    cross-check → high recall.

Pass 2 — SCORE (single call, reasoning over verified evidence):
    Feed the verifier outputs + original content into a scoring-only call on
    `openai-large` (reasoning, 1M ctx). The model's only job is "given this
    PRE-VERIFIED evidence, score 6 pillars and write a summary." No web
    search needed at this stage → no role-conflict, no stale memory.

Total: ~10-15s, ~3 API calls, dramatically higher accuracy.
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timezone

from app.models.schemas import AnalyzeResponse, PillarScore
from app.services.pollinations import get_pollinations_client
from app.core.rag.chunking import semantic_chunk
from app.core.rag.contextual import enrich_chunks

logger = logging.getLogger(__name__)


# Pillar weights — content accuracy is king
PILLAR_WEIGHTS = {
    "content_consistency": 0.40,
    "source_reputation": 0.20,
    "language_analysis": 0.15,
    "bengali_context": 0.10,
    "author_network": 0.10,
    "image_authenticity": 0.05,
}

PILLAR_NAMES_BN = {
    "source_reputation": "উৎস সুনাম",
    "content_consistency": "বিষয়বস্তু সামঞ্জস্য",
    "language_analysis": "ভাষা বিশ্লেষণ",
    "bengali_context": "বাংলাদেশ প্রসঙ্গ",
    "image_authenticity": "ছবি সত্যতা",
    "author_network": "লেখক নেটওয়ার্ক",
}

VERDICTS = [
    (85, "True / Verified", "সত্য / যাচাইকৃত"),
    (70, "Mostly True", "অধিকাংশ সত্য"),
    (50, "Misleading / Mixed", "বিভ্রান্তিকর / মিশ্র"),
    (30, "Mostly False", "অধিকাংশ মিথ্যা"),
    (15, "False", "মিথ্যা"),
    (0, "Unverifiable", "যাচাইযোগ্য নয়"),
]

# ───────────── PASS 1: VERIFIER PROMPT ─────────────
# Tiny, terse, single-purpose. Forces live web search.
VERIFY_PROMPT = """You are a real-time fact-checker with live web search access.

═══ TODAY: {today} ═══
Your training data is older than today. For ANY claim about a current
office-holder, recent event, or anything time-sensitive you MUST search the
web NOW and trust fresh search results over your training data. Bangladesh
has had major political change since August 2024 — verify, don't assume.

CONTENT TO FACT-CHECK:
---
{content}
---

TASK:
1. Extract every concrete factual claim (people, dates, numbers, events).
2. For each claim, run a CURRENT web search (year {year}). For Bangladesh
   political claims, search "Bangladesh Prime Minister {year}" or "Bangladesh
   current government {year}". Use Bengali search terms too.
3. Mark each claim: true / false / misleading / unverifiable.
4. Cite the source URL and its publication date (the actual date on the
   article, not today's date).

Return ONLY this JSON, nothing else:
{{
  "today": "{today}",
  "summary": "<1-sentence neutral summary of what the post says>",
  "claims": [
    {{
      "claim": "<the specific claim, in English>",
      "verdict": "true|false|misleading|unverifiable",
      "evidence": "<what your search found, 1-2 sentences>",
      "source_url": "<actual URL from search>",
      "source_date": "<YYYY-MM-DD if known, else unknown>",
      "source_outlet": "<e.g., Reuters, Prothom Alo, BBC Bangla>"
    }}
  ],
  "overall": "true|mostly_true|misleading|mostly_false|false|unverifiable",
  "key_finding": "<1 sentence — the single fact that decides this verdict>"
}}"""

# ───────────── PASS 2: SCORING PROMPT ─────────────
# Reasoning over already-verified evidence. NO web search expected.
SCORE_PROMPT = """You are TrustLens, scoring trustworthiness based on PRE-VERIFIED
fact-check evidence retrieved seconds ago from live web searches.

═══ TODAY: {today} ═══

ORIGINAL CONTENT:
---
{content}
---

═══ FACT-CHECK EVIDENCE (live web searches, just retrieved) ═══

Source A — Google Grounded Search (gemini-search-fast):
{evidence_a}

Source B — Perplexity Web Search (perplexity-fast):
{evidence_b}

═══ YOUR JOB ═══
DO NOT do new web searches. Use ONLY the evidence above — it was retrieved
moments ago from the live web. If both sources agree on a fact treat it as
verified. If they disagree, prefer the one citing a more reputable outlet
(Reuters, AP, BBC, Prothom Alo, AFP, Rumor Scanner, BOOM). If both say
"unverifiable" be decisive (low score for content_consistency) — do NOT
default to 50.

Score the 6 trust pillars 0-100. Be DECISIVE — a 50 across the board is a
failure mode. Pick a side based on evidence.

═══ SCORING RUBRIC ═══
For EVERY pillar:
  • 85-100 → Strong evidence FOR trustworthiness.
  • 60-84  → Mostly trustworthy with minor concerns.
  • 40-59  → Mixed / genuinely ambiguous (use sparingly).
  • 15-39  → Mostly untrustworthy.
  • 0-14   → Strong evidence AGAINST.

Per-pillar guidance:
  • content_consistency (40% weight): How well do the claims hold up against
    the verified evidence above?
      - Both sources confirm → 80+
      - Sources contradict the post → 5-20
      - No coverage anywhere → 25-40
  • source_reputation: Is the page/author/domain credible?
      - Established outlet (BBC Bangla, Prothom Alo, Reuters, AP) → 80+
      - Anonymous FB page with partisan framing → 20-40
      - Known disinformation source → 0-15
  • language_analysis: Tone & framing.
      - Neutral, factual, attributed → 70+
      - Hedged / qualified → 50-65
      - Emotional, ALL CAPS, loaded words → 15-35
  • bengali_context: Bangladesh-specific patterns.
      - Aligns with verified local reporting → 70+
      - Matches known rumor template (communal, smear) → 10-30
  • author_network: The poster.
      - Verified journalist / official page → 80+
      - Random page, low followers, no track record → 30-50
      - Page known for partisan rumor-mongering → 10-25
  • image_authenticity: Only if an image is referenced. None → 50 ("no image").

═══ BENGALI WRITING RULES ═══
  • `explanation_bn` MUST be natural fluent Bengali — like a Bangladeshi
    journalist would write.
  • DO NOT start with "রায়:" / "Verdict:" / any label prefix.
  • DO NOT dump raw enum tokens (no "mostly_true", "false", "unverifiable").
    Use proper Bengali phrases: "অধিকাংশ সত্য", "মিথ্যা", "যাচাইযোগ্য নয়",
    "বিভ্রান্তিকর", "মূলত মিথ্যা", "সত্য".
  • Keep proper nouns (Reuters, AP, etc.) in original form.
  • Use Bengali numerals (০-৯) for plain numbers; keep version numbers and
    percentages in their natural form.

Return ONLY this JSON:
{{
  "pillar_scores": {{
    "source_reputation": {{"score": <0-100>, "reason": "<one sentence>"}},
    "content_consistency": {{"score": <0-100>, "reason": "<cite verified evidence>"}},
    "language_analysis": {{"score": <0-100>, "reason": "<one sentence>"}},
    "bengali_context": {{"score": <0-100>, "reason": "<one sentence>"}},
    "image_authenticity": {{"score": <0-100>, "reason": "<one sentence or 'no image'>"}},
    "author_network": {{"score": <0-100>, "reason": "<one sentence>"}}
  }},
  "overall_verdict": "true|mostly_true|misleading|mostly_false|false|unverifiable",
  "explanation_en": "<2-3 sentences. Specific. No 'Verdict:' prefix.>",
  "explanation_bn": "<২-৩ বাক্যের ঝরঝরে বাংলা। 'রায়:' উপসর্গ ছাড়া। ইংরেজি enum না।>",
  "evidence_urls": ["<top 3 actual URLs from the evidence above>"]
}}"""

# Map raw enum tokens → human-readable strings (for scrubber).
VERDICT_REWRITE_EN = {
    "mostly_true": "Mostly true",
    "mostly_false": "Mostly false",
    "unverifiable": "Unverifiable",
    "misleading": "Misleading",
    "true": "True",
    "false": "False",
}
VERDICT_REWRITE_BN = {
    "mostly_true": "অধিকাংশ সত্য",
    "mostly_false": "মূলত মিথ্যা",
    "unverifiable": "যাচাইযোগ্য নয়",
    "misleading": "বিভ্রান্তিকর",
    "true": "সত্য",
    "false": "মিথ্যা",
}


def _scrub_explanation(text: str, is_bn: bool) -> str:
    """Strip enum-tag leakage and label prefixes from LLM-generated text."""
    if not text:
        return text
    cleaned = text.strip()
    prefix_patterns = [
        r"^\s*(?:Verdict|verdict|VERDICT)\s*[:：]\s*([a-zA-Z_]+)\s*[.।]?\s*",
        r"^\s*রায়\s*[:：]\s*([a-zA-Z_]+)\s*[।.]?\s*",
        r"^\s*(?:Verdict|verdict|VERDICT)\s*[:：]\s*",
        r"^\s*রায়\s*[:：]\s*",
    ]
    for pat in prefix_patterns:
        cleaned = re.sub(pat, "", cleaned, count=1)
    rewrite_map = VERDICT_REWRITE_BN if is_bn else VERDICT_REWRITE_EN
    for token, replacement in rewrite_map.items():
        cleaned = re.sub(rf"\b{re.escape(token)}\b", replacement, cleaned)
    return cleaned.strip()


def get_verdict(score: float) -> tuple[str, str]:
    for threshold, en, bn in VERDICTS:
        if score >= threshold:
            return en, bn
    return VERDICTS[-1][1], VERDICTS[-1][2]


def _extract_json(text: str) -> dict | None:
    """Extract JSON from a response that may have markdown code fences."""
    if not text:
        return None
    if "```" in text:
        m = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", text)
        if m:
            text = m.group(1)
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    raw = m.group()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Strip trailing commas before } or ]
        raw = re.sub(r",\s*([}\]])", r"\1", raw)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None


def _build_rag_context(enriched: list) -> str:
    """Distill enriched (contextual) chunks into a compact context block that
    is prepended to the verifier prompt.

    This is the consumption side of the Contextual-RAG pipeline: the
    semantic chunker (chunking.semantic_chunk) splits the post on claim/
    sentence boundaries, contextual.enrich_chunks annotates each chunk with
    an LLM-generated topic, extracted claims, source attribution, language
    and keywords, and here we fold those signals into a structured hint so the
    downstream web-grounded verifier searches the *actual* claims rather than
    the raw blob.
    """
    if not enriched:
        return ""

    all_claims: list[str] = []
    topics: set[str] = set()
    keywords: set[str] = set()
    sources: set[str] = set()
    languages: set[str] = set()

    for ec in enriched:
        for c in getattr(ec, "claims", []) or []:
            if isinstance(c, str) and c.strip():
                all_claims.append(c.strip())
        topic = getattr(ec, "topic", None)
        if topic and topic != "unknown":
            topics.add(topic)
        for kw in getattr(ec, "keywords", []) or []:
            if isinstance(kw, str) and kw.strip():
                keywords.add(kw.strip())
        src = getattr(ec, "source_mentioned", None)
        if src:
            sources.add(src)
        lang = getattr(ec, "language", None)
        if lang:
            languages.add(lang)

    # Dedupe claims while preserving order.
    seen: set[str] = set()
    deduped_claims = []
    for c in all_claims:
        key = c.lower()[:80]
        if key not in seen:
            seen.add(key)
            deduped_claims.append(c)

    lines = ["═══ EXTRACTED CLAIM CONTEXT (Contextual RAG pre-processing) ═══"]
    if deduped_claims:
        lines.append("Distinct factual claims detected (verify each):")
        for c in deduped_claims[:10]:
            lines.append(f"  • {c[:200]}")
    if topics:
        lines.append(f"Topics: {', '.join(sorted(topics)[:6])}")
    if keywords:
        lines.append(f"Search keywords: {', '.join(sorted(keywords)[:12])}")
    if sources:
        lines.append(f"Sources mentioned in text: {', '.join(sorted(sources)[:6])}")
    if languages:
        lines.append(f"Detected language(s): {', '.join(sorted(languages))}")
    return "\n".join(lines)


def _stringify_verifier_output(data: dict | None, fallback: str) -> str:

    """Turn a verifier JSON dict into a compact human/LLM-readable block."""
    if not data:
        return f"(no structured output — raw: {fallback[:300]})"
    out = []
    if "summary" in data:
        out.append(f"Summary: {data['summary']}")
    if "overall" in data:
        out.append(f"Overall: {data['overall']}")
    if "key_finding" in data:
        out.append(f"Key finding: {data['key_finding']}")
    claims = data.get("claims", [])
    if claims:
        out.append("Claims:")
        for c in claims[:8]:
            if not isinstance(c, dict):
                continue
            line = (
                f"  • [{c.get('verdict', '?')}] {c.get('claim', '')[:200]} "
                f"— {c.get('evidence', '')[:200]} "
                f"(src: {c.get('source_outlet', '?')} {c.get('source_url', '')[:80]} "
                f"@ {c.get('source_date', '?')})"
            )
            out.append(line)
    return "\n".join(out) or f"(empty structured output; raw: {fallback[:300]})"


async def _verify_with_model(
    model: str,
    prompt: str,
    timeout: float,
    label: str,
) -> tuple[dict | None, str]:
    """Run one verifier call. Returns (parsed_json_or_none, raw_text)."""
    client = get_pollinations_client()
    try:
        raw = await client.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a real-time fact-checker. You have live web "
                        "search access — use it. Return ONLY valid JSON, no "
                        "prose outside it."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            timeout=timeout,
            max_retries=1,
        )
        parsed = _extract_json(raw)
        logger.info(
            f"[Verify:{label}] {model} returned {len(raw)} chars, "
            f"parsed={'yes' if parsed else 'no'}, "
            f"claims={len(parsed.get('claims', [])) if parsed else 0}"
        )
        return parsed, raw
    except Exception as e:
        logger.warning(f"[Verify:{label}] {model} failed: {type(e).__name__}: {e}")
        return None, ""


async def _verify_facts(content: str, today: str, year: int) -> tuple[dict | None, dict | None, str, str]:
    """Run TWO independent verifiers in parallel. Returns
    (parsed_a, parsed_b, raw_a, raw_b)."""
    prompt = VERIFY_PROMPT.format(content=content, today=today, year=year)

    # Primary pair: Google grounded + Perplexity web.
    task_a = _verify_with_model("gemini-search-fast", prompt, 35.0, "A:gemini-search")
    task_b = _verify_with_model("perplexity-fast", prompt, 35.0, "B:perplexity-fast")

    (a_parsed, a_raw), (b_parsed, b_raw) = await asyncio.gather(task_a, task_b)

    # Fallbacks if either one came back empty.
    if not a_parsed:
        logger.info("[Verify] A failed — falling back to gemini-search")
        a_parsed, a_raw = await _verify_with_model("gemini-search", prompt, 40.0, "A-fb:gemini-search")
    if not b_parsed:
        logger.info("[Verify] B failed — falling back to perplexity-reasoning")
        b_parsed, b_raw = await _verify_with_model("perplexity-reasoning", prompt, 45.0, "B-fb:perplexity-reasoning")

    # Last-ditch: if BOTH still empty, try perplexity-deep solo.
    if not a_parsed and not b_parsed:
        logger.warning("[Verify] Both verifiers empty — trying perplexity-deep")
        a_parsed, a_raw = await _verify_with_model("perplexity-deep", prompt, 60.0, "last-resort")

    return a_parsed, b_parsed, a_raw, b_raw


async def _score_with_evidence(
    content: str,
    evidence_a: str,
    evidence_b: str,
    today: str,
    image_url: str | None,
) -> tuple[dict | None, str]:
    """Run the scoring pass (no web search needed)."""
    client = get_pollinations_client()
    prompt = SCORE_PROMPT.format(
        content=content, evidence_a=evidence_a, evidence_b=evidence_b, today=today
    )

    def _msgs(use_vision: bool) -> list[dict]:
        if use_vision and image_url:
            return [
                {"role": "system", "content": f"Today is {today}. Return ONLY JSON."},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                            + "\n\nAn image is attached. Examine it for "
                            "manipulation cues (deepfake artifacts, edited "
                            "text overlays, inconsistent lighting). "
                            "Incorporate findings into image_authenticity.",
                        },
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ]
        return [
            {"role": "system", "content": f"Today is {today}. Return ONLY JSON, no prose."},
            {"role": "user", "content": prompt},
        ]

    # Cascade: openai-large (reasoning, 1M ctx) → gpt-5.5 → gemini-3.5-flash
    has_image = bool(image_url)
    cascade = (
        [
            ("openai-large", 45.0, True, "openai-large-vision"),
            ("gemini-3.5-flash", 35.0, True, "gemini-3.5-flash-vision"),
            ("openai", 30.0, True, "openai-vision"),
        ]
        if has_image
        else [
            ("openai-large", 40.0, False, "openai-large"),
            ("gpt-5.5", 35.0, False, "gpt-5.5"),
            ("gemini-3.5-flash", 30.0, False, "gemini-3.5-flash"),
        ]
    )

    last_err: Exception | None = None
    for model, to, vision, label in cascade:
        try:
            raw = await client.chat(
                model=model,
                messages=_msgs(vision),
                temperature=0.2,
                timeout=to,
                max_retries=1,
            )
            parsed = _extract_json(raw)
            if parsed:
                logger.info(f"[Score] {model} parsed OK ({len(raw)} chars)")
                return parsed, label
            else:
                logger.warning(f"[Score] {model} returned unparseable output ({len(raw)} chars); trying next")
        except Exception as e:
            logger.warning(f"[Score] {model} failed ({type(e).__name__}: {e}); trying next")
            last_err = e
            continue

    logger.error(f"[Score] All scoring models failed: {last_err}")
    return None, "scoring-failed"


async def run_analysis(content: str, image_url: str | None = None) -> AnalyzeResponse:
    """Verifier-first 2-pass analysis.

    Pass 1: Run two web-grounded verifiers in parallel (gemini-search-fast +
    perplexity-fast). Each returns a JSON of claims+verdicts+sources.

    Pass 2: Feed both verifier outputs into a scoring-only call (openai-large,
    no web search needed). Returns 6 pillar scores + bilingual summary.
    """
    start_time = time.time()
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    year = datetime.now(timezone.utc).year

    logger.info(f"[Scoring] === Verifier-first analysis START (image={'yes' if image_url else 'no'}) ===")

    # ───── PASS 0: Contextual RAG pre-processing ─────
    # Variable/semantic chunking + Anthropic-style contextual enrichment.
    # Each chunk is split on claim/sentence boundaries (Bengali । + English . ? !)
    # then an LLM annotates topic, extracted claims, source, language & keywords.
    # The distilled claim context is prepended to the verifier prompt so the
    # web-grounded search targets the actual factual claims in the post.
    rag_context = ""
    try:
        pass0_t = time.time()
        chunks = semantic_chunk(content)
        if chunks:
            enriched = await enrich_chunks(chunks)
            rag_context = _build_rag_context(enriched)
            logger.info(
                f"[Scoring] Pass 0 (contextual RAG) done in {time.time() - pass0_t:.1f}s — "
                f"{len(chunks)} semantic chunks, {len(enriched)} enriched"
            )
    except Exception as e:
        logger.warning(f"[Scoring] Pass 0 (contextual RAG) skipped: {type(e).__name__}: {e}")

    verify_content = content if not rag_context else f"{content}\n\n{rag_context}"

    # ───── PASS 1: Verify ─────
    pass1_t = time.time()
    a_parsed, b_parsed, a_raw, b_raw = await _verify_facts(verify_content, today, year)
    logger.info(f"[Scoring] Pass 1 (verify) done in {time.time() - pass1_t:.1f}s")


    if not a_parsed and not b_parsed:
        return _error_response("All verifiers failed — could not retrieve current evidence", start_time)

    evidence_a = _stringify_verifier_output(a_parsed, a_raw)
    evidence_b = _stringify_verifier_output(b_parsed, b_raw)

    # ───── PASS 2: Score ─────
    pass2_t = time.time()
    scored, model_used = await _score_with_evidence(content, evidence_a, evidence_b, today, image_url)
    logger.info(f"[Scoring] Pass 2 (score) done in {time.time() - pass2_t:.1f}s")

    if not scored:
        # Fall back to a simple "translate verifier overall → score" path.
        logger.warning("[Scoring] Scoring step failed — synthesizing from verifier evidence")
        scored = _synthesize_from_verifiers(a_parsed, b_parsed)
        model_used = "verifier-synth"

    # ───── Build response ─────
    pillar_results: list[PillarScore] = []
    for pillar_key, weight in PILLAR_WEIGHTS.items():
        pdata = scored.get("pillar_scores", {}).get(pillar_key, {}) if scored else {}
        score = float(pdata.get("score", 50)) if isinstance(pdata, dict) else 50.0
        reason = pdata.get("reason", "No analysis available") if isinstance(pdata, dict) else "No analysis available"
        score = max(0.0, min(100.0, score))
        pillar_results.append(
            PillarScore(
                name=pillar_key.replace("_", " ").title(),
                name_bn=PILLAR_NAMES_BN.get(pillar_key, pillar_key),
                score=score,
                weight=weight,
                explanation_en=reason,
                explanation_bn=reason,
                evidence=_collect_evidence(a_parsed, b_parsed, scored),
                model_used=model_used,
                active=True,
            )
        )

    trust_score = sum(p.score * p.weight for p in pillar_results)
    trust_score = round(max(0.0, min(100.0, trust_score)), 1)
    verdict_en, verdict_bn = get_verdict(trust_score)

    ai_verdict = (scored or {}).get("overall_verdict", "")
    if ai_verdict:
        verdict_en, verdict_bn = _map_ai_verdict(ai_verdict, trust_score)

    explanation_en = _scrub_explanation((scored or {}).get("explanation_en", ""), is_bn=False)
    explanation_bn = _scrub_explanation((scored or {}).get("explanation_bn", ""), is_bn=True)

    if not explanation_en:
        explanation_en = f"Trust score: {trust_score}/100. {verdict_en}."
    if not explanation_bn:
        explanation_bn = f"বিশ্বাসযোগ্যতা স্কোর: {trust_score}/১০০। {verdict_bn}।"

    # Confidence: fraction of claims that got a definitive verdict.
    all_claims = (a_parsed or {}).get("claims", []) + (b_parsed or {}).get("claims", [])
    verified = [
        c for c in all_claims
        if isinstance(c, dict) and c.get("verdict") in ("true", "false", "misleading")
    ]
    confidence = min(1.0, (len(verified) + 1) / max(len(all_claims), 1))

    processing_time_ms = int((time.time() - start_time) * 1000)
    logger.info(
        f"[Scoring] === DONE in {processing_time_ms}ms. "
        f"score={trust_score} verdict={verdict_en} model={model_used} ==="
    )

    return AnalyzeResponse(
        trust_score=trust_score,
        verdict=verdict_en,
        verdict_bn=verdict_bn,
        pillars=pillar_results,
        explanation_en=explanation_en,
        explanation_bn=explanation_bn,
        confidence=round(confidence, 2),
        cached=False,
        processing_time_ms=processing_time_ms,
    )


def _collect_evidence(a: dict | None, b: dict | None, scored: dict | None) -> list[str]:
    """Collect human-readable evidence lines from both verifiers."""
    out = []
    seen = set()

    def push(claim_obj: dict, src: str):
        if not isinstance(claim_obj, dict):
            return
        key = (claim_obj.get("claim", "")[:60], claim_obj.get("source_url", "")[:60])
        if key in seen or not key[0]:
            return
        seen.add(key)
        line = (
            f"[{claim_obj.get('verdict', '?')}] "
            f"{claim_obj.get('claim', '')[:120]} — "
            f"{claim_obj.get('source_outlet', '?')} "
            f"({claim_obj.get('source_date', '?')}): "
            f"{claim_obj.get('source_url', '')[:120]}"
        )
        out.append(f"{src}: {line}")

    for c in (a or {}).get("claims", [])[:5]:
        push(c, "Google")
    for c in (b or {}).get("claims", [])[:5]:
        push(c, "Perplexity")

    # If scoring step gave us evidence_urls, append them too (deduped).
    for url in (scored or {}).get("evidence_urls", [])[:3] or []:
        if isinstance(url, str) and url and url not in " ".join(out):
            out.append(f"Cited: {url}")

    return out[:8]


def _synthesize_from_verifiers(a: dict | None, b: dict | None) -> dict:
    """Build a minimal scored dict from verifier outputs when the scoring
    pass fails entirely. Trust the verifiers' overall verdicts."""
    overall = (a or {}).get("overall") or (b or {}).get("overall") or "unverifiable"
    score_map = {
        "true": 90, "mostly_true": 75, "misleading": 45,
        "mostly_false": 25, "false": 10, "unverifiable": 30,
    }
    base = score_map.get(overall, 50)

    key_finding = (
        (a or {}).get("key_finding")
        or (b or {}).get("key_finding")
        or "Verifiers ran but the scoring step failed."
    )

    return {
        "pillar_scores": {
            "content_consistency": {"score": base, "reason": key_finding},
            "source_reputation": {"score": 40, "reason": "Source could not be evaluated by scoring step."},
            "language_analysis": {"score": 50, "reason": "Language analysis unavailable in fallback path."},
            "bengali_context": {"score": 50, "reason": "Context analysis unavailable in fallback path."},
            "image_authenticity": {"score": 50, "reason": "Not evaluated."},
            "author_network": {"score": 50, "reason": "Not evaluated."},
        },
        "overall_verdict": overall,
        "explanation_en": key_finding,
        "explanation_bn": key_finding,  # let scrubber pass through; better than empty.
        "evidence_urls": [],
    }


def _map_ai_verdict(ai_verdict: str, score: float) -> tuple[str, str]:
    mapping = {
        "true": ("True / Verified", "সত্য / যাচাইকৃত"),
        "mostly_true": ("Mostly True", "অধিকাংশ সত্য"),
        "misleading": ("Misleading / Mixed", "বিভ্রান্তিকর / মিশ্র"),
        "mostly_false": ("Mostly False", "অধিকাংশ মিথ্যা"),
        "false": ("False", "মিথ্যা"),
        "unverifiable": ("Unverifiable", "যাচাইযোগ্য নয়"),
    }
    return mapping.get(ai_verdict.lower(), get_verdict(score))


def _error_response(error_msg: str, start_time: float) -> AnalyzeResponse:
    processing_time_ms = int((time.time() - start_time) * 1000)
    pillar_results = []
    for pillar_key, weight in PILLAR_WEIGHTS.items():
        pillar_results.append(
            PillarScore(
                name=pillar_key.replace("_", " ").title(),
                name_bn=PILLAR_NAMES_BN.get(pillar_key, pillar_key),
                score=50.0,
                weight=weight,
                explanation_en=f"Analysis failed: {error_msg[:120]}",
                explanation_bn="বিশ্লেষণে ত্রুটি হয়েছে।",
                evidence=[],
                model_used="none",
                active=False,
            )
        )
    return AnalyzeResponse(
        trust_score=50.0,
        verdict="Analysis Failed",
        verdict_bn="বিশ্লেষণ ব্যর্থ",
        pillars=pillar_results,
        explanation_en=f"Analysis could not be completed: {error_msg[:200]}",
        explanation_bn="বিশ্লেষণ সম্পন্ন করা যায়নি।",
        confidence=0.0,
        cached=False,
        processing_time_ms=processing_time_ms,
    )
