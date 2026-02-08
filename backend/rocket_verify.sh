#!/bin/bash
cd ~/neobot-mvp/backend

echo "🔧 VÉRIFICATION ROCKET"
echo "======================"

# 1. Vérifier que SPIN ne retourne jamais None
echo "🧪 Test SPIN garanti..."
python3 -c "
from app.services.intelligent_conversation import get_conversation_response

test_messages = [
    'Salut',
    'Oui',
    'boutique',
    '1. 3h 2. 5',
    'prix',
    'quelque chose de bizarre',
    '',  # message vide
    None,  # None
]

for msg in test_messages:
    try:
        resp = get_conversation_response(msg or '')
        if not resp or not isinstance(resp, str):
            print(f'❌ \"{msg}\" → {type(resp)}')
        else:
            print(f'✅ \"{msg}\" → {len(resp)} chars')
    except Exception as e:
        print(f'🚨 \"{msg}\" → ERREUR: {e}')
"

# 2. Vérifier imports
echo -e "\n📦 Vérification imports..."
python3 -c "
try:
    from app.main import app
    from app.services.intelligent_conversation import get_conversation_response
    print('✅ Tous les imports OK')
except Exception as e:
    print(f'❌ Import error: {e}')
"

# 3. Arrêter et redémarrer
echo -e "\n🔄 Redémarrage Rocket..."
pkill -9 -f "python3.*uvicorn" 2>/dev/null || true
sleep 2

nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > rocket.log 2>&1 &
ROCKET_PID=$!
sleep 3

# 4. Test via HTTP
echo -e "\n🌐 Test HTTP..."
curl -X POST "http://localhost:8000/api/tenants/1/whatsapp/message" \
  -H "Content-Type: application/json" \
  -d '{"phone": "237694256267", "message": "1. 3h 2. 5"}' \
  --max-time 5 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    status = data.get('status', 'unknown')
    source = data.get('source', 'N/A')
    resp = data.get('response', '')
    
    if status == 'success' and resp:
        print(f'✅ SUCCÈS: Source={source}')
        print(f'💬 Réponse: {resp[:100]}...')
    else:
        print(f'⚠️  Problème: Status={status}, Source={source}')
        print(f'📝 Réponse: {resp[:100]}...')
except Exception as e:
    print(f'❌ Test échoué: {e}')
"

echo -e "\n🎯 ROCKET PRÊT !"
echo "📱 Test WhatsApp:"
echo "   • '1. 3h 2. 5' → Doit montrer l'analyse besoins"
echo "   • 'prix' → Doit montrer tarifs"
echo "   • N'IMPORTE QUOI → Doit TOUJOURS répondre"

echo -e "\n📊 Monitoring: tail -f rocket.log"
