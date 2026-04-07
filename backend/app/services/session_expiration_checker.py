"""
Session Expiration Checker - Gère expiration QR code et sessions Baileys
Phase 8M: Session Management
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models import WhatsAppSessionQR
import logging
import asyncio

logger = logging.getLogger(__name__)


class SessionExpirationChecker:
    """Détecte et gère expiration des sessions et QR codes"""
    
    @staticmethod
    async def check_qr_expiration(session_id: str, db: Session) -> dict:
        """
        Vérifie si QR code expiré (2 min max)
        """
        session = db.query(WhatsAppSessionQR).filter(
            WhatsAppSessionQR.session_id == session_id
        ).first()
        
        if not session:
            return {
                "error": "Session not found",
                "status": "not_found"
            }
        
        now = datetime.utcnow()
        
        # QR code expire après 2 minutes
        if session.qr_expires_at and now > session.qr_expires_at:
            session.status = "expired"
            db.commit()
            
            logger.warning(f"⏰ QR code expiré pour {session_id}")
            
            return {
                "status": "expired",
                "message": "QR code expiré (2 minutes dépassées)",
                "can_regenerate": True,
                "expired_at": session.qr_expires_at.isoformat()
            }
        
        # Si en attente de scan
        if session.status == "pending":
            expires_in = (session.qr_expires_at - now).total_seconds() if session.qr_expires_at else 0
            
            return {
                "status": "pending",
                "expires_in_seconds": max(0, int(expires_in)),
                "message": f"Scannez avant {max(0, int(expires_in))}s",
                "phone_number": session.phone_number
            }
        
        # Si connecté
        if session.status == "connected":
            return {
                "status": "connected",
                "phone_number": session.phone_number,
                "connected_at": session.connected_at.isoformat() if session.connected_at else None,
                "last_activity": session.last_activity.isoformat() if session.last_activity else None,
                "message": "✅ Connecté et actif"
            }
        
        return {
            "status": session.status,
            "phone_number": session.phone_number
        }
    
    @staticmethod
    async def check_session_expiration(session_id: str, db: Session) -> bool:
        """
        Vérifie si session globale expirée (30 jours inactivité)
        Retourne True si expiré
        """
        session = db.query(WhatsAppSessionQR).filter(
            WhatsAppSessionQR.session_id == session_id
        ).first()
        
        if not session:
            return False
        
        now = datetime.utcnow()
        
        # Expire après 30 jours d'inactivité
        if session.session_expires_at and now > session.session_expires_at:
            session.status = "expired"
            db.commit()
            logger.warning(f"⏰ Session {session_id} expirée (30 jours)")
            return True
        
        # Ou si inactivité depuis >30 jours
        if session.last_activity:
            days_inactive = (now - session.last_activity).days
            if days_inactive > 30:
                session.status = "expired"
                db.commit()
                logger.warning(f"⏰ Session {session_id} inactive depuis {days_inactive} jours")
                return True
        
        return False
    
    @staticmethod
    async def regenerate_qr_code(session_id: str, db: Session) -> dict:
        """
        Régénère nouveau QR code pour session
        """
        session = db.query(WhatsAppSessionQR).filter(
            WhatsAppSessionQR.session_id == session_id
        ).first()
        
        if not session:
            return {
                "error": "Session not found",
                "status": "failed"
            }
        
        # Si connecté, déconnecte d'abord
        if session.status == "connected":
            # Importer ici pour éviter imports circulaires
            try:
                from .baileys_service import BaileysService
                await BaileysService.logout(session_id)
                logger.info(f"🔌 Déconnecte session {session_id}")
            except Exception as e:
                logger.error(f"Erreur logout: {e}")
        
        # TODO: Générer nouveau QR avec Baileys
        # Pour l'instant, simulation
        now = datetime.utcnow()
        session.status = "pending"
        session.qr_generated_at = now
        session.qr_expires_at = now + timedelta(minutes=2)
        session.phone_number = None  # Reset phone
        session.last_activity = now
        db.commit()
        
        logger.info(f"✅ QR code régénéré pour {session_id}")
        
        return {
            "session_id": session_id,
            "qr_code": session.qr_code_data,  # Base64 ou placeholder
            "status": "pending",
            "expires_in_seconds": 120,
            "message": "✅ Nouveau QR code généré, scannez maintenant"
        }
    
    @staticmethod
    async def disconnect_and_regenerate(tenant_id: int, db: Session) -> dict:
        """
        Déconnecte et crée nouveau QR pour reconnexion
        """
        from .baileys_service import BaileysService
        import uuid
        
        # Récupère session actuelle
        current_session = db.query(WhatsAppSessionQR).filter(
            and_(
                WhatsAppSessionQR.tenant_id == tenant_id,
                WhatsAppSessionQR.status == "connected"
            )
        ).first()
        
        old_session_id = None
        if current_session:
            old_session_id = current_session.session_id
            # Déconnecte
            try:
                await BaileysService.logout(current_session.session_id)
            except Exception as e:
                logger.warning(f"Logout session {current_session.session_id} échoué (non critique): {e}")
            current_session.status = "disconnected"
        
        # Crée nouveau
        new_session_id = f"sess_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        
        new_session = WhatsAppSessionQR(
            tenant_id=tenant_id,
            session_id=new_session_id,
            status="pending",
            qr_code_data="placeholder",  # À remplacer par vrai QR
            qr_generated_at=now,
            qr_expires_at=now + timedelta(minutes=2)
        )
        db.add(new_session)
        db.commit()
        
        logger.info(f"✅ Nouvelle session créée: {new_session_id}")
        
        return {
            "old_session_id": old_session_id,
            "new_session_id": new_session_id,
            "qr_code": new_session.qr_code_data,
            "status": "pending",
            "expires_in_seconds": 120,
            "message": "✅ Déconnecté. Nouveau QR code généré"
        }
    
    @staticmethod
    async def update_last_activity(session_id: str, db: Session) -> None:
        """
        Met à jour last_activity pour éviter expiration
        """
        session = db.query(WhatsAppSessionQR).filter(
            WhatsAppSessionQR.session_id == session_id
        ).first()
        
        if session:
            session.last_activity = datetime.utcnow()
            db.commit()
    
    @staticmethod
    async def cleanup_expired_sessions(db: Session) -> dict:
        """
        Task périodique: nettoie les sessions expirées
        À appeler toutes les heures
        """
        now = datetime.utcnow()
        
        # Trouve sessions expirées
        expired = db.query(WhatsAppSessionQR).filter(
            and_(
                WhatsAppSessionQR.session_expires_at <= now,
                WhatsAppSessionQR.status == "connected"
            )
        ).all()
        
        count = 0
        for session in expired:
            logger.warning(f"⏰ Session {session.session_id} expirée (30 jours)")
            session.status = "expired"
            count += 1
        
        db.commit()
        
        logger.info(f"🧹 Cleanup: {count} sessions expirées nettoyées")
        
        return {
            "cleaned": count,
            "message": f"{count} sessions nettoyées"
        }
    
    @staticmethod
    async def get_tenant_session_status(tenant_id: int, db: Session) -> dict:
        """
        Récupère le statut de session du tenant
        """
        session = db.query(WhatsAppSessionQR).filter(
            WhatsAppSessionQR.tenant_id == tenant_id
        ).first()
        
        if not session:
            return {
                "status": "not_initialized",
                "message": "Aucune session créée",
                "connected": False
            }
        
        return {
            "status": session.status,
            "phone_number": session.phone_number,
            "connected": session.status == "connected",
            "connected_at": session.connected_at.isoformat() if session.connected_at else None,
            "last_activity": session.last_activity.isoformat() if session.last_activity else None,
            "message": f"Session {session.status}"
        }
