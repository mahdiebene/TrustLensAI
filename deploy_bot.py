"""Deploy the Telegram bot to the VPS: git hard-reset + build + up -d bot + logs.

Usage (Windows PowerShell):
    $env:VPS_HOST='107.161.168.216'; $env:VPS_USER='root'; $env:VPS_PASS='...'; python deploy_bot.py

Mirrors deploy_jina.py (backend) but targets the `bot` compose service.
Uses `git fetch + reset --hard` (NOT `git pull`) because the VPS clone ends up
with divergent history when master is force-pushed.
"""
import os
import sys
import paramiko


def _safe_print(text: str) -> None:
    """Print text without crashing on Windows cp1252 consoles.

    SSH output (git log, docker logs) can contain Unicode like '→' or Bengali
    that the default Windows console encoding can't represent. Re-encode to the
    stdout encoding with replacement so the deploy never dies on a print().
    """
    enc = (sys.stdout.encoding or "utf-8")
    sys.stdout.buffer.write(text.encode(enc, errors="replace"))
    sys.stdout.buffer.write(b"\n")
    sys.stdout.flush()


def run(client, cmd, timeout=300):
    _safe_print(f"\n$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out.strip():
        _safe_print(out)
    if err.strip():
        _safe_print("[stderr] " + err)
    return out, err



def main():
    host = os.environ.get("VPS_HOST")
    user = os.environ.get("VPS_USER", "root")
    password = os.environ.get("VPS_PASS")

    if not host or not password:
        print("ERROR: set VPS_HOST and VPS_PASS environment variables before running.")
        sys.exit(1)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        host, username=user, password=password,
        look_for_keys=False, allow_agent=False, banner_timeout=20,
    )

    # 1) Pre-flight: confirm TELEGRAM_BOT_TOKEN is present in .env (the bot needs it).
    run(client, "cd /opt/trustlens && grep -q '^TELEGRAM_BOT_TOKEN=' .env && echo 'TOKEN_PRESENT' || echo 'TOKEN_MISSING'")

    # 2) Deploy the bot service.
    deploy_cmd = (
        "cd /opt/trustlens && "
        "git fetch origin master && git reset --hard origin/master && "
        "git log -1 --oneline && "
        "docker compose build bot && "
        "docker compose up -d bot && "
        "sleep 6 && "
        "echo '--- BOT STATUS ---' && "
        "docker compose ps bot && "
        "echo '--- BOT LOGS ---' && "
        "docker logs --tail=30 trustlens-bot-1"
    )
    run(client, deploy_cmd, timeout=600)

    client.close()
    print("\n[+] Bot deploy done")


if __name__ == "__main__":
    main()
