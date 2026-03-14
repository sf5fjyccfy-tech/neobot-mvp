"""
Service de mapping WhatsApp - Phone number to Tenant mapping
"""
from sqlalchemy.orm import Session
from app.models import WhatsAppSession
import logging

logger = logging.getLogger(__name__)

class WhatsAppMappingService:
    """Service pour mapper les numéros WhatsApp aux tenants"""
    
    @staticmethod
    def get_tenant_from_phone(phone: str, db: Session) -> int | None:
        """
        Récupère le tenant_id associé à un numéro WhatsApp
        
        Args:
            phone: Numéro WhatsApp (format: "221780123456")
            db: Session de base de données
            
        Returns:
            tenant_id ou None si pas trouvé
        """
        session = db.query(WhatsAppSession).filter(
            WhatsAppSession.whatsapp_phone == phone
        ).first()
        
        if not session:
            logger.warning(f"⚠️  No tenant found for phone: {phone}")
            return None
        
        logger.info(f"✅ Mapped phone {phone} -> tenant {session.tenant_id}")
        return session.tenant_id
    
    @staticmethod
    def get_phone_from_tenant(tenant_id: int, db: Session) -> str | None:
        """
        Récupère le numéro WhatsApp associé à un tenant
        
        Args:
            tenant_id: ID du tenant
            db: Session de base de données
            
        Returns:
            whatsapp_phone ou None si pas trouvé
        """
        session = db.query(WhatsAppSession).filter(
            WhatsAppSession.tenant_id == tenant_id
        ).first()
        
        if not session:
            logger.warning(f"⚠️  No WhatsApp phone found for tenant: {tenant_id}")
            return None
        
        return session.whatsapp_phone
    
    @staticmethod
    def is_tenant_connected(tenant_id: int, db: Session) -> bool:
        """
        Vérifie si un tenant est connecté à WhatsApp
        """
        session = db.query(WhatsAppSession).filter(
            WhatsAppSession.tenant_id == tenant_id
        ).first()
        
        if not session:
            return False
        
        return session.is_connected
    
    @staticmethod
    def create_session(tenant_id: int, whatsapp_phone: str, db: Session) -> WhatsAppSession:
        """
        Crée une nouvelle session WhatsApp
        """
        new_session = WhatsAppSession(
            tenant_id=tenant_id,
            whatsapp_phone=whatsapp_phone,
            is_connected=False,
            failed_attempts=0,
        )
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        logger.info(f"✅ WhatsApp session created: tenant={tenant_id}, phone={whatsapp_phone}")
        return new_session
    
    @staticmethod
    def mark_connected(tenant_id: int, db: Session):
        """
        Marque une session comme connectée
        """
        session = db.query(WhatsAppSession).filter(
            WhatsAppSession.tenant_id == tenant_id
        ).first()
        
        if session:
            session.is_connected = True
            session.failed_attempts = 0
            db.commit()
            logger.info(f"✅ Tenant {tenant_id} marked as connected")
    
    @staticmethod
    def mark_disconnected(tenant_id: int, db: Session):
        """
        Marque une session comme déconnectée
        """
        session = db.query(WhatsAppSession).filter(
            WhatsAppSession.tenant_id == tenant_id
        ).first()
        
        if session:
            session.is_connected = False
            session.failed_attempts += 1
            db.commit()
            logger.warning(f"⚠️  Tenant {tenant_id} marked as disconnected (attempts: {session.failed_attempts})")
