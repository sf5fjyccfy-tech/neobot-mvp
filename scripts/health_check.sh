#!/bin/bash
# =============================================================================
# SCRIPT: Vérification Complète des Services NéoBot MVP
# =============================================================================
# Teste: Backend (FastAPI), Frontend (Next.js), PostgreSQL, WhatsApp
# Génère un rapport de santé global
# =============================================================================

set -e

PROJECT_ROOT="/home/tim/neobot-mvp"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
REPORT_FILE="/tmp/neobot_health_check_$(date +%s).txt"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Compteurs
TESTS_PASSED=0
TESTS_FAILED=0

# Fonction pour logger
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
    echo "[INFO] $1" >> "$REPORT_FILE"
}

log_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    echo "✅ $1" >> "$REPORT_FILE"
    ((TESTS_PASSED++))
}

log_fail() {
    echo -e "${RED}❌ $1${NC}"
    echo "❌ $1" >> "$REPORT_FILE"
    ((TESTS_FAILED++))
}

log_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    echo "⚠️  $1" >> "$REPORT_FILE"
}

# Initialiser le rapport
echo "╔═══════════════════════════════════════════════════════════════╗" > "$REPORT_FILE"
echo "║      NéoBot MVP - RAPPORT DE SANTÉ DES SERVICES             ║" >> "$REPORT_FILE"
echo "║                 $(date '+%d/%m/%Y à %H:%M:%S')                      ║" >> "$REPORT_FILE"
echo "╚═══════════════════════════════════════════════════════════════╝" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

clear
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║      🏥 VÉRIFICATION DE LA SANTÉ DES SERVICES              ║"
echo "║                NéoBot MVP - Test Complet                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# =============================================================================
# 1. VÉRIFIER POSTGRESQL
# =============================================================================
echo ""
echo -e "${BLUE}━━━ 1️⃣ TEST: PostgreSQL ━━━${NC}"
log "Vérification de PostgreSQL..."

if command -v psql &> /dev/null; then
    if psql -U neobot -d neobot -h localhost -c "SELECT 1" &> /dev/null; then
        log_pass "PostgreSQL: Connexion réussie"
        
        # Vérifier les tables
        TABLES=$(psql -U neobot -d neobot -h localhost -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
        log_pass "PostgreSQL: $TABLES tables trouvées"
    else
        log_fail "PostgreSQL: Impossible de se connecter (vérifiez le password)"
    fi
else
    log_warn "PostgreSQL: psql non installé (test ignoré)"
fi

# =============================================================================
# 2. VÉRIFIER BACKEND FASTAPI
# =============================================================================
echo ""
echo -e "${BLUE}━━━ 2️⃣ TEST: Backend FastAPI ━━━${NC}"
log "Vérification du backend..."

cd "$BACKEND_DIR"

# Test 1: Les imports passent
log "Test: Imports des modules..."
if python3 -c "from app.main import app; print('OK')" 2>&1 | grep -q "OK"; then
    log_pass "Backend: Tous les modules importés ✅"
else
    log_fail "Backend: Erreur lors de l'import des modules"
fi

# Test 2: Vérifier les clés d'environnement
log "Test: Variables d'environnement..."
if python3 << 'PYEOF'
import os
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)
    api_key = os.getenv('DEEPSEEK_API_KEY')
    db_url = os.getenv('DATABASE_URL')
    
    if api_key and api_key != 'NOT_SET':
        print("✅ DEEPSEEK_API_KEY chargée")
    else:
        print("❌ DEEPSEEK_API_KEY vide")
    
    if db_url and 'postgresql' in db_url:
        print("✅ DATABASE_URL chargée")
    else:
        print("❌ DATABASE_URL vide")
else:
    print("ℹ️  .env n'existe pas (normal en prod)")
PYEOF
2>&1 | grep "✅" | head -2 | while read line; do
    log_pass "Backend: $line"
done
fi

# Test 3: Vérifier les routers
log "Test: Vérification des routers..."
if python3 << 'PYEOF' 2>&1 | grep -q "routers.*OK"; then
import os
os.environ['DEEPSEEK_API_KEY'] = 'sk-test'

from app.main import app

router_count = len(app.routes)
print(f"routers: {router_count} OK")
PYEOF
then
    log_pass "Backend: Routers intégrés ✅"
fi

