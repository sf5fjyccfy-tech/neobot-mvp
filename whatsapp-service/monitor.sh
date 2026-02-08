#!/bin/bash
cd ~/neobot-mvp

echo "📊 DASHBOARD NÉOBOT - $(date)"
echo "=========================================="

# Backend
echo -e "\n🌐 BACKEND FASTAPI:"
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ En ligne: http://localhost:8000"
    echo "   📈 Health: $(curl -s http://localhost:8000/health | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")"
else
    echo "   ❌ Hors ligne"
fi

# WhatsApp Service
echo -e "\n📱 SERVICE WHATSAPP:"
if pgrep -f "node.*whatsapp" > /dev/null; then
    echo "   ✅ Processus en cours: $(pgrep -f "node.*whatsapp")"
    
    # État connexion
    if tail -5 ~/neobot-mvp/whatsapp-service/whatsapp.log 2>/dev/null | grep -q "QR CODE\|SCANNEZ"; then
        echo "   🔄 En attente scan QR"
    elif tail -5 ~/neobot-mvp/whatsapp-service/whatsapp.log 2>/dev/null | grep -q "CONNECTÉ\|✅"; then
        echo "   🎉 Connecté à WhatsApp"
    else
        echo "   ⏳ Initialisation..."
    fi
else
    echo "   ❌ Arrêté"
fi

# Base de données
echo -e "\n🗄️  BASE DE DONNÉES:"
cd ~/neobot-mvp/backend
python3 -c "
from app.database import SessionLocal
from app.models import Tenant, Conversation
db = SessionLocal()
try:
    tenants = db.query(Tenant).count()
    conversations = db.query(Conversation).count()
    print(f'   • Tenants: {tenants}')
    print(f'   • Conversations: {conversations}')
    db.close()
except Exception as e:
    print(f'   ❌ Erreur: {e}')
"

# Logs récents
echo -e "\n📝 LOGS RÉCENTS:"
echo "   Backend:"
tail -3 ~/neobot-mvp/backend/backend.log 2>/dev/null || echo "      (aucun log)"
echo "   WhatsApp:"
tail -3 ~/neobot-mvp/whatsapp-service/whatsapp.log 2>/dev/null || echo "      (aucun log)"

echo -e "\n=========================================="
echo "🔧 COMMANDES:"
echo "   • Arrêter: pkill -f 'uvicorn|node'"
echo "   • Redémarrer: cd ~/neobot-mvp && ./launch_neobot.sh"
echo "   • Voir logs: tail -f ~/neobot-mvp/backend/backend.log"
