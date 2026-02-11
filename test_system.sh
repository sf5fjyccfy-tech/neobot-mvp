#!/bin/bash
# Test complet du système Business Intelligence

set -e  # Exit on error

echo "🧪 TEST COMPLET - Business Intelligence System"
echo "=============================================="

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="http://localhost:8000"
TIMEOUT=5

# Fonction pour faire des requêtes API
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -z "$data" ]; then
        curl -s -X "$method" "$API_URL$endpoint" -H "Content-Type: application/json"
    else
        curl -s -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data"
    fi
}

# TEST 1: Backend Health
echo -e "\n${BLUE}[TEST 1]${NC} Backend Health Check"
if curl -s -I "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend running${NC}"
else
    echo -e "${RED}❌ Backend not responding${NC}"
    exit 1
fi

# TEST 2: Business Types
echo -e "\n${BLUE}[TEST 2]${NC} Business Types"
TYPES=$(api_call GET "/api/business/types")
echo "$TYPES" | grep -q "neobot" && echo -e "${GREEN}✅ Business types loaded${NC}" || echo -e "${RED}❌ No business types${NC}"

# TEST 3: Tenant 1 Config
echo -e "\n${BLUE}[TEST 3]${NC} Tenant 1 Business Config"
CONFIG=$(api_call GET "/api/tenants/1/business/config")
if echo "$CONFIG" | grep -q "NéoBot"; then
    echo -e "${GREEN}✅ NéoBot config exists${NC}"
    echo "$CONFIG" | grep -o '"company_name":"[^"]*"' || true
else
    echo -e "${YELLOW}⚠️  NéoBot config not yet configured${NC}"
fi

# TEST 4: Send WhatsApp Message
echo -e "\n${BLUE}[TEST 4]${NC} WhatsApp Message"
MESSAGE_RESPONSE=$(api_call POST "/api/whatsapp/message" '{
    "phone": "+237612345678",
    "message": "Neobot cest combien ?",
    "tenant_id": 1
}')

if echo "$MESSAGE_RESPONSE" | grep -q "success\|received"; then
    echo -e "${GREEN}✅ Message processed${NC}"
    echo "$MESSAGE_RESPONSE" | grep -o '"status":"[^"]*"' || true
else
    echo -e "${RED}❌ Message processing failed${NC}"
    echo "$MESSAGE_RESPONSE" | head -100
fi

echo -e "\n${YELLOW}================================${NC}"
echo -e "${GREEN}✅ Tests completed${NC}"
echo -e "${YELLOW}================================\n${NC}"
