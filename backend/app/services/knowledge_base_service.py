"""
Knowledge Base Service - Récupère les infos réelles du business depuis la BD
Cela transforme le bot générique en bot spécialisé au business
"""

import json
import logging
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

logger = logging.getLogger(__name__)

class KnowledgeBaseService:
    """Service pour récupérer et formater la connaissance métier du tenant"""
    
    @staticmethod
    def get_tenant_profile(db: Session, tenant_id: int) -> Dict:
        """
        Récupérer le profil complet du tenant (avec toutes ses données métier)
        Cela sera injecté dans le prompt IA pour qu'il réponde correctement
        """
        from ..models import Tenant, TenantBusinessConfig, BusinessTypeModel
        
        try:
            # 1. Récupérer le tenant
            tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
            if not tenant:
                logger.warning(f"Tenant {tenant_id} not found")
                return {}
            
            # 2. Récupérer la config business
            config = db.query(TenantBusinessConfig).filter(
                TenantBusinessConfig.tenant_id == tenant_id
            ).first()
            
            profile = {
                "tenant_id": tenant.id,
                "name": tenant.name or "NéoBot",
                "business_type": tenant.business_type or "neobot",
                "plan": str(tenant.plan) if tenant.plan else "neobot"
            }
            
            # 3. Ajouter les infos du config si existent
            if config:
                profile.update({
                    "company_name": config.company_name,
                    "company_description": config.company_description,
                    "tone": config.tone,
                    "selling_focus": config.selling_focus,
                    "products_services": json.loads(config.products_services) if isinstance(config.products_services, str) else config.products_services or []
                })
            else:
                # Valeurs par défaut si pas de config
                profile.update({
                    "company_name": tenant.name or "NéoBot",
                    "company_description": "",
                    "tone": "Professional, Friendly",
                    "selling_focus": "Quality, Efficiency",
                    "products_services": []
                })
            
            return profile
            
        except Exception as e:
            logger.error(f"Error getting tenant profile: {e}")
            return {}
    
    @staticmethod
    def format_profile_for_prompt(profile: Dict) -> str:
        """
        Formater le profil en texte pour injecter dans le prompt système
        Cela donne au bot les infos réelles à utiliser
        """
        if not profile:
            return ""
        
        text = f"""
PROFIL MÉTIER:
- Entreprise: {profile.get('company_name', 'sans nom')}
- Type: {profile.get('business_type', 'autre')}
- Ton: {profile.get('tone', 'professionnel')}
- Focus: {profile.get('selling_focus', 'qualité')}
- Description: {profile.get('company_description', '')}
"""
        
        # Ajouter les produits/services si existent
        products = profile.get('products_services', [])
        if products:
            text += "\nPRODUITS/SERVICES:\n"
            if isinstance(products, list):
                for item in products:
                    if isinstance(item, dict):
                        name = item.get('name', 'sans nom')
                        price = item.get('price', 'N/A')
                        desc = item.get('description', '')
                        text += f"- {name}: {price} FCFA"
                        if desc:
                            text += f" ({desc})"
                        text += "\n"
            elif isinstance(products, str):
                # Si c'est déjà une string, l'ajouter directement
                text += products + "\n"
        
        return text
    
    @staticmethod
    def create_default_neobot_profile(db: Session, tenant_id: int = 1) -> Dict:
        """
        Créer ou METTRE À JOUR le profil par défaut pour NéoBot (tenant 1)
        Remplace le profil existant avec les données NéoBot
        """
        from ..models import TenantBusinessConfig, BusinessTypeModel
        
        try:
            # 1. Chercher le profil existant
            existing = db.query(TenantBusinessConfig).filter(
                TenantBusinessConfig.tenant_id == tenant_id
            ).first()
            
            # 2. Récupérer le business type NéoBot
            neobot_type = db.query(BusinessTypeModel).filter(
                BusinessTypeModel.slug == "neobot"
            ).first()
            
            if not neobot_type:
                logger.error("BusinessType 'neobot' not found in database")
                return {}
            
            # 3. Données NéoBot complètes
            neobot_data = {
                "company_name": "NéoBot",
                "company_description": "Plateforme d'automatisation WhatsApp avec IA - Répondez à vos clients 24/7",
                "tone": "Professional, Friendly, Expert, Persuasif",
                "selling_focus": "Efficacité, Scaling, Support client",
                "products_services": json.dumps([
                    {
                        "name": "Basique",
                        "price": 20000,
                        "description": "2000 messages/mois + Réponses automatiques + Dashboard - Seul plan actif",
                        "features": ["2000 messages/mois", "Support email", "Réponses automatiques", "Dashboard", "Essai gratuit 7 jours"]
                    }
                ])
            }
            
            if existing:
                # METTRE À JOUR le profil existant
                logger.info(f"Updating profile for tenant {tenant_id} to NéoBot...")
                existing.business_type_id = neobot_type.id
                existing.company_name = neobot_data["company_name"]
                existing.company_description = neobot_data["company_description"]
                existing.tone = neobot_data["tone"]
                existing.selling_focus = neobot_data["selling_focus"]
                existing.products_services = neobot_data["products_services"]
                db.commit()
                logger.info(f"✅ NéoBot profile UPDATED for tenant {tenant_id}")
            else:
                # CRÉER un nouveau profil
                logger.info(f"Creating new NéoBot profile for tenant {tenant_id}...")
                neobot_profile = TenantBusinessConfig(
                    tenant_id=tenant_id,
                    business_type_id=neobot_type.id,
                    company_name=neobot_data["company_name"],
                    company_description=neobot_data["company_description"],
                    tone=neobot_data["tone"],
                    selling_focus=neobot_data["selling_focus"],
                    products_services=neobot_data["products_services"]
                )
                db.add(neobot_profile)
                db.commit()
                logger.info(f"✅ NéoBot profile CREATED for tenant {tenant_id}")
            
            return KnowledgeBaseService.get_tenant_profile(db, tenant_id)
            
        except Exception as e:
            logger.error(f"Error creating/updating NéoBot profile: {e}")
            db.rollback()
            return {}
    
    @staticmethod
    def get_rag_context(db: Session, tenant_id: int, query: str = "") -> str:
        """
        Retrieval Augmented Generation - Récupérer le contexte pertinent pour répondre
        """
        profile = KnowledgeBaseService.get_tenant_profile(db, tenant_id)
        if not profile:
            # Créer le profil par défaut si inexistant
            profile = KnowledgeBaseService.create_default_neobot_profile(db, tenant_id)
        
        return KnowledgeBaseService.format_profile_for_prompt(profile)
