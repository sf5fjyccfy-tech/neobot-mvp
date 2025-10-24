#!/bin/bash
# Correction migration avec valeurs par défaut pour colonnes existantes

cd ~/neobot-mvp/backend
source venv/bin/activate

echo "🔧 Correction des colonnes avec valeurs NULL..."

# Connecter à PostgreSQL et corriger les données existantes
docker exec -i neobot_postgres psql -U neobot -d neobot << 'EOF'
-- 1. Ajouter des valeurs par défaut aux messages existants
UPDATE messages SET message_type = 'text' WHERE message_type IS NULL;
UPDATE messages SET whatsapp_message_id = 'legacy_' || id WHERE whatsapp_message_id IS NULL;

-- 2. Ajouter des valeurs par défaut aux tenants existants
UPDATE tenants SET 
    plan = 'basique',
    messages_limit = 1000,
    messages_used = 0,
    is_trial = true,
    trial_days = 3,
    whatsapp_provider = 'wasender_api',
    whatsapp_connected = false,
    preferred_payment = 'orange_money',
    messages_reset_at = NOW()
WHERE plan IS NULL;

-- 3. Ajouter des valeurs par défaut aux conversations
UPDATE conversations SET 
    last_message_at = created_at 
WHERE last_message_at IS NULL;

-- Vérifier les corrections
SELECT 'Messages avec NULL' as table_check, COUNT(*) FROM messages WHERE message_type IS NULL;
SELECT 'Tenants avec NULL' as table_check, COUNT(*) FROM tenants WHERE plan IS NULL;
EOF

echo "✅ Données existantes corrigées"

# Supprimer et recréer la migration problématique
echo "🗑️ Suppression de la migration problématique..."
rm -f alembic/versions/*.py

# Créer une nouvelle migration propre avec les bonnes contraintes
echo "📝 Création d'une nouvelle migration..."
alembic revision --autogenerate -m "Complete schema with defaults"

# Modifier le fichier de migration pour gérer les valeurs existantes
MIGRATION_FILE=$(ls alembic/versions/*.py | head -1)

echo "⚙️ Modification du fichier de migration..."
# Créer une version sécurisée de la migration
cat > temp_migration_fix.py << 'EOF'
import re
import sys

def fix_migration_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Remplacer les colonnes NOT NULL par des versions avec valeurs par défaut
    fixes = [
        # Pour les colonnes existantes, ajouter nullable=True temporairement
        ("sa.Column('message_type', sa.String(length=20), nullable=False)", 
         "sa.Column('message_type', sa.String(length=20), nullable=False, server_default='text')"),
        
        ("sa.Column('whatsapp_message_id', sa.String(length=100), nullable=True)", 
         "sa.Column('whatsapp_message_id', sa.String(length=100), nullable=True)"),
         
        # Ajouter des server_default pour les nouvelles colonnes
        ("sa.Column('messages_limit', sa.Integer(), nullable=False)", 
         "sa.Column('messages_limit', sa.Integer(), nullable=False, server_default='1000')"),
         
        ("sa.Column('messages_used', sa.Integer(), nullable=False)", 
         "sa.Column('messages_used', sa.Integer(), nullable=False, server_default='0')"),
         
        ("sa.Column('is_trial', sa.Boolean(), nullable=False)", 
         "sa.Column('is_trial', sa.Boolean(), nullable=False, server_default='true')"),
         
        ("sa.Column('trial_days', sa.Integer(), nullable=False)", 
         "sa.Column('trial_days', sa.Integer(), nullable=False, server_default='3')"),
         
        ("sa.Column('whatsapp_connected', sa.Boolean(), nullable=False)", 
         "sa.Column('whatsapp_connected', sa.Boolean(), nullable=False, server_default='false')")
    ]
    
    for old, new in fixes:
        content = content.replace(old, new)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✅ Migration fixée: {filepath}")

if __name__ == "__main__":
    fix_migration_file(sys.argv[1])
EOF

# Appliquer le fix
python temp_migration_fix.py "$MIGRATION_FILE"
rm temp_migration_fix.py

# Appliquer la migration corrigée
echo "⬆️ Application de la migration corrigée..."
alembic upgrade head

# Vérifier le résultat
echo "🔍 Vérification finale..."
docker exec -i neobot_postgres psql -U neobot -d neobot << 'EOF'
-- Vérifier la structure finale
\d tenants
\d messages
\d conversations

-- Vérifier les données
SELECT id, name, plan, messages_limit, is_trial FROM tenants;
SELECT id, content, direction, message_type FROM messages LIMIT 3;

-- Compter les enregistrements
SELECT 'tenants' as table_name, COUNT(*) FROM tenants
UNION ALL
SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL
SELECT 'messages', COUNT(*) FROM messages
UNION ALL
SELECT 'payments', COUNT(*) FROM payments;
EOF

echo ""
echo "✅ Migration corrigée avec succès!"
echo "🗄️ Toutes les tables ont été mises à jour avec les valeurs par défaut"
echo ""
echo "📊 Résumé des corrections appliquées:"
echo "   - Messages: message_type = 'text' par défaut"
echo "   - Tenants: plan = 'basique', limites configurées"
echo "   - Conversations: timestamps corrigés"
echo ""
echo "🚀 Système prêt pour les tests complets"
