"""
Response Delay Service - Gère délai modulable des réponses
Phase 8M: Feature 3 - Temps de réponse modulable
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models import TenantSettings, QueuedMessage, ConversationHumanState
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ResponseDelayService:
    """Gère les délais de réponse pour paraître plus naturel"""
    
    # Délais disponibles
    DELAY_OPTIONS = {
        0: ("Instantané", 0),
        15: ("Rapide", 15),
        30: ("Normal", 30),
        60: ("Modéré", 60),
        120: ("Très modéré", 120)
    }
    
    @staticmethod
    def get_tenant_delay(tenant_id: int, db: Session) -> int:
        """
        Récupère délai configuré du tenant (par défaut: 30s)
        """
        settings = db.query(TenantSettings).filter(
            TenantSettings.tenant_id == tenant_id
        ).first()
        
        if not settings:
            # Crée setting par défaut
            settings = TenantSettings(
                tenant_id=tenant_id,
                response_delay_seconds=30
            )
            db.add(settings)
            db.commit()
            return 30
        
        return settings.response_delay_seconds
    
    @staticmethod
    def get_contact_specific_delay(tenant_id: int, phone_number: str, db: Session) -> int:
        """
        Récupère délai spécifique à un contact (si configuré)
        Sinon retourne délai par défaut du tenant
        """
        settings = db.query(TenantSettings).filter(
            TenantSettings.tenant_id == tenant_id
        ).first()
        
        if not settings:
            return 30  # Default
        
        # Vérifier override pour ce contact
        if settings.contact_delays and phone_number in settings.contact_delays:
            delay = settings.contact_delays[phone_number]
            logger.info(f"⏱️ Délai custom pour {phone_number}: {delay}s")
            return delay
        
        return settings.response_delay_seconds
    
    @staticmethod
    def set_tenant_delay(tenant_id: int, delay_seconds: int, db: Session) -> dict:
        """
        Configure le délai par défaut du tenant
        Doit être l'une des valeurs DELAY_OPTIONS
        """
        if delay_seconds not in ResponseDelayService.DELAY_OPTIONS:
            return {
                "error": f"Délai invalide. Options valides: {list(ResponseDelayService.DELAY_OPTIONS.keys())}",
                "valid_options": ResponseDelayService.DELAY_OPTIONS
            }
        
        settings = db.query(TenantSettings).filter(
            TenantSettings.tenant_id == tenant_id
        ).first()
        
        if not settings:
            settings = TenantSettings(
                tenant_id=tenant_id,
                response_delay_seconds=delay_seconds
            )
            db.add(settings)
        else:
            settings.response_delay_seconds = delay_seconds
            settings.updated_at = datetime.utcnow()
        
        db.commit()
        
        label, _ = ResponseDelayService.DELAY_OPTIONS[delay_seconds]
        logger.info(f"⏱️ Délai tenant {tenant_id} configuré: {label} ({delay_seconds}s)")
        
        return {
            "tenant_id": tenant_id,
            "delay_seconds": delay_seconds,
            "label": label,
            "message": f"Délai configuré: {label}"
        }
    
    @staticmethod
    def set_contact_specific_delay(tenant_id: int, phone_number: str, 
                                  delay_seconds: int, db: Session) -> dict:
        """
        Configure un délai spécifique pour un contact
        """
        if delay_seconds not in ResponseDelayService.DELAY_OPTIONS:
            return {
                "error": f"Délai invalide. Options valides: {list(ResponseDelayService.DELAY_OPTIONS.keys())}",
                "valid_options": ResponseDelayService.DELAY_OPTIONS
            }
        
        settings = db.query(TenantSettings).filter(
            TenantSettings.tenant_id == tenant_id
        ).first()
        
        if not settings:
            settings = TenantSettings(
                tenant_id=tenant_id,
                contact_delays={phone_number: delay_seconds}
            )
            db.add(settings)
        else:
            if settings.contact_delays is None:
                settings.contact_delays = {}
            settings.contact_delays[phone_number] = delay_seconds
            settings.updated_at = datetime.utcnow()
        
        db.commit()
        
        label, _ = ResponseDelayService.DELAY_OPTIONS[delay_seconds]
        logger.info(f"⏱️ Délai custom {phone_number}: {label} ({delay_seconds}s)")
        
        return {
            "phone_number": phone_number,
            "delay_seconds": delay_seconds,
            "label": label,
            "message": f"Délai configuré pour ce contact: {label}"
        }
    
    @staticmethod
    async def queue_response(conversation_id: int, 
                            phone_number: str, 
                            tenant_id: int,
                            response_text: str,
                            db: Session) -> dict:
        """
        Met en queue une réponse avec délai approprié
        """
        # Récupère délai
        delay = ResponseDelayService.get_contact_specific_delay(
            tenant_id, 
            phone_number, 
            db
        )
        
        # Vérifie pas d'intervention humain
        state = db.query(ConversationHumanState).filter(
            ConversationHumanState.conversation_id == conversation_id
        ).first()
        
        if state and state.human_active:
            logger.info(f"🚫 Pas de queue (humain actif) pour {conversation_id}")
            return {
                "queued": False,
                "reason": "Humain actif sur cette conversation",
                "message": "Message non envoyé (humain en conversation)"
            }
        
        # Crée queue item
        send_at = datetime.utcnow() + timedelta(seconds=delay)
        
        queued_msg = QueuedMessage(
            conversation_id=conversation_id,
            phone_number=phone_number,
            tenant_id=tenant_id,
            response_text=response_text,
            send_at=send_at,
            sent=False
        )
        db.add(queued_msg)
        db.commit()
        
        label, _ = ResponseDelayService.DELAY_OPTIONS.get(delay, ("Custom", delay))
        logger.info(f"📅 Réponse en queue, envoi dans {delay}s ({label})")
        
        return {
            "queued": True,
            "conversation_id": conversation_id,
            "phone_number": phone_number,
            "send_at": send_at.isoformat(),
            "delay_seconds": delay,
            "delay_label": label,
            "message": f"Réponse en queue, envoi dans {delay}s"
        }
    
    @staticmethod
    async def send_queued_messages(db: Session) -> dict:
        """
        Task périodique (toutes les secondes): envoie les messages en queue dont le délai est passé
        À appeler dans un background task
        """
        now = datetime.utcnow()
        
        # Trouve messages à envoyer
        pending = db.query(QueuedMessage).filter(
            and_(
                QueuedMessage.send_at <= now,
                QueuedMessage.sent == False
            )
        ).all()
        
        sent_count = 0
        
        for item in pending:
            try:
                # Vérifie toujours pas d'humain actif
                state = db.query(ConversationHumanState).filter(
                    ConversationHumanState.conversation_id == item.conversation_id
                ).first()
                
                if state and state.human_active:
                    # Rémet en queue (attendre fin intervention humain)
                    item.send_at = datetime.utcnow() + timedelta(seconds=60)
                    db.commit()
                    logger.info(f"⏸️ {item.id}: Report envoi (humain actif)")
                    continue
                
                # TODO: Appeler Baileys pour envoyer le message
                # await baileys_service.send_message(item.phone_number, item.response_text)
                
                item.sent = True
                item.sent_at = now
                db.commit()
                
                sent_count += 1
                logger.info(f"✅ Message {item.id} envoyé après délai")
                
            except Exception as e:
                logger.error(f"❌ Erreur envoi message {item.id}: {e}")
                item.retry_count = (item.retry_count or 0) + 1
                item.last_retry_at = now
                
                # Après 3 tentatives, donne up
                if item.retry_count >= 3:
                    item.sent = False  # Marque comme failed
                    logger.error(f"❌ Message {item.id}: donnée up après 3 tentatives")
                
                db.commit()
        
        logger.info(f"📊 Queue: {sent_count} messages envoyés")
        
        return {
            "sent": sent_count,
            "pending": len(pending),
            "message": f"{sent_count} messages envoyés"
        }
    
    @staticmethod
    def get_tenant_settings(tenant_id: int, db: Session) -> dict:
        """
        Récupère tous les settings du tenant
        """
        settings = db.query(TenantSettings).filter(
            TenantSettings.tenant_id == tenant_id
        ).first()
        
        if not settings:
            return {
                "tenant_id": tenant_id,
                "response_delay_seconds": 30,
                "response_delay_label": "Normal",
                "contact_delays": {},
                "message": "Configuration par défaut"
            }
        
        label, _ = ResponseDelayService.DELAY_OPTIONS.get(
            settings.response_delay_seconds,
            ("Custom", settings.response_delay_seconds)
        )
        
        return {
            "tenant_id": tenant_id,
            "response_delay_seconds": settings.response_delay_seconds,
            "response_delay_label": label,
            "contact_delays": settings.contact_delays or {},
            "available_options": ResponseDelayService.DELAY_OPTIONS
        }
    
    @staticmethod
    def get_pending_queue(tenant_id: int, db: Session) -> dict:
        """
        Récupère les messages en attente pour ce tenant
        """
        pending = db.query(QueuedMessage).filter(
            and_(
                QueuedMessage.tenant_id == tenant_id,
                QueuedMessage.sent == False
            )
        ).all()
        
        return {
            "tenant_id": tenant_id,
            "pending_count": len(pending),
            "pending_messages": [
                {
                    "id": msg.id,
                    "phone_number": msg.phone_number,
                    "send_at": msg.send_at.isoformat(),
                    "time_remaining_seconds": max(0, int((msg.send_at - datetime.utcnow()).total_seconds()))
                }
                for msg in pending
            ]
        }
