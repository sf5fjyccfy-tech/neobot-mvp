#!/bin/bash
set -e
cd /opt/neobot
git pull origin main
cp nginx/neobot-ai.com.conf /etc/nginx/sites-available/neobot-ai.com
ln -sf /etc/nginx/sites-available/neobot-ai.com /etc/nginx/sites-enabled/neobot-ai.com
nginx -t && systemctl reload nginx
echo "NGINX OK"
docker compose up -d --build frontend
docker compose ps
