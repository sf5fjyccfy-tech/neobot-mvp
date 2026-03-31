#!/usr/bin/env bash
# NeoBot — Script d'arrêt
# Tue proprement les 3 services via les fichiers .pid
# Usage : ./stop.sh

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[STOP]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

STOPPED=0

for pid_file in "$ROOT_DIR/logs/backend.pid" "$ROOT_DIR/logs/whatsapp.pid" "$ROOT_DIR/logs/frontend.pid"; do
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        SERVICE=$(basename "$pid_file" .pid)
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            log "Service '$SERVICE' arrêté (PID $PID)"
            STOPPED=$((STOPPED + 1))
        else
            warn "Service '$SERVICE' déjà arrêté (PID $PID introuvable)"
        fi
        rm -f "$pid_file"
    fi
done

# Nettoyage des processus orphelins par port (sécurité)
for PORT in 8000 3001 3002; do
    PIDS=$(lsof -ti ":$PORT" 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo "$PIDS" | xargs kill 2>/dev/null || true
        warn "Processus orphelins sur le port $PORT terminés"
    fi
done

if [ "$STOPPED" -eq 0 ]; then
    warn "Aucun service NeoBot actif trouvé."
else
    log "$STOPPED service(s) arrêté(s)."
fi
