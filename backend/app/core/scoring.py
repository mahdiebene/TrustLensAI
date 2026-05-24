"""Score aggregation and synthesis."""

import asyncio
import time

from app.core.pillars.source_reputation import SourceReputationPillar
from app.core.pillars.content_consistency import ContentConsistencyPillar
from app.core.pillars.language_analysis import LanguageAnalysisPillar
from app.core.pillars.bengali_context import BengaliContextPillar
from app.core.pillars.image_authenticity import ImageAuthenticityPillar
from app.core.pillars.author_network import AuthorNetworkPillar
from app.models.schemas import AnalyzeResponse, PillarScore


# Verdict mappings
VERDICTS = [
    (80, "Highly Trustworthy", "অত্যন্ত বিশ্বাসযোগ্য"),
    (60, "Generally Reliable", "সাধারণত নির্ভরযোগ্য"),
    (40, "Questionable", "সন্দেহজনক"),
    (20, "Likely Unreliable", "সম্ভবত অবিশ্বাসযোগ্য"),
    (0, "High Risk", "উচ্চ ঝুঁকি"),
]


def get_verdict(score: float) -> tuple[str, str]:
    """Get verdict strings based on score."""
    for threshold, en, bn in VERDICTS:
        if score >= threshold:
            return en, bn
    return VERDICTS[-1][1], VERDICTS[-1][2]


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

    # Processing time
    processing_time_ms = int((time.time() - start_time) * 1000)

    return AnalyzeResponse(
        trust_score=round(trust_score, 1),
        verdict=verdict_en,
        verdict_bn=verdict_bn,
        pillars=results,
        explanation_en=f"Analysis based on {active_count}/6 active pillars. Score: {trust_score:.1f}/100.",
        explanation_bn=f"{active_count}/৬টি সক্রিয় স্তম্ভের উপর ভিত্তি করে বিশ্লেষণ। স্কোর: {trust_score:.1f}/১০০।",
        confidence=round(confidence, 2),
        cached=False,
        processing_time_ms=processing_time_ms,
    )
