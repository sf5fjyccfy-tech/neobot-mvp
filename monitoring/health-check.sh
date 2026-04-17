#!/bin/bash
#
# NeoBot Server Health Check & Alert System (Pure Bash version)
# Monitoring des endpoints critiques avec alertes email via Brevo
# Lancé par cron toutes les 5 minutes
#

set -u

# Configuration
BREVO_API_KEY="${BREVO_API_KEY:-}"
ALERT_EMAIL="${ALERT_EMAIL:-timpatrick561@gmail.com}"
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@neobot-ai.com}"
LOG_DIR="/root/neobot-mvp/logs/monitoring"
LOG_FILE="$LOG_DIR/health-check.log"
STATUS_FILE="$LOG_DIR/last_status.txt"

# Créer le répertoire des logs s'il n'existe pas
mkdir -p "$LOG_DIR"

# Fonction de logging
log() {
    local level="$1"
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Fonction pour envoyer une alerte email via Brevo
send_alert_email() {
    local subject="$1"
    local message="$2"
    local is_critical="${3:-false}"
    
    if [ -z "$BREVO_API_KEY" ]; then
        log "WARN" "BREVO_API_KEY not configured, skipping email"
        return 0
    fi
    
    # Construire le JSON payload directement en bash
    local json_payload=$(cat <<'EOF'
{
    "sender": {"name": "NeoBot Monitoring", "email": "ADMIN_EMAIL_HERE"},
    "to": [{"email": "ALERT_EMAIL_HERE", "name": "Tim"}],
    "subject": "SUBJECT_HERE",
    "htmlContent": "HTML_BODY_HERE"
}
EOF
)
    
    # Remplacer les variables
    json_payload="${json_payload//ADMIN_EMAIL_HERE/$ADMIN_EMAIL}"
    json_payload="${json_payload//ALERT_EMAIL_HERE/$ALERT_EMAIL}"
    json_payload="${json_payload//SUBJECT_HERE/$subject}"
    
    local html_escaped=$(echo "<p>$message</p><p style=\"color: #999; font-size: 11px; margin-top: 20px;\">$(date -u '+%Y-%m-%d %H:%M:%S UTC')</p>" | sed 's/"/\\"/g')
    json_payload="${json_payload//HTML_BODY_HERE/$html_escaped}"
    
    local response=$(curl -s -X POST \
        -H "api-key: $BREVO_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$json_payload" \
        "https://api.brevo.com/v3/smtp/email" 2>&1)
    
    if echo "$response" | grep -q 'messageId'; then
        log "INFO" "✅ Alert email sent: $subject"
        return 0
    else
        log "ERROR" "❌ Brevo API error (first 100 chars): ${response:0:100}"
        return 1
    fi
}

# Fonction pour vérifier la santé d'un endpoint
check_endpoint() {
    local name="$1"
    local url="$2"
    local timeout="${3:-10}"
    
    local http_code=$(curl -s -o /dev/null -w '%{http_code}' --max-time "$timeout" -L "$url" 2>/dev/null)
    
    if [ "$http_code" -lt 400 ]; then
        echo "healthy"
        return 0
    else
        echo "down:$http_code"
        return 1
    fi
}

# Récupérer le statut d'une clé depuis le fichier
get_status_value() {
    local key="$1"
    if [ -f "$STATUS_FILE" ]; then
        grep "^${key}=" "$STATUS_FILE" 2>/dev/null | cut -d'=' -f2 || echo "unknown"
    else
        echo "unknown"
    fi
}

# Main
main() {
    log "INFO" "========================================================"
    log "INFO" "🔍 Starting health check..."
    
    local all_healthy=true
    local new_status=""
    local tmp_status_file="${STATUS_FILE}.tmp"
    
    # Endpoints à vérifier
    declare -a endpoint_names=("Frontend" "Backend Internal")
    declare -a endpoint_urls=("https://neobot-ai.com/" "http://localhost:8000/health")
    
    # Vérifier chaque endpoint
    for i in "${!endpoint_names[@]}"; do
        local name="${endpoint_names[$i]}"
        local url="${endpoint_urls[$i]}"
        local result=$(check_endpoint "$name" "$url" 10)
        
        if [ "$result" = "healthy" ]; then
            log "INFO" "✅ HEALTHY - $name"
            echo "${name}=true" >> "$tmp_status_file"
        else
            log "WARN" "❌ DOWN - $name (HTTP ${result#*:})"
            all_healthy=false
            echo "${name}=false" >> "$tmp_status_file"
            
            # Vérifier si c'est une nouvelle défaillance
            local was_healthy=$(get_status_value "$name")
            if [ "$was_healthy" != "false" ]; then
                # Première fois que c'est down → envoyer alerte
                local alert_msg="$name is not responding. URL: $url. Action: SSH to VPS and check containers."
                send_alert_email "🚨 NeoBot Alert: $name is DOWN" "$alert_msg" "true"
            fi
        fi
    done
    
    # Vérifier les récupérations
    if [ -f "$STATUS_FILE" ]; then
        while IFS='=' read -r key val; do
            [ -z "$key" ] && continue
            local was_healthy="$val"
            local current=$(get_status_value "$key" < "$tmp_status_file" || echo "unknown")
            
            if [ "$was_healthy" = "false" ] && [ "$current" = "true" ]; then
                log "INFO" "✅ $key RECOVERED"
                local recovery_msg="$key has recovered and is responding normally."
                send_alert_email "✅ NeoBot Alert: $key is BACK ONLINE" "$recovery_msg" "false"
            fi
        done < "$STATUS_FILE"
    fi
    
    # Sauvegarder le nouveau statut
    mv "$tmp_status_file" "$STATUS_FILE" 2>/dev/null || true
    
    # Résumé
    if [ "$all_healthy" = "true" ]; then
        log "INFO" "✅ All systems healthy"
    else
        log "WARN" "⚠️  Some systems are down"
    fi
    
    log "INFO" "========================================================"
}

main "$@"
