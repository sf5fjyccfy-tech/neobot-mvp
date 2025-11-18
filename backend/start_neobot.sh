#!/bin/bash
# Script de démarrage robuste pour NéoBot

echo "🚀 DÉMARRAGE NÉOBOT..."
cd ~/neobot-mvp/backend

# Vérifier les dépendances
echo "🔍 Vérification des prérequis..."
python3 -c "
import sys
try:
    import fastapi, sqlalchemy, uvicorn
    print('✅ Dépendances Python OK')
except ImportError as e:
    print(f'❌ Dépendance manquante: {e}')
    sys.exit(1)
"

# Vérifier les fichiers essentiels
echo "📁 Vérification des fichiers..."
ESSENTIAL_FILES=(
    "app/main.py"
    "app/database.py" 
    "app/models.py"
    "app/services/fallback_service.py"
    "app/services/closeur_pro_service.py"
)

for file in "${ESSENTIAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file - MANQUANT"
        exit 1
    fi
done

# Vérifier les imports
echo "🔧 Vérification des imports..."
python3 -c "
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

try:
    from app.main import app
    from app.database import SessionLocal
    from app.services.fallback_service import FallbackService
    from app.services.closeur_pro_service import CloseurProService
    print('✅ Tous les imports fonctionnent')
except Exception as e:
    print(f'❌ Erreur import: {e}')
    sys.exit(1)
"

# Démarrer le serveur
echo "🎉 DÉMARRAGE DU SERVEUR..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
