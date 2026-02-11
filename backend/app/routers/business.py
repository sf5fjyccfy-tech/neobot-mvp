"""
Router pour les endpoints business généraux (sans tenant_id)
Endpoints: /api/business/*
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import BusinessTypeModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/business", tags=["business"])

@router.get("/types")
async def list_business_types(db: Session = Depends(get_db)):
    """Liste tous les types de business disponibles"""
    
    try:
        types = db.query(BusinessTypeModel).order_by(BusinessTypeModel.name).all()
        
        return {
            "status": "success",
            "total": len(types),
            "business_types": [
                {
                    "id": t.id,
                    "slug": t.slug,
                    "name": t.name,
                    "description": t.description,
                    "icon": t.icon
                }
                for t in types
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing business types: {e}")
        raise HTTPException(status_code=500, detail=str(e))
