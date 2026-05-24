"""Web scraping utilities for URL content extraction.

Extracts text content from URLs, especially Facebook posts.
Uses Playwright headless browser for Facebook (renders JS like a real browser).
Uses httpx + BeautifulSoup for generic URLs.
"""

import re
import logging
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

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


def normalize_facebook_url(url: str) -> str:
    """Normalize Facebook URL to www.facebook.com for Playwright rendering."""
    parsed = urlparse(url)
    if "facebook.com" in parsed.netloc or "fb.com" in parsed.netloc:
        # Use www.facebook.com (full desktop version renders best in headless)
        new_url = url.replace("web.facebook.com", "www.facebook.com")
        new_url = new_url.replace("m.facebook.com", "www.facebook.com")
        new_url = new_url.replace("mbasic.facebook.com", "www.facebook.com")
        return new_url
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

        # Facebook-specific scraping with Playwright
        if "facebook.com" in parsed.netloc or "fb.com" in parsed.netloc:
            return await scrape_facebook(url, result)

        # Generic URL scraping
        return await scrape_generic(url, result)

    except Exception as e:
        logger.error(f"[Scraper] Failed to scrape {url}: {e}")
        result["text"] = f"[URL: {url}] Content could not be extracted."
        return result


async def scrape_facebook(url: str, result: dict) -> dict:
    """Scrape a Facebook post using Playwright headless browser.

    This launches a real Chromium browser in headless mode, navigates to the
    Facebook URL, waits for the page to render (including JS), then extracts
    the post content from the rendered DOM.

    Works for public posts without login.
    """
    fb_url = normalize_facebook_url(url)
    logger.info(f"[Scraper] Scraping Facebook with Playwright: {fb_url}")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--single-process",
                ]
            )

            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 900},
                locale="en-US",
            )

            page = await context.new_page()

            # Navigate to the Facebook URL
            await page.goto(fb_url, wait_until="domcontentloaded", timeout=30000)

            # Wait a bit for dynamic content to load
            await page.wait_for_timeout(3000)

            # Try to close any login popups/overlays that Facebook shows
            try:
                close_btn = page.locator('[aria-label="Close"]').first
                if await close_btn.is_visible(timeout=2000):
                    await close_btn.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

            # Strategy 1: Extract from meta tags (most reliable for public posts)
            title = await page.evaluate("""
                () => {
                    const og = document.querySelector('meta[property="og:title"]');
                    return og ? og.content : '';
                }
            """)

            description = await page.evaluate("""
                () => {
                    const og = document.querySelector('meta[property="og:description"]');
                    return og ? og.content : '';
                }
            """)

            # Strategy 2: Extract post text from rendered DOM
            post_text = await page.evaluate("""
                () => {
                    // Facebook post content selectors (public posts)
                    const selectors = [
                        '[data-ad-preview="message"]',
                        '[data-testid="post_message"]',
                        'div[dir="auto"][style*="text-align"]',
                        'div[dir="auto"]',
                    ];

                    let texts = [];

                    for (const selector of selectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const el of elements) {
                            const text = el.innerText.trim();
                            if (text.length > 30 && !text.includes('Log in') && !text.includes('Sign up')) {
                                texts.push(text);
                            }
                        }
                        if (texts.length > 0) break;
                    }

                    // Deduplicate (child elements may repeat parent text)
                    if (texts.length > 1) {
                        texts = texts.filter((t, i) => {
                            for (let j = 0; j < texts.length; j++) {
                                if (i !== j && texts[j].includes(t) && texts[j].length > t.length) {
                                    return false;
                                }
                            }
                            return true;
                        });
                    }

                    return texts.join('\\n\\n');
                }
            """)

            # Strategy 3: Get all visible text as fallback
            if not post_text and not description:
                post_text = await page.evaluate("""
                    () => {
                        const body = document.body.innerText;
                        const lines = body.split('\\n')
                            .map(l => l.trim())
                            .filter(l => l.length > 30)
                            .filter(l => !l.includes('Log in') && !l.includes('Sign up') && !l.includes('Create new account'));
                        return lines.slice(0, 20).join('\\n');
                    }
                """)

            # Extract author name
            author = await page.evaluate("""
                () => {
                    // Try h2 links (page/profile name on posts)
                    const h2Link = document.querySelector('h2 a, h3 a, [data-testid="story-subtitle"] a');
                    if (h2Link) return h2Link.innerText.trim();

                    // Try strong tags
                    const strong = document.querySelector('strong a');
                    if (strong) return strong.innerText.trim();

                    // Try og:title which often has "Author - post text"
                    const og = document.querySelector('meta[property="og:title"]');
                    if (og && og.content) {
                        const parts = og.content.split(' - ');
                        if (parts.length > 1) return parts[0].trim();
                    }

                    return '';
                }
            """)

            # Extract images
            images = await page.evaluate("""
                () => {
                    const imgs = document.querySelectorAll('img[src*="scontent"]');
                    return Array.from(imgs)
                        .map(img => img.src)
                        .filter(src => src.includes('scontent') && !src.includes('emoji'))
                        .slice(0, 5);
                }
            """)

            await browser.close()

            # Assemble result
            # Prefer post_text from DOM, fall back to og:description
            final_text = post_text if post_text and len(post_text) > 20 else description
            if not final_text:
                final_text = title

            if final_text:
                result["text"] = final_text.strip()[:5000]
                result["success"] = True
            else:
                result["text"] = f"[Facebook post] URL: {url}. Public content could not be fully extracted."

            result["title"] = title or ""
            result["author"] = author or ""
            result["images"] = images or []

            logger.info(f"[Scraper] Playwright Facebook: extracted {len(result['text'])} chars, author='{result['author']}'")
            return result

    except Exception as e:
        logger.error(f"[Scraper] Playwright Facebook failed: {e}")
        # Fallback to httpx method for meta tags
        return await scrape_facebook_fallback(url, result)


async def scrape_facebook_fallback(url: str, result: dict) -> dict:
    """Fallback Facebook scraper using httpx (for when Playwright fails)."""
    logger.info(f"[Scraper] Trying fallback httpx scraper for: {url}")

    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        try:
            response = await client.get(url, headers=HEADERS)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # Try og:description meta tag
                og_desc = soup.find("meta", property="og:description")
                if og_desc and og_desc.get("content"):
                    result["text"] = og_desc["content"]
                    result["success"] = True

                # Try og:title
                og_title = soup.find("meta", property="og:title")
                if og_title and og_title.get("content"):
                    result["title"] = og_title["content"]

                if result["text"]:
                    logger.info(f"[Scraper] Fallback got og:description: {len(result['text'])} chars")
                    return result

        except Exception as e:
            logger.warning(f"[Scraper] Fallback httpx also failed: {e}")

    result["text"] = f"[Facebook post] URL: {url}. Content extraction failed - post may be private or restricted."
    return result


async def scrape_generic(url: str, result: dict) -> dict:
    """Scrape a generic webpage using httpx + BeautifulSoup."""
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
