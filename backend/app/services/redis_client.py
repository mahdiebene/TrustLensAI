"""Redis caching service."""

import hashlib
import json
import logging
from typing import Any

from redis import asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching for API responses."""

    def __init__(self):
        settings = get_settings()
        self._redis: aioredis.Redis | None = None
        self._url = settings.REDIS_URL

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = aioredis.from_url(self._url, decode_responses=True)
        return self._redis

    @staticmethod
    def make_key(prefix: str, content: str) -> str:
        """Generate cache key from content hash."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"trustlens:{prefix}:{content_hash}"

    async def get_cached(self, key: str) -> dict | None:
        """Get cached value by key."""
        try:
            redis = await self._get_redis()
            value = await redis.get(key)
            if value:
                logger.info(f"[Cache] HIT: {key}")
                return json.loads(value)
            logger.debug(f"[Cache] MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"[Cache] Error reading {key}: {e}")
            return None

    async def set_cached(self, key: str, value: dict, ttl: int = 86400) -> None:
        """Set cached value with TTL (default 24h)."""
        try:
            redis = await self._get_redis()
            await redis.set(key, json.dumps(value), ex=ttl)
            logger.info(f"[Cache] SET: {key} (TTL={ttl}s)")
        except Exception as e:
            logger.warning(f"[Cache] Error writing {key}: {e}")

    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.aclose()
            self._redis = None


# Singleton
_cache: CacheService | None = None


def get_cache_service() -> CacheService:
    """Get or create singleton cache service."""
    global _cache
    if _cache is None:
        _cache = CacheService()
    return _cache
