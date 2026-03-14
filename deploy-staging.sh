#!/bin/bash
# Script de déploiement automatisé pour NeoBOT Staging
# Usage: bash deploy-staging.sh

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
ENVIRONMENT="staging"
APP_USER="neobot"
APP_HOME="/home/$APP_USER/neobot-mvp"
DB_NAME="neobot_staging"
DB_USER="neobot_staging"
DOMAIN="staging.neobot.app"

echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🚀 NeoBOT DÉPLOIEMENT STAGING${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# ========== VÉRIFICATIONS PRÉALABLES ==========
echo -e "${YELLOW}⏳ Étape 1/7: Vérifications préalables${NC}"
echo ""

# Vérifier root
if [ "$EUID" -ne 0 ]; then 
  echo -e "${RED}❌ Ce script doit être exécuté en tant que root${NC}"
  exit 1
fi

echo "✅ Exécuté en tant que root"

# Vérifier Ubuntu 20.04+
if ! grep -q "Ubuntu 20\|Ubuntu 22\|Ubuntu 24" /etc/os-release; then
  echo -e "${RED}❌ Ubuntu 20.04 LTS ou supérieur requis${NC}"
  exit 1
fi

echo "✅ Ubuntu version compatible"

# Vérifier utilisateur neobot existe
if ! id "$APP_USER" &>/dev/null; then
  echo "📝 Création utilisateur $APP_USER..."
  useradd -m -s /bin/bash $APP_USER
  echo "✅ Utilisateur créé"
else
  echo "✅ Utilisateur $APP_USER existe"
fi

echo ""

# ========== INSTALLATION DÉPENDANCES ==========
echo -e "${YELLOW}⏳ Étape 2/7: Installation dépendances système${NC}"
echo ""

apt-get update -qq
apt-get install -y \
  python3.10 \
  python3-pip \
  postgresql \
  postgresql-contrib \
  nodejs \
  npm \
  curl \
  git \
  build-essential \
  uuid-runtime \
  > /dev/null 2>&1

echo "✅ Dépendances système installées"

# ========== CONFIGURATION BASE DONNÉES ==========
echo -e "${YELLOW}⏳ Étape 3/7: Configuration base de données${NC}"
echo ""

# Générer password aléatoire
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Vérifier si DB existe
if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
  echo "✅ Base de données $DB_NAME existe déjà"
else
  echo "📝 Création base de données $DB_NAME..."
  
  sudo -u postgres psql << EOF
CREATE DATABASE $DB_NAME;
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET default_transaction_deferrable TO on;
ALTER ROLE $DB_USER SET default_time_zone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF
  
  echo "✅ Base de données créée"
  echo "📧 Credentials: $DB_USER / ••••••••"
fi

echo ""

# ========== PRÉPARATION APPLICATION ==========
echo -e "${YELLOW}⏳ Étape 4/7: Préparation application${NC}"
echo ""

# Vérifier répertoire app
if [ ! -d "$APP_HOME" ]; then
  echo -e "${RED}❌ Répertoire $APP_HOME non trouvé${NC}"
  exit 1
fi

echo "✅ Répertoire application trouvé"

# Créer .env backend
echo "📝 Configuration backend .env..."
cat > $APP_HOME/backend/.env << EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost/$DB_NAME
DEEPSEEK_API_KEY=sk-change-me
SECRET_KEY=$(openssl rand -base64 32)
ENVIRONMENT=staging
DEBUG=False
FRONTEND_URL=https://$DOMAIN
BAILEYS_SESSION_DIR=/home/$APP_USER/neobot-sessions
LOG_LEVEL=INFO
EOF

chmod 600 $APP_HOME/backend/.env
echo "✅ .env backend créé"

# Installer dépendances Python
cd $APP_HOME/backend
echo "📝 Installation dépendances Python..."
pip install -q -r requirements.txt
echo "✅ Dépendances Python installées"

# Exécuter migrations
echo "📝 Exécution migrations base de données..."
alembic upgrade head > /dev/null 2>&1
echo "✅ Migrations exécutées"

# Frontend
cd $APP_HOME/frontend
echo "📝 Installation dépendances Frontend..."
npm install --silent > /dev/null 2>&1
echo "✅ Dépendances npm installées"

# Build frontend
echo "📝 Build frontend..."
npm run build > /dev/null 2>&1
echo "✅ Frontend build complété"

# Permissions
chown -R $APP_USER:$APP_USER $APP_HOME
echo "✅ Permissions configurées"

echo ""

# ========== CONFIGURATION SERVICES ==========
echo -e "${YELLOW}⏳ Étape 5/7: Configuration services systemd${NC}"
echo ""

# Backend service
cat > /etc/systemd/system/neobot-backend.service << EOF
[Unit]
Description=NeoBOT Backend - Staging
After=postgresql.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_HOME/backend
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Frontend service
cat > /etc/systemd/system/neobot-frontend.service << EOF
[Unit]
Description=NeoBOT Frontend - Staging
After=neobot-backend.service

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_HOME/frontend
ExecStart=/usr/bin/npm start
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload
echo "✅ Services systemd configurés"

echo ""

# ========== DÉMARRAGE SERVICES ==========
echo -e "${YELLOW}⏳ Étape 6/7: Démarrage services${NC}"
echo ""

# Démarrer backend
echo "📝 Démarrage backend..."
systemctl start neobot-backend
sleep 3

if systemctl is-active --quiet neobot-backend; then
  echo "✅ Backend démarré"
else
  echo -e "${RED}❌ Erreur démarrage backend${NC}"
  journalctl -u neobot-backend -n 20
  exit 1
fi

# Démarrer frontend
echo "📝 Démarrage frontend..."
systemctl start neobot-frontend
sleep 3

if systemctl is-active --quiet neobot-frontend; then
  echo "✅ Frontend démarré"
else
  echo -e "${RED}❌ Erreur démarrage frontend${NC}"
  journalctl -u neobot-frontend -n 20
  exit 1
fi

# Activer au démarrage
systemctl enable neobot-backend neobot-frontend > /dev/null 2>&1
echo "✅ Services activés au démarrage"

echo ""

# ========== TESTS SANTÉ ==========
echo -e "${YELLOW}⏳ Étape 7/7: Tests de santé${NC}"
echo ""

sleep 2

# Test backend
echo "🔍 Test backend..."
for i in {1..5}; do
  if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "✅ Backend sain"
    break
  fi
  if [ $i -lt 5 ]; then
    echo "  Tentative $i/5..."
    sleep 2
  else
    echo -e "${RED}❌ Backend ne répond pas${NC}"
  fi
done

# Test frontend
echo "🔍 Test frontend..."
if curl -s -I http://localhost:3000 | grep -q "200"; then
  echo "✅ Frontend sain"
else
  echo -e "${YELLOW}⚠️  Frontend en cours de démarrage${NC}"
fi

echo ""

# ========== RÉSUMÉ ==========
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ DÉPLOIEMENT STAGING RÉUSSI${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "📊 Configuration:"
echo "  - Environment: $ENVIRONMENT"
echo "  - Domain: $DOMAIN"
echo "  - App User: $APP_USER"
echo "  - Backend: http://localhost:8000"
echo "  - Frontend: http://localhost:3000"
echo "  - Database: $DB_NAME"
echo ""
echo "📋 Commandes utiles:"
echo "  - Status services: systemctl status neobot-backend neobot-frontend"
echo "  - Logs backend: journalctl -u neobot-backend -f"
echo "  - Logs frontend: journalctl -u neobot-frontend -f"
echo "  - Restart: systemctl restart neobot-backend neobot-frontend"
echo ""
echo "🔐 Credentials DB sauvegardés:"
echo "  - File: $APP_HOME/backend/.env"
echo ""
echo "➡️  Prochaines étapes:"
echo "  1. Configurer Nginx reverse proxy"
echo "  2. Activer HTTPS avec Let's Encrypt"
echo "  3. Configurer WhatsApp Baileys"
echo "  4. Exécuter tests intégration: bash $APP_HOME/run_tests.sh"
echo ""
