#!/usr/bin/env python3
"""
Configuration du Tenant 1 comme NéoBot
Script d'installation du business intelligence system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Tenant, TenantBusinessConfig, BusinessTypeModel
from app.services.business_kb_service import BusinessKBService
import json

def setup():
    """Configurer le système complet"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("🚀 SETUP NEOBOT - Business Intelligence System")
        print("="*60)
        
        # ÉTAPE 1: Initialiser les business types
        print("\n1️⃣  Initialisation des types de business...")
        try:
            BusinessKBService.initialize_business_types(db)
            types = db.query(BusinessTypeModel).count()
            print(f"   ✅ {types} types de business créés")
        except Exception as e:
            print(f"   ⚠️  Types déjà créés (ou erreur: {e})")
        
        # ÉTAPE 2: Vérifier le tenant 1
        print("\n2️⃣  Vérification du Tenant 1...")
        tenant = db.query(Tenant).filter(Tenant.id == 1).first()
        if tenant:
            print(f"   ✅ Tenant trouvé: {tenant.name}")
        else:
            print("   ❌ ERREUR: Tenant 1 n'existe pas!")
            return False
        
        # ÉTAPE 3: Configurer le tenant 1 comme NéoBot
        print("\n3️⃣  Configuration du Tenant 1 comme NéoBot...")
        
        # Chercher le business type "neobot"
        neobot_type = db.query(BusinessTypeModel).filter(
            BusinessTypeModel.slug == "neobot"
        ).first()
        
        if not neobot_type:
            print("   ❌ ERREUR: Business type 'neobot' n'existe pas!")
            return False
        
        # Chercher la config existante
        existing_config = db.query(TenantBusinessConfig).filter(
            TenantBusinessConfig.tenant_id == 1
        ).first()
        
        if existing_config:
            # Mettre à jour
            existing_config.business_type_id = neobot_type.id
            existing_config.company_name = "NéoBot"
            existing_config.company_description = "Plateforme d'automatisation WhatsApp avec IA - Vendre NéoBot"
            existing_config.tone = "Professional, Friendly, Expert"
            existing_config.selling_focus = "Automatisation, Efficacité, Scaling"
            existing_config.products_services = json.dumps([
                {
                    "name": "NéoBot Starter",
                    "price": 20000,
                    "description": "Plan de base - 500 messages/mois + Support"
                },
                {
                    "name": "NéoBot Pro",
                    "price": 50000,
                    "description": "Plan professionnel - Messages illimités + Analytics + API"
                },
                {
                    "name": "NéoBot Enterprise",
                    "price": 100000,
                    "description": "Plan enterprise - Tout illimité + Serveur dédié + Support prioritaire"
                },
                {
                    "name": "Integration Setup",
                    "price": 5000,
                    "description": "Configuration gratuite de l'intégration WhatsApp"
                }
            ])
            db.commit()
            print("   ✅ Configuration mise à jour")
        else:
            # Créer
            new_config = TenantBusinessConfig(
                tenant_id=1,
                business_type_id=neobot_type.id,
                company_name="NéoBot",
                company_description="Plateforme d'automatisation WhatsApp avec IA - Vendre NéoBot",
                tone="Professional, Friendly, Expert",
                selling_focus="Automatisation, Efficacité, Scaling",
                products_services=json.dumps([
                    {
                        "name": "NéoBot Starter",
                        "price": 20000,
                        "description": "Plan de base - 500 messages/mois + Support"
                    },
                    {
                        "name": "NéoBot Pro",
                        "price": 50000,
                        "description": "Plan professionnel - Messages illimités + Analytics + API"
                    },
                    {
                        "name": "NéoBot Enterprise",
                        "price": 100000,
                        "description": "Plan enterprise - Tout illimité + Serveur dédié + Support prioritaire"
                    },
                    {
                        "name": "Integration Setup",
                        "price": 5000,
                        "description": "Configuration gratuite de l'intégration WhatsApp"
                    }
                ])
            )
            db.add(new_config)
            db.commit()
            print("   ✅ Configuration créée")
        
        # ÉTAPE 4: Vérification
        print("\n4️⃣  Vérification finale...")
        config = db.query(TenantBusinessConfig).filter(
            TenantBusinessConfig.tenant_id == 1
        ).first()
        
        if config:
            products = json.loads(config.products_services) if isinstance(config.products_services, str) else config.products_services
            print(f"   ✅ Business: {config.company_name}")
            print(f"   ✅ Type: {neobot_type.name}")
            print(f"   ✅ Produits: {len(products)} plans offering")
            print(f"   ✅ Ton: {config.tone}")
        else:
            print("   ❌ ERREUR: Config non trouvée après création!")
            return False
        
        print("\n" + "="*60)
        print("✅ SETUP COMPLETED - NéoBot Tenant Ready!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = setup()
    sys.exit(0 if success else 1)
