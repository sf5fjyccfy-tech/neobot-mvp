#!/bin/bash
echo "📱 Démarrage NéoBot WhatsApp Service RÉEL"
echo "========================================"

cd whatsapp-service

# Vérifier Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js non installé"
    exit 1
fi

# Vérifier dépendances
if [ ! -d "node_modules" ]; then
    echo "📦 Installation des dépendances..."
    npm install
fi

# Créer dossiers nécessaires
mkdir -p auth_sessions

echo "🚀 Lancement du service WhatsApp..."
echo "📱 API sur: http://localhost:3001"
echo "🔌 WebSocket sur: ws://localhost:3002"
echo ""
node index.js
