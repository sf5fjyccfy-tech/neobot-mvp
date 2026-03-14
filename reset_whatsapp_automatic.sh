#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════╗
# ║                                                                    ║
# ║  🧹 SYSTÈME AUTOMATIQUE DE NETTOYAGE WHATSAPP (NéoBot)           ║
# ║                                                                    ║
# ║  Détecte et supprime automatiquement les sessions expirées        ║
# ║  Régénère les QR codes et relance le service                     ║
# ║                                                                    ║
# ╚════════════════════════════════════════════════════════════════════╝

set -e

WHATSAPP_DIR="/home/tim/neobot-mvp/whatsapp-service"
LOG_FILE="$WHATSAPP_DIR/cleanup.log"
RESTART_DELAY=2
MAX_CLEANUP_ATTEMPTS=3
CLEANUP_ATTEMPT=0

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ========== FONCTIONS UTILITAIRES ==========

log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" >> "$LOG_FILE"
}

log_console() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${BLUE}[${timestamp}]${NC} ℹ️  ${message}"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[${timestamp}]${NC} ✅ ${message}"
            ;;
        "WARNING")
            echo -e "${YELLOW}[${timestamp}]${NC} ⚠️  ${message}"
            ;;
        "ERROR")
            echo -e "${RED}[${timestamp}]${NC} ❌ ${message}"
            ;;
    esac
}

log_both() {
    local level=$1
    local message=$2
    log_console "$level" "$message"
    log_message "$level" "$message"
}

# ========== DÉTECTION DE SESSION EXPIRÉE ==========

