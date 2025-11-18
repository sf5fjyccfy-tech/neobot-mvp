"""
Routes API pour les analytics vendeur
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/api/tenants/{tenant_id}/analytics/dashboard")
async def get_dashboard(tenant_id: int, db: Session = Depends(get_db)):
    """Dashboard complet du vendeur"""
    analytics_service = AnalyticsService(db)
    
    try:
        dashboard_data = analytics_service.get_dashboard_overview(tenant_id)
        return {
            "tenant_id": tenant_id,
            "period": "today",
            "data": dashboard_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics: {str(e)}")

@router.get("/api/tenants/{tenant_id}/analytics/products/popular")
async def get_popular_products(
    tenant_id: int, 
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Produits les plus populaires"""
    analytics_service = AnalyticsService(db)
    
    try:
        popular_products = analytics_service.get_popular_products(tenant_id, limit)
        return {
            "tenant_id": tenant_id,
            "limit": limit,
            "products": popular_products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics: {str(e)}")

@router.get("/api/tenants/{tenant_id}/analytics/conversion")
async def get_conversion_rate(tenant_id: int, db: Session = Depends(get_db)):
    """Taux de conversion"""
    analytics_service = AnalyticsService(db)
    
    try:
        conversion_rate = analytics_service.get_conversion_rate(tenant_id)
        return {
            "tenant_id": tenant_id,
            "conversion_rate": f"{conversion_rate}%",
            "period": "all_time"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analytics: {str(e)}")
