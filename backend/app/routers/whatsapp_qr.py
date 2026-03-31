"""
WhatsApp QR Code Endpoints - Phase 8M: Baileys Integration
Gère: QR generation, status, regeneration, session management
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import asyncio
import logging

from ..database import SessionLocal, get_db
from ..models import WhatsAppSessionQR, User
from ..services.session_expiration_checker import SessionExpirationChecker
from ..dependencies import verify_tenant, verify_tenant_access, get_current_user, get_superadmin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])

# ========== QR CODE GENERATION ==========

@router.post("/qr-generate")
async def generate_qr_code(
    tenant_id: int,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    _: bool = Depends(verify_tenant_access)
):
    """
    Génère un nouveau QR code pour authentification Baileys
    
    Returns:
    {
        "session_id": "sess_abc123",
        "qr_code": "data:image/png;base64,iVBORw0KGgo...",
        "status": "pending",
        "expires_in_seconds": 120,
        "message": "Scannez ce code avec votre téléphone"
    }
    """
    try:
        session_id = f"sess_{uuid.uuid4().hex[:16]}"
        now = datetime.utcnow()
        
        # Crée session en BD
        session = WhatsAppSessionQR(
            tenant_id=tenant_id,
            session_id=session_id,
            status="pending",
            qr_code_data="generating",  # Placeholder
            qr_generated_at=now,
            qr_expires_at=now + timedelta(minutes=2)
        )
        db.add(session)
        db.commit()
        
        logger.info(f"📱 QR code généré: {session_id} pour tenant {tenant_id}")
        
        # TODO: Appeler Baileys service pour générer le vrai QR
        # qr_data = await baileys_service.generate_qr(session_id)
        
        return {
            "session_id": session_id,
            "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
            "status": "pending",
            "expires_in_seconds": 120,
            "message": "Scannez ce code avec votre téléphone"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur génération QR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}/status")
async def get_session_status(
    session_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """
    Récupère le statut d'une session
    
    Returns:
    {
        "status": "pending|connected|expired|disconnected",
        "phone_number": "+237...",
        "expires_in_seconds": 120,
        "can_regenerate": true/false
    }
    """
    try:
        checker = SessionExpirationChecker()
        status = await checker.check_qr_expiration(session_id, db)
        return status
        
    except Exception as e:
        logger.error(f"❌ Erreur statut session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/qr-display/{session_id}")
async def get_qr_display(
    session_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """
    Récupère le QR code pour affichage (ne le fait pas expirer)
    """
    try:
        session = db.query(WhatsAppSessionQR).filter(
            WhatsAppSessionQR.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        expires_in = 0
        if session.qr_expires_at:
            expires_in = max(0, int((session.qr_expires_at - datetime.utcnow()).total_seconds()))
        
        return {
            "qr_code": session.qr_code_data,
            "status": session.status,
            "expires_in_seconds": expires_in,
            "message": "QR code valide 2 minutes"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur affichage QR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/qr-regenerate")
async def regenerate_qr_code(
    session_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """
    Régénère un QR code si expiré
    """
    try:
        checker = SessionExpirationChecker()
        result = await checker.regenerate_qr_code(session_id, db)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur régénération QR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect-reconnect")
async def disconnect_and_regenerate(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Déconnecte session actuelle et crée nouveau QR
    """
    try:
        checker = SessionExpirationChecker()
        result = await checker.disconnect_and_regenerate(tenant_id, db)
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur disconnect-reconnect: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== SESSION MANAGEMENT ==========

@router.get("/session/status/{tenant_id}")
async def get_tenant_session_status(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Récupère le statut de session du tenant
    """
    try:
        checker = SessionExpirationChecker()
        status = await checker.get_tenant_session_status(tenant_id, db)
        return status
        
    except Exception as e:
        logger.error(f"❌ Erreur statut tenant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disconnect")
async def disconnect_whatsapp(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Déconnecte WhatsApp pour ce tenant
    """
    try:
        session = db.query(WhatsAppSessionQR).filter(
            WhatsAppSessionQR.tenant_id == tenant_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session.status = "disconnected"
        db.commit()
        
        logger.info(f"🔌 Déconnecté tenant {tenant_id}")
        
        return {
            "status": "disconnected",
            "message": "WhatsApp déconnecté"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur déconnexion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== HEALTH & MONITORING ==========

@router.get("/health")
async def whatsapp_health(
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user)
):
    """
    Récupère santé du service WhatsApp
    """
    try:
        # Compte sessions connectées
        connected = db.query(WhatsAppSessionQR).filter(
            WhatsAppSessionQR.status == "connected"
        ).count()
        
        # Compte sessions en attente
        pending = db.query(WhatsAppSessionQR).filter(
            WhatsAppSessionQR.status == "pending"
        ).count()
        
        # Compte sessions expirées
        expired = db.query(WhatsAppSessionQR).filter(
            WhatsAppSessionQR.status == "expired"
        ).count()
        
        return {
            "status": "healthy",
            "connected_sessions": connected,
            "pending_sessions": pending,
            "expired_sessions": expired,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/sessions")
async def list_all_sessions(
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user)
):
    """
    Liste toutes les sessions WhatsApp
    """
    try:
        sessions = db.query(WhatsAppSessionQR).all()
        
        return {
            "total": len(sessions),
            "sessions": [
                {
                    "session_id": s.session_id,
                    "tenant_id": s.tenant_id,
                    "phone_number": s.phone_number,
                    "status": s.status,
                    "connected_at": s.connected_at.isoformat() if s.connected_at else None,
                    "last_activity": s.last_activity.isoformat() if s.last_activity else None
                }
                for s in sessions
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur listing sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== BACKGROUND TASKS ==========

async def cleanup_expired_qr_codes(db: Session):
    """
    Task périodique: nettoie les sessions expirées
    À appeler toutes les heures
    """
    try:
        checker = SessionExpirationChecker()
        result = await checker.cleanup_expired_sessions(db)
        logger.info(f"🧹 Cleanup: {result['cleaned']} sessions nettoyées")
    except Exception as e:
        logger.error(f"❌ Erreur cleanup: {e}")
