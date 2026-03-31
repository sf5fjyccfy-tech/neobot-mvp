"""
Setup Routers - Endpoints pour initialiser NéoBot et les profils
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.knowledge_base_service import KnowledgeBaseService
from app.dependencies import get_superadmin_user
from app.models import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/setup", tags=["setup"])


@router.post("/init-neobot-profile")
async def init_neobot_profile(
    tenant_id: int = 1,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    """
    Initialize or update NéoBot profile with real data
    This profile is used by RAG system to generate intelligent responses
    """
    try:
        logger.info(f"Initializing NéoBot profile for tenant {tenant_id}...")
        
        profile = KnowledgeBaseService.create_default_neobot_profile(db, tenant_id)
        
        if not profile:
            raise HTTPException(status_code=400, detail="Could not create profile")
        
        return {
            "status": "success",
            "message": f"NéoBot profile initialized for tenant {tenant_id}",
            "profile": {
                "name": profile.get("company_name"),
                "business_type": profile.get("business_type"),
                "tone": profile.get("tone"),
                "selling_focus": profile.get("selling_focus"),
                "products_count": len(profile.get("products_services", []))
            }
        }
    except Exception as e:
        logger.error(f"Error initializing profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{tenant_id}")
async def get_tenant_profile(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    """
    Get the full profile of a tenant (used by RAG system)
    """
    try:
        profile = KnowledgeBaseService.get_tenant_profile(db, tenant_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile not found for tenant {tenant_id}")
        
        return {
            "status": "success",
            "profile": profile
        }
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{tenant_id}/formatted")
async def get_formatted_rag_context(tenant_id: int, db: Session = Depends(get_db)):
    """
    Get the formatted RAG context (what the AI will see)
    """
    try:
        profile = KnowledgeBaseService.get_tenant_profile(db, tenant_id)
        
        if not profile:
            raise HTTPException(status_code=404, detail=f"Profile not found for tenant {tenant_id}")
        
        rag_text = KnowledgeBaseService.format_profile_for_prompt(profile)
        
        return {
            "status": "success",
            "tenant_id": tenant_id,
            "company_name": profile.get("company_name"),
            "rag_context": rag_text
        }
    except Exception as e:
        logger.error(f"Error formatting RAG context: {e}")
        raise HTTPException(status_code=500, detail=str(e))
