#!/bin/bash
# TrustLens VPS Setup Script
# Run as root on Ubuntu 26.04

set -e

echo "=== TrustLens VPS Setup ==="

# 1. System update
apt update && apt upgrade -y

# 2. Add swap (4GB)
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap configured."
fi

# 3. Install essentials
apt install -y git curl wget ufw software-properties-common \
    apt-transport-https ca-certificates gnupg lsb-release

# 4. Firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw allow 7474/tcp
ufw allow 7687/tcp
ufw --force enable

# 5. Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker
systemctl start docker

# 6. Docker Compose
apt install -y docker-compose-plugin

# 7. Node.js 22 LTS
curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && apt install -y nodejs

# 8. Nginx
apt install -y nginx
systemctl enable nginx

# 9. Certbot
apt install -y certbot python3-certbot-nginx

echo "=== Setup Complete ==="
echo "Next: Clone repo, copy .env, run docker compose up -d"
