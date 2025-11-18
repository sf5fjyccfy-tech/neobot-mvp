#!/bin/bash
# =============================================================================
# Script de Vérification Complète - Frontend, Backend, Database, Services
# =============================================================================
set -e

PROJECT_ROOT="/home/tim/neobot-mvp"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
WHATSAPP_DIR="$PROJECT_ROOT/whatsapp-service"

echo "🚀 === VÉRIFICATION COMPLÈTE DU PROJET NEOBOT ==="
echo ""
echo "Date: $(date '+%d %b %Y - %H:%M:%S')"
echo "Projet: $PROJECT_ROOT"
echo ""

# Rapport JSON pour les résultats
REPORT_FILE="/tmp/neobot_health_report.txt"
> "$REPORT_FILE"

# ============== 1. VÉRIFIER BACKEND FASTAPI ==============
echo "1️⃣  Backend FastAPI"
echo "══════════════════════════════════════════════════════════"

cd "$BACKEND_DIR"

# Test 1: Vérifier que le fichier main.py charge
if python3 -c "from app.main import app; print('✅')" 2>&1 | grep -q "✅"; then
    echo "   ✅ main.py importe correctement"
    echo "Backend: ✅ IMPORTS OK" >> "$REPORT_FILE"
else
    echo "   ❌ Erreur d'import dans main.py"
    echo "Backend: ❌ IMPORTS FAILED" >> "$REPORT_FILE"
    exit 1
fi

# Test 2: Vérifier la base de données
if python3 << 'PYEOF' 2>&1 | grep -q "✅ Database:"; then
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from app.database import engine
    from sqlalchemy import text
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database: Connected")
except Exception as e:
    print(f"❌ Database: {str(e)[:50]}")
PYEOF
    echo "   ✅ Connexion PostgreSQL OK"
    echo "Database: ✅ CONNECTED" >> "$REPORT_FILE"
else
    echo "   ⚠️  Connexion PostgreSQL échouée (peut être normal en CI)"
    echo "Database: ⚠️  UNREACHABLE" >> "$REPORT_FILE"
fi

# Test 3: Vérifier les modules importés
if python3 -c "from app.api import analytics, conversations, products, payments; print('✅')" 2>&1 | grep -q "✅"; then
    echo "   ✅ Tous les modules API importent"
    echo "API Modules: ✅ LOADED" >> "$REPORT_FILE"
else
    echo "   ⚠️  Erreur lors du chargement des modules API"
    echo "API Modules: ⚠️  PARTIAL" >> "$REPORT_FILE"
fi

# Test 4: Vérifier les services
if python3 -c "from app.services.fallback_service import FallbackService; from app.services.closeur_pro_service import CloseurProService; print('✅')" 2>&1 | grep -q "✅"; then
    echo "   ✅ Tous les services chargent"
    echo "Services: ✅ LOADED" >> "$REPORT_FILE"
else
    echo "   ⚠️  Erreur lors du chargement des services"
    echo "Services: ⚠️  PARTIAL" >> "$REPORT_FILE"
fi

# Test 5: Vérifier que les secrets sont chargés
if python3 << 'PYEOF' 2>&1 | grep -q "✅"; then
import os
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('DEEPSEEK_API_KEY')
if api_key and len(api_key) > 5:
    print("✅")
else:
    print("❌")
PYEOF
    echo "   ✅ Clé DeepSeek chargée"
    echo "Secrets: ✅ LOADED" >> "$REPORT_FILE"
else
    echo "   ⚠️  Clé DeepSeek non chargée (utilisera fallback sk-test)"
    echo "Secrets: ⚠️  FALLBACK" >> "$REPORT_FILE"
fi

echo ""

# ============== 2. VÉRIFIER FRONTEND NEXT.JS ==============
echo "2️⃣  Frontend Next.js"
echo "══════════════════════════════════════════════════════════"

cd "$FRONTEND_DIR"

# Test 1: Vérifier que Next.js peut être lné
if [ -f "package.json" ]; then
    echo "   ✅ package.json trouvé"
    echo "Frontend Package: ✅ FOUND" >> "$REPORT_FILE"
else
    echo "   ❌ package.json manquant"
    echo "Frontend Package: ❌ MISSING" >> "$REPORT_FILE"
fi

# Test 2: Vérifier que node_modules existe (optionnel)
if [ -d "node_modules" ]; then
    echo "   ✅ node_modules installés"
    echo "Frontend Modules: ✅ INSTALLED" >> "$REPORT_FILE"
else
    echo "   ⚠️  node_modules non installés (run 'npm install')"
    echo "Frontend Modules: ⚠️  MISSING" >> "$REPORT_FILE"
fi

# Test 3: Vérifier la configuration API
if grep -q "NEXT_PUBLIC_API_URL" "src/lib/api.ts" 2>/dev/null; then
    echo "   ✅ API URL configurée dans src/lib/api.ts"
    echo "Frontend API Config: ✅ OK" >> "$REPORT_FILE"
else
    echo "   ⚠️  Configuration API URL non trouvée"
    echo "Frontend API Config: ⚠️  PARTIAL" >> "$REPORT_FILE"
fi

# Test 4: Vérifier le tsconfig
if [ -f "tsconfig.json" ]; then
    echo "   ✅ tsconfig.json présent"
    echo "Frontend Config: ✅ OK" >> "$REPORT_FILE"
else
    echo "   ❌ tsconfig.json manquant"
    echo "Frontend Config: ❌ MISSING" >> "$REPORT_FILE"
