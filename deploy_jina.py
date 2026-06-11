"""Deploy: git pull + rebuild backend container + clear cache + smoke test.

Usage:
    set VPS_HOST=...  # or export on Linux
    set VPS_USER=root
    set VPS_PASS=...
    python deploy_jina.py
"""
import os
import sys
import paramiko


def run(client, cmd, timeout=300):
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    if out.strip():
        print(out)
    if err.strip():
        print("[stderr]", err)
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

    # Combined chained command — `cd` doesn't persist across exec_command sessions
    # IMPORTANT: use fetch + hard reset, NOT `git pull`. The VPS clone ends up
    # with divergent history whenever master is force-pushed, and a plain pull
    # dies with "Need to specify how to reconcile divergent branches" — shipping
    # nothing. The hard reset always lands exactly on origin/master.
    deploy_cmd = (
        "cd /opt/trustlens && "
        "git fetch origin master && git reset --hard origin/master && "
        "git log -1 --oneline && "
        "docker compose build backend && "
        "docker compose up -d backend && "
        "sleep 8 && "
        "docker exec trustlens-redis-1 sh -c "
        "'redis-cli KEYS \"trustlens:analysis:*\" | xargs -r redis-cli DEL' && "
        "echo '--- BACKEND LOGS ---' && "
        "docker logs --tail=30 trustlens-backend-1"
    )

    run(client, deploy_cmd, timeout=600)

    client.close()
    print("\n[+] Deploy done")


if __name__ == "__main__":
    main()
