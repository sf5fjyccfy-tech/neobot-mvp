#!/bin/bash

set -e  # Arrêter si erreur

echo "========================================="
echo "  NETTOYAGE SÉCURITÉ NEOBOT - TOUT EN UN"
echo "========================================="
echo ""
echo "⚠️  CE SCRIPT VA :"
echo "  1. Faire un backup"
echo "  2. Nettoyer les secrets du HEAD"
echo "  3. Scanner l'historique"
echo "  4. Purger l'historique (force push)"
echo "  5. Générer nouveaux secrets"
echo ""
read -p "Continuer ? (oui/non) : " CONFIRM
if [ "$CONFIRM" != "oui" ]; then
    echo "Annulé"
    exit 1
fi

# ========== ÉTAPE 1 : BACKUP ==========
echo ""
echo "📦 ÉTAPE 1/6 : Backup..."
cd ~
git clone --mirror https://github.com/timpatrix/neobot-mvp.git neobot-backup-$(date +%Y%m%d).git
echo "✓ Backup créé : ~/neobot-backup-$(date +%Y%m%d).git"

# ========== ÉTAPE 2 : NETTOYAGE HEAD ==========
echo ""
echo "🧹 ÉTAPE 2/6 : Nettoyage HEAD..."
cd ~/neobot-mvp

# Créer branche de nettoyage
git switch -c security/sanitize-secrets 2>/dev/null || git checkout security/sanitize-secrets

# Retirer fichiers sensibles du suivi
git rm --cached backend/.env 2>/dev/null || true
git rm --cached backend/.env.production 2>/dev/null || true
git rm --cached frontend/.env.production 2>/dev/null || true
git rm --cached -r auth_* 2>/dev/null || true
git rm --cached -r whatsapp-service/auth* 2>/dev/null || true

# .gitignore complet
cat > .gitignore << 'EOF'
# Secrets
.env
.env.local
.env.*.local
*.key
*.pem

# Python
__pycache__/
*.pyc
venv/

# Node
node_modules/
.next/

# WhatsApp sessions
auth_info_baileys/
auth_*/

# Logs
*.log
*.pid

# Backup
*.old
*.backup
*.broken
EOF

# backend/.env.example
cat > backend/.env.example << 'EOF'
DATABASE_URL=postgresql://user:password@host:5432/dbname
ENCRYPTION_KEY=your_encryption_key_here
DEEPSEEK_API_KEY=***REDACTED***
BASE_URL=http://localhost:8000
EOF

# Commit
git add .gitignore backend/.env.example
git commit -m "security: sanitize secrets and add proper gitignore" || echo "Nothing to commit"

echo "✓ HEAD nettoyé"

# ========== ÉTAPE 3 : SCANNER HISTORIQUE ==========
echo ""
echo "🔍 ÉTAPE 3/6 : Scan de l'historique..."
echo "Recherche de secrets dans TOUS les commits..."

SECRETS_FOUND=$(git log --all --full-history --source --pretty=format:"%H" -- backend/.env backend/.env.production frontend/.env.production 2>/dev/null | wc -l)

if [ "$SECRETS_FOUND" -gt 0 ]; then
    echo "⚠️  $SECRETS_FOUND commit(s) contiennent des fichiers sensibles"
    echo "   → Purge nécessaire"
    NEED_PURGE=1
else
    echo "✓ Aucun fichier sensible trouvé dans l'historique"
    NEED_PURGE=0
fi

# ========== ÉTAPE 4 : PURGE HISTORIQUE ==========
if [ "$NEED_PURGE" -eq 1 ]; then
    echo ""
    echo "🔥 ÉTAPE 4/6 : Purge de l'historique..."
    echo ""
    echo "⚠️  ATTENTION : Cette opération est IRRÉVERSIBLE"
    echo "   Elle va réécrire l'historique Git"
    echo "   Tous les collaborateurs devront re-cloner"
    echo ""
    read -p "Confirmer la PURGE ? (PURGE/annuler) : " PURGE_CONFIRM
    
    if [ "$PURGE_CONFIRM" != "PURGE" ]; then
        echo "Purge annulée. Secrets toujours dans l'historique."
        echo "Lance manuellement plus tard ou continue sans purge."
        NEED_PURGE=0
    else
        # Installer git-filter-repo si nécessaire
        if ! command -v git-filter-repo &> /dev/null; then
            echo "Installation de git-filter-repo..."
            pip3 install --user git-filter-repo
        fi
        
        # Créer clone temporaire
        cd ~
        TEMP_REPO="neobot-purge-temp-$(date +%Y%m%d%H%M%S)"
        git clone --mirror https://github.com/timpatrix/neobot-mvp.git $TEMP_REPO
        cd $TEMP_REPO
        
        # Purger les fichiers
        git filter-repo --force --invert-paths \
            --path backend/.env \
            --path backend/.env.production \
            --path frontend/.env.production \
            --path 'auth_*' \
            --path 'whatsapp-service/auth*'
        
        # Force push
        echo "Force push vers GitHub..."
        git push --force --all
        git push --force --tags
        
        cd ~/neobot-mvp
        echo "✓ Historique purgé"
    fi
