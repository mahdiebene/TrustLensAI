"""Web scraping utilities — Facebook-aware with Open Graph extraction.

For Facebook URLs, we extract Open Graph meta tags which public pages expose
with the actual post description/title. Share links are resolved to their
real permalink via redirect following. The extracted text is then passed to
the AI for fact-checking, rather than relying on the AI's browser which hits
Facebook's login wall.
"""

import re
import logging
from urllib.parse import urlparse, unquote

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Browser-like headers — must look like a real browser to get OG tags
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

# Mobile headers as fallback
MOBILE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 14; SM-S928B) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def is_url(text: str) -> bool:
    """Check if the text is a URL."""
    text = text.strip()
    return bool(re.match(r"https?://[^\s]+", text))


def is_facebook_url(url: str) -> bool:
    """Check if URL is from Facebook."""
    parsed = urlparse(url)
    fb_domains = ["facebook.com", "fb.com", "web.facebook.com", "m.facebook.com"]
    return any(domain in parsed.netloc for domain in fb_domains)


def is_social_media_url(url: str) -> bool:
    """Check if URL is from a social media platform."""
    parsed = urlparse(url)
    social_domains = [
        "facebook.com", "fb.com", "web.facebook.com", "m.facebook.com",
        "twitter.com", "x.com",
        "instagram.com",
        "tiktok.com",
    ]
    return any(domain in parsed.netloc for domain in social_domains)


def _extract_og_tags(soup: BeautifulSoup) -> dict:
    """Extract Open Graph and Twitter Card meta tags from BeautifulSoup."""
    tags = {}
    # Open Graph
    for tag in soup.find_all("meta", property=lambda x: x and x.startswith("og:")):
        tags[tag.get("property")] = tag.get("content", "")
    # Twitter cards (fallback)
    for tag in soup.find_all("meta", attrs={"name": lambda x: x and x.startswith("twitter:")}):
        tags[tag.get("name")] = tag.get("content", "")
    # Standard description/title as fallback
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag:
        tags["std:description"] = desc_tag.get("content", "")
    return tags


def _build_text_from_og(og_tags: dict, title: str) -> str:
    """Build extractable text from OG tags, deduplicating overlapping content."""
    seen = set()
    parts = []

    def _add_unique(text: str) -> None:
        text = text.strip()
        if not text or text == "Facebook":
            return
        # Check if this is a substring of something already added (or vice versa)
        for existing in list(seen):
            if text in existing or existing in text:
                # Keep the longer one
                if len(text) > len(existing):
                    seen.discard(existing)
                    seen.add(text)
                    # Replace in parts list
                    try:
                        idx = parts.index(existing)
                        parts[idx] = text
                    except ValueError:
                        parts.append(text)
                return
        seen.add(text)
        parts.append(text)

    # og:description is the actual post text for public page posts (best quality)
    if og_tags.get("og:description"):
        _add_unique(og_tags["og:description"])
    # og:title often has the page name + post snippet
    if og_tags.get("og:title"):
        _add_unique(og_tags["og:title"])
    # Twitter fallback
    if og_tags.get("twitter:description"):
        _add_unique(og_tags["twitter:description"])
    # Standard meta description
    if og_tags.get("std:description"):
        _add_unique(og_tags["std:description"])
    # Title tag as last resort
    if title and title != "Facebook":
        _add_unique(title)

    text = "\n\n".join(parts)
    # Clean up excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


async def _resolve_facebook_url(url: str) -> str:
    """Resolve Facebook share/short links to their real permalink.

    Facebook /share/p/XXX links redirect to the actual post URL.
    We follow redirects to get the canonical URL which has better OG tags.
    """
    try:
        async with httpx.AsyncClient(
            timeout=10.0, follow_redirects=True, max_redirects=5
        ) as client:
            r = await client.head(url, headers=HEADERS)
            if r.status_code in (301, 302, 303, 307, 308):
                # httpx followed redirects, get final URL
                final = str(r.url)
                if final != url:
                    logger.info(f"[Scraper] Resolved FB share link: {url[:60]}... -> {final[:80]}...")
                    return final
            # Also try GET to catch JS/meta redirects
            r2 = await client.get(url, headers=HEADERS)
            final = str(r2.url)
            if final != url:
                return final
    except Exception as e:
        logger.warning(f"[Scraper] Failed to resolve FB URL: {e}")
    return url


