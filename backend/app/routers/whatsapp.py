"""
WhatsApp Router - Gestion des sessions et QR codes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import logging

from app.database import get_db
from app.models import WhatsAppSession, Tenant, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["whatsapp"])

# ========== SCHEMAS ==========

class WhatsAppSessionResponse(BaseModel):
    id: int
    tenant_id: int
    whatsapp_phone: str
    is_connected: bool
    last_connected_at: datetime | None
    failed_attempts: int
    
    class Config:
        from_attributes = True

class WhatsAppQRResponse(BaseModel):
    tenant_id: int
    status: str  # "awaiting_scan", "connected", "error"
    qr_code: str | None  # Base64 encoded QR code image or empty
    phone: str | None
    message: str

# ========== UTILITY FUNCTIONS ==========

def get_tenant_from_phone(phone: str, db: Session) -> int | None:
    """
    Map un numéro WhatsApp à un tenant_id
    Retourne l'ID du tenant ou None si pas trouvé
    """
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.whatsapp_phone == phone
    ).first()
    
    if not session:
        return None
    
    return session.tenant_id

def get_tenant_phone(tenant_id: int, db: Session) -> str | None:
    """
    Map un tenant_id à son numéro WhatsApp
    """
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        return None
    
    return session.whatsapp_phone

# ========== ENDPOINTS ==========

@router.get("/{tenant_id}/whatsapp/session", response_model=WhatsAppSessionResponse | None)
async def get_whatsapp_session(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Récupère la session WhatsApp actuelle du tenant
    """
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pas de session WhatsApp pour ce tenant"
        )
    
    return session

@router.post("/{tenant_id}/whatsapp/session")
async def create_whatsapp_session(
    tenant_id: int,
    whatsapp_phone: str,
    db: Session = Depends(get_db),
):
    """
    Crée une nouvelle session WhatsApp pour un tenant
    """
    # Vérifier que le tenant existe
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant non trouvé"
        )
    
    # Vérifier qu'il n'existe pas déjà une session
    existing = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce tenant a déjà une session WhatsApp"
        )
    
    # Vérifier que le phone n'est pas utilisé par un autre tenant
    phone_in_use = db.query(WhatsAppSession).filter(
        WhatsAppSession.whatsapp_phone == whatsapp_phone
    ).first()
    
    if phone_in_use:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce numéro WhatsApp est déjà utilisé"
        )
    
    # Créer la session
    new_session = WhatsAppSession(
        tenant_id=tenant_id,
        whatsapp_phone=whatsapp_phone,
        is_connected=False,
        failed_attempts=0,
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    logger.info(f"✅ WhatsApp session created for tenant {tenant_id}: {whatsapp_phone}")
    
    return {
        "id": new_session.id,
        "tenant_id": new_session.tenant_id,
        "whatsapp_phone": new_session.whatsapp_phone,
        "is_connected": new_session.is_connected,
    }

@router.get("/{tenant_id}/whatsapp/qr", response_model=WhatsAppQRResponse)
async def get_whatsapp_qr(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Récupère le QR code pour authentifier WhatsApp
    
    Flow:
    1. Si pas de session: Retourner message "créer une session d'abord"
    2. Si session existe + is_connected: Retourner status "connecté"
    3. Si session existe + !is_connected: Retourner QR code à scanner
    
    TODO: Intégrer avec Baileys pour générer/récupérer le QR code réel
    """
    # Vérifier que le tenant existe
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant non trouvé"
        )
    
    # Chercher la session WhatsApp
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        return WhatsAppQRResponse(
            tenant_id=tenant_id,
            status="error",
            qr_code=None,
            phone=None,
            message="Aucune session WhatsApp créée. Veuillez d'abord connecter un numéro."
        )
    
    if session.is_connected:
        return WhatsAppQRResponse(
            tenant_id=tenant_id,
            status="connected",
            qr_code=None,
            phone=session.whatsapp_phone,
            message=f"✅ Connecté: {session.whatsapp_phone}"
        )
    
    # TODO: Appeler Baileys pour obtenir le QR code réel
    # Pour maintenant, retourner un placeholder
    
    return WhatsAppQRResponse(
        tenant_id=tenant_id,
        status="awaiting_scan",
        qr_code=None,  # TODO: Générer QR code réel avec Baileys
        phone=session.whatsapp_phone,
        message=f"En attente de scan du QR code pour {session.whatsapp_phone}"
    )

@router.post("/{tenant_id}/whatsapp/session/mark-connected")
async def mark_whatsapp_connected(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Marquer une session WhatsApp comme connectée
    Appelé par: webhook Baileys après authentification réussie
    """
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session WhatsApp non trouvée"
        )
    
    session.is_connected = True
    session.last_connected_at = datetime.utcnow()
    session.failed_attempts = 0
    
    db.commit()
    db.refresh(session)
    
    logger.info(f"✅ WhatsApp session marked as connected for tenant {tenant_id}")
    
    return {
        "status": "success",
        "message": f"Session connectée: {session.whatsapp_phone}"
    }

@router.post("/{tenant_id}/whatsapp/session/mark-disconnected")
async def mark_whatsapp_disconnected(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Marquer une session WhatsApp comme déconnectée
    Appelé par: webhook Baileys quand connexion perdue
    """
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session WhatsApp non trouvée"
        )
    
    session.is_connected = False
    session.failed_attempts += 1
    
    db.commit()
    
    logger.warning(f"⚠️  WhatsApp session disconnected for tenant {tenant_id}")
    
    return {
        "status": "disconnected",
        "failed_attempts": session.failed_attempts
    }

@router.delete("/{tenant_id}/whatsapp/session")
async def delete_whatsapp_session(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Supprime la session WhatsApp d'un tenant
    """
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session WhatsApp non trouvée"
        )
    
    db.delete(session)
    db.commit()
    
    logger.info(f"🗑️  WhatsApp session deleted for tenant {tenant_id}")
    
    return {
        "status": "deleted",
        "message": f"Session WhatsApp supprimée pour le tenant {tenant_id}"
    }
