"""
Admin Router — Accès superadmin uniquement
Gestion globale : tenants, agents, stats, suspension, impersonation
"""
import os
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

WHATSAPP_SERVICE_URL = os.getenv("WHATSAPP_SERVICE_URL", "http://localhost:3001")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")

from app.database import get_db
from app.models import (
    User, Tenant, AgentTemplate, AgentType, PlanType, PLAN_LIMITS,
    Subscription, Conversation, WhatsAppSession, UsageTracking, Message,
)
from typing import List
from fastapi import BackgroundTasks
from app.dependencies import get_superadmin_user
from app.services.auth_service import create_access_token
from app.services.email_service import (
    send_welcome_email,
    send_password_reset_email,
    send_confirmation_email,
    send_custom_broadcast,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ======================== SCHEMAS ========================

class TenantSuspendRequest(BaseModel):
    reason: Optional[str] = None

class TenantPlanRequest(BaseModel):
    plan: PlanType
    messages_limit: Optional[int] = None

class AgentTypeChangeRequest(BaseModel):
    agent_type: AgentType

class BroadcastEmailRequest(BaseModel):
    subject: str
    body: str
    target: str = "all"  # all | active_paid | trial | single
    tenant_id: Optional[int] = None  # requis si target == 'single'


class WhatsAppMessageRequest(BaseModel):
    message: str


class AgentUpdateRequest(BaseModel):
    # custom_prompt_override intentionnellement absent : l'admin ne modifie pas les prompts clients
    tone: Optional[str] = None
    name: Optional[str] = None
    max_response_length: Optional[int] = None
    language: Optional[str] = None
    emoji_enabled: Optional[bool] = None
    availability_start: Optional[str] = None
    availability_end: Optional[str] = None
    off_hours_message: Optional[str] = None


# ======================== STATS GLOBALES ========================

@router.get("/stats")
def get_global_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    # Utiliser datetime.utcnow() (naive) pour compatibilité avec TIMESTAMP sans timezone
    week_ago = datetime.utcnow() - timedelta(days=7)

    def _count(q):
        try:
            return q.scalar() or 0
        except Exception:
            db.rollback()
            return 0

    total_tenants    = _count(db.query(func.count(Tenant.id)).filter(Tenant.is_deleted == False))  # noqa: E712
    active_tenants   = _count(db.query(func.count(Tenant.id)).filter(Tenant.is_deleted == False, Tenant.is_suspended == False))  # noqa: E712
    suspended_count  = _count(db.query(func.count(Tenant.id)).filter(Tenant.is_deleted == False, Tenant.is_suspended == True))  # noqa: E712
    wa_connected     = _count(db.query(func.count(WhatsAppSession.id)).filter(WhatsAppSession.is_connected == True))  # noqa: E712
    total_conversations = _count(db.query(func.count(Conversation.id)))
    total_agents     = _count(db.query(func.count(AgentTemplate.id)))
    messages_total   = _count(db.query(func.sum(Tenant.messages_used)).filter(Tenant.is_deleted == False))  # noqa: E712
    new_this_week    = _count(db.query(func.count(Tenant.id)).filter(Tenant.is_deleted == False, Tenant.created_at >= week_ago))  # noqa: E712

    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "suspended_tenants": suspended_count,
        "whatsapp_connected": wa_connected,
        "total_conversations": total_conversations,
        "total_agents": total_agents,
        "messages_this_month": messages_total,
        "new_tenants_this_week": new_this_week,
    }


# ======================== LISTE TENANTS ========================

