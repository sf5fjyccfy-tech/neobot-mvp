"""
📊 Analytics Routes
Endpoints pour les dashboards et rapports d'analytics
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
import logging

from app.database import get_db
from app.services.analytics_service import AnalyticsService
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/dashboard/{tenant_id}")
async def get_dashboard(tenant_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    Récupère le dashboard complet pour un tenant
    
    Retour:
    {
        "conversations": {...},
        "usage": {...},
        "conversion": {...},
        "escalations": {...},
        "daily_trend": [...],
        "top_intents": [...]
    }
    """
    try:
        dashboard = {
            "conversations": AnalyticsService.get_conversation_metrics(tenant_id, db, days=30),
            "usage": AnalyticsService.get_usage_metrics(tenant_id, db),
            "conversion": AnalyticsService.get_conversion_metrics(tenant_id, db, days=30),
            "escalations": AnalyticsService.get_escalation_metrics(tenant_id, db=db),
            "daily_trend": AnalyticsService.get_daily_trend(tenant_id, db),
            "top_intents": AnalyticsService.get_top_intents(tenant_id, db),
            "weekly_comparison": AnalyticsService.get_weekly_comparison(tenant_id, db=db)
        }
        
        logger.info(f"✅ Dashboard analytics récupéré pour tenant {tenant_id}")
        return dashboard
        
    except Exception as e:
        logger.error(f"❌ Erreur dashboard analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{tenant_id}")
async def get_conversation_metrics(tenant_id: int, days: int = 30, db: Session = Depends(get_db)) -> Dict:
    """
    Récupère les métriques de conversations
    """
    try:
        metrics = AnalyticsService.get_conversation_metrics(tenant_id, db, days=days)
        return metrics
    except Exception as e:
        logger.error(f"❌ Erreur conversation metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversion/{tenant_id}")
async def get_conversion_funnel(tenant_id: int, days: int = 30, db: Session = Depends(get_db)) -> Dict:
    """
    Récupère le funnel de conversion
    """
    try:
        funnel = AnalyticsService.get_conversion_funnel(tenant_id, days=days, db=db)
        return funnel
    except Exception as e:
        logger.error(f"❌ Erreur conversion funnel: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/escalations/{tenant_id}")
async def get_escalations(tenant_id: int, days: int = 30, db: Session = Depends(get_db)) -> Dict:
    """
    Récupère les métriques d'escalade
    """
    try:
        escalations = AnalyticsService.get_escalation_metrics(tenant_id, days=days, db=db)
        return escalations
    except Exception as e:
        logger.error(f"❌ Erreur escalation metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/usage/{tenant_id}")
async def get_usage(tenant_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    Récupère les métriques d'utilisation du plan
    """
    try:
        usage = AnalyticsService.get_usage_metrics(tenant_id, db)
        return usage
    except Exception as e:
        logger.error(f"❌ Erreur usage metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/summary/{tenant_id}")
async def get_summary_report(tenant_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    Récupère le rapport texte (utilisable pour email, PDF, etc.)
    """
    try:
        analytics = {
            "conversations": AnalyticsService.get_conversation_metrics(tenant_id, db, days=30),
            "usage": AnalyticsService.get_usage_metrics(tenant_id, db),
            "conversion": AnalyticsService.get_conversion_metrics(tenant_id, db, days=30),
            "escalations": AnalyticsService.get_escalation_metrics(tenant_id, db=db),
            "top_intents": AnalyticsService.get_top_intents(tenant_id, db),
        }
        
        report = ReportService.generate_summary_report(analytics)
        
        return {
            "status": "success",
            "report": report,
            "generated_at": str(__import__("datetime").datetime.now().isoformat())
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur summary report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/html/{tenant_id}")
async def get_html_dashboard(tenant_id: int, db: Session = Depends(get_db)):
    """
    Récupère le dashboard HTML interactif
    """
    try:
        analytics = {
            "conversations": AnalyticsService.get_conversation_metrics(tenant_id, db, days=30),
            "usage": AnalyticsService.get_usage_metrics(tenant_id, db),
            "conversion": AnalyticsService.get_conversion_metrics(tenant_id, db, days=30),
            "escalations": AnalyticsService.get_escalation_metrics(tenant_id, db=db),
            "top_intents": AnalyticsService.get_top_intents(tenant_id, db),
        }
        
        html = ReportService.generate_html_dashboard(analytics)
        
        return {
            "status": "success",
            "html": html,
            "generated_at": str(__import__("datetime").datetime.now().isoformat())
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur HTML report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends/{tenant_id}")
async def get_trends(tenant_id: int, db: Session = Depends(get_db)) -> Dict:
    """
    Récupère les tendances (semaine vs semaine précédente)
    """
    try:
        trends = AnalyticsService.get_weekly_comparison(tenant_id, db=db)
        return trends
    except Exception as e:
        logger.error(f"❌ Erreur trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))
