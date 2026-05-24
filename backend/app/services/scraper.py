"""Web scraping utilities for URL content extraction.

Extracts text content from URLs, especially Facebook posts.
Uses mbasic.facebook.com for simpler HTML parsing.
"""

import re
import logging
from urllib.parse import urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Browser-like headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
}


def is_url(text: str) -> bool:
    """Check if the text is a URL."""
    text = text.strip()
    return bool(re.match(r'https?://[^\s]+', text))


def normalize_facebook_url(url: str) -> str:
    """Convert any Facebook URL to mbasic.facebook.com for easier scraping."""
    parsed = urlparse(url)
    # Replace any facebook domain with mbasic
    if "facebook.com" in parsed.netloc:
        new_netloc = "mbasic.facebook.com"
        return urlunparse(parsed._replace(netloc=new_netloc, scheme="https"))
    return url


async def scrape_url(url: str) -> dict:
    """
    Scrape content from a URL.

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

        # Facebook-specific scraping
        if "facebook.com" in parsed.netloc or "fb.com" in parsed.netloc:
            return await scrape_facebook(url, result)

        # Generic URL scraping
        return await scrape_generic(url, result)

    except Exception as e:
        logger.error(f"[Scraper] Failed to scrape {url}: {e}")
        result["text"] = f"[URL: {url}] Content could not be extracted."
        return result


async def scrape_facebook(url: str, result: dict) -> dict:
    """Scrape a Facebook post using mbasic.facebook.com."""
    mbasic_url = normalize_facebook_url(url)
    logger.info(f"[Scraper] Scraping Facebook: {mbasic_url}")

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        # Try mbasic first (simplest HTML)
        try:
            response = await client.get(mbasic_url, headers=HEADERS)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Extract post text from mbasic
                # mbasic uses simple div structure
                post_text = ""

                # Method 1: Look for the main post content div
                story_div = soup.find("div", {"class": "story_body_container"})
                if story_div:
                    # Get text paragraphs
                    for p in story_div.find_all(["p", "div"], recursive=False):
                        text = p.get_text(strip=True)
                        if text and len(text) > 5:
                            post_text += text + "\n"

                # Method 2: Look for data-ft divs (post content)
                if not post_text:
                    for div in soup.find_all("div", attrs={"data-ft": True}):
                        text = div.get_text(strip=True)
                        if text and len(text) > 20:
                            post_text += text + "\n"
                            break

                # Method 3: Look for any substantial text block
                if not post_text:
                    # Find the largest text block on the page
                    all_text_blocks = []
                    for tag in soup.find_all(["p", "div", "span"]):
                        text = tag.get_text(strip=True)
                        if len(text) > 50 and "log in" not in text.lower() and "sign up" not in text.lower():
                            all_text_blocks.append(text)

                    if all_text_blocks:
                        # Get the longest text block
                        post_text = max(all_text_blocks, key=len)

                # Extract author
                author_tag = soup.find("strong") or soup.find("h3")
                if author_tag:
                    result["author"] = author_tag.get_text(strip=True)

                # Extract title
                title_tag = soup.find("title")
                if title_tag:
                    result["title"] = title_tag.get_text(strip=True)

                if post_text:
                    result["text"] = post_text.strip()
                    result["success"] = True
                    logger.info(f"[Scraper] Facebook mbasic: extracted {len(post_text)} chars")
                    return result

        except Exception as e:
            logger.warning(f"[Scraper] mbasic failed: {e}")

        # Fallback: try the regular mobile version
        try:
            mobile_url = url.replace("web.facebook.com", "m.facebook.com").replace("www.facebook.com", "m.facebook.com")
            response = await client.get(mobile_url, headers=HEADERS)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Look for og:description meta tag (often has post text)
                og_desc = soup.find("meta", property="og:description")
                if og_desc and og_desc.get("content"):
                    result["text"] = og_desc["content"]
                    result["success"] = True
                    logger.info(f"[Scraper] Facebook mobile og:description: {len(result['text'])} chars")
                    return result

                # Look for og:title
                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    result["title"] = og_title["content"]

                # Try to get any visible text
                body_text = soup.get_text(separator="\n", strip=True)
                # Filter out navigation/login text
                lines = [l for l in body_text.split("\n") if len(l) > 30 and "log in" not in l.lower() and "sign up" not in l.lower() and "facebook" not in l.lower()]
                if lines:
                    result["text"] = "\n".join(lines[:10])
                    result["success"] = True
                    return result

        except Exception as e:
            logger.warning(f"[Scraper] Mobile FB failed: {e}")

    # If all methods fail
    result["text"] = f"[Facebook post from {result.get('author', 'unknown')}] URL: {url}. Content extraction partially failed."
    return result


async def scrape_generic(url: str, result: dict) -> dict:
    """Scrape a generic webpage."""
    logger.info(f"[Scraper] Scraping generic URL: {url}")

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
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