check_session_health() {
    log_console "INFO" "Vérification de la santé de la session..."
    
    # Vérifier les fichiers de session
    local auth_files=$(find "$WHATSAPP_DIR/auth_info_baileys/" -type f 2>/dev/null | wc -l)
    
    if [ $auth_files -gt 0 ]; then
        # Vérifier si le service peut se connecter
        local status=$(curl -s http://localhost:3001/health || echo '{"status":"error"}')
        
        if echo "$status" | grep -q "unhealthy"; then
            log_console "WARNING" "Service unhealthy détecté"
            return 1  # Expirée
        elif echo "$status" | grep -q "error"; then
            log_console "WARNING" "Service inaccessible"
            return 1  # Expirée
        else
            log_console "SUCCESS" "Service healthy"
            return 0  # OK
        fi
    else
        log_console "INFO" "Pas de fichiers de session trouvés"
        return 1  # Pas de session
    fi
}

# ========== STOP SERVICE ==========

stop_whatsapp_service() {
    log_console "INFO" "Arrêt du service WhatsApp..."
    
    # Arrêter par nom de processus
    pkill -f "node.*index.js" 2>/dev/null || true
    pkill -f "npm.*start" 2>/dev/null || true
    
    # Attendre
    sleep 1
    
    # Vérifier si arrêté
    if pgrep -f "node.*index.js" > /dev/null; then
        log_console "WARNING" "Forçage de l'arrêt..."
        pkill -9 -f "node.*index.js" 2>/dev/null || true
    fi
    
    sleep 1
    log_console "SUCCESS" "Service WhatsApp arrêté"
    log_message "INFO" "Service WhatsApp arrêté"
}

# ========== SUPPRESSION DES SESSIONS ==========

cleanup_sessions() {
    log_console "INFO" "Suppression des sessions expirées..."
    local removed=0
    
    # Dossiers à supprimer
    local dirs=(
        "$WHATSAPP_DIR/auth_info_baileys"
        "$WHATSAPP_DIR/.wwebjs_auth"
        "$WHATSAPP_DIR/session"
        "/home/tim/neobot-mvp/auth_info_baileys"
    )
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            log_console "INFO" "Suppression: $dir"
            rm -rf "$dir"
            ((removed++))
            log_message "INFO" "Supprimé: $dir"
        fi
    done
    
    # Supprimer fichiers de timeout
    if [ -f "$WHATSAPP_DIR/session_timeouts.json" ]; then
        rm "$WHATSAPP_DIR/session_timeouts.json"
        ((removed++))
        log_console "INFO" "Suppression: session_timeouts.json"
    fi
    
    log_console "SUCCESS" "Nettoyage terminé ($removed dossiers/fichiers)"
    log_message "INFO" "Nettoyage terminé - $removed éléments supprimés"
    
    return 0
}

# ========== VÉRIFICATION ==========

verify_cleanup() {
    log_console "INFO" "Vérification du nettoyage..."
    
    local still_exist=0
    local dirs=(
        "$WHATSAPP_DIR/auth_info_baileys"
        "$WHATSAPP_DIR/.wwebjs_auth"
        "$WHATSAPP_DIR/session"
    )
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir" ]; then
            log_console "WARNING" "Dossier encore existant: $dir"
            ((still_exist++))
        fi
    done
    
    if [ $still_exist -eq 0 ]; then
        log_console "SUCCESS" "Tous les fichiers ont été supprimés"
        return 0
    else
        log_console "ERROR" "$still_exist dossiers n'ont pas pu être supprimés"
        return 1
    fi
}

# ========== REDÉMARRAGE ==========

restart_whatsapp_service() {
    log_console "INFO" "Redémarrage du service WhatsApp..."
    
    cd "$WHATSAPP_DIR"
    
    # Vérifier package.json
    if [ ! -f "package.json" ]; then
        log_console "ERROR" "package.json non trouvé"
        return 1
    fi
    
    # Démarrer en background
    nohup npm start > whatsapp.log 2>&1 &
    local pid=$!
    
    echo $pid > whatsapp.pid
    log_console "SUCCESS" "Service WhatsApp démarré (PID: $pid)"
    log_message "INFO" "Service démarré avec PID: $pid"
    
    # Attendre le démarrage
    sleep 3
    
    # Vérifier si démarré
    if pgrep -f "node.*index.js" > /dev/null; then
        log_console "SUCCESS" "Service vérifié en cours d'exécution"
        return 0
    else
        log_console "ERROR" "Service n'a pas démarré"
        return 1
    fi
}

# ========== ATTENDRE NOUVEAU QR ==========

wait_for_qr() {
    log_console "INFO" "En attente du nouveau QR code..."
    
    local max_wait=120  # 2 minutes
    local elapsed=0
    
    while [ $elapsed -lt $max_wait ]; do
        if grep -q "SCANNER LE CODE QR" "$WHATSAPP_DIR/whatsapp.log" 2>/dev/null; then
            log_console "SUCCESS" "QR code généré avec succès!"
            log_console "INFO" "Veuillez scanner le code QR avec votre WhatsApp"
            return 0
        fi
        
        sleep 2
        ((elapsed+=2))
        echo -ne "\r⏳ Attente: ${elapsed}s / ${max_wait}s"
    done
    
    echo ""
    log_console "WARNING" "Timeout en attente du QR code"
    return 1
}

# ========== FONCTION PRINCIPALE ==========

run_cleanup() {
    log_console "INFO" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_console "INFO" "Démarrage du nettoyage automatique des sessions..."
    log_console "INFO" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 1. Vérifier la santé
    if check_session_health; then
        log_console "SUCCESS" "Session saine, pas de nettoyage nécessaire"
        return 0
    fi
    
    # 2. Arrêter le service
    stop_whatsapp_service
    
    # 3. Supprimer les sessions
    if ! cleanup_sessions; then
        ((CLEANUP_ATTEMPT++))
        if [ $CLEANUP_ATTEMPT -lt $MAX_CLEANUP_ATTEMPTS ]; then
            log_console "WARNING" "Nouvelle tentative de nettoyage..."
            sleep 2
            run_cleanup
            return
        fi
    fi
    
    # 4. Vérifier le nettoyage
    if ! verify_cleanup; then
        log_console "ERROR" "Nettoyage incomplet - tentative forcée"
        for dir in "$WHATSAPP_DIR/auth_info_baileys" "$WHATSAPP_DIR/.wwebjs_auth"; do
            sudo rm -rf "$dir" 2>/dev/null || true
        done
    fi
    
    # 5. Redémarrer
    sleep $RESTART_DELAY
    if ! restart_whatsapp_service; then
        log_console "ERROR" "Impossible de redémarrer le service"
        return 1
    fi
    
    # 6. Attendre le QR
    wait_for_qr
    
    log_console "SUCCESS" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_console "SUCCESS" "Nettoyage et redémarrage terminés!"
    log_console "SUCCESS" "Vérifiez les logs: tail -f $LOG_FILE"
    log_console "SUCCESS" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ========== MODE CRON (AUTOMATIQUE) ==========

run_cron_check() {
    # Appelé par cron toutes les heures
    # Arrête le service uniquement si vraiment expirée
    if ! check_session_health; then
        log_both "WARNING" "Session expirée détectée en vérification cron"
        run_cleanup
    fi
}

# ========== MAIN ==========

# Créer le répertoire de logs
mkdir -p "$WHATSAPP_DIR"

case "${1:-manual}" in
    "manual")
        run_cleanup
        ;;
    "cron")
        run_cron_check
        ;;
    *)
        echo "Usage: $0 [manual|cron]"
        echo "  manual - Nettoyage immédiat et redémarrage"
        echo "  cron   - Vérification périodique (pour cron)"
        exit 1
        ;;
esac
