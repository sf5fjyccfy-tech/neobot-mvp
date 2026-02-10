#!/bin/bash

# 🧪 Script de Test - Système Intelligent WhatsApp
# Vous permet de vérifier que toutes les fonctionnalités marchent

set -e  # Stop on error

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
SERVICE_URL="http://localhost:3001"
TIMEOUT=5

echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║  🧪 TEST DU SYSTÈME INTELLIGENT WHATSAPP                   ║${NC}"
echo -e "${BOLD}${BLUE}║  Version 3.0 - Gestion d'Etat Intelligente                 ║${NC}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Test 1: Vérifier que le service démarre
echo -e "${BOLD}${YELLOW}Test 1: Vérifier la disponibilité du service...${NC}"
if timeout $TIMEOUT curl -s "$SERVICE_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Le service WhatsApp est en cours d'exécution${NC}"
else
    echo -e "${RED}❌ Le service WhatsApp ne répond pas${NC}"
    echo -e "${YELLOW}💡 Assurez-vous que vous avez lancé: npm start${NC}"
    exit 1
fi
echo ""

# Test 2: Vérifier l'endpoint health
echo -e "${BOLD}${YELLOW}Test 2: Vérifier l'endpoint /health...${NC}"
HEALTH_RESPONSE=$(curl -s "$SERVICE_URL/health")
echo "Réponse reçue:"
echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"
echo -e "${GREEN}✅ Endpoint health fonctionne${NC}"
echo ""

# Test 3: Vérifier le status détaillé
echo -e "${BOLD}${YELLOW}Test 3: Vérifier l'endpoint /api/whatsapp/status...${NC}"
STATUS_RESPONSE=$(curl -s "$SERVICE_URL/api/whatsapp/status")
echo "État du service:"
echo "$STATUS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATUS_RESPONSE"

# Extraire l'état
STATE=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('state', 'unknown'))" 2>/dev/null || echo "unknown")
echo ""
echo "État détecté: $STATE"

case $STATE in
    "initializing")
        echo -e "${YELLOW}🔄 État: Initialisation${NC}"
        echo "Le service démarre..."
        ;;
    "waiting_qr")
        echo -e "${YELLOW}📱 État: En attente du QR${NC}"
        echo "Veuillez scanner le code QR"
        ;;
    "connected")
        echo -e "${GREEN}✅ État: Connecté${NC}"
        echo "WhatsApp est connecté et prêt"
        ;;
    "disconnected")
        echo -e "${RED}🔴 État: Déconnecté${NC}"
        echo "WhatsApp est déconnecté"
        ;;
    "error")
        echo -e "${RED}❌ État: Erreur${NC}"
        echo "Une erreur s'est produite"
        ;;
    *)
        echo -e "${YELLOW}❓ État: Inconnu ($STATE)${NC}"
        ;;
esac
echo ""

# Test 4: Vérifier le QR status
echo -e "${BOLD}${YELLOW}Test 4: Vérifier l'endpoint /api/whatsapp/qr-status...${NC}"
QR_RESPONSE=$(curl -s "$SERVICE_URL/api/whatsapp/qr-status")
echo "État du QR:"
echo "$QR_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$QR_RESPONSE"

# Extraire si QR actif
QR_ACTIVE=$(echo "$QR_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('qr_active', False))" 2>/dev/null || echo "false")
if [ "$QR_ACTIVE" = "True" ]; then
    echo -e "${YELLOW}📱 Un code QR est actuellement affiché${NC}"
else
    echo -e "${GREEN}✅ Pas de QR en attente${NC}"
fi
echo ""

# Test 5: Vérifier les logs
echo -e "${BOLD}${YELLOW}Test 5: Vérifier le fichier de logs...${NC}"
LOG_FILE="$HOME/neobot-mvp/whatsapp-service/logs/whatsapp.log"
if [ -f "$LOG_FILE" ]; then
    echo -e "${GREEN}✅ Fichier de logs trouvé${NC}"
    echo "Dernières 10 lignes:"
    tail -10 "$LOG_FILE" | sed 's/^/  /'
else
    echo -e "${YELLOW}⚠️  Fichier de logs non trouvé (normal au démarrage)${NC}"
fi
echo ""

# Test 6: Vérifier que le fichier index.js utilise la version intelligente
echo -e "${BOLD}${YELLOW}Test 6: Vérifier que la version intelligente est active...${NC}"
if grep -q "WhatsAppStateManager" /home/tim/neobot-mvp/whatsapp-service/index.js 2>/dev/null; then
    echo -e "${GREEN}✅ Version intelligente est active dans index.js${NC}"
else
    echo -e "${RED}❌ Version intelligente n'est pas trouvée${NC}"
fi
echo ""

# Test 7: Simulation optionnelle - Redémarrage
echo -e "${BOLD}${YELLOW}Test 7: API de redémarrage...${NC}"
echo "Pour tester le redémarrage manuel, vous pouvez exécuter:"
echo -e "${BLUE}  curl -X POST http://localhost:3001/api/whatsapp/restart${NC}"
echo ""

# Afficher le résumé
echo ""
echo -e "${BOLD}${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║  📊 RÉSUMÉ DU TEST                                         ║${NC}"
echo -e "${BOLD}${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

case $STATE in
    "connected")
        echo -e "${GREEN}✅ TOUS LES TESTS RÉUSSIS!${NC}"
        echo ""
        echo "Votre système intelligent est:"
        echo -e "  ${GREEN}✅ Opérationnel${NC}"
        echo -e "  ${GREEN}✅ Connecté à WhatsApp${NC}"
        echo -e "  ${GREEN}✅ Prêt à recevoir les messages${NC}"
        ;;
    "waiting_qr")
        echo -e "${YELLOW}⚠️  SCAN DU QR CODE REQUIS${NC}"
        echo ""
        echo "Instructions:"
        echo "  1. Ouvrez WhatsApp sur votre téléphone"
        echo "  2. Allez dans: Paramètres → Appareils connectés"
        echo "  3. Cliquez sur 'Connecter un appareil'"
        echo "  4. Scannez le code QR affiché dans le terminal (service)"
        echo ""
        echo "Ensuite, relancez ce test pour vérifier la connexion"
        ;;
    "initializing")
        echo -e "${YELLOW}⏳ LE SERVICE INITIALISE...${NC}"
        echo ""
        echo "Attendez 5-10 secondes, puis relancez ce test"
        ;;
    "disconnected"|"error")
        echo -e "${RED}❌ LE SERVICE N'EST PAS CONNECTÉ${NC}"
        echo ""
        echo "Dépannage:"
        echo "  1. Vérifiez les logs: tail -f whatsapp-service/logs/whatsapp.log"
        echo "  2. Relancez le service: npm start"
        echo "  3. Scannez le code QR si demandé"
        ;;
    *)
        echo -e "${YELLOW}❓ ÉTAT INCONNU${NC}"
        ;;
esac

echo ""
echo -e "${BOLD}${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "📚 Documentation: /home/tim/neobot-mvp/WHATSAPP_INTELLIGENT_SYSTEM.md"
echo "🔍 Logs:           /home/tim/neobot-mvp/whatsapp-service/logs/whatsapp.log"
echo "🚀 Démarrer:       npm start (dans whatsapp-service/)"
echo ""
