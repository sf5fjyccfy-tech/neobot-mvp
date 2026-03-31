"""
Router pour configurer et gérer les business types
Endpoints: /api/tenants/{tenant_id}/business/*
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.dependencies import verify_tenant_access
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


class BusinessSettingsUpdateRequest(BaseModel):
    """Modèle léger pour la page Paramètres — pas besoin de business_type_slug"""
    business_name: Optional[str] = None
    sector: Optional[str] = None
    phone: Optional[str] = None
    greeting_message: Optional[str] = None

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
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
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
        
        # Stocker les produits comme liste Python (la colonne est JSON/JSONB)
        products_list = None
        if config.products_services:
            products_list = [
                {
                    "name": p.name,
                    "price": p.price,
                    "description": p.description,
                    "category": p.category
                }
                for p in config.products_services
            ]
        
        if existing_config:
            # Mise à jour
            existing_config.business_type_id = business_type.id
            existing_config.company_name = config.company_name
            existing_config.company_description = config.company_description
            existing_config.products_services = products_list
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
                products_services=products_list,
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

@router.put("/{tenant_id}/business/config", status_code=200)
async def update_business_settings(
    tenant_id: int,
    body: BusinessSettingsUpdateRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Met à jour les paramètres de base du tenant (page Paramètres).
    N'écrase pas la config détaillée (produits, tone…).
    """
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")

        # Mise à jour des champs Tenant
        if body.business_name is not None:
            tenant.name = body.business_name
        if body.sector is not None:
            tenant.business_type = body.sector
        if body.phone is not None:
            tenant.phone = body.phone

        # Mise à jour TenantBusinessConfig si elle existe
        config = db.query(TenantBusinessConfig).filter(
            TenantBusinessConfig.tenant_id == tenant_id
        ).first()
        if config:
            if body.business_name is not None:
                config.company_name = body.business_name
            if body.greeting_message is not None:
                config.company_description = body.greeting_message

        db.commit()
        logger.info(f"✅ Business settings updated for tenant {tenant_id}")
        return {"status": "success", "message": "Paramètres mis à jour"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating business settings: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{tenant_id}/business/config")
async def get_business_config(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
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
        
        # products_services est une colonne JSON/JSONB — SQLAlchemy retourne déjà une liste
        raw = config.products_services
        if isinstance(raw, str):
            # ancienne donnée double-encodée : on décode
            try:
                import json as _json
                raw = _json.loads(raw)
                if isinstance(raw, str):
                    raw = _json.loads(raw)
            except Exception:
                raw = []
        products = raw if isinstance(raw, list) else []
        
        return {
            "status": "success",
            "business_type": config.business_type.slug if config.business_type else None,
            "company_name": config.company_name,
            "company_description": config.company_description,
            "products_services": products,
            "tone": config.tone,
            "selling_focus": config.selling_focus,
            # Champs compatibles avec la page Paramètres
            "business_name": config.company_name,
            "sector": tenant.business_type,
            "phone": tenant.phone,
            "email": tenant.email,
            "greeting_message": config.company_description or "",
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
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
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
