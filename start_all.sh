#!/bin/bash
echo "=== DÉMARRAGE NEOBOT ==="
echo ""

echo "1. Docker..."
cd ~/neobot-mvp
docker-compose up -d
sleep 3

echo "2. Backend API..."
cd ~/neobot-mvp/backend
source venv/bin/activate
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
echo $! > backend.pid
sleep 5

echo "3. Frontend..."
cd ~/neobot-mvp/frontend
nohup npm run dev > frontend.log 2>&1 &
echo $! > frontend.pid
sleep 10

echo ""
echo "✅ Tous les services démarrés"
echo "Dashboard: http://localhost:3000"
echo "API: http://localhost:8000/docs"
