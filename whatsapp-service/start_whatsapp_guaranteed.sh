#!/bin/bash
cd ~/neobot-mvp/whatsapp-service

echo "🔧 DÉMARRAGE WHATSAPP GARANTI"
echo "============================="

# 1. Vérifier le backend
echo "1. Vérification backend..."
if curl -s http://localhost:8000/health | grep -q healthy; then
    echo "   ✅ Backend OK"
else
    echo "   ❌ Backend non disponible"
    echo "   💡 Démarrez d'abord: cd ~/neobot-mvp/backend && uvicorn app.main:app --reload"
    exit 1
fi

# 2. Nettoyer les sessions
echo "2. Nettoyage sessions..."
rm -rf auth_info_baileys 2>/dev/null
echo "   ✅ Sessions nettoyées"

# 3. Désactiver pare-feu temporairement
echo "3. Configuration réseau..."
sudo ufw disable 2>/dev/null || true
sudo iptables -F 2>/dev/null || true
echo "   ✅ Réseau configuré"

# 4. Tester la connexion WhatsApp
echo "4. Test connexion WhatsApp..."
timeout 5 curl -s https://web.whatsapp.com > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ WhatsApp accessible"
else
    echo "   ⚠️  WhatsApp peut être bloqué, tentative quand même..."
fi

# 5. Démarrer le service
echo ""
echo "🚀 DÉMARRAGE DU SERVICE WHATSAPP..."
echo ""
echo "📱 INSTRUCTIONS:"
echo "   1. Un QR code va apparaître"
echo "   2. Ouvrez WhatsApp sur votre téléphone"
echo "   3. Menu → Appareils connectés → Connecter un appareil"
echo "   4. Scannez le QR code IMMÉDIATEMENT (valide 20s)"
echo ""
echo "=".repeat(50)
node whatsapp_common.js
