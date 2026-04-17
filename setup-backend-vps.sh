#!/bin/bash
# NeoBot Backend Setup — Exécuter après reset OS Hetzner
set -e

echo "=== NEOBOT BACKEND VPS SETUP ==="
echo "1️⃣ Mise à jour système..."
apt update && apt upgrade -y

echo "2️⃣ Installation dépendances..."
apt install -y python3 python3-pip python3-venv git curl postgresql-client

echo "3️⃣ Clone repo..."
cd /root && git clone https://github.com/sf5fjyccfy-tech/neobot-mvp.git 2>/dev/null || (cd /root/neobot-mvp && git pull)

echo "4️⃣ Setup Python venv..."
cd /root/neobot-mvp
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip > /dev/null
pip install -r backend/requirements.txt

echo "5️⃣ Lancement backend (port 8000)..."
cd /root/neobot-mvp/backend
nohup python3 -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload > /root/neobot-mvp/backend.log 2>&1 &

sleep 3

echo ""
echo "✅ SETUP COMPLET!"
echo ""
echo "🔗 Tester: curl http://localhost:8000/health"
echo "📊 Logs: tail -20 /root/neobot-mvp/backend.log"
echo ""
curl http://localhost:8000/health 2>/dev/null | head -3 || echo "(En démarrage...)"
