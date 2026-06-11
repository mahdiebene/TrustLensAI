"""Smoke-test the new verifier-first analyze pipeline against prod.

Calls the prod backend from INSIDE the trustlens-backend-1 container so
we hit it on localhost:8000 (no rate limit, no proxy noise). Prints a
compact human-readable summary for each test case.
"""
import os, json, paramiko

CASES = [
    ("FALSE_CLAIM_HASINA",  "Bangladesh er bortoman Prime Minister Sheikh Hasina."),
    ("TRUE_CLAIM_TARIQUE",  "বাংলাদেশের বর্তমান প্রধানমন্ত্রী তারেক রহমান।"),
    ("TRUE_GENERIC_FACT",   "The capital of Bangladesh is Dhaka."),
]

RUNNER = r"""
import json, urllib.request, sys
body = open('/tmp/_smoke.json','rb').read()
req = urllib.request.Request(
    'http://localhost:8000/api/analyze',
    data=body,
    headers={'Content-Type':'application/json'},
)
sys.stdout.buffer.write(urllib.request.urlopen(req, timeout=120).read())
"""

def fmt(label, d):
    print(f"\n{'='*72}\n{label}\n{'='*72}")
    if not isinstance(d, dict) or "trust_score" not in d:
        print("ERROR / unexpected payload:", str(d)[:600]); return
    print(f"SCORE: {d.get('trust_score')}  VERDICT: {d.get('verdict')} / {d.get('verdict_bn')}")
    print(f"CONF: {d.get('confidence')}  TIME: {d.get('processing_time_ms')}ms  CACHED: {d.get('cached')}")
    print(f"EXPL_EN: {(d.get('explanation_en') or '')[:300]}")
    print(f"EXPL_BN: {(d.get('explanation_bn') or '')[:300]}")
    print("\nPillars:")
    for p in d.get("pillars", []):
        print(f"  {p['name']:<22} {p['score']:>5.1f}  | {(p.get('explanation_en') or '')[:120]}")
    ev = d.get("pillars",[{}])[0].get("evidence",[]) if d.get("pillars") else []
    if ev:
        print("\nEvidence (pillar 0):")
        for e in ev[:6]:
            print(f"  - {e}")

def main():
    host = os.environ.get("VPS_HOST","107.161.168.216")
    pwd  = os.environ["VPS_PASS"]
    c = paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(host, username="root", password=pwd, look_for_keys=False, allow_agent=False, timeout=15)

    # Upload runner script once.
    sftp = c.open_sftp()
    with sftp.open("/tmp/_smoke_runner.py","w") as f:
        f.write(RUNNER)
    for label, content in CASES:
        body = json.dumps({"content": content}, ensure_ascii=False)
        with sftp.open("/tmp/_smoke.json","w") as f:
            f.write(body)
        # Copy both files into the container (container has no /tmp share with host)
        cmd = (
            "docker cp /tmp/_smoke.json        trustlens-backend-1:/tmp/_smoke.json && "
            "docker cp /tmp/_smoke_runner.py   trustlens-backend-1:/tmp/_smoke_runner.py && "
            "docker exec trustlens-backend-1 python /tmp/_smoke_runner.py"
        )
        _, o, e = c.exec_command(cmd, timeout=180)
        out = o.read().decode("utf-8", errors="replace").strip()
        err = e.read().decode("utf-8", errors="replace").strip()
        try:
            d = json.loads(out)
        except Exception:
            print(f"\n[{label}] non-JSON\nSTDOUT: {out[:600]}\nSTDERR: {err[:400]}")
            continue
        fmt(label, d)
    sftp.close(); c.close()

if __name__ == "__main__":
    main()
