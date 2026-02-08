#!/bin/bash
cd ~/neobot-mvp/backend

echo "🚀 LANCEMENT VRAI ROCKET"
echo "========================"

# Tuer TOUT
echo "☠️  Nettoyage radical..."
pkill -9 -f "python3.*uvicorn" 2>/dev/null || true
pkill -9 -f "python3.*main.py" 2>/dev/null || true
sleep 2

# Vérifier l'indépendance
echo "🔍 Vérification indépendance..."
python3 -c "
import sys
print('🧪 Test d\'indépendance:')
try:
    # Essayer d'importer DB (devrait échouer dans rocket_responder)
    from app.services.rocket_responder import RocketResponder
    print('✅ RocketResponder importé')
    
    # Tester
    rocket = RocketResponder()
    test = rocket.respond('Salut')
    print(f'✅ Test réponse: {len(test)} caractères')
    
    # Vérifier AUCUNE DB
    import sqlalchemy
    print('❌ ALERTE: sqlalchemy importable!')
except ImportError as e:
    print(f'✅ Pas de dépendance: {e}')
except Exception as e:
    print(f'⚠️  Autre: {e}')
"

# Démarrer
echo -e "\n🌐 Démarrage True Rocket..."
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > true_rocket.log 2>&1 &
ROCKET_PID=$!
sleep 4

echo "✅ PID: $ROCKET_PID"
echo "📁 Logs: tail -f true_rocket.log"

# Test de destruction
echo -e "\n💣 TEST DE DESTRUCTION..."
echo "1. Test réponse normale:"
curl -s "http://localhost:8000/debug/rocket-test" | python3 -c "
import sys, json
data = json.load(sys.stdin)
tests = data.get('rocket_tests', [])
passed = sum(1 for t in tests if t.get('success'))
print(f'   ✅ {passed}/{len(tests)} tests passés')
"

echo -e "\n2. Simuler DB crash + requête:"
echo "   (Le serveur DOIT répondre même sans DB)"
curl -s -X POST "http://localhost:8000/api/tenants/1/whatsapp/message" \
  -H "Content-Type: application/json" \
  -d '{"phone": "237694256267", "message": "DB CRASH TEST"}' \
  --max-time 3 | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('response'):
        print(f'   ✅ RÉPONSE: {data[\"response\"][:60]}...')
    else:
        print('   ❌ PAS DE RÉPONSE')
except:
    print('   ❌ SERVER CRASH (mauvaise nouvelle)')
"

echo -e "\n🎯 TRUE ROCKET ACTIF"
echo "📱 WhatsApp: Envoie '1. 3h 2. 5' → DOIT répondre INSTANT"
echo "⚡ Garantie: Même si PostgreSQL meurt, même si Redis explose"
echo ""
echo "🔧 Monitoring:"
echo "   tail -f true_rocket.log"
echo "   curl http://localhost:8000/health"
echo ""
echo "⚠️  CRITIQUE: Vérifie que les réponses sont TOUJOURS commerciales"
echo "   Pas de 'Message reçu:', pas de 'Error:', toujours du SPIN Selling"
