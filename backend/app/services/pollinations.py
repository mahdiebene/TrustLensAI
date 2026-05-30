"""Pollinations AI API client with retry logic and connection pooling."""

import asyncio
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)


class ContentFilterError(Exception):
    """Raised when the API rejects a prompt due to content policy (HTTP 400). Don't retry; fall back to a different model."""
    pass


MODEL_MAP = {
    "analysis": "perplexity-reasoning",
    "summary": "gemini-2.5-flash",
    "embeddings": "openai-3-large",
}

# Pollinations API base URL (OpenAI-compatible)
BASE_URL = "https://gen.pollinations.ai"


class PollinationsClient:
    """Async client for Pollinations AI API with retry and connection pooling."""

    def __init__(self):
        settings = get_settings()
        self._api_key = settings.POLLINATIONS_API_KEY
        self._max_retries = 2
        self._base_delay = 1.0
        # Large connection pool — no semaphore, let HTTP/2 handle concurrency
        self._http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(20.0, connect=5.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        timeout: float = 20.0,
        max_retries: int | None = None,
    ) -> str:
        """Call chat completions using Pollinations OpenAI-compatible endpoint."""
        retries = max_retries if max_retries is not None else self._max_retries
        for attempt in range(retries):
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
                    try:
                        content = data["choices"][0]["message"]["content"] or ""
                    except (KeyError, IndexError, TypeError) as parse_err:
                        logger.error(f"[Pollinations] Unexpected response structure for {model}: {str(data)[:200]}")
                        raise Exception(f"Unexpected response format: {parse_err}")
                    logger.info(f"[Pollinations] model={model} chars={len(content)} attempt={attempt + 1}")
                    return content
                elif response.status_code == 429:
                    delay = self._base_delay * (2 ** attempt)
                    logger.warning(f"[Pollinations] Rate limited for {model}, waiting {delay}s (attempt {attempt + 1})")
                    if attempt < retries - 1:
                        await asyncio.sleep(delay)
                        continue
                    else:
                        error_text = response.text[:200]
                        raise Exception(f"HTTP 429 after all retries: {error_text}")
                elif response.status_code == 400:
                    error_text = response.text[:300]
                    logger.error(f"[Pollinations] Bad request for {model}: {error_text}")
                    # Content filter or bad prompt — don't retry, fail fast so we can fall back
                    raise ContentFilterError(f"HTTP 400: {error_text}")
                else:
                    error_text = response.text[:200]
                    raise Exception(f"HTTP {response.status_code}: {error_text}")

            except httpx.TimeoutException as e:
                delay = self._base_delay * (2 ** attempt)
                logger.warning(f"[Pollinations] Timeout for {model}: {e} (attempt {attempt + 1})")
                if attempt < retries - 1:
                    await asyncio.sleep(delay)
                else:
                    raise Exception(f"Timeout after {retries} attempts for {model}")

            except ContentFilterError:
                # Content filter rejection — don't retry, propagate so caller can pick a different model
                logger.warning(f"[Pollinations] Content filter rejected prompt for {model}; not retrying")
                raise

            except Exception as e:
                if "429" in str(e) or "Rate" in str(e):
                    delay = self._base_delay * (2 ** attempt)
                else:
                    delay = self._base_delay
                logger.warning(f"[Pollinations] Retry {attempt + 1}/{retries} for {model}: {e}")
                if attempt < retries - 1:
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
                    timeout=20.0,
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
