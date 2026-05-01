"""
Router pour les endpoints d'analytique.
Fournit les statistiques et données pour le tableau de bord.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import verify_tenant_access
from ..services.analytics_service import AnalyticsService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["analytics"])


@router.get("/{tenant_id}/analytics/dashboard")
async def get_analytics_dashboard(
    tenant_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """Tableau de bord analytique complet. ?days=7|30|90"""
    try:
        data = AnalyticsService.get_complete_dashboard(tenant_id, days=days, db=db)
        return {
            "status": "success",
            "data": data
        }
    except Exception as e:
        logger.error(f"❌ Erreur dashboard analytics: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/{tenant_id}/analytics/messages")
async def get_message_stats(
    tenant_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Récupère les stats de messages pour les N derniers jours.
    
    Paramètres:
    - days: Nombre de jours à analyser (défaut: 30)
    
    Retour:
    {
        "total_messages": 1250,
        "today": 45,
        "this_week": 320,
        "this_month": 1250,
        "average_per_day": 41.67,
        "trend": "up"
    }
    """
    try:
        stats = AnalyticsService.get_message_stats(tenant_id, days=days, db=db)
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"❌ Erreur stats messages: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/{tenant_id}/analytics/conversations")
async def get_conversation_stats(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Récupère les stats de conversations.
    
    Retour:
    {
        "total_conversations": 45,
        "active_conversations": 12,
        "closed_conversations": 33,
        "average_messages_per_conversation": 27.8
    }
    """
    try:
        stats = AnalyticsService.get_conversation_stats(tenant_id, db=db)
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"❌ Erreur stats conversations: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/{tenant_id}/analytics/revenue")
async def get_revenue_stats(
    tenant_id: int,
    months: int = 12,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Récupère les stats de revenus (dépassements).
    
    Paramètres:
    - months: Nombre de mois à analyser (défaut: 12)
    
    Retour:
    {
        "total_overages": 3,
        "total_revenue": 21000,
        "monthly_revenue": [
            {"month": "2026-01", "revenue": 7000},
            ...
        ],
        "average_monthly": 1750
    }
    """
    try:
        stats = AnalyticsService.get_revenue_stats(tenant_id, months=months, db=db)
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"❌ Erreur stats revenus: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/{tenant_id}/analytics/chart/messages")
async def get_message_chart(
    tenant_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Récupère les messages par jour pour un graphique.
    
    Paramètres:
    - days: Nombre de jours (défaut: 30)
    
    Retour:
    [
        {"date": "2026-01-01", "count": 25},
        {...}
    ]
    """
    try:
        chart_data = AnalyticsService.get_daily_message_chart(tenant_id, days=days, db=db)
        return {
            "status": "success",
            "data": chart_data
        }
    except Exception as e:
        logger.error(f"❌ Erreur graphique: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/{tenant_id}/analytics/clients/top")
async def get_top_clients(
    tenant_id: int,
    limit: int = 10,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Récupère les N clients les plus actifs.
    
    Paramètres:
    - limit: Nombre de clients (défaut: 10)
    
    Retour:
    [
        {"phone": "+237...", "name": "Client 1", "message_count": 52},
        ...
    ]
    """
    try:
        clients = AnalyticsService.get_top_clients(tenant_id, limit=limit, db=db)
        return {
            "status": "success",
            "data": clients
        }
    except Exception as e:
        logger.error(f"❌ Erreur clients: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/{tenant_id}/analytics/response-time")
async def get_response_time_stats(
    tenant_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Récupère les stats de temps de réponse IA.
    
    Paramètres:
    - days: Nombre de jours (défaut: 30)
    
    Retour:
    {
        "average_response_time_ms": 1250,
        "median_response_time_ms": 980,
        "total_ai_responses": 450,
        "responses_under_1s": 380,
        "responses_under_5s": 445
    }
    """
    try:
        stats = AnalyticsService.get_response_time_stats(tenant_id, days=days, db=db)
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"❌ Erreur réponse time: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

# ===== PHASE 7E: ANALYTICS AVANCÉS =====

@router.get("/{tenant_id}/analytics/escalations")
async def get_escalations_metrics(
    tenant_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Récupère les métriques d'escalade
    
    Retour:
    {
        "total_escalations": 15,
        "escalation_rate_percent": 8.5,
        "by_reason": {...},
        "resolved_percent": 60.0
    }
    """
    try:
        metrics = AnalyticsService.get_escalation_metrics(tenant_id, days=days, db=db)
        return {
            "status": "success",
            "data": metrics
        }
    except Exception as e:
        logger.error(f"❌ Erreur escalations: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/{tenant_id}/analytics/conversion-funnel")
async def get_conversion_funnel(
    tenant_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Récupère le funnel de conversion (vues -> conversion)
    
    Retour:
    {
        "views": 100,
        "interested": 45,
        "engaged": 25,
        "contacted": 8,
        "converted": 3,
        "conversion_rate_percent": 3.0
    }
    """
    try:
        funnel = AnalyticsService.get_conversion_funnel(tenant_id, days=days, db=db)
        return {
            "status": "success",
            "data": funnel
        }
    except Exception as e:
        logger.error(f"❌ Erreur conversion funnel: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/{tenant_id}/analytics/weekly-trend")
async def get_weekly_trend(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Récupère la tendance semaine vs semaine précédente
    
    Retour:
    {
        "this_week_messages": 250,
        "last_week_messages": 200,
        "growth_percent": 25.0,
        "trend": "up"
    }
    """
    try:
        trend = AnalyticsService.get_weekly_comparison(tenant_id, db=db)
        return {
            "status": "success",
            "data": trend
        }
    except Exception as e:
        logger.error(f"❌ Erreur weekly trend: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/{tenant_id}/analytics/report/text")
async def get_text_report(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Génère un rapport texte pour email ou PDF
    
    Retour:
    {
        "status": "success",
        "report": "...",
        "generated_at": "2026-02-25T18:30:00"
    }
    """
    try:
        from ..services.report_service import ReportService
        
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
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erreur text report: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/{tenant_id}/analytics/report/dashboard-html")
async def get_dashboard_html(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access)
):
    """
    Récupère le dashboard HTML interactif (peut être ouvert dans un navigateur)
    
    Retour:
    {
        "status": "success",
        "html": "<html>...</html>",
        "generated_at": "2026-02-25T18:30:00"
    }
    """
    try:
        from ..services.report_service import ReportService
        
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
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"❌ Erreur dashboard HTML: {e}")
        return {
            "status": "error",
            "message": str(e)
        }