"""
Usage Router - Endpoints pour l'utilisation et les statistiques
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Tenant
from app.services.usage_tracking_service import UsageTrackingService

router = APIRouter(prefix="/api/tenants", tags=["usage"])

# ========== SCHEMAS ==========

class UsageSummaryResponse(BaseModel):
    tenant_id: int
    plan: str
    plan_limit: int
    whatsapp_used: int
    other_used: int
    total_used: int
    remaining: int
    percent: int
    over_limit: bool
    overage_messages: int

class UsageHistoryItem(BaseModel):
    month_year: str
    whatsapp_messages: int
    other_messages: int
    total: int

# ========== ENDPOINTS ==========

@router.get("/{tenant_id}/usage", response_model=UsageSummaryResponse)
async def get_usage_summary(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Récupère le résumé d'utilisation du mois courant
    
    Response:
    ```json
    {
        "tenant_id": 1,
        "plan": "Pro",
        "plan_limit": 40000,
        "whatsapp_used": 12345,
        "other_used": 0,
        "total_used": 12345,
        "remaining": 27655,
        "percent": 31,
        "over_limit": false,
        "overage_messages": 0
    }
    ```
    """
    # Vérifier que le tenant existe
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant non trouvé"
        )
    
    summary = UsageTrackingService.get_usage_summary(tenant_id, db)
    
    if "error" in summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=summary["error"]
        )
    
    return summary

@router.get("/{tenant_id}/usage/history")
async def get_usage_history(
    tenant_id: int,
    months: int = 12,
    db: Session = Depends(get_db),
):
    """
    Récupère l'historique d'utilisation sur les N derniers mois
    
    Query Parameters:
    - months: Nombre de mois à retourner (default: 12, max: 36)
    
    Response:
    ```json
    [
        {
            "month_year": "2026-02",
            "whatsapp_messages": 12345,
            "other_messages": 0,
            "total": 12345
        },
        ...
    ]
    ```
    """
    # Limiter à 36 mois max
    months = min(months, 36)
    
    # Vérifier que le tenant existe
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant non trouvé"
        )
    
    history = UsageTrackingService.get_usage_history(tenant_id, months, db)
    
    return history

@router.get("/{tenant_id}/usage/check-quota")
async def check_quota_status(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Vérifie si le quota du tenant est dépassé
    
    Response:
    ```json
    {
        "tenant_id": 1,
        "quota_exceeded": false,
        "message": "✅ Utilisateur dans les limits"
    }
    ```
    """
    # Vérifier que le tenant existe
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant non trouvé"
        )
    
    exceeded = UsageTrackingService.check_quota_exceeded(tenant_id, db)
    
    if exceeded:
        summary = UsageTrackingService.get_usage_summary(tenant_id, db)
        message = f"⚠️  Quota dépassé! {summary['overage_messages']} messages au-delà de la limite"
    else:
        summary = UsageTrackingService.get_usage_summary(tenant_id, db)
        message = f"✅ {summary['remaining']} messages restants"
    
    return {
        "tenant_id": tenant_id,
        "quota_exceeded": exceeded,
        "message": message
    }
