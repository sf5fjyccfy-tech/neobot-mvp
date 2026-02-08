#!/bin/bash

echo "════════════════════════════════════════════════════════════════"
echo "🔍 VÉRIFICATION COMPLÈTE DU SYSTÈME NÉOBOT"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction de vérification
check_service() {
    local name=$1
    local url=$2
    local expected_status=$3
    
    echo -n "Vérification $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_status" ] || [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ OK (HTTP $response)${NC}"
        return 0
    else
        echo -e "${RED}❌ ERREUR (HTTP $response)${NC}"
        return 1
    fi
}

check_port() {
    local port=$1
    local name=$2
    
    echo -n "Vérification port $port ($name)... "
    
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}✅ OUVERT${NC}"
        return 0
    else
        echo -e "${RED}❌ FERMÉ${NC}"
        return 1
    fi
}

# =================== VÉRIFICATION 1 ===================
echo -e "${BLUE}═══════ VÉRIFICATION 1: PORTS ET CONNEXIONS DE BASE ═══════${NC}"
echo ""

check_port 8000 "Backend"
BACKEND=$?

check_port 3001 "WhatsApp"
WHATSAPP=$?

check_port 3000 "Frontend"
FRONTEND=$?

check_port 5432 "Database"
DB=$?

echo ""

# =================== VÉRIFICATION 2 ===================
echo -e "${BLUE}═══════ VÉRIFICATION 2: ENDPOINTS API ═══════${NC}"
echo ""

check_service "Backend /docs" "http://localhost:8000/docs" "200"
API_DOCS=$?

check_service "WhatsApp /health" "http://localhost:3001/health" "200"
WA_HEALTH=$?

echo ""

# =================== VÉRIFICATION 3 ===================
echo -e "${BLUE}═══════ VÉRIFICATION 3: FLUX COMPLET (WEBHOOK) ═══════${NC}"
echo ""

echo -n "Test du webhook WhatsApp... "
webhook_response=$(curl -s -X POST "http://localhost:8000/api/whatsapp/message" \
  -H "Content-Type: application/json" \
  -d '{"from":"237123456789","message":"test","tenant_id":1}' 2>/dev/null)

if echo "$webhook_response" | grep -q '"status":"ok"'; then
    echo -e "${GREEN}✅ OK${NC}"
    WEBHOOK=0
    echo "Réponse du webhook:"
    echo "$webhook_response" | python3 -m json.tool 2>/dev/null || echo "$webhook_response"
else
    echo -e "${RED}❌ ERREUR${NC}"
    WEBHOOK=1
    echo "Réponse:"
    echo "$webhook_response"
fi

echo ""
echo -n "Test envoi message via WhatsApp /send... "
send_response=$(curl -s -X POST "http://localhost:3001/send" \
  -H "Content-Type: application/json" \
  -d '{"phone":"237123456789","message":"Test"}' 2>/dev/null)

if echo "$send_response" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ OK${NC}"
    SEND=0
else
    echo -e "${RED}❌ ERREUR${NC}"
    SEND=1
fi

echo ""

# =================== RÉSUMÉ ===================
echo -e "${BLUE}═══════ RÉSUMÉ ═══════${NC}"
echo ""

TOTAL_OK=0
TOTAL_ERRORS=0

services=(
    ["Backend:8000"]=$BACKEND
    ["WhatsApp:3001"]=$WHATSAPP
    ["Frontend:3000"]=$FRONTEND
    ["Database:5432"]=$DB
    ["API Docs"]=$API_DOCS
    ["WhatsApp Health"]=$WA_HEALTH
    ["Webhook"]=$WEBHOOK
    ["Send Message"]=$SEND
)

for service in "${!services[@]}"; do
    status=${services[$service]}
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}✅${NC} $service"
        ((TOTAL_OK++))
    else
        echo -e "${RED}❌${NC} $service"
        ((TOTAL_ERRORS++))
    fi
done

echo ""
echo "════════════════════════════════════════════════════════════════"
echo -e "Résultat: ${GREEN}$TOTAL_OK OK${NC} | ${RED}$TOTAL_ERRORS ERREURS${NC}"
echo "════════════════════════════════════════════════════════════════"

if [ $TOTAL_ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 TOUS LES TESTS PASSENT! LE SYSTÈME EST PRÊT!${NC}"
    exit 0
else
    echo -e "${RED}⚠️  CERTAINS TESTS ONT ÉCHOUÉ. VÉRIFIEZ LES ERREURS.${NC}"
    exit 1
fi
