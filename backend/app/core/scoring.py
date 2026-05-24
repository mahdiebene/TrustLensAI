"""Score aggregation and synthesis."""

import asyncio
import json
import logging
import time

from app.core.pillars.source_reputation import SourceReputationPillar
from app.core.pillars.content_consistency import ContentConsistencyPillar
from app.core.pillars.language_analysis import LanguageAnalysisPillar
from app.core.pillars.bengali_context import BengaliContextPillar
from app.core.pillars.image_authenticity import ImageAuthenticityPillar
from app.core.pillars.author_network import AuthorNetworkPillar
from app.models.schemas import AnalyzeResponse, PillarScore
from app.services.pollinations import get_pollinations_client
from app.services.redis_client import get_cache_service

logger = logging.getLogger(__name__)

# Verdict mappings
VERDICTS = [
    (80, "Highly Trustworthy", "অত্যন্ত বিশ্বাসযোগ্য"),
    (60, "Generally Reliable", "সাধারণত নির্ভরযোগ্য"),
    (40, "Questionable", "সন্দেহজনক"),
    (20, "Likely Unreliable", "সম্ভবত অবিশ্বাসযোগ্য"),
    (0, "High Risk", "উচ্চ ঝুঁকি"),
]

SYNTHESIS_PROMPT = """You are the final synthesis engine for TrustLens, a trust scoring platform for Bengali social media.

You have received analysis results from 6 specialized AI pillars. Your job is to:
1. Synthesize all findings into a coherent explanation
2. Highlight the most important factors affecting trustworthiness
3. Provide actionable guidance to the reader

Pillar Results:
{pillar_summary}

Overall Weighted Score: {score}/100
Verdict: {verdict}

Generate a final explanation in BOTH English and Bengali. Be specific — reference actual findings from the pillars. Do not be generic.

Return JSON:
{{
  "explanation_en": "<2-3 sentence English explanation referencing specific findings>",
  "explanation_bn": "<2-3 sentence Bengali explanation referencing specific findings>"
}}"""


def get_verdict(score: float) -> tuple[str, str]:
    """Get verdict strings based on score."""
    for threshold, en, bn in VERDICTS:
        if score >= threshold:
            return en, bn
    return VERDICTS[-1][1], VERDICTS[-1][2]


async def synthesize_explanation(
    pillar_results: list[PillarScore],
    trust_score: float,
    verdict_en: str,
    content: str,
) -> tuple[str, str]:
    """
    Use gpt-5.5 to generate a final synthesized explanation.
    Falls back to a template-based explanation if the API call fails.
    """
    try:
        # Build pillar summary for the synthesis prompt
        pillar_summary = "\n".join([
            f"- {r.name} ({r.score:.0f}/100): {r.explanation_en[:150]}"
            for r in pillar_results if r.active
        ])

        prompt = SYNTHESIS_PROMPT.format(
            pillar_summary=pillar_summary,
            score=f"{trust_score:.1f}",
            verdict=verdict_en,
        )

        client = get_pollinations_client()
        response = await client.chat(
            model="gpt-5.5",
            messages=[
                {"role": "system", "content": "You are a concise trust analysis synthesizer. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            timeout=60.0,  # gpt-5.5 may be slower
        )

        # Parse response
        text = response.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            result = json.loads(json_match.group())
            return result.get("explanation_en", ""), result.get("explanation_bn", "")

        return text, text

    except Exception as e:
        logger.warning(f"[Synthesis] gpt-5.5 synthesis failed, using template: {e}")
        # Fallback: template-based explanation
        active_pillars = [r for r in pillar_results if r.active]
        top_concern = min(active_pillars, key=lambda r: r.score) if active_pillars else None
        top_strength = max(active_pillars, key=lambda r: r.score) if active_pillars else None

        en = f"Analysis based on {len(active_pillars)} active pillars. Score: {trust_score:.1f}/100."
        bn = f"{len(active_pillars)}টি সক্রিয় স্তম্ভের উপর ভিত্তি করে বিশ্লেষণ। স্কোর: {trust_score:.1f}/১০০।"

        if top_concern and top_concern.score < 50:
            en += f" Main concern: {top_concern.name} scored {top_concern.score:.0f}/100."
            bn += f" প্রধান উদ্বেগ: {top_concern.name_bn} স্কোর {top_concern.score:.0f}/১০০।"
        if top_strength and top_strength.score >= 70:
            en += f" Strength: {top_strength.name} scored {top_strength.score:.0f}/100."
            bn += f" শক্তি: {top_strength.name_bn} স্কোর {top_strength.score:.0f}/১০০।"

        return en, bn


async def run_analysis(content: str, image_url: str | None = None) -> AnalyzeResponse:
    """
    Run all 6 pillars in parallel and aggregate scores.

    Args:
        content: Text content or URL to analyze
        image_url: Optional image URL

    Returns:
        Complete AnalyzeResponse with all pillar scores
    """
    start_time = time.time()

    # Initialize all pillars
    pillars = [
        SourceReputationPillar(),
        ContentConsistencyPillar(),
        LanguageAnalysisPillar(),
        BengaliContextPillar(),
        ImageAuthenticityPillar(),
        AuthorNetworkPillar(),
    ]

    # Run all pillars in parallel
    results: list[PillarScore] = await asyncio.gather(
        *[pillar.analyze(content, image_url) for pillar in pillars]
    )

    # Calculate weighted score
    trust_score = sum(r.score * r.weight for r in results)

    # Get verdict
    verdict_en, verdict_bn = get_verdict(trust_score)

    # Calculate confidence (based on how many pillars are active)
    active_count = sum(1 for r in results if r.active)
    confidence = active_count / len(results)

    # Synthesize explanation using gpt-5.5
    explanation_en, explanation_bn = await synthesize_explanation(
        results, trust_score, verdict_en, content
    )

    # Processing time
    processing_time_ms = int((time.time() - start_time) * 1000)

    return AnalyzeResponse(
        trust_score=round(trust_score, 1),
        verdict=verdict_en,
        verdict_bn=verdict_bn,
        pillars=results,
        explanation_en=explanation_en,
        explanation_bn=explanation_bn,
        confidence=round(confidence, 2),
        cached=False,
        processing_time_ms=processing_time_ms,
    )
