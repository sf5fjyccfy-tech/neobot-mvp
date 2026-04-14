#!/usr/bin/env bash
# =============================================================================
# NeoBot — Setup VPS Hetzner (Ubuntu 24.04 LTS)
# =============================================================================
# Exécuter UNE SEULE FOIS en root après la création du VPS :
#   chmod +x setup-server.sh && ./setup-server.sh
#
# Ce script fait :
#   1. Mise à jour système + essentiels
#   2. Installation Docker + Docker Compose plugin
#   3. Configuration UFW (firewall)
#   4. Création du répertoire de travail /opt/neobot
#   5. Instructions pour cloner le repo et configurer le .env
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# Vérifier qu'on est root
[[ $EUID -ne 0 ]] && error "Ce script doit être exécuté en root (su - ou sudo -i)"

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║        NeoBot — Setup VPS Hetzner          ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# =============================================================================
# 1. Mise à jour système
# =============================================================================
info "Mise à jour du système..."
apt-get update -qq
apt-get upgrade -y -qq
apt-get install -y -qq \
    ca-certificates \
    curl \
    gnupg \
    git \
    htop \
    ufw \
    unzip

# =============================================================================
# 2. Installation Docker
# =============================================================================
if command -v docker &>/dev/null; then
    info "Docker déjà installé : $(docker --version)"
else
    info "Installation Docker..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
      https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
      > /etc/apt/sources.list.d/docker.list

    apt-get update -qq
    apt-get install -y -qq \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin

    systemctl enable docker
    systemctl start docker
    info "Docker installé : $(docker --version)"
fi

# Vérifier docker compose plugin
docker compose version &>/dev/null || error "docker compose plugin non disponible"
info "Docker Compose plugin OK"

# =============================================================================
# 3. Configuration UFW (firewall)
# =============================================================================
info "Configuration UFW..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP (Cloudflare)'
ufw allow 443/tcp comment 'HTTPS (Cloudflare)'
# Port 8000 accessible uniquement depuis les IPs Cloudflare
# Note : Cloudflare proxifie en HTTPS → le VPS reçoit du trafic HTTP sur 80 ou 443 selon config
# Pour une config simple sans Nginx (Cloudflare → port 8000 direct) :
ufw allow 8000/tcp comment 'Backend API (Cloudflare only — restreindre si besoin)'
echo "y" | ufw enable
info "UFW activé"
ufw status numbered

# =============================================================================
# 4. Répertoire de travail
# =============================================================================
info "Création /opt/neobot..."
mkdir -p /opt/neobot
mkdir -p /opt/neobot/logs/backend
mkdir -p /opt/neobot/logs/whatsapp
mkdir -p /opt/neobot/auth_info_baileys

# =============================================================================
# 5. Swap (optionnel — 2GB pour éviter OOM sur 4GB RAM)
# =============================================================================
if [[ ! -f /swapfile ]]; then
    info "Création d'un swapfile 2GB..."
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    info "Swap 2GB activé"
else
    info "Swapfile déjà présent"
fi

# =============================================================================
# Fin du provisioning — instructions manuelles
# =============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║              PROVISIONING TERMINÉ ✓                             ║"
echo "║                                                                  ║"
echo "║  PROCHAINES ÉTAPES (dans l'ordre) :                             ║"
echo "║                                                                  ║"
echo "║  1. Cloner le repo dans /opt/neobot :                           ║"
echo "║     cd /opt/neobot                                               ║"
echo "║     git clone https://github.com/TON_ORG/neobot-mvp.git .       ║"
echo "║                                                                  ║"
echo "║  2. Configurer le .env :                                         ║"
echo "║     cp .env.example .env                                         ║"
echo "║     nano .env   ← remplir TOUTES les valeurs CHANGE_THIS        ║"
echo "║                                                                  ║"
echo "║  3. Construire et démarrer les services :                        ║"
echo "║     docker compose build --no-cache                              ║"
echo "║     docker compose up -d                                         ║"
echo "║                                                                  ║"
echo "║  4. Vérifier que tout est UP :                                   ║"
echo "║     docker compose ps                                            ║"
echo "║     docker compose logs -f                                       ║"
echo "║     curl http://localhost:8000/health                            ║"
echo "║                                                                  ║"
echo "║  5. Sur Cloudflare :                                             ║"
echo "║     A record  api.neobot-ai.com → 178.104.163.245               ║"
echo "║     Proxy activé (orange) + SSL/TLS Full (strict)               ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""
