#!/bin/bash

# Script de démarrage pour tous les services NéoBot

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PROJECT_DIR="$HOME/neobot-mvp"

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🚀 NéoBot MVP - Démarrage        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"

# Vérifier que tous les dossiers existent
if [ ! -d "$PROJECT_DIR/backend" ] || [ ! -d "$PROJECT_DIR/frontend" ] || [ ! -d "$PROJECT_DIR/whatsapp-service" ]; then
    echo -e "${RED}❌ Erreur: Le répertoire du projet n'est pas trouvé à $PROJECT_DIR${NC}"
    exit 1
fi

# Vérifier PostgreSQL
echo -e "${YELLOW}⏳ Vérification de PostgreSQL...${NC}"
if ! pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL ne tourne pas. Démarre-le d'abord:${NC}"
    echo -e "${YELLOW}   sudo systemctl start postgresql${NC}"
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL en ligne${NC}\n"

# Backend
echo -e "${BLUE}1️⃣  Lancement du Backend (FastAPI)...${NC}"
cd "$PROJECT_DIR/backend"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/neobot_backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${GREEN}✅ Backend lancé (PID: $BACKEND_PID)${NC}"
echo -e "   📍 http://localhost:8000${NC}\n"

sleep 2

# Frontend
echo -e "${BLUE}2️⃣  Lancement du Frontend (Next.js)...${NC}"
cd "$PROJECT_DIR/frontend"
nohup npm run dev > /tmp/neobot_frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend lancé (PID: $FRONTEND_PID)${NC}"
echo -e "   📍 http://localhost:3000${NC}\n"

sleep 2

# WhatsApp Service
echo -e "${BLUE}3️⃣  Lancement du Service WhatsApp...${NC}"
cd "$PROJECT_DIR/whatsapp-service"
nohup npm start > /tmp/neobot_whatsapp.log 2>&1 &
WHATSAPP_PID=$!
echo -e "${GREEN}✅ WhatsApp Service lancé (PID: $WHATSAPP_PID)${NC}"
echo -e "   📍 http://localhost:3001${NC}\n"

sleep 3

# Vérifier que tout tourne
echo -e "${BLUE}═══════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Tous les services sont lancés!${NC}"
echo -e "${BLUE}═══════════════════════════════════════${NC}\n"

echo -e "${YELLOW}📊 Statut des services:${NC}"
echo -e "   Backend (8000):      $(curl -s http://localhost:8000/health > /dev/null && echo '🟢 OK' || echo '🔴 KO')"
echo -e "   Frontend (3000):     $(curl -s http://localhost:3000 > /dev/null && echo '🟢 OK' || echo '🔴 KO')"
echo -e "   WhatsApp (3001):     $(curl -s http://localhost:3001/health > /dev/null && echo '🟢 OK' || echo '🔴 KO')\n"

echo -e "${GREEN}🎯 Prochaines étapes:${NC}"
echo -e "   1. Ouvre http://localhost:3000 dans le navigateur"
echo -e "   2. Pour WhatsApp: scanne le QR code dans la console"
echo -e "   3. Voir les logs: tail -f /tmp/neobot_*.log\n"

echo -e "${YELLOW}⏸️  Appuie sur Ctrl+C pour arrêter${NC}\n"

# Garder le script actif
wait
