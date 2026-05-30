"""Rebuild backend container with new code."""
import paramiko
import time

HOST = "107.161.168.216"
USER = "root"
PWD = "***REDACTED***"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PWD,
               look_for_keys=False, allow_agent=False, banner_timeout=20)

# Single chained command since cd doesn't persist across exec_command
cmd = (
    "cd /opt/trustlens && "
    "docker compose build backend 2>&1 | tail -20 && "
    "docker compose up -d backend 2>&1 && "
    "sleep 6 && "
    "docker logs --tail=15 trustlens-backend-1 2>&1"
)

print("Running rebuild + restart...")
stdin, stdout, stderr = client.exec_command(cmd, timeout=300)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
print(out)
if err:
    print("STDERR:", err)

client.close()
print("\n=== DONE ===")
