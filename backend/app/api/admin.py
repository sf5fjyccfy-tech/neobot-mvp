"""
Endpoints Admin - Pour toi (Super Admin)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Tenant, PLAN_LIMITS

router = APIRouter()

@router.get("/admin/tenants")
def list_tenants(db: Session = Depends(get_db)):
    """Lister tous les clients businesses"""
    tenants = db.query(Tenant).all()
    
    return {
        "total": len(tenants),
        "tenants": [
            {
                "id": t.id,
                "business_name": t.business_name,
                "sector": t.business_sector.value,
                "plan": t.plan.value,
                "is_active": t.is_active,
                "whatsapp_connected": t.whatsapp_connected,
                "created_at": t.created_at.isoformat()
            }
            for t in tenants
        ]
    }

@router.get("/admin/analytics")
def platform_analytics(db: Session = Depends(get_db)):
    """Analytics globale de la plateforme"""
    total_tenants = db.query(Tenant).count()
    active_tenants = db.query(Tenant).filter(Tenant.is_active == True).count()
    
    # Calculer le MRR
    mrr = 0
    for tenant in db.query(Tenant).filter(Tenant.is_active == True):
        plan_config = PLAN_LIMITS.get(tenant.plan, PLAN_LIMITS[PlanType.BASIQUE])
        mrr += plan_config["price_fcfa"]
    
    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "monthly_recurring_revenue": mrr,
        "conversion_rate": round((active_tenants / total_tenants * 100) if total_tenants > 0 else 0, 1)
    }

@router.post("/admin/tenants/{tenant_id}/activate")
def activate_tenant(tenant_id: int, db: Session = Depends(get_db)):
    """Activer/désactiver un tenant"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise HTTPException(404, "Tenant non trouvé")
    
    tenant.is_active = not tenant.is_active
    db.commit()
    
    return {
        "tenant_id": tenant_id,
        "business_name": tenant.business_name,
        "is_active": tenant.is_active,
        "action": "activated" if tenant.is_active else "deactivated"
    }
