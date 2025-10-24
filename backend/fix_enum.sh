#!/bin/bash
# Correction des types Enum PostgreSQL manquants

cd ~/neobot-mvp/backend
source venv/bin/activate

echo "🔧 Correction des types Enum PostgreSQL..."

# 1. Se connecter à PostgreSQL et créer les types Enum manquants
docker exec -i neobot_postgres psql -U neobot -d neobot << 'EOF'
-- Créer les types Enum s'ils n'existent pas
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'plantype') THEN
        CREATE TYPE plantype AS ENUM ('basique', 'standard', 'pro');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'whatsappprovider') THEN
        CREATE TYPE whatsappprovider AS ENUM ('wasender_api', 'whatsapp_business_api');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'paymentprovider') THEN
        CREATE TYPE paymentprovider AS ENUM ('pawapay', 'orange_money');
    END IF;
END $$;

-- Vérifier que les types sont créés
SELECT typname FROM pg_type WHERE typname IN ('plantype', 'whatsappprovider', 'paymentprovider');
EOF

# 2. Maintenant appliquer la migration
echo "⬆️ Application de la migration..."
alembic upgrade head

# 3. Vérifier que tout fonctionne
echo "🔍 Vérification des tables..."
docker exec -i neobot_postgres psql -U neobot -d neobot << 'EOF'
-- Lister toutes les tables
\dt

-- Vérifier la structure de la table tenants
\d tenants

-- Compter les enregistrements
SELECT 'tenants' as table_name, COUNT(*) as count FROM tenants
UNION ALL
SELECT 'conversations', COUNT(*) FROM conversations
UNION ALL
SELECT 'messages', COUNT(*) FROM messages;
EOF

echo "✅ Types Enum créés et migration appliquée avec succès"
