"""Web scraping utilities — Facebook-aware with Jina Reader + OG fallback.

For Facebook URLs we use a multi-stage strategy:
  1. Jina Reader (https://r.jina.ai/<url>) — primary path. Returns clean
     LLM-ready markdown with full post text, author, image alt-text,
     reactions, comments. Works from datacenter IPs (where Facebook serves
     a 400 error page to direct requests).
  2. Open Graph meta tags via direct fetch — fallback if Jina is unreachable.
     Works for residential IPs but NOT VPS/datacenter IPs.

Share links (/share/p/...) are resolved to their canonical permalink first.
The extracted text is then passed to the AI for fact-checking, rather than
relying on the AI's browser which hits Facebook's login wall.
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


async def _scrape_via_jina(url: str) -> dict:
    """Scrape a URL via Jina Reader (https://r.jina.ai/).

    Jina Reader is a free LLM-friendly web scraper that returns clean
    markdown. It works from datacenter IPs where direct Facebook fetches
    are blocked (returns 400 error page).

    Returns dict with: text, title, author, image_url, success
    """
    out = {"text": "", "title": "", "author": "", "image_url": None, "success": False}
    jina_url = f"https://r.jina.ai/{url}"
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            # Plain text/markdown response
            jina_headers = {
                "User-Agent": "TrustLens/1.0",
                "Accept": "text/plain, text/markdown, */*",
                # Optional: 'X-Return-Format: markdown' is default; we keep it implicit
            }
            r = await client.get(jina_url, headers=jina_headers)
            if r.status_code != 200 or not r.text:
                logger.warning(f"[Scraper] Jina HTTP {r.status_code} for {url[:60]}...")
                return out
            md = r.text

        # Parse the Jina markdown header block (Title:, URL Source:, Markdown Content:)
        title_m = re.search(r"^Title:\s*(.+)$", md, re.MULTILINE)
        if title_m:
            out["title"] = title_m.group(1).strip()

        # Find the body after "Markdown Content:"
        body_split = re.split(r"^Markdown Content:\s*$", md, maxsplit=1, flags=re.MULTILINE)
        body = body_split[1] if len(body_split) > 1 else md

        # Strip Jina's leading H1 (often "PageName - post snippet | Facebook")
        body = re.sub(r"^\s*#\s+.*$", "", body, count=1, flags=re.MULTILINE)

        # Extract author from "## <Name>'s Post" pattern (Facebook-specific)
        author_m = re.search(r"##\s+([^\n]+?)'s Post", body)
        if author_m:
            out["author"] = author_m.group(1).strip()
        else:
            # Fallback: bold name link near top
            bold_m = re.search(r"###\s*\[\*\*([^*\]]+)\*\*\]", body)
            if bold_m:
                out["author"] = bold_m.group(1).strip()

        # Find first image URL (the post's main image)
        img_m = re.search(r"!\[[^\]]*\]\((https?://[^)\s]+)\)", body)
        if img_m:
            out["image_url"] = img_m.group(1)

        # Clean the text:
        # 1. Remove markdown image syntax but KEEP alt text (often contains OCR'd image text)
        cleaned = re.sub(
            r"!\[([^\]]*)\]\([^)]+\)",
            lambda m: f"[Image: {m.group(1)}]" if m.group(1).strip() else "",
            body,
        )
        # 2. Convert links [text](url) to just text
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
        # 3. Drop common Facebook chrome/boilerplate lines
        boilerplate_patterns = [
            r"^Log In\s*$",
            r"^Forgot Account\?\s*$",
            r"^All reactions:\s*$",
            r"^Most relevant\s*$",
            r"^Like\s*$",
            r"^Comment\s*$",
            r"^Share\s*$",
            r"^See more\s*$",
            r"^View \d+ repl(y|ies)\s*$",
            r"^View all \d+ replies\s*$",
            r"^\*\s*\*\s*\*$",  # markdown rule
        ]
        for pat in boilerplate_patterns:
            cleaned = re.sub(pat, "", cleaned, flags=re.MULTILINE | re.IGNORECASE)
        # 4. Collapse whitespace
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        # 5. Detect Facebook "post unavailable / restricted" error pages.
        #    Jina returns these as legitimate-looking content but they're not the post.
        #    Signals: very short body, or body matches FB error patterns.
        unavailable_signals = [
            r"this content isn'?t available",
            r"this content is no longer available",
            r"the link you followed may be broken",
            r"page may have been removed",
            r"page isn'?t available",
            r"you must log in to continue",
            r"log in or sign up to view",
            r"to see more from .* on facebook, log in",
            r"privacy settings",
            r"audience for this post",
            r"this post is no longer available",
        ]
        body_lower = cleaned.lower()
        matched_signal = next(
            (pat for pat in unavailable_signals if re.search(pat, body_lower)),
            None,
        )

        # Heuristic: if cleaned text is very short (< 200 chars) AND matches an
        # unavailable signal → it's a FB error page, not real content.
        # Also: if the cleaned text is dominated by error language (signal
        # within first 300 chars) and short overall → fail.
        is_error_page = bool(matched_signal) and len(cleaned) < 1500

        # 6. Detect Meta login-wall / interface page. When Facebook redirects a
        #    share link (e.g. /share/p/XXX) to the login screen, Jina extracts
        #    the *interface chrome*: a long footer listing Meta products, language
        #    options, legal links — none of which is the actual post. The text
        #    can be 2000+ chars so the length check above won't catch it.
        #
        #    Fingerprint: high density of Meta product names + UI labels + ~zero
        #    narrative content. We count distinct "interface tokens"; if many
        #    appear in the body, it's the login wall, not a real post.
        interface_tokens = [
            "messenger", "facebook lite", "meta pay", "meta quest",
            "ray-ban meta", "instagram", "threads", "meta verified",
            "create page", "create ad", "create group",
            "log in", "sign up", "create new account",
            "forgot password", "forgotten password",
            "facebook © meta", "© meta",
            "english (us)", "english (uk)",
            "privacy policy", "cookies policy", "terms of service",
            "ad choices", "ad preferences",
        ]
        token_hits = sum(1 for tok in interface_tokens if tok in body_lower)
        # Bengali login-wall variant
        bn_login_tokens = [
            "লগ ইন", "লগইন", "নতুন একাউন্ট", "নতুন অ্যাকাউন্ট",
            "পাসওয়ার্ড ভুলে", "মেসেঞ্জার", "ইনস্টাগ্রাম",
        ]
        bn_token_hits = sum(1 for tok in bn_login_tokens if tok in cleaned)
        # If 5+ distinct Meta interface tokens appear (or 3+ Bengali login
        # tokens) and the body has no real sentence-like narrative content
        # (very few periods/Bengali full-stops relative to length), it's the
        # login wall.
        sentence_breaks = cleaned.count(". ") + cleaned.count("। ") + cleaned.count(".\n") + cleaned.count("।\n")
        chars_per_sentence = len(cleaned) / max(sentence_breaks, 1)
        is_login_wall = (
            (token_hits >= 5 or bn_token_hits >= 3)
            and chars_per_sentence > 200  # mostly link/list lines, no prose
        )

        if is_login_wall:
            is_error_page = True
            matched_signal = f"login-wall (tokens={token_hits}, bn={bn_token_hits})"
            out["failure_reason"] = (
                "Facebook redirected this share link to its login page, so the "
                "actual post content is not accessible. Paste the post text or "
                "upload a screenshot to get a real trust score."
            )
            out["failure_reason_bn"] = (
                "ফেসবুক এই শেয়ার লিংকটিকে লগইন পেজে রিডাইরেক্ট করেছে, তাই পোস্টের "
                "আসল কনটেন্ট পাওয়া যায়নি। সঠিক ট্রাস্ট স্কোর পেতে পোস্টের লেখা "
                "পেস্ট করুন অথবা স্ক্রিনশট আপলোড করুন।"
            )

        if is_error_page:
            out["success"] = False
            out["text"] = ""  # don't pass error page to AI
            if not out.get("failure_reason"):
                out["failure_reason"] = (
                    "Facebook returned a 'content unavailable' page — this post is "
                    "private, deleted, or restricted to logged-in users."
                )
            if not out.get("failure_reason_bn"):
                out["failure_reason_bn"] = (
                    "ফেসবুক 'কনটেন্ট উপলব্ধ নয়' পেজ ফেরত দিয়েছে — এই পোস্ট প্রাইভেট, "
                    "ডিলিট হয়েছে, অথবা লগইন ছাড়া দেখা যায় না।"
                )
            logger.warning(
                f"[Scraper] Jina returned FB error page for {url[:60]}... "
                f"(matched: {matched_signal}, len={len(cleaned)})"
            )
        else:
            out["text"] = cleaned[:3500]
            out["success"] = bool(cleaned and len(cleaned) > 20)
            if out["success"]:
                logger.info(
                    f"[Scraper] Jina extracted {len(cleaned)} chars, "
                    f"author='{out['author']}', title='{out['title'][:50]}'"
                )
    except Exception as e:
        logger.warning(f"[Scraper] Jina request failed for {url[:60]}...: {e}")

    return out


async def scrape_facebook_url(url: str) -> dict:
    """Scrape a Facebook URL.

    Strategy:
      1. Try Jina Reader first (works from VPS/datacenter IPs).
      2. Fall back to direct OG-tag scrape (only works from residential IPs).

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
        "failure_reason": "",
        "failure_reason_bn": "",
    }

    # Step 1: Resolve share links to real permalink (cheap HEAD request)
    resolved_url = await _resolve_facebook_url(url)
    result["original_url"] = resolved_url

    # Step 2: PRIMARY — Jina Reader
    jina_result = await _scrape_via_jina(resolved_url)
    if jina_result["success"]:
        result["text"] = jina_result["text"]
        result["title"] = jina_result["title"]
        result["author"] = jina_result["author"]
        result["image_url"] = jina_result["image_url"]
        result["success"] = True
        return result

    # Step 3: FALLBACK — direct fetch + OG tags (works on residential IPs)
    html_text = ""
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            r = await client.get(resolved_url, headers=HEADERS)
            if r.status_code == 200 and len(r.text) > 2000:
                html_text = r.text
            else:
                logger.warning(
                    f"[Scraper] FB desktop HTTP {r.status_code} len={len(r.text)}"
                )
    except Exception as e:
        logger.warning(f"[Scraper] FB desktop request failed: {e}")

    if not html_text:
        try:
            mobile_url = resolved_url.replace("web.facebook.com", "m.facebook.com").replace(
                "www.facebook.com", "m.facebook.com"
            )
            async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
                r = await client.get(mobile_url, headers=MOBILE_HEADERS)
                if r.status_code == 200 and len(r.text) > 2000:
                    html_text = r.text
                else:
                    logger.warning(f"[Scraper] FB mobile HTTP {r.status_code}")
        except Exception as e:
            logger.warning(f"[Scraper] FB mobile request failed: {e}")

    if not html_text:
        logger.error(f"[Scraper] All FB strategies failed for {resolved_url[:80]}...")
        # Best-effort failure classification based on URL shape
        lower = resolved_url.lower()
        if "/groups/" in lower:
            result["failure_reason"] = (
                "This looks like a private Facebook group post. Group posts are not publicly accessible without login."
            )
            result["failure_reason_bn"] = (
                "এটি একটি প্রাইভেট ফেসবুক গ্রুপ পোস্ট। লগইন ছাড়া গ্রুপ পোস্ট অ্যাক্সেস করা যায় না।"
            )
        elif "login" in lower or "checkpoint" in lower:
            result["failure_reason"] = "Facebook requires login to view this post."
            result["failure_reason_bn"] = "এই পোস্ট দেখতে ফেসবুক লগইন চাইছে।"
        else:
            result["failure_reason"] = (
                "Could not retrieve this Facebook post — it may be private, deleted, or restricted to logged-in users."
            )
            result["failure_reason_bn"] = (
                "এই ফেসবুক পোস্টটি আনতে পারিনি — সম্ভবত এটি প্রাইভেট, ডিলিট করা হয়েছে, অথবা লগইন ছাড়া দেখা যায় না।"
            )
        return result

    soup = BeautifulSoup(html_text, "html.parser")
    og_tags = _extract_og_tags(soup)

    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    text = _build_text_from_og(og_tags, title)

    author = ""
    if og_tags.get("og:title"):
        author_part = og_tags["og:title"].split(" - ")[0].split(" | ")[0].strip()
        if author_part and author_part != "Facebook":
            author = author_part

    image_url = og_tags.get("og:image") or og_tags.get("twitter:image")

    result["text"] = text[:8000]
    result["title"] = title
    result["author"] = author
    result["image_url"] = image_url
    result["success"] = bool(text and len(text) > 20)

    if result["success"]:
        logger.info(
            f"[Scraper] FB OG-fallback extracted {len(text)} chars, author='{author}'"
        )
    else:
        logger.warning(
            f"[Scraper] FB minimal extraction from {resolved_url[:60]}... "
            f"OG tags: {list(og_tags.keys())}"
        )
        result["failure_reason"] = (
            "Could not extract this Facebook post — the page returned no usable content "
            "(it may be private, deleted, or restricted to logged-in users)."
        )
        result["failure_reason_bn"] = (
            "এই ফেসবুক পোস্টের কনটেন্ট পাওয়া যায়নি — সম্ভবত এটি প্রাইভেট, ডিলিট হয়েছে, "
            "বা লগইন ছাড়া দেখা যায় না।"
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
