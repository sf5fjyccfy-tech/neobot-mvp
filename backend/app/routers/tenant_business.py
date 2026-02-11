"""
Router pour configurer et gérer les business types
Endpoints: /api/tenants/{tenant_id}/business/*
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models import (
    Tenant,
    TenantBusinessConfig,
    BusinessTypeModel
)
from app.services.business_kb_service import BusinessKBService
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["tenant-business"])

# ========== PYDANTIC MODELS ==========

class ProductServiceItem(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None

class BusinessConfigRequest(BaseModel):
    business_type_slug: str
    company_name: str
    company_description: Optional[str] = None
    products_services: Optional[List[ProductServiceItem]] = None
    tone: Optional[str] = "professional"
    selling_focus: Optional[str] = "Quality"

class BusinessConfigResponse(BaseModel):
    business_type: str
    company_name: str
    company_description: Optional[str]
    products_services: Optional[list]
    tone: str
    selling_focus: str

# ========== ENDPOINTS ==========

@router.post("/{tenant_id}/business/config", status_code=200)
async def configure_business(
    tenant_id: int,
    config: BusinessConfigRequest,
    db: Session = Depends(get_db)
):
    """
    Configure le business type et la KB pour un tenant
    
    Exemple:
    ```
    POST /api/tenants/1/business/config
    {
      "business_type_slug": "restaurant",
      "company_name": "La Saveur Restaurant",
      "company_description": "Restaurant français haut de gamme",
      "products_services": [
        {"name": "Pizza Margherita", "price": 5000, "description": "Classique"},
        {"name": "Pasta Carbonara", "price": 6000, "description": "Spécialité"}
      ],
      "tone": "Friendly",
      "selling_focus": "Quality and Experience"
    }
    ```
    """
    
    try:
        # 1. Vérifier que le tenant existe
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # 2. Vérifier que le business type existe
        business_type = db.query(BusinessTypeModel).filter(
            BusinessTypeModel.slug == config.business_type_slug
        ).first()
        
        if not business_type:
            raise HTTPException(
                status_code=404,
                detail=f"Business type '{config.business_type_slug}' not found"
            )
        
        # 3. Chercher ou créer la config
        existing_config = db.query(TenantBusinessConfig).filter(
            TenantBusinessConfig.tenant_id == tenant_id
        ).first()
        
        # Convertir les produits en JSON
        products_json = None
        if config.products_services:
            products_json = json.dumps([
                {
                    "name": p.name,
                    "price": p.price,
                    "description": p.description,
                    "category": p.category
                }
                for p in config.products_services
            ])
        
        if existing_config:
            # Mise à jour
            existing_config.business_type_id = business_type.id
            existing_config.company_name = config.company_name
            existing_config.company_description = config.company_description
            existing_config.products_services = products_json
            existing_config.tone = config.tone
            existing_config.selling_focus = config.selling_focus
            db.commit()
            logger.info(f"✅ Business config updated for tenant {tenant_id}")
        else:
            # Création
            new_config = TenantBusinessConfig(
                tenant_id=tenant_id,
                business_type_id=business_type.id,
                company_name=config.company_name,
                company_description=config.company_description,
                products_services=products_json,
                tone=config.tone,
                selling_focus=config.selling_focus
            )
            db.add(new_config)
            db.commit()
            logger.info(f"✅ Business config created for tenant {tenant_id}")
        
        return {
            "status": "success",
            "message": f"Business configured: {config.company_name}",
            "business_type": config.business_type_slug,
            "tenant_id": tenant_id
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error configuring business: {e}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error configuring business: {str(e)}"
        )

@router.get("/{tenant_id}/business/config")
async def get_business_config(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """Récupère la configuration business d'un tenant"""
    
    try:
        # Vérifier tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Récupérer config
        config = db.query(TenantBusinessConfig).filter(
            TenantBusinessConfig.tenant_id == tenant_id
        ).first()
        
        if not config:
            return {
                "status": "not_configured",
                "message": "No business configured for this tenant",
                "tenant_id": tenant_id
            }
        
        # Parser les produits
        try:
            products = json.loads(config.products_services) if config.products_services else []
        except:
            products = []
        
        return {
            "status": "success",
            "business_type": config.business_type.slug if config.business_type else None,
            "company_name": config.company_name,
            "company_description": config.company_description,
            "products_services": products,
            "tone": config.tone,
            "selling_focus": config.selling_focus,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error getting business config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{tenant_id}/business/config")
async def delete_business_config(
    tenant_id: int,
    db: Session = Depends(get_db)
):
    """Supprime la configuration business d'un tenant"""
    
    try:
        # Vérifier tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Trouver et supprimer la config
        config = db.query(TenantBusinessConfig).filter(
            TenantBusinessConfig.tenant_id == tenant_id
        ).first()
        
        if not config:
            raise HTTPException(status_code=404, detail="No business configuration found")
        
        db.delete(config)
        db.commit()
        logger.info(f"✅ Business config deleted for tenant {tenant_id}")
        
        return {
            "status": "success",
            "message": "Business configuration deleted",
            "tenant_id": tenant_id
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"❌ Error deleting business config: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
