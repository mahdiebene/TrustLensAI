"""Deploy Playwright-based scraper to VPS."""
import paramiko
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(
    '107.161.168.216',
    username='root',
    password='***REDACTED***',
    timeout=20,
    look_for_keys=False,
    allow_agent=False,
    banner_timeout=20
)

print("Connected to VPS. Starting deployment...")

# Step 1: Pull latest code
print("[1/4] Pulling latest code...")
stdin, stdout, stderr = client.exec_command(
    'cd /opt/trustlens && git pull origin master 2>&1',
    timeout=30
)
pull = stdout.read().decode()
print(f"  Pull: {pull.strip()}")

# Step 2: Build backend (takes 3-5 min for Chromium)
print("[2/4] Building backend Docker image (Chromium install ~3-5 min)...")
stdin, stdout, stderr = client.exec_command(
    'cd /opt/trustlens && docker compose build --no-cache backend 2>&1 | tail -30',
    timeout=600
)
build = stdout.read().decode()
print(f"  Build (last 30 lines):\n{build}")

# Step 3: Restart backend
print("[3/4] Restarting backend container...")
stdin, stdout, stderr = client.exec_command(
    'cd /opt/trustlens && docker compose up -d backend 2>&1',
    timeout=30
)
up = stdout.read().decode()
print(f"  Up: {up.strip()}")

# Wait for container to start
print("  Waiting 12s for container to start...")
time.sleep(12)

# Step 4: Verify
print("[4/4] Verifying deployment...")
stdin, stdout, stderr = client.exec_command(
    'cd /opt/trustlens && git log --oneline -1 && echo "---" && docker compose logs backend --tail=5 2>&1 && echo "---" && curl -s http://localhost:8000/api/health',
    timeout=15
)
verify = stdout.read().decode()
print(f"  Verify:\n{verify}")

client.close()

with open('vps_deploy_result.txt', 'w', encoding='utf-8') as f:
    f.write(f"PULL:\n{pull}\n\nBUILD (tail):\n{build}\n\nUP:\n{up}\n\nVERIFY:\n{verify}\n")

print("\nDONE - Deployment complete!")
