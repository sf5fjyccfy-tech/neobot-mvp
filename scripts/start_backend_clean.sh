#!/bin/bash
echo "🚀 Démarrage Backend NéoBot (Version Propre)"
echo "============================================="

cd ~/neobot-mvp/backend

if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel non trouvé"
    exit 1
fi

source venv/bin/activate

echo "🔍 Vérification syntaxe Python..."
python -m py_compile app/main.py app/models.py app/database.py app/ai_service.py

if [ $? -eq 0 ]; then
    echo "✅ Syntaxe Python correcte"
else
    echo "❌ Erreur de syntaxe détectée"
    exit 1
fi

echo "🌐 Démarrage sur http://localhost:8000"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
