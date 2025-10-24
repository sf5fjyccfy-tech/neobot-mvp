#!/bin/bash

echo "🧹 Création d'un repo propre..."

# Créer nouveau dossier
cd ~
mkdir neobot-mvp-clean
cd neobot-mvp-clean

# Copier UNIQUEMENT les fichiers nécessaires (pas .git, pas secrets)
rsync -av --exclude='.git' --exclude='*.log' --exclude='*.pid' \
  --exclude='auth_*' --exclude='*.old' --exclude='*.backup' \
  --exclude='*.broken' --exclude='node_modules' --exclude='__pycache__' \
  --exclude='venv' --exclude='.next' \
  ~/neobot-mvp/ ./

# Créer .env.example (pas .env)
cat > backend/.env.example << 'EOF'
DATABASE_URL=postgresql://user:password@host:5432/dbname
DEEPSEEK_API_KEY=sk-your-key-here
ENCRYPTION_KEY=your-encryption-key
BASE_URL=http://localhost:8000
EOF

# Supprimer tous les .env réels
find . -name ".env" -type f -delete
find . -name ".env.production" -type f -delete

# Init git propre
git init
git add .
git commit -m "Initial commit - NeoBot MVP (clean)"

echo "✅ Repo propre créé dans ~/neobot-mvp-clean"
echo ""
echo "Prochaine étape : créer repo GitHub et push"
