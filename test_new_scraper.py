"""Test the new Facebook scraper locally — writes to file to avoid console encoding issues."""
import asyncio
import sys
sys.path.insert(0, "backend")

from app.services.scraper import scrape_url, is_facebook_url

TEST_URLS = [
    "https://web.facebook.com/share/p/1EfTBoVsrL/",
    "https://web.facebook.com/factbuddy.pg/posts/pfbid02KASxVQonABiQM9MUpe8JxhnSs1mK8PJFd8fXStZK2RBWYhT6DzBTmfYN6RUebWxQl",
    "https://www.facebook.com/share/p/1EfTBoVsrL/",
]

async def main():
    lines = []
    for url in TEST_URLS:
        lines.append(f"\n{'='*60}")
        lines.append(f"Testing: {url}")
        lines.append(f"is_facebook: {is_facebook_url(url)}")
        result = await scrape_url(url)
        lines.append(f"Success: {result['success']}")
        lines.append(f"Title: {result['title'][:100] if result['title'] else 'N/A'}")
        lines.append(f"Author: {result['author'][:100] if result['author'] else 'N/A'}")
        lines.append(f"Image: {result['image_url'][:80] if result['image_url'] else 'N/A'}")
        lines.append(f"Text ({len(result['text'])} chars):")
        lines.append(result['text'][:800])
        lines.append("-" * 40)

    with open("test_scraper_results.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Results written to test_scraper_results.txt")

if __name__ == "__main__":
    asyncio.run(main())