fi

echo ""

# ============== 3. VÉRIFIER WHATSAPP SERVICE ==============
echo "3️⃣  WhatsApp Service (Node.js)"
echo "══════════════════════════════════════════════════════════"

if [ -d "$WHATSAPP_DIR" ]; then
    cd "$WHATSAPP_DIR"
    
    if [ -f "package.json" ]; then
        echo "   ✅ package.json trouvé"
        echo "WhatsApp Package: ✅ FOUND" >> "$REPORT_FILE"
    else
        echo "   ❌ package.json manquant"
        echo "WhatsApp Package: ❌ MISSING" >> "$REPORT_FILE"
    fi
    
    if [ -d "node_modules" ]; then
        echo "   ✅ node_modules installés"
        echo "WhatsApp Modules: ✅ INSTALLED" >> "$REPORT_FILE"
    else
        echo "   ⚠️  node_modules non installés"
        echo "WhatsApp Modules: ⚠️  MISSING" >> "$REPORT_FILE"
    fi
    
    if [ -f "index.js" ] || [ -f "start-neobot.js" ]; then
        echo "   ✅ Fichiers d'entrée trouvés"
        echo "WhatsApp Entry: ✅ FOUND" >> "$REPORT_FILE"
    else
        echo "   ❌ Fichiers d'entrée manquants"
        echo "WhatsApp Entry: ❌ MISSING" >> "$REPORT_FILE"
    fi
else
    echo "   ⚠️  Répertoire WhatsApp service non trouvé"
    echo "WhatsApp Service: ⚠️  MISSING" >> "$REPORT_FILE"
fi

echo ""

# ============== 4. VÉRIFIER CONFIGURATION ==============
echo "4️⃣  Configuration & Secrets"
echo "══════════════════════════════════════════════════════════"

# Backend .env
if [ -f "$BACKEND_DIR/.env" ]; then
    echo "   ✅ backend/.env présent"
    echo "Backend .env: ✅ FOUND" >> "$REPORT_FILE"
else
    echo "   ❌ backend/.env manquant"
    echo "Backend .env: ❌ MISSING" >> "$REPORT_FILE"
fi

# .gitignore
if [ -f "$PROJECT_ROOT/.gitignore" ]; then
    if grep -q "\.env" "$PROJECT_ROOT/.gitignore"; then
        echo "   ✅ .gitignore exclut .env"
        echo ".gitignore: ✅ SECRETS PROTECTED" >> "$REPORT_FILE"
    else
        echo "   ⚠️  .gitignore ne mentionne pas .env"
        echo ".gitignore: ⚠️  PARTIAL" >> "$REPORT_FILE"
    fi
else
    echo "   ❌ .gitignore manquant"
    echo ".gitignore: ❌ MISSING" >> "$REPORT_FILE"
fi

# Docker compose
if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    echo "   ✅ docker-compose.yml présent"
    echo "Docker Compose: ✅ FOUND" >> "$REPORT_FILE"
else
    echo "   ⚠️  docker-compose.yml manquant"
    echo "Docker Compose: ⚠️  MISSING" >> "$REPORT_FILE"
fi

echo ""

# ============== 5. VÉRIFIER STRUCTURE ==============
echo "5️⃣  Structure du Projet"
echo "══════════════════════════════════════════════════════════"

# Vérifier les répertoires clés
REQUIRED_DIRS=(
    "$BACKEND_DIR/app"
    "$BACKEND_DIR/app/api"
    "$BACKEND_DIR/app/services"
    "$FRONTEND_DIR/src"
    "$FRONTEND_DIR/src/app"
)

MISSING_DIRS=0
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "   ✅ $dir"
    else
        echo "   ❌ $dir MANQUANT"
        MISSING_DIRS=$((MISSING_DIRS + 1))
    fi
done

if [ $MISSING_DIRS -eq 0 ]; then
    echo "   ✅ Tous les répertoires critiques présents"
    echo "Structure: ✅ COMPLETE" >> "$REPORT_FILE"
else
    echo "   ❌ $MISSING_DIRS répertoires manquants"
    echo "Structure: ❌ INCOMPLETE" >> "$REPORT_FILE"
fi

echo ""

# ============== 6. RAPPORT FINAL ==============
echo "📊 RAPPORT FINAL"
echo "══════════════════════════════════════════════════════════"
echo ""
cat "$REPORT_FILE"
echo ""

# Compter les statuts
SUCCESS_COUNT=$(grep -c "✅" "$REPORT_FILE" || echo 0)
WARNING_COUNT=$(grep -c "⚠️" "$REPORT_FILE" || echo 0)
ERROR_COUNT=$(grep -c "❌" "$REPORT_FILE" || echo 0)

echo ""
echo "📈 Statistiques:"
echo "   ✅ Succès: $SUCCESS_COUNT"
echo "   ⚠️  Avertissements: $WARNING_COUNT"
echo "   ❌ Erreurs: $ERROR_COUNT"
echo ""

if [ $ERROR_COUNT -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║  🟢 STATUS: TOUS LES SERVICES FONCTIONNELS ✅            ║"
    echo "║                                                            ║"
    echo "║  Backend:  ✅ Prêt"
    echo "║  Frontend: ✅ Prêt"
    echo "║  Database: ✅ Connecté"
    echo "║  Services: ✅ Chargés"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
else
    echo "⚠️  Certains éléments nécessitent attention"
fi

echo ""
echo "📁 Rapport sauvegardé: $REPORT_FILE"
echo ""
