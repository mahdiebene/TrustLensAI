"""Analyze endpoint — main trust scoring API."""

import hashlib
from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.schemas import AnalyzeRequest, AnalyzeResponse
from app.core.scoring import run_analysis
from app.services.redis_client import get_cache_service

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
    # Generate cache key from content hash
    content_hash = hashlib.sha256(body.content.encode()).hexdigest()[:16]
    cache_key = f"trustlens:analysis:{content_hash}"

    # Check cache first
    cache = get_cache_service()
    cached_result = await cache.get_cached(cache_key)
    if cached_result:
        result = AnalyzeResponse(**cached_result)
        result.cached = True
        return result

    # Run analysis pipeline
    result = await run_analysis(content=body.content, image_url=body.image_url)

    # Cache the result (24 hours)
    await cache.set_cached(cache_key, result.model_dump(), ttl=86400)

    return result
