"""Test script to find what Facebook data is accessible server-side."""
import asyncio
import json
import httpx

# Test URLs from the project
TEST_URLS = [
    "https://web.facebook.com/share/p/1EfTBoVsrL/",
    "https://web.facebook.com/factbuddy.pg/posts/pfbid02KASxVQonABiQM9MUpe8JxhnSs1mK8PJFd8fXStZK2RBWYhT6DzBTmfYN6RUebWxQl",
    "https://www.facebook.com/share/p/1EfTBoVsrL/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
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

MOBILE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def test_oembed(url: str):
    """Test Facebook oEmbed API."""
    oembed_url = f"https://www.facebook.com/plugins/post/oembed.json/?url={url}"
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r = await client.get(oembed_url, headers=HEADERS)
            print(f"\n=== oEmbed for {url[:60]}... ===")
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                print(f"Title: {data.get('title', 'N/A')[:200]}")
                print(f"Author: {data.get('author_name', 'N/A')}")
                print(f"HTML snippet: {data.get('html', 'N/A')[:300]}")
                return data
            else:
                print(f"Body: {r.text[:500]}")
    except Exception as e:
        print(f"oEmbed ERROR: {e}")
    return None


async def test_mbasic(url: str):
    """Test mbasic.facebook.com (mobile basic, no-JS version)."""
    # Convert URL to mbasic
    mbasic_url = url.replace("web.facebook.com", "mbasic.facebook.com").replace("www.facebook.com", "mbasic.facebook.com")
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r = await client.get(mbasic_url, headers=MOBILE_HEADERS)
            print(f"\n=== mbasic for {url[:60]}... ===")
            print(f"Status: {r.status_code}")
            print(f"Final URL: {r.url}")
            if r.status_code == 200:
                text = r.text
                # Look for post content patterns
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(text, "html.parser")
                # mbasic has specific structure
                # Try to find the post story
                story = soup.find("div", {"data-ft": True})
                if story:
                    print(f"Story text: {story.get_text(strip=True)[:500]}")
                # Look for any div with substantial text
                texts = []
                for div in soup.find_all("div"):
                    t = div.get_text(strip=True)
                    if len(t) > 50 and len(t) < 2000:
                        texts.append(t[:300])
                if texts:
                    print(f"Candidate texts ({len(texts)}):")
                    for i, t in enumerate(texts[:5]):
                        print(f"  [{i}] {t}")
                else:
                    print(f"HTML preview: {text[:1000]}")
            else:
                print(f"Body preview: {r.text[:500]}")
    except Exception as e:
        print(f"mbasic ERROR: {e}")


async def test_og_tags(url: str):
    """Test Open Graph meta tag extraction."""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r = await client.get(url, headers=HEADERS)
            print(f"\n=== OG Tags for {url[:60]}... ===")
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, "html.parser")
                og_tags = {}
                for tag in soup.find_all("meta", property=lambda x: x and x.startswith("og:")):
                    og_tags[tag.get("property")] = tag.get("content", "")
                for tag in soup.find_all("meta", attrs={"name": lambda x: x and x.startswith("twitter:")}):
                    og_tags[tag.get("name")] = tag.get("content", "")
                print(f"OG tags: {json.dumps(og_tags, indent=2, ensure_ascii=False)[:800]}")
                # Also look for any visible text
                title = soup.find("title")
                if title:
                    print(f"Title: {title.get_text(strip=True)}")
    except Exception as e:
        print(f"OG ERROR: {e}")


async def test_graphql_ghost(url: str):
    """Test if we can get any data from Facebook's share endpoint."""
    # Try the share dialog endpoint which sometimes exposes metadata
    share_url = f"https://www.facebook.com/sharer/sharer.php?u={url}"
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            r = await client.get(share_url, headers=HEADERS)
            print(f"\n=== Share dialog for {url[:60]}... ===")
            print(f"Status: {r.status_code}")
            if r.status_code == 200:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, "html.parser")
                # Look for link preview data
                preview = soup.find("div", class_=lambda x: x and "preview" in x.lower())
                if preview:
                    print(f"Preview: {preview.get_text(strip=True)[:500]}")
                else:
                    print(f"No preview found. HTML: {r.text[:500]}")
    except Exception as e:
        print(f"Share dialog ERROR: {e}")


async def test_scontent_cdn(url: str):
    """Check if the URL redirects to a CDN or gives any hints."""
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=False) as client:
            r = await client.get(url, headers=HEADERS)
            print(f"\n=== Raw response for {url[:60]}... ===")
            print(f"Status: {r.status_code}")
            print(f"Headers: {dict(r.headers)}")
            if r.status_code in (301, 302, 303, 307, 308):
                print(f"Redirect to: {r.headers.get('location', 'N/A')}")
            elif r.status_code == 200:
                print(f"Body first 800 chars: {r.text[:800]}")
    except Exception as e:
        print(f"Raw ERROR: {e}")


async def main():
    for url in TEST_URLS:
        print(f"\n{'='*60}")
        print(f"TESTING: {url}")
        print(f"{'='*60}")
        await test_scontent_cdn(url)
        await test_oembed(url)
        await test_mbasic(url)
        await test_og_tags(url)
        await test_graphql_ghost(url)


if __name__ == "__main__":
    asyncio.run(main())
