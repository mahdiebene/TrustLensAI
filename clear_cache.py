"""Clear Redis cache on VPS."""
import paramiko

HOST = "107.161.168.216"
USER = "root"
PWD = "***REDACTED***"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PWD,
               look_for_keys=False, allow_agent=False, banner_timeout=20)

# Clear all trustlens analysis cache keys
cmd = "docker exec trustlens-redis-1 redis-cli KEYS 'trustlens:analysis:*' | xargs -r docker exec trustlens-redis-1 redis-cli DEL"
stdin, stdout, stderr = client.exec_command(cmd)
out = stdout.read().decode("utf-8", errors="replace")
err = stderr.read().decode("utf-8", errors="replace")
print("OUT:", out)
if err:
    print("ERR:", err)

client.close()
