"""TrustLens scoring engine — single-call architecture.

Uses ONE perplexity-reasoning call for complete analysis (URL reading, claim
extraction, web verification, all 6 pillar scores) followed by ONE gemini-2.5-flash
call for summary generation. Total: ~13s, 2 API calls.
"""

import json
import logging
import re
import time

from app.models.schemas import AnalyzeResponse, PillarScore
from app.services.pollinations import get_pollinations_client

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

# Verdict mappings — now truth-focused
VERDICTS = [
    (85, "True / Verified", "সত্য / যাচাইকৃত"),
    (70, "Mostly True", "অধিকাংশ সত্য"),
    (50, "Misleading / Mixed", "বিভ্রান্তিকর / মিশ্র"),
    (30, "Mostly False", "অধিকাংশ মিথ্যা"),
    (15, "False", "মিথ্যা"),
    (0, "Unverifiable", "যাচাইযোগ্য নয়"),
]

ANALYSIS_PROMPT = """You are TrustLens, a fact-checking AI for Bengali / Bangladeshi social media.

The content below has ALREADY BEEN EXTRACTED for you (post text, author, source). Do NOT
say you cannot read URLs — work with the text provided. Use web search to verify the
factual claims you find in the text.

CONTENT TO ANALYZE:
---
{content}
---

WHAT TO DO:
1. Read the extracted text above carefully.
2. List every concrete factual claim (who/what/where/when, numbers, named people, events).
3. For each claim, run a web search and report what you found (confirms, contradicts, or no result).
4. Detect manipulation cues: emotional/inflammatory words, fear-mongering, urgency, undisclosed bias.
5. Apply the Bangladesh context: known misinformation patterns, partisan accounts, communal framing.
6. Score the 6 pillars 0–100 using the rubric below — and DO NOT default to 50 unless you genuinely have no signal at all.

═══ SCORING RUBRIC (use these anchors, don't hedge at 50) ═══

For EVERY pillar:
  • 85–100 → Strong evidence FOR trustworthiness (verified by reputable sources, neutral language, established author).
  • 60–84  → Mostly trustworthy with minor concerns.
  • 40–59  → Mixed / genuinely ambiguous — only use when evidence is balanced, NOT as a "safe" default.
  • 15–39  → Mostly untrustworthy (contradicted by sources, manipulative language, suspicious account).
  • 0–14   → Strong evidence AGAINST (clearly false, fabricated, known disinformation).

Per-pillar guidance:
  • content_consistency (40% weight, MOST IMPORTANT): How well do the claims hold up against web sources?
      - Multiple reputable sources confirm → 80+
      - No matching coverage anywhere (only the original post) → 25–40 (suspicious, not "neutral")
      - Reputable sources contradict → 5–20
  • source_reputation: Is the page/author/domain known and credible?
      - Established outlet (BBC Bangla, Prothom Alo, BOOM, Rumor Scanner) → 80+
      - Anonymous/unknown FB page with partisan framing → 20–40
      - Known disinformation source → 0–15
  • language_analysis: Tone & framing.
      - Neutral, factual, attributed quotes → 70+
      - Hedged ("reportedly", "allegedly") → 50–65
      - Emotional/inflammatory/loaded words, ALL CAPS, excessive punctuation → 15–35
  • bengali_context: Bangladesh-specific patterns.
      - Aligns with verified local reporting → 70+
      - Matches known rumor template (communal, political smear, miracle cure, etc.) → 10–30
  • author_network: The poster.
      - Verified journalist / official page → 80+
      - Random page with low followers / no track record → 30–50
      - Page known for partisan rumor-mongering → 10–25
  • image_authenticity: Only if an image is referenced. If no image at all → score 50 and say "no image to assess".

═══ HARD RULES ═══
  • Be DECISIVE. A score of exactly 50 across multiple pillars is a failure mode — pick a side based on evidence.
  • If the claim is unverifiable due to lack of sources, that itself is a NEGATIVE signal for content_consistency (score it 25–40, not 50).
  • Do NOT invent sources. If a search returned nothing, say so.
  • Bengali content is fine — analyze it directly.

Return THIS EXACT JSON (no markdown, no prose outside the JSON):
{{
  "content_extracted": "<short summary of what the post actually says, 1-2 sentences>",
  "claims": [
    {{"claim": "<specific claim>", "verdict": "true|false|unverifiable|misleading", "evidence": "<source URL or what your search found>"}}
  ],
  "pillar_scores": {{
    "source_reputation": {{"score": <0-100>, "reason": "<one sentence, cite a signal>"}},
    "content_consistency": {{"score": <0-100>, "reason": "<one sentence, cite what search found>"}},
    "language_analysis": {{"score": <0-100>, "reason": "<one sentence, cite specific words/tone>"}},
    "bengali_context": {{"score": <0-100>, "reason": "<one sentence>"}},
    "image_authenticity": {{"score": <0-100>, "reason": "<one sentence or 'no image'>"}},
    "author_network": {{"score": <0-100>, "reason": "<one sentence about the page/author>"}}
  }},
  "overall_verdict": "true|mostly_true|misleading|mostly_false|false|unverifiable",
  "explanation_en": "<2-3 sentence English summary. Start with the verdict. Be specific about what is true/false/unverified.>",
  "explanation_bn": "<2-3 sentence Bengali summary in fluent Bengali. Start with the verdict. Be specific.>"
}}"""

