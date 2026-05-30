"""Run the scraper INSIDE the VPS container to verify it works on VPS network."""
import paramiko
import textwrap
import sys

VPS_HOST = "107.161.168.216"
VPS_USER = "root"
VPS_PASS = "***REDACTED***"

TEST_SCRIPT = r"""
import asyncio
import sys
sys.path.insert(0, '/app')
from app.services.scraper import scrape_facebook_url, _resolve_facebook_url
import httpx
import re

URLS = [
    "https://web.facebook.com/factbuddy.pg/posts/pfbid02KASxVQonABiQM9MUpe8JxhnSs1mK8PJFd8fXStZK2RBWYhT6DzBTmfYN6RUebWxQl",
    "https://web.facebook.com/share/p/1EfTBoVsrL/",
]

async def main():
    for url in URLS:
        print("=" * 70, flush=True)
        print("URL:", url, flush=True)
        print("=" * 70, flush=True)

        try:
            resolved = await _resolve_facebook_url(url)
            print("RESOLVED:", resolved, flush=True)
        except Exception as e:
            print("RESOLVE_ERR:", repr(e), flush=True)

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                "Accept-Language": "en-US,en;q=0.9",
            }
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as c:
                r = await c.get(url)
                print("RAW_STATUS:", r.status_code, flush=True)
                print("RAW_FINAL_URL:", str(r.url), flush=True)
                print("RAW_LEN:", len(r.text), flush=True)
                og_desc = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']', r.text)
                og_title = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](.*?)["\']', r.text)
                print("OG_TITLE:", (og_title.group(1)[:200] if og_title else None), flush=True)
                print("OG_DESC:", (og_desc.group(1)[:200] if og_desc else None), flush=True)
                low = r.text.lower()[:5000]
                if "log into facebook" in low or "checkpoint" in low or "you must log in" in low:
                    print("WARNING: login wall detected", flush=True)
                title_m = re.search(r'<title[^>]*>([^<]{0,300})', r.text)
                if title_m:
                    print("PAGE_TITLE:", title_m.group(1), flush=True)
        except Exception as e:
            print("RAW_ERR:", repr(e), flush=True)

        try:
            result = await scrape_facebook_url(url)
            print("SCRAPE_SUCCESS:", result.get("success"), flush=True)
            print("SCRAPE_TITLE:", result.get("title"), flush=True)
            print("SCRAPE_AUTHOR:", result.get("author"), flush=True)
            print("SCRAPE_TEXT_LEN:", len(result.get("text", "")), flush=True)
            preview = result.get("text", "")[:300]
            print("SCRAPE_TEXT_PREVIEW:", preview, flush=True)
            print("SCRAPE_ERROR:", result.get("error"), flush=True)
        except Exception as e:
            print("SCRAPE_ERR:", repr(e), flush=True)
        print(flush=True)

asyncio.run(main())
"""


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        VPS_HOST,
        username=VPS_USER,
        password=VPS_PASS,
        look_for_keys=False,
        allow_agent=False,
        banner_timeout=20,
    )

    # 1. Write test script to /tmp on host via SFTP
    sftp = client.open_sftp()
    with sftp.open("/tmp/scrape_test.py", "w") as f:
        f.write(TEST_SCRIPT)
    sftp.close()
    print("[+] uploaded /tmp/scrape_test.py")

    # 2. Copy into container then exec
    cmd = (
        "docker cp /tmp/scrape_test.py trustlens-backend-1:/tmp/scrape_test.py && "
        "docker exec trustlens-backend-1 python /tmp/scrape_test.py 2>&1"
    )
    print(f"[*] running: {cmd}\n")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=120)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")

    # Save first (avoid losing data on Windows charmap errors)
    with open("vps_scrape_test.txt", "w", encoding="utf-8") as f:
        f.write("STDOUT:\n")
        f.write(out)
        f.write("\nSTDERR:\n")
        f.write(err)
    print("[+] saved to vps_scrape_test.txt")

    # Now print (best-effort, may fail on cp1252 with Bengali)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    print("=" * 70)
    print("STDOUT:")
    print("=" * 70)
    try:
        print(out)
    except UnicodeEncodeError:
        print(out.encode("ascii", "replace").decode("ascii"))
    if err.strip():
        print("=" * 70)
        print("STDERR:")
        print("=" * 70)
        try:
            print(err)
        except UnicodeEncodeError:
            print(err.encode("ascii", "replace").decode("ascii"))

    client.close()


if __name__ == "__main__":
    main()
