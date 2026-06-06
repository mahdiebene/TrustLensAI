"""Analyze endpoint — main trust scoring API.

Flow:
  1. Cache check (instant).
  2. If input is a URL:
       - For Facebook: try to scrape (Jina Reader → OG fallback).
         * On success → pass extracted text to AI.
         * On failure → return a structured `scrape_failed` response asking
           the user to paste the post text / upload a screenshot. We do NOT
           run an AI call here, because without the actual content the AI
           just returns hedged 50/50 scores (poor UX, wasted ~30s).
       - For other URLs: scrape generically; if it fails, pass the URL itself.
  3. If input is plain text: pass through directly.
  4. Run analysis (perplexity-reasoning + gemini summary).
  5. Cache result for 24h — but NOT errors / all-50 default responses.
"""

import hashlib
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import AnalyzeRequest, AnalyzeResponse, PillarScore
from app.core.scoring import run_analysis, PILLAR_WEIGHTS, PILLAR_NAMES_BN
from app.services.redis_client import get_cache_service
from app.services.scraper import is_url, is_facebook_url, scrape_url

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


def _scrape_failed_response(
    url: str,
    reason_en: str,
    reason_bn: str,
    start_time: float,
) -> AnalyzeResponse:
    """Build an AnalyzeResponse signaling scrape failure → frontend should
    prompt the user for text/image input.

    We return a "neutral / unknown" body (50s, but flagged via
    `scrape_failed=True` so the frontend renders a different UI). No AI
    call has been made — this is fast (< 5s).
    """
    pillars: list[PillarScore] = []
    for pillar_key, weight in PILLAR_WEIGHTS.items():
        pillars.append(PillarScore(
            name=pillar_key.replace("_", " ").title(),
            name_bn=PILLAR_NAMES_BN.get(pillar_key, pillar_key),
            score=0.0,
            weight=weight,
            explanation_en="Awaiting content — paste the post text or upload a screenshot.",
            explanation_bn="কনটেন্টের অপেক্ষায় — পোস্টের লেখা পেস্ট করুন বা স্ক্রিনশট আপলোড করুন।",
            evidence=[],
            model_used="none",
            active=False,
        ))

    processing_time_ms = int((time.time() - start_time) * 1000)

    return AnalyzeResponse(
        trust_score=0.0,
        verdict="Content Not Accessible",
        verdict_bn="কনটেন্ট অ্যাক্সেস করা যায়নি",
        pillars=pillars,
        explanation_en=reason_en or "Could not retrieve this URL. Paste the post text or upload a screenshot to get a trust score.",
        explanation_bn=reason_bn or "এই লিংকটি আনতে পারিনি। ট্রাস্ট স্কোর পেতে পোস্টের লেখা পেস্ট করুন বা স্ক্রিনশট আপলোড করুন।",
        confidence=0.0,
        cached=False,
        processing_time_ms=processing_time_ms,
        scrape_failed=True,
        scrape_reason_en=reason_en,
        scrape_reason_bn=reason_bn,
        needs_user_input=True,
        original_url=url,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze_content(request: Request, body: AnalyzeRequest) -> AnalyzeResponse:
    """Analyze content for trustworthiness."""
    start_time = time.time()
    content = body.content.strip()

    # ─── Cache check FIRST ───
    # `v2` namespace = bumped after the recency-aware prompt rewrite, so old
    # cached "Tarique=false" type answers (built before the date-injection fix)
    # are invalidated. Date in the key ensures political claims re-verify each
    # day — facts about current office-holders shouldn't be cached for 24h
    # across days when the underlying world can change overnight.
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    today_key = datetime.now(timezone.utc).strftime("%Y%m%d")
    cache_key = f"trustlens:analysis:v2:{today_key}:{content_hash}"
    cache = get_cache_service()
    cached_result = await cache.get_cached(cache_key)
    if cached_result:
        cached_result["cached"] = True
        return AnalyzeResponse(**cached_result)

    # ─── Prepare content for analysis ───
    analysis_content = content
    image_url = body.image_url

    if is_url(content):
        logger.info(f"[Analyze] URL detected: {content}")
        scraped = await scrape_url(content)

        if scraped["success"] and scraped["text"]:
            # Build a clean prompt input from the extracted text
            parts = [f"URL: {content}"]
            if scraped.get("source_domain"):
                parts.append(f"Source: {scraped['source_domain']}")
            if scraped.get("author"):
                parts.append(f"Author / Page: {scraped['author']}")
            if scraped.get("title"):
                parts.append(f"Title: {scraped['title']}")
            parts.append("")
            parts.append("Extracted Post Content:")
            parts.append(scraped["text"])
            analysis_content = "\n".join(parts)

            # Pass image to AI if scraped one and caller didn't provide
            if not image_url and scraped.get("image_url"):
                image_url = scraped["image_url"]

            logger.info(
                f"[Analyze] Scraped {len(scraped['text'])} chars from "
                f"{'Facebook' if is_facebook_url(content) else 'generic URL'}, passing to analysis"
            )
        else:
            # Scrape failed
            if is_facebook_url(content):
                # User wants: show reason + ask for text/image input.
                # No AI call — return immediately with structured signal.
                reason_en = scraped.get("failure_reason") or (
                    "Could not retrieve this Facebook post — it may be private, "
                    "in a closed group, deleted, or restricted to logged-in users."
                )
                reason_bn = scraped.get("failure_reason_bn") or (
                    "এই ফেসবুক পোস্টটি আনতে পারিনি — সম্ভবত এটি প্রাইভেট, "
                    "ক্লোজড গ্রুপে আছে, ডিলিট হয়েছে, অথবা লগইন ছাড়া দেখা যায় না।"
                )
                logger.warning(
                    f"[Analyze] FB scrape failed → returning scrape_failed response. "
                    f"Reason: {reason_en[:80]}"
                )
                result = _scrape_failed_response(content, reason_en, reason_bn, start_time)
                # Don't cache this — user will retry with text/image
                return result
            else:
                # Generic URL scrape failed → let perplexity-reasoning try its own browsing
                analysis_content = (
                    f"URL: {content}\n"
                    f"Instructions: Read this URL using your web browsing capabilities. "
                    f"Extract the content, then analyze for trustworthiness."
                )
                logger.info("[Analyze] Generic scrape failed — passing URL to perplexity-reasoning")

    # ─── Run analysis (2 API calls inside) ───
    result = await run_analysis(content=analysis_content, image_url=image_url)

    # ─── Cache result (24h) — but NOT errors / all-default responses ───
    is_error = (
        result.verdict in ("Analysis Failed", "Error", "Content Not Accessible")
        or result.scrape_failed
        or all(p.score == 50.0 for p in result.pillars)  # all-default scores = AI failed
    )
    if not is_error:
        await cache.set_cached(cache_key, result.model_dump(), ttl=86400)
    else:
        logger.warning(f"[Analyze] Skipping cache for error result: {result.verdict}")

    return result
