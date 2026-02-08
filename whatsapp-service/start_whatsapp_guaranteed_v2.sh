#!/bin/bash
cd ~/neobot-mvp/whatsapp-service

echo "🚀 WHATSAPP NÉOBOT - VERSION GARANTIE"
echo "====================================="

# 1. Nettoyer
echo "🧹 Nettoyage..."
rm -rf .wwebjs_auth 2>/dev/null

# 2. Vérifier dépendances
echo "📦 Vérification whatsapp-web.js..."
if [ ! -d "node_modules/whatsapp-web.js" ]; then
    echo "   Installation whatsapp-web.js..."
    npm install whatsapp-web.js qrcode-terminal axios
fi

# 3. Vérifier backend
echo "🔍 Vérification backend..."
if curl -s http://localhost:8000/health | grep -q healthy; then
    echo "   ✅ Backend OK"
else
    echo "   ❌ Backend arrêté"
    echo "   💡 Démarrez: cd ~/neobot-mvp/backend && uvicorn app.main:app --reload"
    exit 1
fi

# 4. Démarrer
echo ""
echo "📱 DÉMARRAGE WHATSAPP..."
echo ""
echo "INSTRUCTIONS:"
echo "1. Un QR code va apparaître"
echo "2. Scannez-le AVEC WHATSAPP sur votre téléphone"
echo "3. Attendez 'CONNECTÉ À WHATSAPP !'"
echo "4. Testez en envoyant un message"
echo ""
echo "=".repeat(50)

node whatsapp_working.js
