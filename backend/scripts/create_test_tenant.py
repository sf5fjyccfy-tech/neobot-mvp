#!/usr/bin/env python3
"""
Création automatique d'un client de test pour NéoBot
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, create_tables
from app.models import Tenant, PlanType
from datetime import datetime

def create_test_tenant():
    print("👤 CRÉATION DU CLIENT TEST NÉOBOT...")
    
    db = SessionLocal()
    try:
        # Créer les tables si nécessaire
        create_tables()
        
        # Vérifier si le client test existe
        test_tenant = db.query(Tenant).filter(Tenant.email == 'test@neobot.cm').first()
        
        if not test_tenant:
            # Créer le client test
            test_tenant = Tenant(
                name='Restaurant NéoBot Test',
                email='test@neobot.cm',
                phone='+237612345678',
                business_type='restaurant',
                plan=PlanType.STANDARD,
                whatsapp_connected=True
            )
            test_tenant.activate_trial()
            
            db.add(test_tenant)
            db.commit()
            db.refresh(test_tenant)
            
            print(f"✅ CLIENT TEST CRÉÉ - ID: {test_tenant.id}")
            print(f"   📧 Email: test@neobot.cm")
            print(f"   🏢 Type: restaurant")
            print(f"   📱 WhatsApp: connecté")
        else:
            print(f"✅ CLIENT TEST EXISTANT - ID: {test_tenant.id}")
            
        return test_tenant.id
        
    except Exception as e:
        print(f"❌ Erreur création client: {e}")
        db.rollback()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    tenant_id = create_test_tenant()
    if tenant_id:
        print(f"🎯 ID CLIENT POUR TESTS: {tenant_id}")
    else:
        print("❌ Échec création client")
