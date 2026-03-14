"""
👤 CRM Service
Gère les données clients pour suivi et escalade
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class CRMService:
    """
    CRM pour gestion clients et historique
    """
    
    @staticmethod
    def get_or_create_customer(phone_number: str, tenant_id: int, customer_name: str, db: Session):
        """
        Récupère ou crée un enregistrement client
        
        Args:
            phone_number: Numéro WhatsApp
            tenant_id: ID du tenant
            customer_name: Nom du client (optionnel)
            db: Session database
            
        Returns:
            Objet Customer
        """
        from app.models import Conversation
        
        try:
            # Chercher une conversation existante pour ce phone
            conversation = db.query(Conversation).filter(
                Conversation.customer_phone == phone_number,
                Conversation.tenant_id == tenant_id
            ).first()
            
            # Si pas de conversation, ne rien créer - la conversation crée par le webhook
            if conversation:
                return conversation
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur get_or_create_customer: {str(e)}")
            return None
    
    @staticmethod
    def update_conversation_metadata(conversation_id: int, db: Session, **kwargs):
        """
        Met à jour les métadonnées de la conversation
        
        Args:
            conversation_id: ID de la conversation
            db: Session database
            **kwargs: Champs à mettre à jour
            
        Returns:
            Conversation mise à jour
        """
        from app.models import Conversation
        
        try:
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            
            if not conversation:
                return None
            
            # Update customer name if provided
            if "customer_name" in kwargs:
                conversation.customer_name = kwargs["customer_name"]
            
            conversation.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(conversation)
            
            logger.info(f"✅ Conversation {conversation_id} mise à jour")
            return conversation
            
        except Exception as e:
            logger.error(f"❌ Erreur update_conversation_metadata: {str(e)}")
            db.rollback()
            return None
    
    @staticmethod
    def get_customer_summary(conversation_id: int, db: Session) -> Dict:
        """
        Retourne un résumé du client pour l'IA
        
        Args:
            conversation_id: ID de la conversation
            db: Session database
            
        Returns:
            Dict avec infos client
        """
        from app.models import Conversation, Message
        
        try:
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            
            if not conversation:
                return {
                    "name": "Client",
                    "phone": "Inconnu",
                    "status": "unknown",
                    "message_count": 0,
                    "first_contact": "Jamais",
                    "last_contact": "Jamais",
                    "notes": "Aucune note"
                }
            
            # Compte les messages
            message_count = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).count()
            
            return {
                "name": conversation.customer_name or "Client",
                "phone": conversation.customer_phone,
                "status": conversation.status,
                "message_count": message_count,
                "first_contact": conversation.created_at.strftime("%d/%m/%Y") if conversation.created_at else "Inconnu",
                "last_contact": conversation.created_at.strftime("%d/%m/%Y") if conversation.created_at else "Jamais",
                "notes": ""
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur get_customer_summary: {str(e)}")
            return {}
    
    @staticmethod
    def get_customer_history_context(conversation_id: int, db: Session) -> str:
        """
        Crée un contexte client enrichi pour le prompt
        
        Args:
            conversation_id: ID de la conversation
            db: Session database
            
        Returns:
            Texte de contexte
        """
        from app.models import Conversation, Message
        
        try:
            summary = CRMService.get_customer_summary(conversation_id, db)
            
            context = f"""
PROFIL CLIENT:
- Nom: {summary.get('name', 'Inconnu')}
- Téléphone: {summary.get('phone', 'N/A')}
- Premiers contact: {summary.get('first_contact', 'Inconnu')}
- Nombre de messages: {summary.get('message_count', 0)}
- Statut: {summary.get('status', 'actif')}
"""
            return context
            
        except Exception as e:
            logger.error(f"❌ Erreur get_customer_history_context: {str(e)}")
            return ""
