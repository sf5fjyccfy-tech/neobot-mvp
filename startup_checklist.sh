#!/bin/bash

# ✅ NéoBot MVP - Checklist Interactive de Démarrage

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
PROJECT_DIR="$HOME/neobot-mvp"
BACKEND_PORT=8000
FRONTEND_PORT=3000
WHATSAPP_PORT=3001
DB_PORT=5432

# Fonctions
check_port() {
    local port=$1
    nc -z localhost $port 2>/dev/null && echo "1" || echo "0"
}

show_header() {
    clear
    echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║    ✅ NéoBot MVP - Startup Checklist           ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}\n"
}

check_service() {
    local service=$1
    local port=$2
    local name=$3
    
    if [ $(check_port $port) -eq 1 ]; then
        echo -e "${GREEN}✅ $name${NC} (Port $port)"
        return 0
    else
        echo -e "${RED}❌ $name${NC} (Port $port) - NOT RUNNING"
        return 1
    fi
}

# Main
show_header

echo -e "${YELLOW}📋 CHECKLIST PRE-STARTUP${NC}\n"

# Check Prerequisites
echo -e "${BLUE}1️⃣  Vérification des prérequis...${NC}\n"

# PostgreSQL
if pg_isready -h localhost -p $DB_PORT > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PostgreSQL${NC} (Port $DB_PORT)"
else
    echo -e "${RED}❌ PostgreSQL${NC} - NOT RUNNING"
    echo -e "${YELLOW}   → Démarre PostgreSQL: sudo systemctl start postgresql${NC}\n"
    exit 1
fi

# Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v)
    echo -e "${GREEN}✅ Node.js${NC} ($NODE_VERSION)"
else
    echo -e "${RED}❌ Node.js${NC} - NOT INSTALLED\n"
    exit 1
fi

# Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python${NC} ($PYTHON_VERSION)"
else
    echo -e "${RED}❌ Python${NC} - NOT INSTALLED\n"
    exit 1
fi

echo -e "\n${BLUE}2️⃣  Vérification des dossiers du projet...${NC}\n"

if [ -d "$PROJECT_DIR/backend" ] && [ -d "$PROJECT_DIR/frontend" ] && [ -d "$PROJECT_DIR/whatsapp-service" ]; then
    echo -e "${GREEN}✅ Tous les dossiers présents${NC}\n"
else
    echo -e "${RED}❌ Dossiers du projet manquants${NC}\n"
    exit 1
fi

echo -e "${BLUE}3️⃣  Vérification des services actuels...${NC}\n"

BACKEND_RUNNING=0
FRONTEND_RUNNING=0
WHATSAPP_RUNNING=0

check_service "Backend" $BACKEND_PORT "FastAPI Backend" && BACKEND_RUNNING=1 || true
check_service "Frontend" $FRONTEND_PORT "Next.js Frontend" && FRONTEND_RUNNING=1 || true
check_service "WhatsApp" $WHATSAPP_PORT "Baileys WhatsApp" && WHATSAPP_RUNNING=1 || true

echo ""

# Résumé
RUNNING_COUNT=$((BACKEND_RUNNING + FRONTEND_RUNNING + WHATSAPP_RUNNING))

echo -e "${BLUE}════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📊 Résumé: $RUNNING_COUNT/3 services en ligne${NC}"
echo -e "${BLUE}════════════════════════════════════════════════${NC}\n"

if [ $RUNNING_COUNT -eq 3 ]; then
    echo -e "${GREEN}🎉 Tous les services sont déjà en ligne!${NC}\n"
    echo -e "${YELLOW}Options:${NC}"
    echo -e "  1) Voir les logs"
    echo -e "  2) Redémarrer les services"
    echo -e "  3) Quitter"
    read -p "Choix (1-3): " choice
    
    case $choice in
        1)
            echo -e "\n${BLUE}Logs disponibles:${NC}"
            ls -lh /tmp/neobot_*.log 2>/dev/null || echo "Aucun log trouvé"
            ;;
        2)
            echo -e "\n${YELLOW}Redémarrage des services...${NC}"
            pkill -f "uvicorn\|npm run dev\|npm start" || true
            sleep 2
            $PROJECT_DIR/start_all_services.sh
            ;;
        3)
            exit 0
            ;;
    esac
else
    echo -e "${YELLOW}🚀 Services à démarrer:${NC}\n"
    [ $BACKEND_RUNNING -eq 0 ] && echo -e "  • Backend (Port 8000)"
    [ $FRONTEND_RUNNING -eq 0 ] && echo -e "  • Frontend (Port 3000)"
    [ $WHATSAPP_RUNNING -eq 0 ] && echo -e "  • WhatsApp (Port 3001)"
    
    echo ""
    read -p "Démarrer les services manquants? (y/n): " confirm
    
    if [ "$confirm" = "y" ]; then
        echo -e "\n${YELLOW}Démarrage en cours...${NC}\n"
        cd $PROJECT_DIR
        ./start_all_services.sh
    fi
fi