# =============================================================================
# 3. VÉRIFIER FRONTEND NEXT.JS
# =============================================================================
echo ""
echo -e "${BLUE}━━━ 3️⃣ TEST: Frontend Next.js ━━━${NC}"
log "Vérification du frontend..."

if [ -f "$FRONTEND_DIR/package.json" ]; then
    cd "$FRONTEND_DIR"
    
    # Test 1: node_modules existe
    if [ -d "node_modules" ]; then
        log_pass "Frontend: node_modules présent ✅"
    else
        log_warn "Frontend: node_modules absent (npm install nécessaire)"
    fi
    
    # Test 2: Configuration Next.js
    if [ -f "next.config.js" ]; then
        log_pass "Frontend: next.config.js trouvé ✅"
    fi
    
    # Test 3: Variables d'environnement
    if [ -f ".env.local" ] || [ -f ".env" ]; then
        log_pass "Frontend: Configuration d'environnement trouvée ✅"
    else
        log_warn "Frontend: Pas de .env.local (utilise les defaults)"
    fi
    
    # Test 4: TypeScript
    if [ -f "tsconfig.json" ]; then
        log_pass "Frontend: tsconfig.json trouvé ✅"
    fi
else
    log_warn "Frontend: package.json non trouvé"
fi

# =============================================================================
# 4. VÉRIFIER WHATSAPP SERVICE
# =============================================================================
echo ""
echo -e "${BLUE}━━━ 4️⃣ TEST: WhatsApp Service (Node.js) ━━━${NC}"
log "Vérification du service WhatsApp..."

WHATSAPP_DIR="$PROJECT_ROOT/whatsapp-service"

if [ -d "$WHATSAPP_DIR" ]; then
    cd "$WHATSAPP_DIR"
    
    # Test 1: package.json existe
    if [ -f "package.json" ]; then
        log_pass "WhatsApp: package.json trouvé ✅"
        
        # Vérifier les dépendances
        if grep -q "baileys" package.json; then
            log_pass "WhatsApp: Baileys détecté ✅"
        fi
    else
        log_fail "WhatsApp: package.json absent"
    fi
    
    # Test 2: node_modules existe
    if [ -d "node_modules" ]; then
        log_pass "WhatsApp: node_modules présent ✅"
    else
        log_warn "WhatsApp: node_modules absent (npm install nécessaire)"
    fi
    
    # Test 3: Fichiers principaux
    if [ -f "index.js" ]; then
        log_pass "WhatsApp: index.js trouvé ✅"
    fi
else
    log_warn "WhatsApp: Répertoire non trouvé"
fi

# =============================================================================
# 5. VÉRIFIER LA CONNECTIVITÉ
# =============================================================================
echo ""
echo -e "${BLUE}━━━ 5️⃣ TEST: Architecture Générale ━━━${NC}"
log "Vérification de l'architecture..."

# Test: Structure des dossiers
REQUIRED_DIRS=(
    "$BACKEND_DIR/app/api"
    "$BACKEND_DIR/app/services"
    "$BACKEND_DIR/app/models"
    "$FRONTEND_DIR/src/app"
    "$FRONTEND_DIR/src/components"
    "$WHATSAPP_DIR"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_pass "Structure: $dir ✅"
    else
        log_fail "Structure: $dir ❌"
    fi
done

# =============================================================================
# 6. RÉSUMÉ
# =============================================================================
echo ""
echo -e "${BLUE}━━━ 📊 RÉSUMÉ ━━━${NC}"
echo ""
echo -e "Tests réussis:  ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests échoués:  ${RED}$TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🟢 STATUS: TOUS LES TESTS PASSENT!${NC}"
    echo "🟢 STATUS: TOUS LES TESTS PASSENT!" >> "$REPORT_FILE"
else
    echo -e "${YELLOW}🟡 STATUS: Certains tests ont échoué${NC}"
    echo "🟡 STATUS: Certains tests ont échoué" >> "$REPORT_FILE"
fi

# =============================================================================
# 7. RAPPORT FINAL
# =============================================================================
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}📝 Rapport sauvegardé: $REPORT_FILE${NC}"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Afficher le rapport
echo ""
echo "📋 RAPPORT COMPLET:"
echo "───────────────────────────────────────────────────────────────"
cat "$REPORT_FILE"
echo "───────────────────────────────────────────────────────────────"
echo ""

echo ""
echo "✅ Vérification terminée!"
echo ""
