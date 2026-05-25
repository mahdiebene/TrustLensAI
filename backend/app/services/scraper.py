"""Web scraping utilities for URL content extraction.

Uses perplexity-reasoning model (with built-in web search/URL reading) for Facebook
and social media URLs. Uses httpx + BeautifulSoup for generic URLs as fallback.
"""

import re
import logging
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.pollinations import get_pollinations_client

logger = logging.getLogger(__name__)

# Browser-like headers for generic scraping
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
}

SCRAPER_PROMPT = """Read the following URL and extract ALL available information. This is critical — be thorough and accurate.

Extract:
1. The FULL post text/content (every word, do not summarize)
2. Author name / Page name (who posted it)
3. Source/platform name
4. Date posted (if visible)
5. Any image descriptions (what images show)
6. Number of reactions/shares/comments (if visible)

CRITICAL RULES:
- Do NOT hallucinate or make up ANY information
- If you cannot access the URL or read its content, say "CANNOT_ACCESS"
- Only report what is ACTUALLY present at the URL
- Do NOT invent author names, dates, or content
- If the post is in Bengali, reproduce the Bengali text exactly as-is

URL: {url}

Return in this exact format:
AUTHOR: <author name or "Unknown">
SOURCE: <source platform/domain>
DATE: <date or "Unknown">
CONTENT: <full post text, preserve original language>
IMAGES: <description of any images or "None">
ENGAGEMENT: <reactions/shares/comments or "Unknown">"""


def is_url(text: str) -> bool:
    """Check if the text is a URL."""
    text = text.strip()
    return bool(re.match(r'https?://[^\s]+', text))


def is_social_media_url(url: str) -> bool:
    """Check if URL is from a social media platform that needs AI scraping."""
    parsed = urlparse(url)
    social_domains = [
        "facebook.com", "fb.com", "web.facebook.com",
        "twitter.com", "x.com",
        "instagram.com",
        "tiktok.com",
    ]
    return any(domain in parsed.netloc for domain in social_domains)


async def scrape_url(url: str) -> dict:
    """
    Scrape content from a URL.

    For social media (Facebook, etc.): Uses perplexity-reasoning model with
    built-in web search to read the URL content directly.
    For generic URLs: Uses httpx + BeautifulSoup.

    Returns:
        dict with keys: text, title, author, source_domain, images, success
    """
    result = {
        "text": "",
        "title": "",
        "author": "",
        "source_domain": "",
        "images": [],
        "success": False,
        "original_url": url,
    }

    try:
        parsed = urlparse(url)
        result["source_domain"] = parsed.netloc

        # Social media URLs — use perplexity-reasoning (has web access)
        if is_social_media_url(url):
            return await scrape_with_perplexity(url, result)

        # Generic URL — try httpx first, fall back to perplexity
        generic_result = await scrape_generic(url, result)
        if generic_result["success"] and len(generic_result["text"]) > 50:
            return generic_result

        # If generic scraping got very little content, try perplexity
        return await scrape_with_perplexity(url, result)

    except Exception as e:
        logger.error(f"[Scraper] Failed to scrape {url}: {e}")
        result["text"] = f"[URL: {url}] Content could not be extracted."
        return result