SUMMARY_PROMPT = """You are a bilingual (English/Bengali) fact-check summarizer.

Given this analysis result, produce a clear, concise summary for the user.
The user wants to know: "Is this content TRUE or FALSE?"

Analysis:
{analysis_json}

Return JSON:
{{
  "explanation_en": "<2-3 sentence plain English summary. Start with the verdict. Be specific about what claims are true/false.>",
  "explanation_bn": "<Same summary in Bengali. Start with verdict. Be specific.>"
}}"""


def get_verdict(score: float) -> tuple[str, str]:
    """Get verdict strings based on score."""
    for threshold, en, bn in VERDICTS:
        if score >= threshold:
            return en, bn
    return VERDICTS[-1][1], VERDICTS[-1][2]


def _extract_json(text: str) -> dict | None:
    """Extract JSON from a response that may contain markdown code blocks or extra text."""
    # Remove markdown code blocks
    if "```" in text:
        # Try to extract content between ```json and ```
        json_block = re.search(r'```(?:json)?\s*\n?([\s\S]*?)\n?```', text)
        if json_block:
            text = json_block.group(1)

    # Find the outermost JSON object
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            # Try fixing common issues
            raw = json_match.group()
            # Remove trailing commas before } or ]
            raw = re.sub(r',\s*([}\]])', r'\1', raw)
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
    return None


