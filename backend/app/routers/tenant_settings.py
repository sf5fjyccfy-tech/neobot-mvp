"""
Tenant Settings Endpoints - Phase 8M: Feature 3
Configuration: délai de réponse modulable, queue management
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..models import User
from ..services.response_delay_service import ResponseDelayService
from ..schemas import SetTenantDelayRequest, SetContactDelayRequest
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["settings"])


@router.get("/{tenant_id}/settings")
async def get_tenant_settings(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "is_superadmin", False) and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Récupère tous les settings du tenant
    (délai réponse, overrides par contact, etc.)
    """
    try:
        settings = ResponseDelayService.get_tenant_settings(tenant_id, db)
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "settings": settings
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur get settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{tenant_id}/settings")
async def update_tenant_settings(
    tenant_id: int,
    body: SetTenantDelayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "is_superadmin", False) and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Met à jour les settings du tenant
    
    Body: {
        "response_delay_seconds": 30  # 0, 15, 30, 60, ou 120
    }
    """
    try:
        delay = body.response_delay_seconds
        
        if delay is None:
            raise HTTPException(status_code=400, detail="response_delay_seconds required")
        
        result = ResponseDelayService.set_tenant_delay(tenant_id, delay, db)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur update settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{tenant_id}/settings/contact-delay/{phone}")
async def set_contact_delay(
    tenant_id: int,
    phone: str,
    body: SetContactDelayRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "is_superadmin", False) and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Configure un délai spécifique pour un contact
    
    Body: {
        "response_delay_seconds": 60  # 0, 15, 30, 60, ou 120
    }
    """
    try:
        delay = body.response_delay_seconds
        
        if delay is None:
            raise HTTPException(status_code=400, detail="delay_seconds required")
        
        result = ResponseDelayService.set_contact_specific_delay(
            tenant_id, 
            phone, 
            delay, 
            db
        )
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur set contact delay: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{tenant_id}/settings/contact-delay/{phone}")
async def remove_contact_delay(
    tenant_id: int,
    phone: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "is_superadmin", False) and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Supprime configuration custom pour ce contact
    (revient au délai par défaut du tenant)
    """
    try:
        from ..models import TenantSettings
        
        settings = db.query(TenantSettings).filter(
            TenantSettings.tenant_id == tenant_id
        ).first()
        
        if not settings or not settings.contact_delays:
            raise HTTPException(status_code=404, detail="Contact override not found")
        
        if phone in settings.contact_delays:
            del settings.contact_delays[phone]
            db.commit()
            
            logger.info(f"🗑️ Supprimé override pour {phone}")
            
            return {
                "status": "success",
                "message": f"Override supprimé pour {phone}"
            }
        else:
            raise HTTPException(status_code=404, detail="Phone not found in overrides")
        
    except Exception as e:
        logger.error(f"❌ Erreur remove contact delay: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tenant_id}/settings/queue")
async def get_message_queue(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "is_superadmin", False) and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Récupère les messages actuellement en queue (en attente d'envoi)
    """
    try:
        queue = ResponseDelayService.get_pending_queue(tenant_id, db)
        
        return {
            "status": "success",
            "data": queue
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur get queue: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tenant_id}/settings/delay-options")
async def get_delay_options():
    """
    Récupère les options de délai disponibles
    """
    return {
        "status": "success",
        "options": ResponseDelayService.DELAY_OPTIONS,
        "description": {
            0: "Réponse instantanée (0s)",
            15: "Très rapide (15s)",
            30: "Normal - recommandé (30s)",
            60: "Modéré - paraît plus naturel (1 min)",
            120: "Très modéré - client attend (2 min)"
        }
    }