async def scrape_with_perplexity(url: str, result: dict) -> dict:
    """Scrape a URL using perplexity-reasoning model (has built-in web search/URL reading).

    This is far more reliable than Playwright for social media sites like Facebook
    which block headless browsers.
    """
    logger.info(f"[Scraper] Using perplexity-reasoning to read: {url}")

    try:
        client = get_pollinations_client()
        response = await client.chat(
            model="perplexity-reasoning",
            messages=[{
                "role": "user",
                "content": SCRAPER_PROMPT.format(url=url),
            }],
            temperature=0.1,
            timeout=15.0,
        )

        if not response or "CANNOT_ACCESS" in response:
            logger.warning(f"[Scraper] Perplexity could not access: {url}")
            result["text"] = f"[URL: {url}] Content could not be extracted from social media post."
            return result

        # Parse the structured response
        parsed = _parse_perplexity_response(response)

        result["text"] = parsed["content"]
        result["author"] = parsed["author"]
        result["title"] = parsed.get("source", "")
        result["success"] = bool(parsed["content"] and len(parsed["content"]) > 20)

        if parsed.get("images") and parsed["images"] != "None":
            result["images"] = [parsed["images"]]

        logger.info(f"[Scraper] Perplexity extracted {len(result['text'])} chars, author='{result['author']}'")
        return result

    except Exception as e:
        logger.error(f"[Scraper] Perplexity scraping failed: {e}")
        result["text"] = f"[URL: {url}] Content extraction failed — {str(e)[:100]}"
        return result


def _parse_perplexity_response(response: str) -> dict:
    """Parse the structured response from perplexity-reasoning."""
    parsed = {
        "author": "Unknown",
        "source": "",
        "date": "Unknown",
        "content": "",
        "images": "None",
        "engagement": "Unknown",
    }

    lines = response.strip().split("\n")
    current_key = None
    content_lines = []

    for line in lines:
        line_upper = line.strip().upper()

        if line_upper.startswith("AUTHOR:"):
            parsed["author"] = line.split(":", 1)[1].strip()
            current_key = "author"
        elif line_upper.startswith("SOURCE:"):
            parsed["source"] = line.split(":", 1)[1].strip()
            current_key = "source"
        elif line_upper.startswith("DATE:"):
            parsed["date"] = line.split(":", 1)[1].strip()
            current_key = "date"
        elif line_upper.startswith("CONTENT:"):
            content_start = line.split(":", 1)[1].strip()
            if content_start:
                content_lines.append(content_start)
            current_key = "content"
        elif line_upper.startswith("IMAGES:"):
            parsed["images"] = line.split(":", 1)[1].strip()
            current_key = "images"
        elif line_upper.startswith("ENGAGEMENT:"):
            parsed["engagement"] = line.split(":", 1)[1].strip()
            current_key = "engagement"
        elif current_key == "content":
            content_lines.append(line)

    parsed["content"] = "\n".join(content_lines).strip()

    # If parsing failed, use the whole response as content
    if not parsed["content"] and len(response) > 50:
        parsed["content"] = response.strip()[:5000]

    return parsed


async def scrape_generic(url: str, result: dict) -> dict:
    """Scrape a generic webpage using httpx + BeautifulSoup."""
    logger.info(f"[Scraper] Scraping generic URL: {url}")

    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        try:
            response = await client.get(url, headers=HEADERS)
            if response.status_code != 200:
                result["text"] = f"[URL returned HTTP {response.status_code}]: {url}"
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            # Get title
            title_tag = soup.find("title")
            if title_tag:
                result["title"] = title_tag.get_text(strip=True)

            # Try og:description first
            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                result["text"] = og_desc["content"]

            # Get article content
            article = soup.find("article") or soup.find("main") or soup.find("div", class_=re.compile(r"content|article|post|story"))
            if article:
                text = article.get_text(separator="\n", strip=True)
                if len(text) > len(result["text"]):
                    result["text"] = text[:5000]  # Limit to 5000 chars

            # Fallback: get body text
            if not result["text"]:
                body_text = soup.get_text(separator="\n", strip=True)
                lines = [l for l in body_text.split("\n") if len(l) > 30]
                result["text"] = "\n".join(lines[:20])

            # Get author
            author_meta = soup.find("meta", attrs={"name": "author"})
            if author_meta:
                result["author"] = author_meta.get("content", "")

            result["success"] = bool(result["text"])
            logger.info(f"[Scraper] Generic: extracted {len(result['text'])} chars")

        except Exception as e:
            logger.error(f"[Scraper] Generic scrape failed: {e}")
            result["text"] = f"[URL: {url}] Content extraction failed."

    return result
