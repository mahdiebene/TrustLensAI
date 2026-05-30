"""Check backend logs and test scraper directly on VPS."""
import paramiko

HOST = "107.161.168.216"
USER = "root"
PWD = "***REDACTED***"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PWD,
               look_for_keys=False, allow_agent=False, banner_timeout=20)

commands = [
    # Recent backend logs
    ("LOGS", "docker logs --tail=40 trustlens-backend-1 2>&1"),
    # Test the scraper directly inside the container
    ("SCRAPER TEST", """docker exec trustlens-backend-1 python -c "
import asyncio
from app.services.scraper import scrape_url
async def t():
    r = await scrape_url('https://web.facebook.com/factbuddy.pg/posts/pfbid02KASxVQonABiQM9MUpe8JxhnSs1mK8PJFd8fXStZK2RBWYhT6DzBTmfYN6RUebWxQl')
    print('SUCCESS:', r['success'])
    print('TEXTLEN:', len(r['text']))
    print('TEXT:', r['text'][:300].encode('ascii','replace').decode())
asyncio.run(t())
" 2>&1"""),
]

for label, cmd in commands:
    print(f"\n{'='*50}\n{label}\n{'='*50}")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")
    print(out)
    if err:
        print("STDERR:", err)

client.close()
