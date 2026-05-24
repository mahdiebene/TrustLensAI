"""Pollinations AI API client with retry logic."""

import asyncio
import logging
import httpx
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

# Pollinations API base URL (OpenAI-compatible)
# Docs: https://gen.pollinations.ai/docs
# Endpoints: POST /v1/chat/completions, POST /v1/embeddings
BASE_URL = "https://gen.pollinations.ai"


class PollinationsClient:
    """Async client for Pollinations AI API with retry and caching."""

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.POLLINATIONS_API_KEY
        self._max_retries = 3
        self._base_delay = 2.0
        # Shared client with connection pooling — limit concurrency
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(90.0, connect=10.0),
            limits=httpx.Limits(max_connections=3, max_keepalive_connections=2),
        )

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        timeout: float = 60.0,
    ) -> str:
        """Call chat completions using Pollinations OpenAI-compatible endpoint."""
        for attempt in range(self._max_retries):
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                }

                headers = {
                    "Content-Type": "application/json",
                }
                if self._api_key:
                    headers["Authorization"] = f"Bearer {self._api_key}"

                response = await self._http_client.post(
                    f"{BASE_URL}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"] or ""
                    logger.info(f"[Pollinations] model={model} chars={len(content)} attempt={attempt + 1}")
                    return content
                elif response.status_code == 429:
                    # Rate limited — wait longer
                    delay = self._base_delay * (2 ** attempt) + 1.0
                    logger.warning(f"[Pollinations] Rate limited for {model}, waiting {delay}s (attempt {attempt + 1})")
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(delay)
                        continue
                    else:
                        error_text = response.text[:200]
                        raise Exception(f"HTTP 429 after all retries: {error_text}")
                elif response.status_code == 400:
                    # Safety filter or bad request — don't retry
                    error_text = response.text[:300]
                    logger.error(f"[Pollinations] Bad request for {model}: {error_text}")
                    raise Exception(f"HTTP 400: {error_text}")
                else:
                    error_text = response.text[:200]
                    raise Exception(f"HTTP {response.status_code}: {error_text}")

            except httpx.TimeoutException as e:
                delay = self._base_delay * (2 ** attempt)
                logger.warning(f"[Pollinations] Timeout for {model}: {e} (attempt {attempt + 1})")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    raise Exception(f"Timeout after {self._max_retries} attempts for {model}")

            except Exception as e:
                if "429" in str(e) or "Rate" in str(e):
                    delay = self._base_delay * (2 ** attempt) + 1.0
                else:
                    delay = self._base_delay * (2 ** attempt)
                logger.warning(f"[Pollinations] Retry {attempt + 1}/{self._max_retries} for {model}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"[Pollinations] All retries failed for {model}: {e}")
                    raise

        return ""

    async def embed(self, text: str, model: str = "openai-3-large") -> list[float]:
        """Get embedding vector for text using OpenAI-compatible endpoint."""
        for attempt in range(self._max_retries):
            try:
                headers = {
                    "Content-Type": "application/json",
                }
                if self._api_key:
                    headers["Authorization"] = f"Bearer {self._api_key}"

                payload = {
                    "model": model,
                    "input": text,
                }

                response = await self._http_client.post(
                    f"{BASE_URL}/v1/embeddings",
                    json=payload,
                    headers=headers,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["data"][0]["embedding"]
                else:
                    error_text = response.text[:200]
                    raise Exception(f"HTTP {response.status_code}: {error_text}")

            except Exception as e:
                delay = self._base_delay * (2 ** attempt)
                logger.warning(f"[Pollinations] Embed retry {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(delay)
                else:
                    raise

        return []

    async def close(self):
        """Close the HTTP client."""
        await self._http_client.aclose()


# Singleton instance
_client: PollinationsClient | None = None


def get_pollinations_client() -> PollinationsClient:
    """Get or create singleton Pollinations client."""
    global _client
    if _client is None:
        _client = PollinationsClient()
    return _client
