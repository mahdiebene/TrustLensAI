"""Analyze endpoint — main trust scoring API."""

import hashlib
import logging
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.core.scoring import run_analysis
from app.services.redis_client import get_cache_service
from app.services.scraper import is_url, scrape_url

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
    """
    content = body.content.strip()
    source_url: str | None = None

    # Detect if content is a URL and scrape it
    if is_url(content):
        source_url = content
        logger.info(f"[Analyze] URL detected, scraping: {source_url}")

        scraped = await scrape_url(source_url)

        if scraped["success"] and scraped["text"]:
            # Build rich context for AI pillars
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
            # Scraping failed — prepend context so AI knows it's a URL
            logger.warning(f"[Analyze] Scraping failed for {source_url}")
            content = (
                f"[NOTE: This is a Facebook/social media URL whose content could not be fully extracted. "
                f"The URL is: {source_url}. "
                f"Source domain: {scraped.get('source_domain', 'unknown')}. "
                f"Please analyze based on the URL pattern and any information you can infer.]\n\n"
                f"URL: {source_url}"
            )
            if scraped.get("author"):
                content += f"\nAuthor/Page: {scraped['author']}"
            if scraped.get("title"):
                content += f"\nTitle: {scraped['title']}"

    # Generate cache key from content hash
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    cache_key = f"trustlens:analysis:{content_hash}"

    # Check cache first
    cache = get_cache_service()
    cached_result = await cache.get_cached(cache_key)
    if cached_result:
        cached_result["cached"] = True
        return AnalyzeResponse(**cached_result)

    # Run analysis pipeline
    result = await run_analysis(content=content, image_url=body.image_url)

    # Cache the result (24 hours)
    await cache.set_cached(cache_key, result.model_dump(), ttl=86400)

    return result
