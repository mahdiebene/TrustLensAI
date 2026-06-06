"""Recency probe — runs inside trustlens-backend-1 container, using the SAME
PollinationsClient + same env the production backend uses, to see what each
upstream model actually returns for a recency-sensitive question.

Usage:
    set VPS_HOST=...  set VPS_USER=root  set VPS_PASS=...  python probe_recency.py
"""
import os
import sys
import paramiko


REMOTE_SCRIPT = r'''
import asyncio, json, sys, time
sys.path.insert(0, "/app")
from app.services.pollinations import get_pollinations_client

QUESTION = (
    "What is today's date? Who is the current Prime Minister of Bangladesh "
    "as of right now (year 2026)? Search the web and cite the URL and "
    "publication date of your top source. If you do NOT have live web access, "
    "say so explicitly. Be terse: today's date, the PM's name, the source URL, "
    "and the source publication date."
)

MODELS = [
    "perplexity-reasoning",
    "openai-large",
    "gemini-2.5-flash",
    "mistral",
    "openai",
]


async def main():
    client = get_pollinations_client()
    print("=== POLLINATIONS RECENCY PROBE (via PollinationsClient) ===\n")
    print(f"Question: {QUESTION}\n")
    for m in MODELS:
        print(f"\n--- MODEL: {m} ---")
        t0 = time.time()
        try:
            out = await client.chat(
                model=m,
                messages=[
                    {"role": "system", "content": "You are a fact-checker. Use live web search if you have it. Today is in 2026."},
                    {"role": "user", "content": QUESTION},
                ],
                temperature=0.1,
                timeout=60.0,
                max_retries=1,
            )
            dt = time.time() - t0
            print(f"[{dt:.1f}s, {len(out)} chars]")
            print(out[:2500])
        except Exception as e:
            dt = time.time() - t0
            print(f"[ERROR after {dt:.1f}s] {type(e).__name__}: {e}")
        print()


asyncio.run(main())
'''


def main():
    host = os.environ.get("VPS_HOST")
    user = os.environ.get("VPS_USER", "root")
    password = os.environ.get("VPS_PASS")
    if not host or not password:
        print("ERROR: set VPS_HOST and VPS_PASS env vars.")
        sys.exit(1)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(host, username=user, password=password,
                   look_for_keys=False, allow_agent=False, banner_timeout=20)

    sftp = client.open_sftp()
    with sftp.open("/tmp/probe_recency.py", "w") as f:
        f.write(REMOTE_SCRIPT)
    sftp.close()

    cmd = (
        "docker cp /tmp/probe_recency.py trustlens-backend-1:/tmp/probe_recency.py && "
        "docker exec trustlens-backend-1 python /tmp/probe_recency.py 2>&1"
    )
    print(f"\n$ {cmd}\n")
    _, out, err = client.exec_command(cmd, timeout=600)
    print(out.read().decode("utf-8", errors="replace"))
    e = err.read().decode("utf-8", errors="replace")
    if e.strip():
        print("[stderr]", e)

    client.close()


if __name__ == "__main__":
    main()
