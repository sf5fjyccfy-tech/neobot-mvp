"""
Contacts Management Endpoints - Phase 8M: Feature 1
Whitelist/Blacklist pour contrôler qui peut recevoir des réponses IA
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging

from ..database import get_db
from ..models import ContactSetting, User
from ..services.contact_filter_service import ContactFilterService
from ..schemas import AIToggleRequest, BulkPhoneRequest
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["contacts"])


@router.get("/{tenant_id}/contacts")
async def get_all_contacts(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "is_superadmin", False) and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Récupère tous les contacts avec leurs settings
    Triés par nombre de messages (décroissant)
    """
    try:
        contacts = ContactFilterService.get_all_contacts(tenant_id, db)
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "total": len(contacts),
            "contacts": contacts
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur listing contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tenant_id}/contacts/disabled")
async def get_disabled_contacts(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "is_superadmin", False) and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Récupère seulement les contacts avec IA désactivée
    """
    try:
        contacts = ContactFilterService.get_disabled_contacts(tenant_id, db)
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "total": len(contacts),
            "disabled_contacts": contacts
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur listing disabled contacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{tenant_id}/contacts/{phone}/ai-toggle")
async def toggle_ai_for_contact(
    tenant_id: int,
    phone: str,
    body: AIToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "is_superadmin", False) and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Active/désactive IA pour un contact spécifique
    
    Body: {"ai_enabled": true}
    """
    try:
        ai_enabled = body.ai_enabled
        
        result = ContactFilterService.toggle_ai_for_contact(
            tenant_id, 
            phone,
            ai_enabled,
            db
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur toggle AI: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tenant_id}/contacts/bulk-disable")
async def bulk_disable_ai(
    tenant_id: int,
    body: BulkPhoneRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "is_superadmin", False) and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Désactive IA pour plusieurs contacts
    
    Body: {"phones": ["237666...", "237777..."]}
    """
    try:
        phones = body.phones
        
        if not phones:
            raise HTTPException(status_code=400, detail="phones list required")
        
        result = ContactFilterService.bulk_disable_ai(tenant_id, phones, db)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur bulk disable: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{tenant_id}/contacts/bulk-enable")
async def bulk_enable_ai(
    tenant_id: int,
    body: BulkPhoneRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not getattr(current_user, "is_superadmin", False) and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    """
    Réactive IA pour plusieurs contacts
    
    Body: {"phones": ["237666...", "237777..."]}
    """
    try:
        phones = body.phones
        
        if not phones:
            raise HTTPException(status_code=400, detail="phones list required")
        
        result = ContactFilterService.bulk_enable_ai(tenant_id, phones, db)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur bulk enable: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tenant_id}/contacts/{phone}")
async def get_contact_info(
    tenant_id: int,
    phone: str,
    db: Session = Depends(get_db)
):
    """
    Récupère les infos d'un contact spécifique
    """
    try:
        setting = db.query(ContactSetting).filter(
            ContactSetting.tenant_id == tenant_id,
            ContactSetting.phone_number == phone
        ).first()
        
        if not setting:
            return {
                "status": "success",
                "contact": {
                    "phone_number": phone,
                    "ai_enabled": True,  # Default
                    "message": "Contact par défaut (IA active)"
                }
            }
        
        return {
            "status": "success",
            "contact": {
                "phone_number": setting.phone_number,
                "name": setting.contact_name,
                "ai_enabled": setting.ai_enabled,
                "message_count": setting.message_count,
                "first_seen": setting.first_seen.isoformat() if setting.first_seen else None,
                "last_seen": setting.last_seen.isoformat() if setting.last_seen else None
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur get contact: {e}")
        raise HTTPException(status_code=500, detail=str(e))
