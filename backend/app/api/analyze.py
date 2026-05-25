"""Analyze endpoint — main trust scoring API."""

import asyncio
import hashlib
import logging
from urllib.parse import urlparse

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.core.scoring import run_analysis
from app.services.redis_client import get_cache_service
from app.services.scraper import is_url, scrape_url, is_social_media_url

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit("10/minute")
async def analyze_content(request: Request, body: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze content for trustworthiness.

    Takes text content or a URL and produces a Trust Score (0-100)
    with an explainable breakdown across 6 pillars.

    For social media URLs: skip scraping, pass URL directly to pillars.
    The perplexity-reasoning model (content_consistency) has built-in web access.
    """
    content = body.content.strip()
    source_url: str | None = None

    # Check cache FIRST (before any processing)
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    cache_key = f"trustlens:analysis:{content_hash}"
    cache = get_cache_service()
    cached_result = await cache.get_cached(cache_key)
    if cached_result:
        cached_result["cached"] = True
        return AnalyzeResponse(**cached_result)

    # Detect if content is a URL
    if is_url(content):
        source_url = content
        logger.info(f"[Analyze] URL detected: {source_url}")
        parsed = urlparse(source_url)

        if is_social_media_url(source_url):
            # For social media: pass URL directly to pillars (NO scraping delay)
            # perplexity-reasoning (content_consistency pillar) has web access
            # and will cross-reference the URL content automatically
            content = (
                f"[Analyze this social media post URL. Use your web search capabilities to read the content.]\n"
                f"URL: {source_url}\n"
                f"Source domain: {parsed.netloc}\n"
                f"Platform: Facebook\n"
                f"Instructions: Read the URL content and analyze for trustworthiness."
            )
            logger.info(f"[Analyze] Social media URL — passing directly to pillars (no scrape)")
        else:
            # For non-social URLs: quick scrape with tight timeout
            try:
                scraped = await asyncio.wait_for(scrape_url(source_url), timeout=8.0)
                if scraped["success"] and scraped["text"]:
                    parts = []
                    if scraped.get("author"):
                        parts.append(f"Author/Page: {scraped['author']}")
                    if scraped.get("title"):
                        parts.append(f"Title: {scraped['title']}")
                    parts.append(f"Source: {scraped.get('source_domain', 'unknown')}")
                    parts.append(f"URL: {source_url}")
                    parts.append(f"\nContent:\n{scraped['text']}")
                    content = "\n".join(parts)
                    logger.info(f"[Analyze] Scraped {len(scraped['text'])} chars from {source_url}")
                else:
                    content = (
                        f"[URL content could not be extracted]\n"
                        f"URL: {source_url}\n"
                        f"Source domain: {parsed.netloc}\n"
                        f"Analyze based on URL pattern and available information."
                    )
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"[Analyze] Scraping timed out/failed for {source_url}: {e}")
                content = (
                    f"[URL content extraction timed out]\n"
                    f"URL: {source_url}\n"
                    f"Source domain: {parsed.netloc}\n"
                    f"Analyze based on URL pattern and available information."
                )

    # Run analysis pipeline
    result = await run_analysis(content=content, image_url=body.image_url)

    # Cache the result (24 hours)
    await cache.set_cached(cache_key, result.model_dump(), ttl=86400)

    return result
