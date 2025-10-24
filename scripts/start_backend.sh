#!/bin/bash
cd backend
source venv/bin/activate
echo "🚀 Démarrage Backend NéoBot"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
