#!/bin/bash
# Script pour exécuter la suite de tests d'intégration
# Usage: bash run_tests.sh

set -e

echo "🚀 NeoBOT - Suite de tests d'intégration"
echo "==========================================="
echo ""

# Vérifier si pytest est installé
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing test requirements..."
    pip install -r backend/requirements-test.txt
fi

echo "📋 Exécution des tests..."
echo ""

cd backend

# Exécuter tests avec rapport détaillé
python -m pytest test_integration.py -v --tb=short --color=yes

echo ""
echo "✅ Tests terminés!"
echo ""
echo "Résumé:"
echo "- Phase 2: Tests d'authentification (signup, login)"
echo "- Phase 3: Tests isolation multi-tenant"
echo "- Phase 4: Tests suivi d'utilisation et quotas"
echo "- Phase 5: Tests facturation des dépassements"
echo "- Phase 7: Tests analytics endpoints"
