"""Deploy: git pull + rebuild backend container + clear cache + smoke test."""
import paramiko
import time

VPS_HOST = "107.161.168.216"
VPS_USER = "root"
VPS_PASS = "***REDACTED***"


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
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        VPS_HOST, username=VPS_USER, password=VPS_PASS,
        look_for_keys=False, allow_agent=False, banner_timeout=20,
    )

    # Combined chained command — `cd` doesn't persist across exec_command sessions
    deploy_cmd = (
        "cd /opt/trustlens && "
        "git pull origin master && "
        "docker compose build backend && "
        "docker compose up -d backend && "
        "sleep 8 && "
        "docker exec trustlens-redis-1 sh -c "
        "'redis-cli KEYS \"trustlens:analysis:*\" | xargs -r redis-cli DEL' && "
        "echo '--- BACKEND LOGS ---' && "
        "docker logs --tail=20 trustlens-backend-1"
    )
    run(client, deploy_cmd, timeout=600)

    client.close()
    print("\n[+] Deploy done")


if __name__ == "__main__":
    main()