@router.get("/tenants")
def list_tenants(
    search: Optional[str] = None,
    plan: Optional[str] = None,
    suspended: Optional[bool] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    q = db.query(Tenant).filter(Tenant.is_deleted == False)
    if search:
        q = q.filter(
            (Tenant.name.ilike(f"%{search}%")) | (Tenant.email.ilike(f"%{search}%"))
        )
    if plan:
        q = q.filter(Tenant.plan == plan)
    if suspended is not None:
        q = q.filter(Tenant.is_suspended == suspended)

    tenants = q.order_by(Tenant.created_at.desc()).all()

    # Bulk-query usage_tracking — table peut ne pas exister sur DB fraîche
    current_month = datetime.now().strftime('%Y-%m')
    try:
        usage_records = db.query(UsageTracking).filter(
            UsageTracking.month_year == current_month
        ).all()
        usage_map = {u.tenant_id: u.whatsapp_messages_used for u in usage_records}
    except Exception:
        db.rollback()
        usage_map = {}

    result = []
    for t in tenants:
        wa = db.query(WhatsAppSession).filter(WhatsAppSession.tenant_id == t.id).first()
        try:
            agent_count = db.query(func.count(AgentTemplate.id)).filter(
                AgentTemplate.tenant_id == t.id
            ).scalar() or 0
        except Exception:
            db.rollback()
            agent_count = 0
        user = db.query(User).filter(User.tenant_id == t.id).first()
        sub = db.query(Subscription).filter(Subscription.tenant_id == t.id).first()
        last_conv_at = db.query(func.max(Conversation.created_at)).filter(
            Conversation.tenant_id == t.id
        ).scalar()

        # Calcul trial — trial_end_date peut être datetime ou date selon la colonne
        trial_ends_at = None
        trial_days_remaining = None
        if sub and sub.is_trial and sub.trial_end_date:
            today = datetime.utcnow().date()  # naive — compatible avec TIMESTAMP sans timezone
            end_date = sub.trial_end_date.date() if hasattr(sub.trial_end_date, 'date') else sub.trial_end_date
            trial_ends_at = end_date.isoformat()
            trial_days_remaining = (end_date - today).days

        plan_value = t.plan.value if hasattr(t.plan, "value") else t.plan
        display_plan = PLAN_LIMITS.get(t.plan, {}).get("display_name", plan_value)

        result.append({
            "id": t.id,
            "name": t.name,
            "email": t.email,
            "plan": plan_value,
            "display_plan": display_plan,
            "messages_used": t.messages_used,
            "messages_limit": t.messages_limit,
            "is_suspended": t.is_suspended,
            "suspension_reason": t.suspension_reason,
            "suspended_at": t.suspended_at.isoformat() if t.suspended_at else None,
            "whatsapp_connected": wa.is_connected if wa else False,
            "whatsapp_phone": wa.whatsapp_phone if wa else None,
            "agent_count": agent_count,
            "user_id": user.id if user else None,
            "user_is_active": user.is_active if user else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "trial_ends_at": trial_ends_at,
            "trial_days_remaining": trial_days_remaining,
            "last_active_at": last_conv_at.isoformat() if last_conv_at else None,
            "messages_this_month": usage_map.get(t.id, 0),
            "subscription_expires_at": (t.subscription_expires_at.isoformat() + "Z") if t.subscription_expires_at else None,
        })
    return result


# ======================== DETAIL TENANT ========================

@router.get("/tenants/{tenant_id}")
def get_tenant_detail(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    try:
        agents = db.query(AgentTemplate).filter(AgentTemplate.tenant_id == tenant_id).all()
    except Exception:
        db.rollback()
        agents = []
    user = db.query(User).filter(User.tenant_id == tenant_id).first()
    wa = db.query(WhatsAppSession).filter(WhatsAppSession.tenant_id == tenant_id).first()
    sub = db.query(Subscription).filter(Subscription.tenant_id == tenant_id).first()
    conv_count = db.query(func.count(Conversation.id)).filter(
        Conversation.tenant_id == tenant_id
    ).scalar()
    last_conv_at = db.query(func.max(Conversation.created_at)).filter(
        Conversation.tenant_id == tenant_id
    ).scalar()

    trial_ends_at = None
    trial_days_remaining = None
    if sub and sub.is_trial and sub.trial_end_date:
        today = datetime.utcnow().date()
        end_date = sub.trial_end_date.date() if hasattr(sub.trial_end_date, 'date') else sub.trial_end_date
        trial_ends_at = end_date.isoformat()
        trial_days_remaining = (end_date - today).days

    plan_value = tenant.plan.value if hasattr(tenant.plan, "value") else tenant.plan
    display_plan = PLAN_LIMITS.get(tenant.plan, {}).get("display_name", plan_value)

    return {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "phone": tenant.phone,
        "plan": plan_value,
        "display_plan": display_plan,
        "messages_used": tenant.messages_used,
        "messages_limit": tenant.messages_limit,
        "is_suspended": tenant.is_suspended,
        "suspension_reason": tenant.suspension_reason,
        "suspended_at": tenant.suspended_at.isoformat() if tenant.suspended_at else None,
        "whatsapp_connected": wa.is_connected if wa else False,
        "whatsapp_phone": wa.whatsapp_phone if wa else None,
        "conversation_count": conv_count,
        "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
        "trial_ends_at": trial_ends_at,
        "trial_days_remaining": trial_days_remaining,
        "last_active_at": last_conv_at.isoformat() if last_conv_at else None,
        "subscription_expires_at": (tenant.subscription_expires_at.isoformat() + "Z") if tenant.subscription_expires_at else None,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": getattr(user, "full_name", None),
            "role": getattr(user, "role", "user"),
            "is_active": user.is_active,
            "last_login": None,
        } if user else None,
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "agent_type": a.agent_type.value if hasattr(a.agent_type, "value") else str(a.agent_type),
                "is_active": a.is_active,
                "prompt_score": getattr(a, "prompt_score", 0),
                "tone": getattr(a, "tone", ""),
                "language": getattr(a, "language", "fr"),
                "emoji_enabled": getattr(a, "emoji_enabled", True),
                "max_response_length": getattr(a, "max_response_length", 400),
                "custom_prompt_override": getattr(a, "custom_prompt_override", None),
                "system_prompt": getattr(a, "system_prompt", None),
                "availability_start": getattr(a, "availability_start", None),
                "availability_end": getattr(a, "availability_end", None),
                "off_hours_message": getattr(a, "off_hours_message", None),
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in agents
        ],
    }


