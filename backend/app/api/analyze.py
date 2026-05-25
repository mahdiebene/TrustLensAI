"""Analyze endpoint — main trust scoring API.

Simplified flow: cache check → single AI call → format response.
"""

import hashlib
import logging

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.core.scoring import run_analysis
from app.services.redis_client import get_cache_service
from app.services.scraper import is_url, is_social_media_url, scrape_generic_url

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze_content(request: Request, body: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze content for trustworthiness.

    Architecture (2 API calls total):
    1. Cache check (instant)
    2. perplexity-reasoning: reads URL, extracts claims, verifies, scores (~10s)
    3. gemini-2.5-flash: bilingual summary (~3s)

    For URLs (including Facebook): passed directly to perplexity-reasoning
    which has built-in web browsing. No separate scraping needed.
    """
    content = body.content.strip()

    # ─── Cache check FIRST ───
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    cache_key = f"trustlens:analysis:{content_hash}"
    cache = get_cache_service()
    cached_result = await cache.get_cached(cache_key)
    if cached_result:
        cached_result["cached"] = True
        return AnalyzeResponse(**cached_result)

    # ─── Prepare content for analysis ───
    if is_url(content):
        logger.info(f"[Analyze] URL detected: {content}")

        if is_social_media_url(content):
            # Social media URLs: pass directly to perplexity-reasoning
            # It has built-in web access and can read Facebook posts
            analysis_content = (
                f"URL: {content}\n"
                f"Instructions: Read this social media post URL using your web browsing capabilities. "
                f"Extract the full content, then analyze for trustworthiness."
            )
            logger.info("[Analyze] Social media URL — passing directly to perplexity-reasoning")
        else:
            # Non-social URLs: try quick scrape, but also pass URL to AI
            scraped = await scrape_generic_url(content)
            if scraped["success"] and scraped["text"]:
                analysis_content = (
                    f"URL: {content}\n"
                    f"Source: {scraped.get('source_domain', 'unknown')}\n"
                )
                if scraped.get("author"):
                    analysis_content += f"Author: {scraped['author']}\n"
                if scraped.get("title"):
                    analysis_content += f"Title: {scraped['title']}\n"
                analysis_content += f"\nContent:\n{scraped['text']}"
                logger.info(f"[Analyze] Scraped {len(scraped['text'])} chars, passing to analysis")
            else:
                # Scrape failed — let perplexity-reasoning read it directly
                analysis_content = (
                    f"URL: {content}\n"
                    f"Instructions: Read this URL using your web browsing capabilities. "
                    f"Extract the content, then analyze for trustworthiness."
                )
                logger.info("[Analyze] Scrape failed — passing URL directly to perplexity-reasoning")
    else:
        # Plain text content
        analysis_content = content

    # ─── Run analysis (2 API calls inside) ───
    result = await run_analysis(content=analysis_content, image_url=body.image_url)

    # ─── Cache result (24 hours) ───
    await cache.set_cached(cache_key, result.model_dump(), ttl=86400)

    return result
