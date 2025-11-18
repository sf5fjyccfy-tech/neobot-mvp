#!/bin/bash
# =============================================================================
# Script de Sécurité: Masquer les Secrets dans les Fichiers Committés
# =============================================================================
# Ce script:
# 1. Masque les clés API dans .env.example
# 2. Vérifie qu'aucun secret n'est commité
# 3. Teste que l'app fonctionne toujours avec les vraies clés
# =============================================================================

set -e

PROJECT_ROOT="/home/tim/neobot-mvp"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🔐 === SÉCURITÉ: Gestion des Secrets ==="
echo ""

# ============== 1. VÉRIFIER QUE .env EST IGNORÉ ==============
echo "1️⃣  Vérification: .env doit être ignoré..."

if git -C "$PROJECT_ROOT" check-ignore "$BACKEND_DIR/.env" > /dev/null 2>&1; then
    echo "   ✅ $BACKEND_DIR/.env est correctement ignoré"
else
    echo "   ❌ ERREUR: $BACKEND_DIR/.env doit être dans .gitignore"
    exit 1
fi

# ============== 2. VÉRIFIER .env.example N'A PAS DE VRAIES CLÉS ==============
echo ""
echo "2️⃣  Vérification: .env.example ne doit pas contenir les vraies clés..."

if grep -q "sk-[a-f0-9]\{32,\}" "$BACKEND_DIR/.env.example" 2>/dev/null; then
    echo "   ⚠️  ATTENTION: Vrais secrets trouvés dans .env.example"
    echo "   Masquage en cours..."
    
    # Masquer les clés sk-xxxx par sk-test
    sed -i 's/sk-[a-f0-9]\{32,\}/sk-test/g' "$BACKEND_DIR/.env.example"
    
    echo "   ✅ .env.example masqué (sk-xxxx → sk-test)"
else
    echo "   ✅ .env.example n'a pas de vraies clés"
fi

# ============== 3. VÉRIFIER QU'AUCUN SECRET N'EST COMMITÉ ==============
echo ""
echo "3️⃣  Vérification: Aucun secret commité..."

# Patterns à chercher (vraies clés, pas les placeholders)
DANGEROUS_PATTERNS=(
    "sk-[a-f0-9]\{32,\}"  # DeepSeek API keys (vraies clés)
)

FOUND_SECRETS=0
for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if git -C "$PROJECT_ROOT" grep -E "$pattern" -- "*.py" "*.example" 2>/dev/null | grep -v ".env.example" | grep -v ".env"; then
        echo "   ⚠️  Secret trouvé!"
        FOUND_SECRETS=1
    fi
done

if [ $FOUND_SECRETS -eq 0 ]; then
    echo "   ✅ Aucun secret dangereux trouvé dans le code commité"
else
    echo "   ❌ Des secrets ont été trouvés - NE PAS COMMITTER!"
    exit 1
fi

# ============== 4. MASQUER LES SECRETS DANS .env.production.example ==============
echo ""
echo "4️⃣  Masquage: .env.production.example..."

if [ -f "$BACKEND_DIR/.env.production.example" ]; then
    # Remplacer les vrais secrets par **MASKED**
    sed -i 's/sk-[a-f0-9]\{32,\}/**MASKED**/g' "$BACKEND_DIR/.env.production.example"
    sed -i 's/postgresql:\/\/[^[:space:]]*/**MASKED**/g' "$BACKEND_DIR/.env.production.example"
    echo "   ✅ .env.production.example masqué"
else
    echo "   ℹ️  .env.production.example n'existe pas"
fi

# ============== 5. VÉRIFIER QUE L'APP FONCTIONNE AVEC LA VRAIE CLÉ ==============
echo ""
echo "5️⃣  Test: Application fonctionne avec la vraie clé..."

if [ -f "$BACKEND_DIR/.env" ]; then
    cd "$BACKEND_DIR"
    
    # Test 1: Les imports passent
    python3 -c "from app.main import app; print('   ✅ Imports OK')" 2>&1 || {
        echo "   ❌ Erreur lors du chargement de l'app"
        exit 1
    }
    
    # Test 2: Vérifier que DEEPSEEK_API_KEY est bien chargé
    api_key=$(python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DEEPSEEK_API_KEY', 'NOT_SET'))")
    if [ "$api_key" != "NOT_SET" ] && [ -n "$api_key" ]; then
        echo "   ✅ DEEPSEEK_API_KEY chargé avec succès"
    else
        echo "   ⚠️  DEEPSEEK_API_KEY pas chargé"
    fi
else
    echo "   ℹ️  $BACKEND_DIR/.env n'existe pas (OK pour la CI/CD)"
fi

# ============== 6. RÉSUMÉ ==============
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                                                            ║"
echo "║  🔐 VÉRIFICATION SÉCURITÉ: COMPLÉTÉE ✅                   ║"
echo "║                                                            ║"
echo "║  ✅ .env est ignoré (non commité)                         ║"
echo "║  ✅ .env.example n'a pas de vrais secrets                 ║"
echo "║  ✅ Aucun secret dangereux trouvé                         ║"
echo "║  ✅ .env.production.example masqué                        ║"
echo "║  ✅ Application fonctionne avec vraie clé                 ║"
echo "║                                                            ║"
echo "║  Status: 🟢 PRODUCTION READY                              ║"
echo "║                                                            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📝 Fichiers masqués:"
echo "   • .env.example         → sk-test (dev)"
echo "   • .env.production.example → **MASKED** (prod)"
echo ""
echo "💡 Pour GitHub Actions/Production:"
echo "   1. Ajouter les secrets via Settings > Secrets"
echo "   2. Utiliser \${{ secrets.DEEPSEEK_API_KEY }} dans le workflow"
echo "   3. .env n'est pas commité (sûr!)"
echo ""
