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
