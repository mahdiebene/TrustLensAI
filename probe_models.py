"""List all models available on Pollinations from inside the prod container."""
import os, sys, paramiko

REMOTE = r'''
import json, urllib.request, os
key = os.environ.get("POLLINATIONS_API_KEY", "")
req = urllib.request.Request(
    "https://gen.pollinations.ai/v1/models",
    headers={"Authorization": f"Bearer {key}", "User-Agent": "trustlens-probe"},
)
try:
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read().decode())
    ids = [m["id"] for m in data.get("data", [])]
    print(f"=== {len(ids)} models ===")
    for i in ids: print(i)
except Exception as e:
    print(f"ERR: {e}")
    # Try plain text endpoint
    req2 = urllib.request.Request("https://text.pollinations.ai/models")
    try:
        with urllib.request.urlopen(req2, timeout=20) as r:
            print("--- text.pollinations.ai/models ---")
            print(r.read().decode()[:6000])
    except Exception as e2:
        print(f"ERR2: {e2}")
'''

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(os.environ["VPS_HOST"], username=os.environ.get("VPS_USER","root"),
              password=os.environ["VPS_PASS"], look_for_keys=False, allow_agent=False)
    sftp = c.open_sftp()
    with sftp.open("/tmp/probe_models.py", "w") as f: f.write(REMOTE)
    sftp.close()
    cmd = "docker cp /tmp/probe_models.py trustlens-backend-1:/tmp/probe_models.py && docker exec trustlens-backend-1 python /tmp/probe_models.py 2>&1"
    _, o, e = c.exec_command(cmd, timeout=60)
    print(o.read().decode("utf-8", errors="replace"))
    err = e.read().decode("utf-8", errors="replace")
    if err.strip(): print("[stderr]", err)
    c.close()

if __name__ == "__main__": main()
