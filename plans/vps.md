# TrustLens VPS Setup Log

> **VPS Details:**
> - IP: 107.161.168.216
> - Username: root
> - Provider: Yotta Src
> - OS: Ubuntu 26.04 LTS

---

## Status

⚠️ **VPS is currently unreachable from development machine** (tested 2026-05-24).
Port 22 connection times out. Possible causes:
- VPS may be powered off
- Network firewall blocking outbound SSH
- IP may have changed

**Action needed:** Access VPS via provider's web console (Yotta Src panel) or from a different network.

---

## Access Method

```bash
ssh root@107.161.168.216
# Password: ***REDACTED***
```

---

## Setup Commands Executed

### Step 1: Initial Connection
```bash
ssh root@107.161.168.216
```

### Step 2: System Update
```bash
apt update && apt upgrade -y
```

### Step 3: Swap (4GB)
```bash
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### Step 4: Install Essentials
```bash
apt install -y git curl wget ufw software-properties-common apt-transport-https ca-certificates gnupg lsb-release
```

### Step 5: Firewall
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw allow 7474/tcp
ufw allow 7687/tcp
ufw --force enable
```

### Step 6: Docker
```bash
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker
```

### Step 7: Docker Compose
```bash
apt install -y docker-compose-plugin
```

### Step 8: Node.js 22
```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt install -y nodejs
```

### Step 9: Nginx
```bash
apt install -y nginx
systemctl enable nginx
```

### Step 10: Certbot
```bash
apt install -y certbot python3-certbot-nginx
```

### Step 11: Clone & Deploy
```bash
cd /opt
git clone https://github.com/mahdiebene/TrustLensAI.git trustlens
cd trustlens
cp .env.example .env
# Edit .env with real values
docker compose up -d
```

### Step 12: Nginx Config
```bash
cp nginx/trustlens.conf /etc/nginx/sites-available/trustlens
ln -s /etc/nginx/sites-available/trustlens /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
```

---

## Useful Commands

```bash
# Check service status
docker compose ps
docker compose logs backend
docker compose logs -f backend

# Restart a service
docker compose restart backend

# Rebuild after code changes
git pull origin main
docker compose build backend
docker compose up -d

# Check disk/memory
df -h
free -h
htop

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Redis CLI
docker compose exec redis redis-cli

# PostgreSQL
docker compose exec postgres psql -U trustlens

# Neo4j browser
# http://107.161.168.216:7474
```
