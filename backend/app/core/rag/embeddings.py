"""Embedding generation and pgvector storage.

Uses Pollinations API with openai-3-large model (3072 dimensions).
Stores embeddings in PostgreSQL with pgvector extension for similarity search.
"""

import logging
from app.services.pollinations import get_pollinations_client
from app.services.redis_client import get_cache_service

logger = logging.getLogger(__name__)


async def get_embedding(text: str) -> list[float]:
    """
    Generate embedding vector for text using Pollinations API.

    Args:
        text: Text to embed (max ~8000 tokens)

    Returns:
        3072-dimensional float vector
    """
    # Check cache first (embeddings are expensive, cache for 7 days)
    cache = get_cache_service()
    cache_key = cache.make_key("embedding", text)
    cached = await cache.get_cached(cache_key)
    if cached:
        return cached.get("vector", [])

    try:
        client = get_pollinations_client()
        vector = await client.embed(text[:8000], model="openai-3-large")

        # Cache for 7 days
        await cache.set_cached(cache_key, {"vector": vector}, ttl=604800)

        logger.info(f"[Embeddings] Generated {len(vector)}-dim vector")
        return vector

    except Exception as e:
        logger.error(f"[Embeddings] Failed to generate embedding: {e}")
        return []


async def similarity_search(query_text: str, top_k: int = 5) -> list[dict]:
    """
    Search pgvector for similar content.

    Args:
        query_text: Text to find similar content for
        top_k: Number of results to return

    Returns:
        List of similar chunks with scores

    TODO: Implement actual pgvector query once database is seeded.
    Currently returns empty list as knowledge base is not yet populated.
    """
    query_embedding = await get_embedding(query_text)
    if not query_embedding:
        return []

    # TODO: Execute pgvector similarity query
    # SELECT content, 1 - (embedding <=> $1) as similarity
    # FROM knowledge_chunks
    # ORDER BY embedding <=> $1
    # LIMIT $2

    logger.info(f"[Embeddings] Similarity search for {len(query_text)} chars (top_k={top_k})")
    return []
