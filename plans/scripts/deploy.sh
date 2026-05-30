#!/bin/bash
# TrustLens Deployment Script
set -e

echo "=== Deploying TrustLens ==="

cd /opt/trustlens

# Pull latest code
git pull origin main

# Rebuild and restart services
docker compose build backend
docker compose up -d

# Restart Nginx
systemctl reload nginx

echo "=== Deployment Complete ==="
