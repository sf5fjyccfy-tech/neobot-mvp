#!/bin/bash

echo "🔄 Arrêt des processus existants..."
# Kill any process using port 3001
fuser -k 3001/tcp 2>/dev/null
sleep 1

# Final cleanup - remove any lingering npm processes
pkill -9 -f "whatsapp-production" 2>/dev/null
pkill -9 -f "whatsapp-service-v6-dual-mode" 2>/dev/null
pkill -9 -f "whatsapp-service-v7-professional" 2>/dev/null
pkill -9 -f "whatsapp-optimized" 2>/dev/null
sleep 1

echo "✅ Nettoyage des sessions..."
rm -rf auth_info_baileys .wwebjs_auth session sessions.json 2>/dev/null

echo "🚀 Démarrage du service NéoBot WhatsApp..."
echo ""

# Start with explicit error handling
cd "$(dirname "$0")" || exit 1
exec node whatsapp-production.js