async def scrape_facebook_url(url: str) -> dict:
    """Scrape a Facebook URL by extracting Open Graph meta tags.

    Public Facebook page posts expose og:description with the actual post text.
    Share links are resolved to their real permalink first.

    Returns dict with keys: text, title, author, source_domain, success, image_url, original_url
    """
    result = {
        "text": "",
        "title": "",
        "author": "",
        "source_domain": "facebook.com",
        "success": False,
        "image_url": None,
        "original_url": url,
    }

    # Step 1: Resolve share links to real permalink
    resolved_url = await _resolve_facebook_url(url)
    result["original_url"] = resolved_url

    # Step 2: Try desktop headers first
    html_text = ""
    try:
        async with httpx.AsyncClient(
            timeout=12.0, follow_redirects=True
        ) as client:
            r = await client.get(resolved_url, headers=HEADERS)
            if r.status_code == 200:
                html_text = r.text
            else:
                logger.warning(f"[Scraper] FB desktop HTTP {r.status_code}")
    except Exception as e:
        logger.warning(f"[Scraper] FB desktop request failed: {e}")

    # Step 3: If desktop failed, try mobile headers
    if not html_text:
        try:
            mobile_url = resolved_url.replace("web.facebook.com", "m.facebook.com").replace("www.facebook.com", "m.facebook.com")
            async with httpx.AsyncClient(
                timeout=12.0, follow_redirects=True
            ) as client:
                r = await client.get(mobile_url, headers=MOBILE_HEADERS)
                if r.status_code == 200:
                    html_text = r.text
                else:
                    logger.warning(f"[Scraper] FB mobile HTTP {r.status_code}")
        except Exception as e:
            logger.warning(f"[Scraper] FB mobile request failed: {e}")

    if not html_text:
        logger.error(f"[Scraper] Could not fetch any HTML from {resolved_url[:80]}...")
        return result

    # Step 4: Parse OG tags
    soup = BeautifulSoup(html_text, "html.parser")
    og_tags = _extract_og_tags(soup)

    # Extract title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Build text from OG tags
    text = _build_text_from_og(og_tags, title)

    # Extract author from og:title or page name patterns
    author = ""
    if og_tags.get("og:title"):
        # For page posts, og:title is often "Page Name - Post snippet"
        author_part = og_tags["og:title"].split(" - ")[0].split(" | ")[0].strip()
        if author_part and author_part != "Facebook":
            author = author_part

    # Extract image
    image_url = og_tags.get("og:image") or og_tags.get("twitter:image")

    result["text"] = text[:8000]  # Cap at 8000 chars
    result["title"] = title
    result["author"] = author
    result["image_url"] = image_url
    result["success"] = bool(text and len(text) > 20)

    if result["success"]:
        logger.info(
            f"[Scraper] FB extracted {len(text)} chars, author='{author}', "
            f"image={bool(image_url)} from {resolved_url[:60]}..."
        )
    else:
        logger.warning(
            f"[Scraper] FB minimal extraction from {resolved_url[:60]}... "
            f"OG tags: {list(og_tags.keys())}"
        )

    return result


async def scrape_generic_url(url: str) -> dict:
    """Quick scrape for non-Facebook URLs using httpx + BeautifulSoup.

    For Facebook URLs, delegates to scrape_facebook_url().

    Returns:
        dict with keys: text, title, author, source_domain, success, image_url, original_url
    """
    result = {
        "text": "",
        "title": "",
        "author": "",
        "source_domain": "",
        "success": False,
        "image_url": None,
        "original_url": url,
    }

    # Facebook URLs get special handling
    if is_facebook_url(url):
        return await scrape_facebook_url(url)

    try:
        parsed = urlparse(url)
        result["source_domain"] = parsed.netloc

        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(url, headers=HEADERS)

            if response.status_code != 200:
                logger.warning(f"[Scraper] HTTP {response.status_code} for {url}")
                return result

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract OG tags first (best quality)
            og_tags = _extract_og_tags(soup)

            # Title
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Try OG-based text first
            text = _build_text_from_og(og_tags, title)

            # If OG gave us nothing substantial, fall back to body scraping
            if len(text) < 100:
                content_tag = soup.find("article") or soup.find("main") or soup.find("body")
                if content_tag:
                    for tag in content_tag.find_all(["script", "style", "nav", "footer", "header"]):
                        tag.decompose()
                    body_text = content_tag.get_text(separator="\n", strip=True)
                    body_text = re.sub(r"\n{3,}", "\n\n", body_text)
                    if len(body_text) > len(text):
                        text = body_text

            result["text"] = text[:8000]
            result["title"] = title
            result["image_url"] = og_tags.get("og:image") or og_tags.get("twitter:image")

            author_meta = soup.find("meta", attrs={"name": "author"})
            if author_meta:
                result["author"] = author_meta.get("content", "")

            result["success"] = bool(result["text"] and len(result["text"]) > 50)
            logger.info(f"[Scraper] Extracted {len(result['text'])} chars from {url}")

    except Exception as e:
        logger.error(f"[Scraper] Failed to scrape {url}: {e}")

    return result


async def scrape_url(url: str) -> dict:
    """Unified URL scraper — handles Facebook specially, generic for others.

    Returns dict with keys: text, title, author, source_domain, success, image_url, original_url
    """
    if is_facebook_url(url):
        return await scrape_facebook_url(url)
    return await scrape_generic_url(url)
