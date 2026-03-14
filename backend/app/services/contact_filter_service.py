"""
Contact Filter Service - Whitelist/Blacklist pour contrôle IA
Phase 8M: Feature 1 - Trier contacts
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models import ContactSetting
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ContactFilterService:
    """Gère whitelist/blacklist de contacts par tenant"""
    
    @staticmethod
    def is_ai_enabled_for_contact(tenant_id: int, phone_number: str, db: Session) -> bool:
        """
        Vérifie si IA doit répondre à ce contact
        """
        setting = db.query(ContactSetting).filter(
            and_(
                ContactSetting.tenant_id == tenant_id,
                ContactSetting.phone_number == phone_number
            )
        ).first()
        
        # Par défaut, IA activée
        if not setting:
            return True
        
        return setting.ai_enabled
    
    @staticmethod
    def toggle_ai_for_contact(tenant_id: int, phone_number: str, 
                              ai_enabled: bool, db: Session) -> dict:
        """
        Active ou désactive IA pour un contact
        """
        setting = db.query(ContactSetting).filter(
            and_(
                ContactSetting.tenant_id == tenant_id,
                ContactSetting.phone_number == phone_number
            )
        ).first()
        
        if not setting:
            # Crée nouveau setting
            setting = ContactSetting(
                tenant_id=tenant_id,
                phone_number=phone_number,
                ai_enabled=ai_enabled
            )
            db.add(setting)
        else:
            setting.ai_enabled = ai_enabled
            setting.updated_at = datetime.utcnow()
        
        db.commit()
        
        status = "✅ Activé" if ai_enabled else "❌ Désactivé"
        logger.info(f"{status} IA pour {phone_number}")
        
        return {
            "phone_number": phone_number,
            "ai_enabled": ai_enabled,
            "message": f"IA {status.lower()} pour ce contact"
        }
    
    @staticmethod
    def get_all_contacts(tenant_id: int, db: Session) -> list:
        """
        Récupère tous les contacts avec leurs settings
        Triés par nombre de messages (décroissant)
        """
        contacts = db.query(ContactSetting).filter(
            ContactSetting.tenant_id == tenant_id
        ).order_by(
            ContactSetting.message_count.desc()
        ).all()
        
        return [
            {
                "phone_number": c.phone_number,
                "name": c.contact_name or "Sans nom",
                "ai_enabled": c.ai_enabled,
                "message_count": c.message_count,
                "first_seen": c.first_seen.isoformat() if c.first_seen else None,
                "last_seen": c.last_seen.isoformat() if c.last_seen else None
            }
            for c in contacts
        ]
    
    @staticmethod
    def get_disabled_contacts(tenant_id: int, db: Session) -> list:
        """
        Récupère seulement les contacts avec IA désactivée
        """
        contacts = db.query(ContactSetting).filter(
            and_(
                ContactSetting.tenant_id == tenant_id,
                ContactSetting.ai_enabled == False
            )
        ).order_by(
            ContactSetting.last_seen.desc()
        ).all()
        
        return [
            {
                "phone_number": c.phone_number,
                "name": c.contact_name or "Sans nom",
                "message_count": c.message_count,
                "last_seen": c.last_seen.isoformat() if c.last_seen else None
            }
            for c in contacts
        ]
    
    @staticmethod
    def bulk_disable_ai(tenant_id: int, phone_numbers: list, db: Session) -> dict:
        """
        Désactive IA pour plusieurs contacts à la fois
        """
        updated = 0
        
        for phone in phone_numbers:
            setting = db.query(ContactSetting).filter(
                and_(
                    ContactSetting.tenant_id == tenant_id,
                    ContactSetting.phone_number == phone
                )
            ).first()
            
            if not setting:
                setting = ContactSetting(
                    tenant_id=tenant_id,
                    phone_number=phone,
                    ai_enabled=False
                )
                db.add(setting)
            else:
                setting.ai_enabled = False
                setting.updated_at = datetime.utcnow()
            
            updated += 1
        
        db.commit()
        logger.info(f"⏹️ Désactivé IA pour {updated} contacts")
        
        return {
            "updated": updated,
            "message": f"IA désactivée pour {updated} contact(s)"
        }
    
    @staticmethod
    def bulk_enable_ai(tenant_id: int, phone_numbers: list, db: Session) -> dict:
        """
        Réactive IA pour plusieurs contacts à la fois
        """
        updated = 0
        
        for phone in phone_numbers:
            setting = db.query(ContactSetting).filter(
                and_(
                    ContactSetting.tenant_id == tenant_id,
                    ContactSetting.phone_number == phone
                )
            ).first()
            
            if not setting:
                setting = ContactSetting(
                    tenant_id=tenant_id,
                    phone_number=phone,
                    ai_enabled=True
                )
                db.add(setting)
            else:
                setting.ai_enabled = True
                setting.updated_at = datetime.utcnow()
            
            updated += 1
        
        db.commit()
        logger.info(f"✅ Réactivé IA pour {updated} contacts")
        
        return {
            "updated": updated,
            "message": f"IA réactivée pour {updated} contact(s)"
        }
    
    @staticmethod
    def update_contact_info(tenant_id: int, phone_number: str, 
                           name: str = None, db: Session = None) -> dict:
        """
        Met à jour les infos d'un contact
        """
        setting = db.query(ContactSetting).filter(
            and_(
                ContactSetting.tenant_id == tenant_id,
                ContactSetting.phone_number == phone_number
            )
        ).first()
        
        if not setting:
            setting = ContactSetting(
                tenant_id=tenant_id,
                phone_number=phone_number
            )
            db.add(setting)
        
        if name:
            setting.contact_name = name
        
        setting.last_seen = datetime.utcnow()
        setting.message_count = (setting.message_count or 0) + 1
        db.commit()
        
        return {
            "phone_number": phone_number,
            "name": setting.contact_name,
            "message_count": setting.message_count
        }
