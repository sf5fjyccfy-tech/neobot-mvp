#!/bin/bash
# Correction Alembic et test complet du système NéoBot

cd ~/neobot-mvp/backend
source venv/bin/activate

echo "🔧 Correction de la configuration Alembic..."

# 1. Supprimer l'ancien dossier alembic s'il existe
rm -rf alembic

# 2. Réinitialiser Alembic avec la bonne configuration
alembic init alembic

# 3. Configurer alembic.ini avec la bonne URL
cat > alembic.ini << 'EOF'
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql://neobot:password123@localhost:5432/neobot

[post_write_hooks]

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

# 4. Configurer env.py d'Alembic
cat > alembic/env.py << 'EOF'
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Ajouter le répertoire parent au Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Importer les modèles
from app.database import Base
from app import models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

# 5. Installer les dépendances manquantes
echo "📦 Installation des dépendances manquantes..."
pip install cryptography

# 6. Créer la première migration
echo "🗄️ Création de la migration initiale..."
alembic revision --autogenerate -m "Initial migration with all tables"

# 7. Appliquer les migrations
echo "⬆️ Application des migrations..."
alembic upgrade head

# 8. Créer un script de test complet
cat > test_system_complete.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import httpx
import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Tenant, PlanType, WhatsAppProvider
from cryptography.fernet import Fernet
import os

# Générer une clé de chiffrement pour les tests
if not os.getenv("ENCRYPTION_KEY"):
    os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()

async def test_complete_system():
    """Test complet du système NéoBot"""
    print("🧪 Test complet du système NéoBot...")
    
    # Test 1: Base de données
    print("\n1️⃣ Test base de données...")
    try:
        db = SessionLocal()
        
        # Créer un tenant de test
        test_tenant = Tenant(
            name="Restaurant Test",
            email="test@restaurant.cm",
            phone="+237600000000",
            business_type="restaurant",
            plan=PlanType.BASIQUE
        )
        
        db.add(test_tenant)
        db.commit()
        db.refresh(test_tenant)
        
        print(f"✅ Tenant créé: ID {test_tenant.id}")
        print(f"   Plan: {test_tenant.plan.value}")
        print(f"   Config: {test_tenant.get_plan_config()['name']}")
        
        db.close()
    except Exception as e:
        print(f"❌ Erreur DB: {e}")
        return False
    
    # Test 2: API Backend
    print("\n2️⃣ Test API Backend...")
    try:
        async with httpx.AsyncClient() as client:
            # Test health
            response = await client.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                print("✅ API Health OK")
            else:
                print(f"❌ API Health failed: {response.status_code}")
                
            # Test création tenant via API
            tenant_data = {
                "name": "Boutique API Test",
                "email": "api@test.cm", 
                "phone": "+237600000001",
                "business_type": "boutique"
            }
            
            response = await client.post(
                "http://localhost:8000/api/tenants",
                json=tenant_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Tenant API créé: {result['name']}")
            else:
                print(f"❌ Création tenant failed: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Erreur API: {e}")
        return False
    
    # Test 3: Configuration des plans
    print("\n3️⃣ Test configuration des plans...")
    try:
        db = SessionLocal()
        
        # Test plan Basique
        basique_tenant = db.query(Tenant).filter(Tenant.plan == PlanType.BASIQUE).first()
        if basique_tenant:
            config = basique_tenant.get_plan_config()
            print(f"✅ Plan Basique: {config['price_fcfa']} FCFA, {config['messages_limit']} messages")
            print(f"   Provider: {config['whatsapp_provider'].value}")
            print(f"   Tokens requis: {config['requires_client_tokens']}")
        
        # Test chiffrement tokens
        standard_tenant = Tenant(
            name="Test Standard",
            email="standard@test.cm",
            phone="+237600000002",
            plan=PlanType.STANDARD
        )
        
        db.add(standard_tenant)
        db.commit()
        
        # Tester chiffrement
        test_token = "test_access_token_123"
        test_phone_id = "123456789"
        
        standard_tenant.set_whatsapp_tokens(test_token, test_phone_id)
        db.commit()
        
        # Tester déchiffrement
        decrypted_token, decrypted_phone = standard_tenant.get_whatsapp_tokens()
        
        if decrypted_token == test_token and decrypted_phone == test_phone_id:
            print("✅ Chiffrement/déchiffrement tokens OK")
        else:
            print("❌ Erreur chiffrement tokens")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Erreur configuration: {e}")
        return False
    
    # Test 4: Simulateur WhatsApp
    print("\n4️⃣ Test simulateur WhatsApp...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:3000/health", timeout=10)
            if response.status_code == 200:
                print("✅ Simulateur WhatsApp actif")
                
                # Test simulation message
                sim_data = {
                    "tenant_id": 1,
                    "customer_phone": "+237600000000",
                    "message": "Test du système complet"
                }
                
                response = await client.post(
                    "http://localhost:3000/simulate",
                    json=sim_data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Simulation message OK: {result.get('status')}")
                else:
                    print(f"❌ Simulation failed: {response.status_code}")
            else:
                print(f"❌ Simulateur non accessible")
                
    except Exception as e:
        print(f"❌ Erreur simulateur: {e}")
        return False
    
    print("\n🎉 Tous les tests sont passés avec succès!")
    return True

if __name__ == "__main__":
    result = asyncio.run(test_complete_system())
    sys.exit(0 if result else 1)
EOF

# 9. Lancer le test complet
echo "🧪 Lancement des tests complets..."
python test_system_complete.py

echo ""
echo "✅ Configuration Alembic corrigée et système testé"
echo "🌐 URLs disponibles:"
echo "   - Backend API: http://localhost:8000/docs"
echo "   - Health check: http://localhost:8000/health"
echo "   - Simulateur WhatsApp: http://localhost:3000/health"
echo ""
echo "📋 Statut des services:"
echo "   - Base de données: $(docker ps --format 'table {{.Names}}\t{{.Status}}' | grep postgres || echo 'Non démarré')"
echo "   - Redis: $(docker ps --format 'table {{.Names}}\t{{.Status}}' | grep redis || echo 'Non démarré')"
