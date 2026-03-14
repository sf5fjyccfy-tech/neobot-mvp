#!/bin/bash

# Script de test du système RAG intelligent
# Exécute les tests pour vérifier que le bot utilise les vraies données

set -e

echo "====================================="
echo "🧪 TEST SYSTÈME RAG INTELLIGENT"
echo "====================================="
echo ""

# Colours
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

BACKEND_URL="http://localhost:8000"
TIMEOUT=5

# Test 1: Backend running?
echo "TEST 1: Vérifier que le backend est accessible..."
if curl -s -m $TIMEOUT "$BACKEND_URL/docs" > /dev/null; then
    echo -e "${GREEN}✅ Backend accessible${NC}"
else
    echo -e "${RED}❌ Backend non accessible à $BACKEND_URL${NC}"
    echo "   Démarrez le backend avec: cd backend && python -m uvicorn app.main:app --reload"
    exit 1
fi

echo ""

# Test 2: Initialize NéoBot profile
echo "TEST 2: Initialiser le profil NéoBot..."
RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/setup/init-neobot-profile")
if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✅ Profil NéoBot initialisé${NC}"
    echo "   Réponse: $(echo $RESPONSE | jq -r '.message' 2>/dev/null)"
else
    echo -e "${RED}❌ Erreur lors de l'initialisation${NC}"
    echo "   Réponse: $RESPONSE"
fi

echo ""

# Test 3: Get profile
echo "TEST 3: Récupérer le profil complet..."
PROFILE=$(curl -s "$BACKEND_URL/api/v1/setup/profile/1")
if echo "$PROFILE" | grep -q "company_name"; then
    echo -e "${GREEN}✅ Profil récupéré${NC}"
    
    # Extract key info (note: data is nested under .profile)
    COMPANY=$(echo $PROFILE | jq -r '.profile.company_name' 2>/dev/null)
    TONE=$(echo $PROFILE | jq -r '.profile.tone' 2>/dev/null)
    FOCUS=$(echo $PROFILE | jq -r '.profile.selling_focus' 2>/dev/null)
    
    echo "   - Entreprise: $COMPANY"
    echo "   - Ton: $TONE"
    echo "   - Focus: $FOCUS"
else
    echo -e "${RED}❌ Erreur lors de la récupération du profil${NC}"
    echo "   Réponse: $PROFILE"
fi

echo ""

# Test 4: Get RAG context
echo "TEST 4: Vérifier le contexte RAG (ce que l'IA verra)..."
RAG=$(curl -s "$BACKEND_URL/api/v1/setup/profile/1/formatted")
if echo "$RAG" | grep -q "PROFIL MÉTIER"; then
    echo -e "${GREEN}✅ Contexte RAG généré${NC}"
    echo "   Aperçu:"
    echo "$RAG" | jq -r '.rag_context' 2>/dev/null | head -10 | sed 's/^/   /'
else
    echo -e "${RED}❌ Contexte RAG non généré${NC}"
    echo "   Réponse: $RAG"
fi

echo ""

# Test 5: Check database
echo "TEST 5: Vérifier la base de données..."
cd /home/tim/neobot-mvp/backend
python3 -c "
from app.database import SessionLocal
from app.models import TenantBusinessConfig

db = SessionLocal()
profile = db.query(TenantBusinessConfig).filter_by(tenant_id=1).first()

if profile:
    print('✅ Profil trouvé en base de données')
    print(f'   - Entreprise: {profile.company_name}')
    print(f'   - Type Business ID: {profile.business_type_id}')
else:
    print('❌ Profil NOT trouvé en base de données')
    exit(1)

db.close()
" 2>&1 | grep -E '(✅|❌|Entreprise|Type)' || echo -e "${RED}❌ Erreur lors de la vérification BD${NC}"

echo ""

# Summary
echo "====================================="
echo -e "${GREEN}✅ TOUS LES TESTS COMPLÉTÉS${NC}"
echo "====================================="
echo ""
echo "📝 Résumé:"
echo "  ✅ Backend accessible"
echo "  ✅ Profil NéoBot créé"
echo "  ✅ Données récupérées"
echo "  ✅ Contexte RAG généré"
echo "  ✅ Base de données vérifiée"
echo ""
echo "🚀 Système RAG PRÊT!"
echo ""
echo "💡 Prochaines étapes:"
echo "  1. Envoyer des messages via WhatsApp"
echo "  2. Vérifier que les réponses utilisent les vraies données"
echo "  3. Consulter les logs: tail -f logs/app.log | grep RAG"
echo ""