# ======================== SUSPENSION ========================

@router.post("/tenants/{tenant_id}/suspend")
def suspend_tenant(
    tenant_id: int,
    body: TenantSuspendRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_superadmin_user),
):
    if tenant_id == admin.tenant_id:
        raise HTTPException(status_code=400, detail="Impossible de suspendre son propre compte")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    user = db.query(User).filter(User.tenant_id == tenant_id).first()
    if user:
        user.is_active = False

    tenant.is_suspended = True
    tenant.suspension_reason = body.reason or "Suspension administrative"
    tenant.suspended_at = datetime.utcnow()
    db.commit()
    return {"status": "suspended", "tenant_id": tenant_id}


@router.post("/tenants/{tenant_id}/activate")
def activate_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    user = db.query(User).filter(User.tenant_id == tenant_id).first()
    if user:
        user.is_active = True

    tenant.is_suspended = False
    tenant.suspension_reason = None
    tenant.suspended_at = None
    db.commit()
    return {"status": "activated", "tenant_id": tenant_id}


# ======================== PLAN / LIMITES ========================

@router.patch("/tenants/{tenant_id}/plan")
def change_tenant_plan(
    tenant_id: int,
    body: TenantPlanRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    plan_config = PLAN_LIMITS.get(body.plan, {})
    tenant.plan = body.plan
    if body.messages_limit is not None:
        tenant.messages_limit = body.messages_limit
    elif plan_config.get("whatsapp_messages") and plan_config["whatsapp_messages"] > 0:
        tenant.messages_limit = plan_config["whatsapp_messages"]

    db.commit()
    return {
        "status": "updated",
        "tenant_id": tenant_id,
        "plan": body.plan.value,
        "messages_limit": tenant.messages_limit,
    }


@router.patch("/tenants/{tenant_id}/messages-limit")
def override_messages_limit(
    tenant_id: int,
    messages_limit: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    if messages_limit < -1:
        raise HTTPException(status_code=400, detail="Limite invalide")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    tenant.messages_limit = messages_limit
    db.commit()
    return {"status": "updated", "messages_limit": messages_limit}


@router.post("/tenants/{tenant_id}/reset-messages")
def reset_messages_counter(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    tenant.messages_used = 0
    db.commit()
    return {"status": "reset", "tenant_id": tenant_id}


class AddMessagesRequest(BaseModel):
    amount: int  # Messages bonus à ajouter à la limite


@router.post("/tenants/{tenant_id}/add-messages")
def add_bonus_messages(
    tenant_id: int,
    body: AddMessagesRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    """Ajoute N messages à la limite du tenant (pour paiement confirmé)."""
    if body.amount <= 0:
        raise HTTPException(status_code=400, detail="Le montant doit être positif")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    current_limit = tenant.messages_limit or 0
    if current_limit == -1:
        return {"status": "unlimited", "messages_limit": -1}
    tenant.messages_limit = current_limit + body.amount
    db.commit()
    return {
        "status": "added",
        "added": body.amount,
        "messages_limit": tenant.messages_limit,
    }


class RenewSubscriptionRequest(BaseModel):
    days: int = 30  # Durée du renouvellement


@router.post("/tenants/{tenant_id}/renew-subscription")
def renew_subscription(
    tenant_id: int,
    body: RenewSubscriptionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    """Renouvelle l'abonnement du tenant de N jours à partir d'aujourd'hui (ou de l'expiration existante)."""
    if body.days <= 0:
        raise HTTPException(status_code=400, detail="La durée doit être positive")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    from datetime import datetime, timedelta
    now = datetime.utcnow()
    # Partir de l'expiration existante si elle est dans le futur, sinon partir d'aujourd'hui
    base = tenant.subscription_expires_at if (tenant.subscription_expires_at and tenant.subscription_expires_at > now) else now
    tenant.subscription_expires_at = base + timedelta(days=body.days)
    # Réinitialiser le trial si applicable
    if tenant.is_trial:
        tenant.is_trial = False
    db.commit()
    return {
        "status": "renewed",
        "subscription_expires_at": tenant.subscription_expires_at.isoformat() + "Z",
        "days_added": body.days,
    }


class ActivateSubscriptionRequest(BaseModel):
    days: int = 30
    plan: Optional[str] = None  # Si fourni, change aussi le plan


@router.post("/tenants/{tenant_id}/activate-subscription")
def activate_subscription(
    tenant_id: int,
    body: ActivateSubscriptionRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    """Active manuellement l'abonnement d'un tenant (paiement confirmé par admin)."""
    from datetime import datetime, timedelta
    from app.models import Subscription

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    now = datetime.utcnow()
    expires = now + timedelta(days=body.days)

    # Mettre à jour le tenant
    tenant.is_trial = False
    tenant.subscription_expires_at = expires
    if body.plan:
        try:
            tenant.plan = PlanType(body.plan)
            plan_config = PLAN_LIMITS.get(tenant.plan, {})
            if plan_config.get("whatsapp_messages", 0) > 0:
                tenant.messages_limit = plan_config["whatsapp_messages"]
        except ValueError:
            pass

    # Mettre à jour ou créer la Subscription
    sub = db.query(Subscription).filter(Subscription.tenant_id == tenant_id).first()
    if sub:
        sub.is_trial = False
        sub.status = "active"
        sub.subscription_start_date = now
        sub.subscription_end_date = expires
        sub.next_billing_date = expires
        if body.plan:
            sub.plan = body.plan
    else:
        sub = Subscription(
            tenant_id=tenant_id,
            plan=body.plan or tenant.plan.value,
            status="active",
            is_trial=False,
            trial_start_date=now,
            trial_end_date=now,
            subscription_start_date=now,
            subscription_end_date=expires,
        )
        db.add(sub)

    db.commit()
    db.refresh(tenant)
    return {
        "status": "activated",
        "tenant_id": tenant_id,
        "subscription_expires_at": expires.isoformat() + "Z",
        "days": body.days,
    }


@router.post("/tenants/{tenant_id}/cancel-subscription")
def cancel_subscription(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    """Résilie l'abonnement d'un tenant (annulation ou non-renouvellement)."""
    from datetime import datetime
    from app.models import Subscription

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    now = datetime.utcnow()
    tenant.subscription_expires_at = now  # Expire immédiatement

    sub = db.query(Subscription).filter(Subscription.tenant_id == tenant_id).first()
    if sub:
        sub.status = "cancelled"
        sub.cancelled_at = now
        sub.auto_renew = False

    db.commit()
    return {"status": "cancelled", "tenant_id": tenant_id}


# ======================== GESTION AGENTS ========================

@router.patch("/agents/{agent_id}")
def update_agent(
    agent_id: int,
    body: AgentUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    agent = db.query(AgentTemplate).filter(AgentTemplate.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")

    ALLOWED_FIELDS = {"tone", "name", "max_response_length", "language",
                      "emoji_enabled", "availability_start", "availability_end", "off_hours_message"}
    for field, value in body.model_dump(exclude_none=True).items():
        if field in ALLOWED_FIELDS:
            setattr(agent, field, value)
    db.commit()
    return {"status": "updated", "agent_id": agent_id}


@router.patch("/agents/{agent_id}/type")
def change_agent_type(
    agent_id: int,
    body: AgentTypeChangeRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    from app.services.agent_service import AGENT_SYSTEM_PROMPTS
    agent = db.query(AgentTemplate).filter(AgentTemplate.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")

    agent.agent_type = body.agent_type
    agent.system_prompt = AGENT_SYSTEM_PROMPTS.get(body.agent_type, "")
    agent.custom_prompt_override = None
    db.commit()
    return {"status": "type_changed", "agent_id": agent_id, "new_type": body.agent_type.value}


@router.post("/agents/{agent_id}/activate")
def activate_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    agent = db.query(AgentTemplate).filter(AgentTemplate.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")

    db.query(AgentTemplate).filter(
        AgentTemplate.tenant_id == agent.tenant_id,
        AgentTemplate.id != agent_id,
    ).update({"is_active": False})

    agent.is_active = True
    db.commit()
    return {"status": "activated", "agent_id": agent_id}


# ======================== SUPPRESSION DOUCE ========================

@router.delete("/tenants/{tenant_id}")
def soft_delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_superadmin_user),
):
    """Suppression douce : is_deleted=True + is_suspended=True. Irréversible depuis l'UI."""
    if tenant_id == 1:
        raise HTTPException(status_code=400, detail="Le tenant fondateur ne peut pas être supprimé")
    if tenant_id == admin.tenant_id:
        raise HTTPException(status_code=400, detail="Impossible de supprimer son propre tenant")

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id,
        Tenant.is_deleted == False,
    ).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé ou déjà supprimé")

    tenant.is_deleted = True
    tenant.is_suspended = True  # coupe l'accès immédiatement
    tenant.deleted_at = datetime.utcnow()
    tenant.suspension_reason = "Supprimé via panel admin"
    db.commit()
    return {"status": "deleted", "tenant_id": tenant_id, "tenant_name": tenant.name}


class BulkDeleteRequest(BaseModel):
    tenant_ids: List[int]
    hard_delete: bool = False  # True = suppression physique complète (cascade), False = soft delete


@router.post("/tenants/bulk-delete")
def bulk_delete_tenants(
    body: BulkDeleteRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(get_superadmin_user),
):
    """
    Supprime plusieurs tenants en une seule opération.
    hard_delete=False (défaut) : soft delete (is_deleted=True, accès coupé).
    hard_delete=True : suppression physique en cascade (messages → conversations → users → tenant).
    Le tenant fondateur (id=1) et le propre tenant de l'admin sont toujours protégés.
    """
    protected = {1, admin.tenant_id}
    ids = [i for i in body.tenant_ids if i not in protected]
    if not ids:
        raise HTTPException(status_code=400, detail="Aucun tenant valide à supprimer (tenant fondateur et votre tenant sont protégés)")

    results = []
    now = datetime.utcnow()

    for tid in ids:
        tenant = db.query(Tenant).filter(Tenant.id == tid).first()
        if not tenant:
            results.append({"tenant_id": tid, "status": "not_found"})
            continue

        if body.hard_delete:
            # Suppression physique en cascade
            conv_ids = [c.id for c in db.query(Conversation.id).filter(Conversation.tenant_id == tid).all()]
            if conv_ids:
                db.query(Message).filter(Message.conversation_id.in_(conv_ids)).delete(synchronize_session=False)
            db.query(Conversation).filter(Conversation.tenant_id == tid).delete(synchronize_session=False)
            db.query(WhatsAppSession).filter(WhatsAppSession.tenant_id == tid).delete(synchronize_session=False)
            db.query(Subscription).filter(Subscription.tenant_id == tid).delete(synchronize_session=False)
            db.query(UsageTracking).filter(UsageTracking.tenant_id == tid).delete(synchronize_session=False)
            db.query(User).filter(User.tenant_id == tid).delete(synchronize_session=False)
            db.delete(tenant)
            results.append({"tenant_id": tid, "name": tenant.name, "status": "hard_deleted"})
        else:
            tenant.is_deleted = True
            tenant.is_suspended = True
            tenant.deleted_at = now
            tenant.suspension_reason = "Supprimé en masse via panel admin"
            results.append({"tenant_id": tid, "name": tenant.name, "status": "soft_deleted"})

    db.commit()
    deleted_count = sum(1 for r in results if r["status"] in ("soft_deleted", "hard_deleted"))
    return {
        "deleted": deleted_count,
        "skipped": len(body.tenant_ids) - len(ids),
        "results": results,
    }


# ======================== IMPERSONATION ========================

# ======================== EMAIL TEST ========================

class TestEmailRequest(BaseModel):
    to: str  # adresse email de destination
    type: str = "welcome"  # welcome | reset | confirmation


@router.post("/test-email")
async def test_email(
    request: TestEmailRequest,
    _: User = Depends(get_superadmin_user),
):
    """
    Envoie un email de test vers l'adresse fournie.
    Types disponibles : welcome | reset | confirmation
    Réservé aux superadmins — ne pas exposer en production sans auth.
    """
    # Validation basique de l'adresse email
    if "@" not in request.to or "." not in request.to.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Adresse email invalide")
    if request.type == "welcome":
        success = await send_welcome_email(
            to_email=request.to,
            user_name="Test User",
            tenant_name="Entreprise Test",
            trial_end_date=None,
        )
    elif request.type == "reset":
        success = await send_password_reset_email(
            to_email=request.to,
            reset_link="https://app.neobot.africa/reset-password?token=TEST_TOKEN",
        )
    elif request.type == "confirmation":
        success = await send_confirmation_email(
            to_email=request.to,
            confirmation_link="https://app.neobot.africa/confirm-email?token=TEST_TOKEN",
        )
    else:
        raise HTTPException(status_code=400, detail="type doit être: welcome | reset | confirmation")

    if not success:
        raise HTTPException(status_code=502, detail="Brevo n'a pas pu envoyer l'email — vérifier BREVO_API_KEY et les logs")

    return {"success": True, "to": request.to, "type": request.type}


@router.post("/tenants/{tenant_id}/impersonate")
def impersonate_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(get_superadmin_user),
):
    """Token temporaire 1h pour tester un compte client sans changer de session."""
    user = db.query(User).filter(User.tenant_id == tenant_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Aucun utilisateur pour ce tenant")

    token = create_access_token(
        data={
            "sub": user.email,
            "user_id": user.id,
            "tenant_id": user.tenant_id,
            "impersonated_by": admin.id,
        },
        expires_delta=timedelta(hours=1),
    )
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    return {
        "access_token": token,
        "tenant_id": tenant_id,
        "tenant_name": tenant.name if tenant else "",
        "user_email": user.email,
        "expires_in": 3600,
    }


# ======================== WHATSAPP MESSAGE ADMIN → CLIENT ========================

@router.post("/tenants/{tenant_id}/whatsapp-message")
async def send_whatsapp_to_tenant(
    tenant_id: int,
    body: WhatsAppMessageRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    """
    Envoie un message WhatsApp à un client depuis le compte WhatsApp admin (tenant 1).
    Utilise le numéro WhatsApp connecté du tenant cible.
    """
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message vide")

    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id,
        Tenant.is_deleted == False,
    ).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    phone = tenant.whatsapp_phone
    if not phone:
        raise HTTPException(status_code=400, detail="Ce client n'a pas de numéro WhatsApp enregistré")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{WHATSAPP_SERVICE_URL}/api/whatsapp/tenants/1/send-message",
                json={"to": phone, "message": body.message.strip()},
                headers={"x-api-key": INTERNAL_API_KEY},
            )
        if r.status_code == 200:
            return {"sent": True, "phone": phone, "tenant": tenant.name}
        raise HTTPException(status_code=503, detail=f"WhatsApp service: {r.text[:200]}")
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="WhatsApp service timeout")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Erreur: {str(e)[:200]}")


# ======================== BROADCAST EMAIL ========================

@router.post("/broadcast-email")
async def broadcast_email(
    request: BroadcastEmailRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_superadmin_user),
):
    """
    Envoie un email personnalisé à tous les clients actifs (non supprimés, non suspendus).
    target='all' → tous, 'trial' → uniquement les clients en trial.
    Retourne {sent, failed, total} pour affichage dans le modal.
    """
    if not request.subject.strip() or not request.body.strip():
        raise HTTPException(status_code=400, detail="Sujet et corps requis")
    if len(request.subject) > 200:
        raise HTTPException(status_code=400, detail="Sujet trop long (200 chars max)")
    if len(request.body) > 5000:
        raise HTTPException(status_code=400, detail="Corps trop long (5000 chars max)")

    if request.target == "single":
        if not request.tenant_id:
            raise HTTPException(status_code=400, detail="tenant_id requis pour target=single")
        tenant = db.query(Tenant).filter(
            Tenant.id == request.tenant_id,
            Tenant.is_deleted == False,
        ).first()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant non trouvé")
        tenants = [tenant]
    else:
        q = db.query(Tenant).filter(Tenant.is_deleted == False, Tenant.is_suspended == False)
        if request.target == "trial":
            q = q.filter(Tenant.is_trial == True)
        tenants = q.all()

    sent, failed = 0, 0
    for t in tenants:
        ok = await send_custom_broadcast(
            to_email=t.email,
            to_name=t.name,
            subject=request.subject,
            body=request.body,
        )
        if ok:
            sent += 1
        else:
            failed += 1

    return {"sent": sent, "failed": failed, "total": len(tenants)}
