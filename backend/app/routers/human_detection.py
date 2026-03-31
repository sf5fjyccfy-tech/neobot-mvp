"""
Human Detection Endpoints - Phase 8M: Feature 2
Détecte quand un humain intervient et pause l'IA automatiquement
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging
from typing import Optional

from ..database import get_db
from ..models import User, Conversation
from ..services.human_detection_service import HumanDetectionService
from ..schemas import MarkHumanRequest
from ..dependencies import get_current_user

logger = logging.getLogger(__name__)


def _check_conv_access(conversation_id: int, current_user: User, db: Session) -> Conversation:
    """Vérifie qu'une conversation existe et appartient au tenant de l'utilisateur."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation introuvable")
    if not getattr(current_user, "is_superadmin", False) and conv.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    return conv

router = APIRouter(prefix="/api/conversations", tags=["human-detection"])


@router.get("/{conversation_id}/state")
async def get_conversation_state(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_conv_access(conversation_id, current_user, db)
    """
    Récupère l'état d'une conversation
    (humain actif, IA pausée, etc.)
    """
    try:
        state = HumanDetectionService.get_conversation_state(conversation_id, db)
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "state": state
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur get state: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/mark-human-active")
async def mark_human_active_endpoint(
    conversation_id: int,
    body: Optional[MarkHumanRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_conv_access(conversation_id, current_user, db)
    """
    Marque manuellement que un humain est actif sur cette conversation
    (IA va se mettre en pause)
    """
    try:
        confidence = body.confidence if body and body.confidence is not None else 80
        
        result = HumanDetectionService.mark_human_active(
            conversation_id, 
            db,
            confidence=confidence
        )
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur mark human active: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/mark-human-inactive")
async def mark_human_inactive_endpoint(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_conv_access(conversation_id, current_user, db)
    """
    Marque que humain a terminé avec cette conversation
    (IA va se réactiver)
    """
    try:
        result = HumanDetectionService.mark_human_inactive(conversation_id, db)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur mark human inactive: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/auto-detect-human")
async def auto_detect_human(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_conv_access(conversation_id, current_user, db)
    """
    Auto-détecte si un humain a intervenu (analyse derniers messages)
    """
    try:
        result = HumanDetectionService.auto_detect_and_update(conversation_id, db)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur auto-detect: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/should-ai-respond")
async def should_ai_respond(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _check_conv_access(conversation_id, current_user, db)
    """
    Vérifies si IA doit répondre (pas d'humain actif)
    À appeler AVANT de générer une réponse IA
    """
    try:
        should_respond = HumanDetectionService.should_ai_respond(conversation_id, db)
        
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "should_ai_respond": should_respond,
            "message": "IA peut répondre" if should_respond else "IA en pause (humain actif)"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur should-respond: {e}")
        raise HTTPException(status_code=500, detail=str(e))
