#!/bin/bash

# === Configuration ===
PROJECT_DIR="$HOME/neobot-mvp/backend"
VENV_DIR="$PROJECT_DIR/venv"
ENV_FILE="$PROJECT_DIR/.env"

# 1️⃣ Vérifier l'environnement virtuel
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Environnement virtuel introuvable dans $VENV_DIR"
    exit 1
fi

# 2️⃣ Activer l'environnement virtuel
source "$VENV_DIR/bin/activate"

# 3️⃣ Aller dans le backend
cd "$PROJECT_DIR" || exit

# 4️⃣ Charger .env
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
    echo "✅ .env chargé"
else
    echo "⚠️ .env introuvable"
fi

# 5️⃣ Lancer le backend
echo "🌐 Démarrage Backend NéoBot..."
./scripts/start_backend_clean.sh &
BACKEND_PID=$!
sleep 5  # attendre que le serveur démarre

# 6️⃣ Vérifier DeepSeek
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "❌ DEEPSEEK_API_KEY non détectée"
else
    echo "✅ DEEPSEEK_API_KEY détectée : ${DEEPSEEK_API_KEY:0:8}****"
fi

# 7️⃣ Vérifier endpoint /health
HEALTH=$(curl -s http://localhost:8000/health)
echo "🔹 /health : $HEALTH"

echo "🚀 Backend lancé avec PID $BACKEND_PID"
