"""Web scraping utilities — simplified.

With the new architecture, URL reading is handled by perplexity-reasoning
directly in the scoring engine. This module only provides URL detection
and basic metadata extraction for non-AI paths.
"""

import re
import logging
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Browser-like headers for generic scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
}


def is_url(text: str) -> bool:
    """Check if the text is a URL."""
    text = text.strip()
    return bool(re.match(r'https?://[^\s]+', text))


def is_social_media_url(url: str) -> bool:
    """Check if URL is from a social media platform."""
    parsed = urlparse(url)
    social_domains = [
        "facebook.com", "fb.com", "web.facebook.com",
        "twitter.com", "x.com",
        "instagram.com",
        "tiktok.com",
    ]
    return any(domain in parsed.netloc for domain in social_domains)


async def scrape_generic_url(url: str) -> dict:
    """
    Quick scrape for non-social-media URLs using httpx + BeautifulSoup.
    
    For social media URLs, the scoring engine passes the URL directly to
    perplexity-reasoning which has built-in web access.

    Returns:
        dict with keys: text, title, author, source_domain, success
    """
    result = {
        "text": "",
        "title": "",
        "author": "",
        "source_domain": "",
        "success": False,
        "original_url": url,
    }

    try:
        parsed = urlparse(url)
        result["source_domain"] = parsed.netloc

        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            response = await client.get(url, headers=HEADERS)

            if response.status_code != 200:
                logger.warning(f"[Scraper] HTTP {response.status_code} for {url}")
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title_tag = soup.find("title")
            if title_tag:
                result["title"] = title_tag.get_text(strip=True)

            # Extract author from meta tags
            author_meta = soup.find("meta", attrs={"name": "author"})
            if author_meta:
                result["author"] = author_meta.get("content", "")

            # Extract main content
            # Try article tag first, then main, then body
            content_tag = soup.find("article") or soup.find("main") or soup.find("body")
            if content_tag:
                # Remove script and style tags
                for tag in content_tag.find_all(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                text = content_tag.get_text(separator="\n", strip=True)
                # Clean up excessive whitespace
                text = re.sub(r'\n{3,}', '\n\n', text)
                result["text"] = text[:5000]  # Cap at 5000 chars

            result["success"] = bool(result["text"] and len(result["text"]) > 50)
            logger.info(f"[Scraper] Extracted {len(result['text'])} chars from {url}")

    except Exception as e:
        logger.error(f"[Scraper] Failed to scrape {url}: {e}")

    return result