async def run_analysis(content: str, image_url: str | None = None) -> AnalyzeResponse:
    """
    Run complete analysis with 2 API calls:
    1. perplexity-reasoning: reads URL, extracts claims, verifies, scores all pillars
    2. gemini-2.5-flash: generates bilingual summary

    Total target: ~13 seconds.
    """
    start_time = time.time()
    client = get_pollinations_client()

    # ─── Step 1: Single perplexity-reasoning call for ALL analysis ───
    logger.info("[Scoring] Step 1: perplexity-reasoning analysis starting...")

    prompt = ANALYSIS_PROMPT.format(content=content)

    raw_response = ""
    model_used = "perplexity-reasoning"
    try:
        raw_response = await client.chat(
            model="perplexity-reasoning",
            messages=[
                {"role": "system", "content": "You are a fact-checking AI. Return ONLY valid JSON. No markdown, no explanation outside the JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            timeout=50.0,
            max_retries=1,
        )
    except Exception as e:
        logger.warning(f"[Scoring] perplexity-reasoning failed ({e}); falling back to openai-large")
        # Fallback to a faster model — no live web search, but still scores from extracted content
        try:
            raw_response = await client.chat(
                model="openai-large",
                messages=[
                    {"role": "system", "content": "You are a fact-checking AI. Use your training knowledge. Return ONLY valid JSON. No markdown, no explanation outside the JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                timeout=30.0,
                max_retries=1,
            )
            model_used = "openai-large-fallback"
        except Exception as e2:
            logger.error(f"[Scoring] Fallback openai-large also failed: {e2}")
            return _error_response(f"Both models failed: {e2}", start_time)

    step1_time = time.time() - start_time
    logger.info(f"[Scoring] Step 1 complete in {step1_time:.1f}s, response length={len(raw_response)}")

    # Parse the JSON response
    analysis = _extract_json(raw_response)
    if not analysis:
        logger.error(f"[Scoring] Failed to parse JSON from perplexity response: {raw_response[:500]}")
        return _error_response("Failed to parse AI response", start_time)

    # ─── Extract pillar scores ───
    pillar_scores_raw = analysis.get("pillar_scores", {})
    pillar_results: list[PillarScore] = []

    for pillar_key, weight in PILLAR_WEIGHTS.items():
        pillar_data = pillar_scores_raw.get(pillar_key, {})
        score = float(pillar_data.get("score", 50)) if isinstance(pillar_data, dict) else 50.0
        reason = pillar_data.get("reason", "No analysis available") if isinstance(pillar_data, dict) else "No analysis available"

        # Clamp score to 0-100
        score = max(0.0, min(100.0, score))

        pillar_results.append(PillarScore(
            name=pillar_key.replace("_", " ").title(),
            name_bn=PILLAR_NAMES_BN.get(pillar_key, pillar_key),
            score=score,
            weight=weight,
            explanation_en=reason,
            explanation_bn=reason,  # Will be overridden by summary step if needed
            evidence=_extract_evidence(analysis),
            model_used=model_used,
            active=True,
        ))

    # Calculate weighted trust score
    trust_score = sum(p.score * p.weight for p in pillar_results)
    trust_score = round(max(0.0, min(100.0, trust_score)), 1)

    # Get verdict
    verdict_en, verdict_bn = get_verdict(trust_score)

    # Override verdict with AI's overall_verdict if it's more specific
    ai_verdict = analysis.get("overall_verdict", "")
    if ai_verdict:
        verdict_en, verdict_bn = _map_ai_verdict(ai_verdict, trust_score)

    # ─── Step 2: gemini-2.5-flash summary (fast) ───
    explanation_en = analysis.get("explanation_en", "")
    explanation_bn = analysis.get("explanation_bn", "")

    if not explanation_en or not explanation_bn:
        try:
            logger.info("[Scoring] Step 2: gemini summary...")
            summary_response = await client.chat(
                model="gemini-2.5-flash",
                messages=[
                    {"role": "system", "content": "Return only valid JSON. Be concise and factual."},
                    {"role": "user", "content": SUMMARY_PROMPT.format(
                        analysis_json=json.dumps(analysis, ensure_ascii=False)[:3000]
                    )},
                ],
                temperature=0.3,
                timeout=10.0,
            )
            summary = _extract_json(summary_response)
            if summary:
                explanation_en = summary.get("explanation_en", explanation_en)
                explanation_bn = summary.get("explanation_bn", explanation_bn)
        except Exception as e:
            logger.warning(f"[Scoring] Summary generation failed (using perplexity output): {e}")

    # Confidence based on claims verified
    claims = analysis.get("claims", [])
    verified_claims = [c for c in claims if c.get("verdict") in ("true", "false", "misleading")]
    confidence = min(1.0, (len(verified_claims) + 1) / max(len(claims), 1))

    processing_time_ms = int((time.time() - start_time) * 1000)
    logger.info(f"[Scoring] Complete in {processing_time_ms}ms. Score={trust_score}, Verdict={verdict_en}")

    return AnalyzeResponse(
        trust_score=trust_score,
        verdict=verdict_en,
        verdict_bn=verdict_bn,
        pillars=pillar_results,
        explanation_en=explanation_en or f"Trust score: {trust_score}/100. {verdict_en}.",
        explanation_bn=explanation_bn or f"বিশ্বাসযোগ্যতা স্কোর: {trust_score}/১০০। {verdict_bn}।",
        confidence=round(confidence, 2),
        cached=False,
        processing_time_ms=processing_time_ms,
    )


def _extract_evidence(analysis: dict) -> list[str]:
    """Extract evidence URLs/reasons from claims."""
    evidence = []
    for claim in analysis.get("claims", [])[:5]:
        if isinstance(claim, dict):
            ev = claim.get("evidence", "")
            if ev:
                evidence.append(f"[{claim.get('verdict', '?')}] {claim.get('claim', '')[:80]} — {ev[:100]}")
    return evidence


def _map_ai_verdict(ai_verdict: str, score: float) -> tuple[str, str]:
    """Map AI's overall_verdict string to display verdicts."""
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
    """Generate a minimal error response when analysis fails."""
    processing_time_ms = int((time.time() - start_time) * 1000)

    pillar_results = []
    for pillar_key, weight in PILLAR_WEIGHTS.items():
        pillar_results.append(PillarScore(
            name=pillar_key.replace("_", " ").title(),
            name_bn=PILLAR_NAMES_BN.get(pillar_key, pillar_key),
            score=50.0,
            weight=weight,
            explanation_en=f"Analysis failed: {error_msg[:100]}",
            explanation_bn="বিশ্লেষণে ত্রুটি হয়েছে।",
            evidence=[],
            model_used="none",
            active=False,
        ))

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
