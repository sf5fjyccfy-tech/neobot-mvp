"""
Usage Router - Endpoints pour l'utilisation et les statistiques
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from app.database import get_db
from app.dependencies import verify_tenant_access
from app.models import Tenant, Message, Conversation, Subscription, User
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
    # Stats du jour
    today_messages: int
    active_conversations: int
    # Infos essai
    is_trial: bool
    trial_ends_at: Optional[str]
    trial_days_left: Optional[int]

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
    _: bool = Depends(verify_tenant_access),
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

    # Enrichir avec les infos d'essai depuis le modèle Subscription (source de vérité)
    subscription = db.query(Subscription).filter(Subscription.tenant_id == tenant_id).first()
    is_superadmin_tenant = False
    if subscription:
        is_trial = bool(subscription.is_trial)
        trial_ends_at = subscription.trial_end_date
    else:
        # Fallback : lire depuis le modèle Tenant si pas de Subscription
        is_trial = bool(tenant.is_trial)
        trial_ends_at = tenant.trial_ends_at

    # Détecter si c'est un compte superadmin (pas de badge plan)
    user = db.query(User).filter(User.tenant_id == tenant_id, User.is_superadmin == True).first()
    if user:
        is_superadmin_tenant = True
        is_trial = False  # Superadmin : jamais en essai
        summary["plan"] = "NeoBot Admin"
        summary["plan_limit"] = -1
        summary["over_limit"] = False
    trial_days_left: Optional[int] = None
    if is_trial and trial_ends_at:
        delta = trial_ends_at - datetime.utcnow()
        trial_days_left = max(0, delta.days)

    summary["is_trial"] = is_trial
    summary["trial_ends_at"] = trial_ends_at.isoformat() if trial_ends_at else None
    summary["trial_days_left"] = trial_days_left
    summary["is_superadmin"] = is_superadmin_tenant

    # Statut abonnement payant
    sub_expires = tenant.subscription_expires_at
    summary["subscription_expires_at"] = sub_expires.isoformat() + "Z" if sub_expires else None
    summary["subscription_active"] = (
        not is_trial
        and sub_expires is not None
        and sub_expires > datetime.utcnow()
    )

    # Messages reçus aujourd'hui (début du jour UTC)
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = (
        db.query(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(
            Conversation.tenant_id == tenant_id,
            Message.created_at >= today_start,
        )
        .scalar() or 0
    )
    summary["today_messages"] = today_count

    # Conversations actives (status='active')
    active_count = (
        db.query(func.count(Conversation.id))
        .filter(
            Conversation.tenant_id == tenant_id,
            Conversation.status == "active",
        )
        .scalar() or 0
    )
    summary["active_conversations"] = active_count

    return summary

@router.get("/{tenant_id}/dashboard/stats")
async def get_dashboard_stats(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access),
):
    """
    Stats consolidées pour le dashboard : usage + outcomes du bot.
    Retourne les métriques du jour et du mois courant.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant non trouvé")

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Messages du jour (tous)
    today_messages = (
        db.query(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Conversation.tenant_id == tenant_id, Message.created_at >= today_start)
        .scalar() or 0
    )

    # Conversations actives en ce moment
    active_conversations = (
        db.query(func.count(Conversation.id))
        .filter(Conversation.tenant_id == tenant_id, Conversation.status == "active")
        .scalar() or 0
    )

    # Outcomes détectés ce mois — comptés par type
    outcome_rows = (
        db.query(Conversation.outcome_type, func.count(Conversation.id))
        .filter(
            Conversation.tenant_id == tenant_id,
            Conversation.outcome_type.isnot(None),
            Conversation.outcome_detected_at >= month_start,
        )
        .group_by(Conversation.outcome_type)
        .all()
    )
    outcomes_month = {row[0]: row[1] for row in outcome_rows}

    # Outcomes détectés aujourd'hui
    outcome_today_rows = (
        db.query(Conversation.outcome_type, func.count(Conversation.id))
        .filter(
            Conversation.tenant_id == tenant_id,
            Conversation.outcome_type.isnot(None),
            Conversation.outcome_detected_at >= today_start,
        )
        .group_by(Conversation.outcome_type)
        .all()
    )
    outcomes_today = {row[0]: row[1] for row in outcome_today_rows}

    # 5 dernières conversations avec outcome (pour le fil d'activité)
    recent_outcomes = (
        db.query(Conversation)
        .filter(
            Conversation.tenant_id == tenant_id,
            Conversation.outcome_type.isnot(None),
        )
        .order_by(Conversation.outcome_detected_at.desc())
        .limit(5)
        .all()
    )
    recent_list = [
        {
            "customer_name": c.customer_name or c.customer_phone,
            "outcome_type": c.outcome_type,
            "detected_at": c.outcome_detected_at.isoformat() if c.outcome_detected_at else None,
        }
        for c in recent_outcomes
    ]

    return {
        "today_messages": today_messages,
        "active_conversations": active_conversations,
        "outcomes_month": outcomes_month,
        "outcomes_today": outcomes_today,
        "recent_outcomes": recent_list,
    }

@router.get("/{tenant_id}/usage/history")
async def get_usage_history(
    tenant_id: int,
    months: int = 12,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access),
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
    _: bool = Depends(verify_tenant_access),
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
