#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════╗
# ║            Script de démarrage NéoBot WhatsApp v2                  ║
# ║                   Robust & Auto-healing                            ║
# ╚════════════════════════════════════════════════════════════════════╝

set -e

WHATSAPP_DIR="/home/tim/neobot-mvp/whatsapp-service"
LOG_FILE="$WHATSAPP_DIR/service.log"
PID_FILE="$WHATSAPP_DIR/whatsapp.pid"
CLEANUP_SCRIPT="/home/tim/neobot-mvp/reset_whatsapp_automatic.sh"

cd "$WHATSAPP_DIR"

echo "═══════════════════════════════════════════════════════════════════"
echo "🚀 Démarrage NéoBot WhatsApp Service v2.0"
echo "═══════════════════════════════════════════════════════════════════"

# 1. Vérifier les dépendances
echo "📦 Vérification des dépendances..."
if [ ! -d "node_modules" ]; then
    echo "   Installation de npm packages..."
    npm install
fi

# 2. Arrêter les instances précédentes
echo "🛑 Arrêt des instances précédentes..."
pkill -f "node.*index.js" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
sleep 1

# 3. Vérifier et nettoyer si nécessaire
echo "🔍 Vérification de la santé de la session..."
if [ -f "$CLEANUP_SCRIPT" ]; then
    # Appeler le script avec détection
    bash "$CLEANUP_SCRIPT" cron 2>/dev/null || true
fi

# 4. Créer les dossiers de session
echo "📁 Création des dossiers de session..."
mkdir -p auth_info_baileys
mkdir -p session

# 5. Démarrer avec le nouveau index_fixed.js
echo "▶️  Démarrage du service..."
nohup node index_fixed.js > "$LOG_FILE" 2>&1 &
SERVICE_PID=$!
echo $SERVICE_PID > "$PID_FILE"

# 6. Attendre le démarrage
echo "⏳ Attente du démarrage..."
sleep 3

# 7. Vérifier l'état
if ps -p $SERVICE_PID > /dev/null; then
    echo "✅ Service démarré (PID: $SERVICE_PID)"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "📌 Informations utiles:"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "📊 Voir les logs:"
    echo "   tail -f $LOG_FILE"
    echo ""
    echo "🛑 Arrêter le service:"
    echo "   pkill -f 'node.*index.js'"
    echo ""
    echo "🔄 Forcer un reset:"
    echo "   bash $CLEANUP_SCRIPT manual"
    echo ""
    echo "🌐 Endpoints disponibles:"
    echo "   GET  http://localhost:3001/health"
    echo "   GET  http://localhost:3001/status"
    echo "   POST http://localhost:3001/api/whatsapp/reset-session"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
else
    echo "❌ Erreur: Service n'a pas pu démarrer"
    echo "📋 Vérifiez les logs:"
    tail -20 "$LOG_FILE"
    exit 1
fi
