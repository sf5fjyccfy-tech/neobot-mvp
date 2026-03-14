"""
Overage Router - Endpoints pour la gestion des dépassements et facturation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import Tenant
from app.services.overage_pricing_service import OveragePricingService

router = APIRouter(prefix="/api/tenants", tags=["overage"])

# ========== SCHEMAS ==========

class OverageSummaryResponse(BaseModel):
    tenant_id: int
    month_year: str
    usage_percent: int
    over_limit: bool
    overage_messages: int
    overage_cost_fcfa: int
    is_billed: bool
    billed_at: str | None
    message: str

class BillingResponse(BaseModel):
    status: str
    message: str
    tenant_id: int
    cost_fcfa: int

# ========== ENDPOINTS ==========

@router.get("/{tenant_id}/overage")
async def get_overage_summary(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Récupère le résumé des frais de dépassement pour le mois courant
    
    Response:
    ```json
    {
        "tenant_id": 1,
        "month_year": "2026-02",
        "usage_percent": 115,
        "over_limit": true,
        "overage_messages": 6000,
        "overage_cost_fcfa": 42000,
        "is_billed": false,
        "message": "⚠️  6000 messages over limit → 42000 FCFA"
    }
    ```
    
    Pricing:
    - 1-1000 messages over = 7,000 FCFA
    - 1001-2000 messages over = 14,000 FCFA
    - 2001-3000 messages over = 21,000 FCFA
    - Etc...
    """
    # Vérifier que le tenant existe
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant non trouvé"
        )
    
    summary = OveragePricingService.get_overage_summary(tenant_id, db)
    
    if "error" in summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=summary["error"]
        )
    
    return summary

@router.post("/{tenant_id}/overage/mark-billed")
async def mark_overage_billed(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """
    Marque un dépassement comme facturé
    Appelé par le système de paiement après paiement réussi
    
    Response:
    ```json
    {
        "status": "success",
        "message": "Overage marked as billed",
        "tenant_id": 1,
        "cost_fcfa": 42000
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
    
    OveragePricingService.mark_overage_as_billed(tenant_id, db)
    
    # Récupérer le résumé pour le coût
    summary = OveragePricingService.get_overage_summary(tenant_id, db)
    
    return {
        "status": "success",
        "message": "Dépassement marqué comme facturé",
        "tenant_id": tenant_id,
        "cost_fcfa": summary["overage_cost_fcfa"]
    }

@router.get("/billing/unbilled")
async def get_unbilled_overages(
    db: Session = Depends(get_db),
):
    """
    Récupère tous les dépassements non facturés
    Endpoint administrateur pour la facturation
    
    Response:
    ```json
    {
        "count": 5,
        "total_fcfa": 175000,
        "overages": [
            {
                "tenant_id": 1,
                "month_year": "2026-02",
                "cost_fcfa": 42000
            },
            ...
        ]
    }
    ```
    """
    result = OveragePricingService.get_unbilled_overages(db)
    
    return {
        "count": result["count"],
        "total_fcfa": result["total_fcfa"],
        "overages": result["overages"],
        "message": f"{result['count']} dépassement(s) à facturer pour {result['total_fcfa']} FCFA"
    }

@router.get("/billing/monthly/{month_year}")
async def get_monthly_overages(
    month_year: str,  # Format: "2026-02"
    db: Session = Depends(get_db),
):
    """
    Récupère tous les dépassements pour un mois donné
    Endpoint administrateur pour le reporting
    
    Example: /api/tenants/billing/monthly/2026-02
    
    Response:
    ```json
    [
        {
            "tenant_id": 1,
            "messages_over": 6000,
            "cost_fcfa": 42000,
            "is_billed": false
        },
        ...
    ]
    ```
    """
    # Valider format mois
    if len(month_year) != 7 or month_year[4] != '-':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format invalide. Utilisez: YYYY-MM (ex: 2026-02)"
        )
    
    overages = OveragePricingService.get_monthly_overages(db, month_year)
    
    total = sum(o["cost_fcfa"] for o in overages)
    
    return {
        "month": month_year,
        "count": len(overages),
        "total_fcfa": total,
        "overages": overages
    }