else
    echo ""
    echo "⏭️  ÉTAPE 4/6 : Purge non nécessaire (skip)"
fi

# ========== ÉTAPE 5 : NOUVEAUX SECRETS ==========
echo ""
echo "🔐 ÉTAPE 5/6 : Génération de nouveaux secrets..."

# Générer nouvelle ENCRYPTION_KEY
NEW_ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

cat > backend/.env.new << EOF
# ⚠️  NE JAMAIS COMMITTER CE FICHIER
# Renomme en .env après avoir mis tes vraies valeurs

DATABASE_URL=postgresql://neobot:CHANGE_THIS_PASSWORD@localhost:5432/neobot
ENCRYPTION_KEY=$NEW_ENCRYPTION_KEY
DEEPSEEK_API_KEY=***REDACTED***
BASE_URL=http://localhost:8000
EOF

echo "✓ Nouveaux secrets générés dans backend/.env.new"
echo ""
echo "📋 ACTIONS MANUELLES REQUISES :"
echo ""
echo "1. DEEPSEEK API :"
echo "   → Va sur https://platform.deepseek.com"
echo "   → Révoque l'ancienne clé"
echo "   → Crée une nouvelle clé"
echo "   → Copie dans backend/.env.new"
echo ""
echo "2. POSTGRES PASSWORD :"
echo "   → Change le mot de passe : docker exec -it neobot_postgres psql -U neobot"
echo "   → ALTER USER neobot WITH PASSWORD 'nouveau_mdp';"
echo "   → Mets dans backend/.env.new"
echo ""
echo "3. RENDER.COM :"
echo "   → Dashboard → Environment Variables"
echo "   → Mets : DATABASE_URL, ENCRYPTION_KEY, DEEPSEEK_API_KEY"
echo ""
echo "4. VERCEL :"
echo "   → Project Settings → Environment Variables"
echo "   → NEXT_PUBLIC_API_URL=https://ton-backend.onrender.com"
echo ""

# ========== ÉTAPE 6 : FINALISATION ==========
echo ""
echo "📝 ÉTAPE 6/6 : Finalisation..."

# Instructions pour collaborateurs
cat > COLLABORATEURS_README.txt << 'EOF'
⚠️  ACTION REQUISE

L'historique Git a été nettoyé pour sécurité.
Vous DEVEZ re-cloner le projet :

1. Sauvegardez vos branches locales non poussées
2. Supprimez votre copie locale :
   rm -rf ~/neobot-mvp

3. Clonez de nouveau :
   git clone https://github.com/timpatrix/neobot-mvp.git

4. Recréez votre .env local avec vos nouvelles clés
   (demandez-les au mainteneur)

Ne tentez PAS de pull/merge, ça ne marchera pas.
EOF

# Push de la branche nettoyée
git push -u origin security/sanitize-secrets --force

echo "✓ Branche security/sanitize-secrets poussée"
echo ""
echo "========================================="
echo "  ✅ NETTOYAGE TERMINÉ"
echo "========================================="
echo ""
echo "📋 RÉSUMÉ :"
echo ""
echo "✓ Backup créé"
echo "✓ Secrets retirés du HEAD"
if [ "$NEED_PURGE" -eq 1 ] && [ "$PURGE_CONFIRM" = "PURGE" ]; then
    echo "✓ Historique purgé (force push fait)"
else
    echo "⏭ Historique non purgé (pas nécessaire ou skip)"
fi
echo "✓ Nouveaux secrets générés"
echo ""
echo "📄 FICHIERS CRÉÉS :"
echo "   - backend/.env.new (nouveaux secrets)"
echo "   - COLLABORATEURS_README.txt (instructions)"
echo ""
echo "🎯 PROCHAINES ACTIONS :"
echo ""
echo "1. Renomme backend/.env.new → backend/.env"
echo "2. Complète avec tes VRAIES nouvelles clés"
echo "3. Mets à jour Render + Vercel avec nouvelles clés"
echo "4. Teste localement : docker compose up + uvicorn"
echo "5. Redéploie backend + frontend"
echo ""
if [ "$NEED_PURGE" -eq 1 ] && [ "$PURGE_CONFIRM" = "PURGE" ]; then
    echo "⚠️  COLLABORATEURS : Envoie-leur COLLABORATEURS_README.txt"
    echo "   Ils doivent re-cloner le repo"
fi
echo ""
echo "========================================="
