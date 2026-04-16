#!/bin/bash
# =============================================================================
# NéoBot — Script de déploiement complet VPS Hetzner
# Usage : bash deploy-vps.sh
# Exécuter en tant que root sur le VPS
# =============================================================================
set -euo pipefail

REPO_URL="https://github.com/sf5fjyccfy-tech/neobot-mvp.git"
APP_DIR="/opt/neobot"
DOMAIN_API="api.neobot-ai.com"
EMAIL_SSL="timpatrick561@gmail.com"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║     NéoBot — Déploiement VPS Hetzner         ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ─── 1. Mise à jour système ───────────────────────────────────────────────────
log "Mise à jour du système..."
apt-get update -qq && apt-get upgrade -y -qq

# ─── 2. Dépendances système ───────────────────────────────────────────────────
log "Installation des dépendances système..."
apt-get install -y -qq \
    curl wget git nginx certbot python3-certbot-nginx \
    ca-certificates gnupg lsb-release ufw fail2ban

# ─── 3. Docker ────────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    log "Installation de Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    log "Docker déjà installé : $(docker --version)"
fi

# Docker Compose v2
if ! docker compose version &>/dev/null; then
    log "Installation de Docker Compose v2..."
    apt-get install -y -qq docker-compose-plugin
fi
log "Docker Compose : $(docker compose version)"

# ─── 4. Firewall UFW ─────────────────────────────────────────────────────────
log "Configuration du firewall UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
log "Firewall activé (SSH + HTTP + HTTPS)"

# ─── 5. Fail2ban ─────────────────────────────────────────────────────────────
log "Activation de Fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

# ─── 6. Clone / mise à jour du repo ──────────────────────────────────────────
if [ -d "$APP_DIR/.git" ]; then
    log "Mise à jour du repo existant..."
    cd "$APP_DIR"
    git fetch origin
    git reset --hard origin/main
    git pull origin main
else
    log "Clonage du repo..."
    mkdir -p "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# ─── 7. Créer les répertoires nécessaires ────────────────────────────────────
log "Création des répertoires..."
mkdir -p "$APP_DIR/logs/backend"
mkdir -p "$APP_DIR/logs/whatsapp"
mkdir -p "$APP_DIR/auth_info_baileys"
mkdir -p /var/www/certbot

# ─── 8. Vérifier que le .env existe ──────────────────────────────────────────
if [ ! -f "$APP_DIR/.env" ]; then
    err "Fichier .env manquant dans $APP_DIR ! Copiez-le manuellement puis relancez."
fi
log "Fichier .env trouvé ✓"

# ─── 9. Build et démarrage Docker ────────────────────────────────────────────
log "Build et démarrage des containers Docker..."
cd "$APP_DIR"
docker compose down --remove-orphans 2>/dev/null || true
docker compose pull 2>/dev/null || true
docker compose up -d --build backend whatsapp

log "Attente du démarrage du backend (30s)..."
sleep 30

# Vérifier le health check
HEALTH=$(curl -sf http://localhost:8000/health 2>/dev/null || echo "FAIL")
if echo "$HEALTH" | grep -q "healthy"; then
    log "Backend opérationnel ✓"
else
    warn "Backend pas encore prêt — vérifiez : docker compose logs backend"
fi

# ─── 10. Nginx — config temporaire HTTP (pour Certbot) ───────────────────────
log "Configuration Nginx temporaire (HTTP)..."
cat > /etc/nginx/sites-available/neobot-api << 'NGINX_HTTP'
server {
    listen 80;
    listen [::]:80;
    server_name api.neobot-ai.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        client_max_body_size 20M;
    }
}
NGINX_HTTP

ln -sf /etc/nginx/sites-available/neobot-api /etc/nginx/sites-enabled/neobot-api
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx
log "Nginx HTTP configuré ✓"

# ─── 11. SSL Let's Encrypt ───────────────────────────────────────────────────
log "Obtention du certificat SSL Let's Encrypt..."
certbot --nginx \
    -d "$DOMAIN_API" \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL_SSL" \
    --redirect

log "SSL configuré ✓"

# ─── 12. Config Nginx finale (HTTPS) ─────────────────────────────────────────
log "Application de la config Nginx finale..."
cp "$APP_DIR/nginx/neobot-ai.com.conf" /etc/nginx/sites-available/neobot-api
nginx -t && systemctl reload nginx
log "Nginx HTTPS configuré ✓"

# ─── 13. Renouvellement SSL automatique ──────────────────────────────────────
log "Configuration du renouvellement SSL automatique..."
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && systemctl reload nginx") | sort -u | crontab -

# ─── 14. Vérification finale ─────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║          VÉRIFICATION FINALE                 ║"
echo "╚══════════════════════════════════════════════╝"

echo ""
log "Containers Docker :"
docker compose -f "$APP_DIR/docker-compose.yml" ps

echo ""
log "Test health check local :"
curl -sf http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "En démarrage..."

echo ""
log "Test HTTPS :"
curl -sf https://api.neobot-ai.com/health | python3 -m json.tool 2>/dev/null || warn "HTTPS pas encore disponible (propagation DNS ?)"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║  ✅ DÉPLOIEMENT TERMINÉ                      ║"
echo "║                                              ║"
echo "║  API : https://api.neobot-ai.com             ║"
echo "║  Health : https://api.neobot-ai.com/health   ║"
echo "║  Logs : docker compose logs -f backend       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
