#!/bin/bash
# NéoBot — Démarrage de tous les services
# Usage: ./start.sh [--no-frontend]

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$ROOT_DIR/logs"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${GREEN}[START]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

# Attend qu'un port soit en écoute
# Frontend Next.js peut prendre jusqu'à 90s pour compiler au premier démarrage
wait_port() {
  local port=$1 name=$2
  local max=${3:-60}  # timeout en secondes, 60 par défaut
  local i=0
  while ! ss -tlnp 2>/dev/null | grep -q ":$port"; do
    sleep 1; i=$((i+1))
    [ $i -ge $max ] && err "$name (port $port) n'a pas démarré en ${max}s — voir logs/$name.log" && return 1
  done
  log "$name UP sur le port $port (${i}s)"
}

# ─── 1. Backend FastAPI ────────────────────────────────────────────────────────
log "Démarrage du backend FastAPI (port 8000)..."
# Vérification réelle via health check (pas juste le port — un zombie peut tenir le port sans répondre)
if curl -s --max-time 2 http://localhost:8000/health | grep -q '"status"'; then
  warn "Backend déjà actif et responsive sur le port 8000, skip."
else
  # Tuer proprement tout processus zombie sur le port 8000 avant de relancer
  fuser -k 8000/tcp 2>/dev/null || true
  cd "$ROOT_DIR"
  VENV="$ROOT_DIR/.venv/bin/activate"
  if [ ! -f "$VENV" ]; then
    VENV="$ROOT_DIR/backend/.venv/bin/activate"
  fi
  if [ ! -f "$VENV" ]; then
    err "venv introuvable — relancer depuis le répertoire du projet"
    exit 1
  fi
  source "$VENV"
  cd "$ROOT_DIR/backend"
  nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload \
    > "$ROOT_DIR/logs/backend.log" 2>&1 &
  echo $! > "$ROOT_DIR/logs/backend.pid"
  wait_port 8000 "backend" 120
fi

# ─── 2. WhatsApp Service Node.js ──────────────────────────────────────────────
log "Démarrage du service WhatsApp (port 3001)..."
if ss -tlnp 2>/dev/null | grep -q ':3001'; then
  warn "Service WhatsApp déjà en écoute sur le port 3001, skip."
else
  cd "$ROOT_DIR/whatsapp-service"
  nohup node --import ./instrument.js whatsapp-production.js \
    > "$ROOT_DIR/logs/whatsapp.log" 2>&1 &
  echo $! > "$ROOT_DIR/logs/whatsapp.pid"
  wait_port 3001 "whatsapp"
fi

# ─── 3. Frontend Next.js ──────────────────────────────────────────────────────
if [[ "$1" != "--no-frontend" ]]; then
  log "Démarrage du frontend Next.js (port 3002)..."
  if ss -tlnp 2>/dev/null | grep -q ':3002'; then
    warn "Frontend déjà en écoute sur le port 3002, skip."
  else
    cd "$ROOT_DIR/frontend"
    nohup npm run dev \
      > "$ROOT_DIR/logs/frontend.log" 2>&1 &
    echo $! > "$ROOT_DIR/logs/frontend.pid"
    info "Frontend Next.js démarre (compilation ~60s au premier lancement)..."
    wait_port 3002 "frontend" 90
  fi
fi

echo ""
log "═══════════════════════════════════════════"
log " NeoBot est PRÊT"
log "═══════════════════════════════════════════"
echo "  • Backend   → http://localhost:8000"
echo "  • WhatsApp  → http://localhost:3001"
echo "  • Frontend  → http://localhost:3002"
echo ""
echo "  Logs  : tail -f $ROOT_DIR/logs/*.log"
echo "  Arrêt : ./stop.sh"
