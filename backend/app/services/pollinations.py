"""Pollinations AI API client with retry logic."""

import asyncio
import logging
from openai import AsyncOpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)

MODEL_MAP = {
    "source_reputation": "gemini",
    "content_consistency": "perplexity-reasoning",
    "language_analysis": "claude",
    "bengali_context": "qwen-large",
    "image_authenticity": "qwen-vision-pro",
    "author_network": "gemini",
    "synthesis": "gpt-5.5",
    "embeddings": "openai-3-large",
}


class PollinationsClient:
    """Async client for Pollinations AI API with retry and caching."""

    def __init__(self):
        settings = get_settings()
        self._client = AsyncOpenAI(
            base_url=settings.POLLINATIONS_BASE_URL,
            api_key=settings.POLLINATIONS_API_KEY,
        )
        self._max_retries = 3
        self._base_delay = 1.0

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        timeout: float = 30.0,
    ) -> str:
        """Call chat completions with retry logic."""
        for attempt in range(self._max_retries):
            try:
                response = await self._client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    timeout=timeout,
                )
                content = response.choices[0].message.content or ""
                logger.info(f"[Pollinations] model={model} chars={len(content)} attempt={attempt + 1}")
                return content
            except Exception as e:
                delay = self._base_delay * (2 ** attempt)
                logger.warning(f"[Pollinations] Retry {attempt + 1}/{self._max_retries} for {model}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"[Pollinations] All retries failed for {model}: {e}")
                    raise

        return ""

    async def embed(self, text: str, model: str = "openai-3-large") -> list[float]:
        """Get embedding vector for text."""
        for attempt in range(self._max_retries):
            try:
                response = await self._client.embeddings.create(
                    model=model,
                    input=text,
                )
                return response.data[0].embedding
            except Exception as e:
                delay = self._base_delay * (2 ** attempt)
                logger.warning(f"[Pollinations] Embed retry {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    raise

        return []


# Singleton instance
_client: PollinationsClient | None = None


def get_pollinations_client() -> PollinationsClient:
    """Get or create singleton Pollinations client."""
    global _client
    if _client is None:
        _client = PollinationsClient()
    return _client
