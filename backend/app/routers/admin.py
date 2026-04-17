"""
Admin Router — Accès superadmin uniquement
Gestion globale : tenants, agents, stats, suspension, impersonation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta

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
    total_tenants = db.query(func.count(Tenant.id)).filter(Tenant.is_deleted == False).scalar()
    active_tenants = db.query(func.count(Tenant.id)).filter(Tenant.is_deleted == False, Tenant.is_suspended == False).scalar()
    suspended_count = db.query(func.count(Tenant.id)).filter(Tenant.is_deleted == False, Tenant.is_suspended == True).scalar()
    wa_connected = db.query(func.count(WhatsAppSession.id)).filter(
        WhatsAppSession.is_connected == True
    ).scalar()
    total_conversations = db.query(func.count(Conversation.id)).scalar()
    total_agents = db.query(func.count(AgentTemplate.id)).scalar()
    messages_total = db.query(func.sum(Tenant.messages_used)).filter(Tenant.is_deleted == False).scalar() or 0

    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    new_this_week = db.query(func.count(Tenant.id)).filter(Tenant.is_deleted == False, Tenant.created_at >= week_ago).scalar()

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

    # Bulk-query usage_tracking pour le mois courant — évite N+1
    current_month = datetime.now().strftime('%Y-%m')
    usage_records = db.query(UsageTracking).filter(
        UsageTracking.month_year == current_month
    ).all()
    usage_map = {u.tenant_id: u.whatsapp_messages_used for u in usage_records}

    result = []
    for t in tenants:
        wa = db.query(WhatsAppSession).filter(WhatsAppSession.tenant_id == t.id).first()
        agent_count = db.query(func.count(AgentTemplate.id)).filter(
            AgentTemplate.tenant_id == t.id
        ).scalar()
        user = db.query(User).filter(User.tenant_id == t.id).first()
        sub = db.query(Subscription).filter(Subscription.tenant_id == t.id).first()
        last_conv_at = db.query(func.max(Conversation.created_at)).filter(
            Conversation.tenant_id == t.id
        ).scalar()

        # Calcul trial — trial_end_date peut être datetime ou date selon la colonne
        trial_ends_at = None
        trial_days_remaining = None
        if sub and sub.is_trial and sub.trial_end_date:
            today = datetime.now(timezone.utc).date()
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
            "subscription_expires_at": t.subscription_expires_at.isoformat() if t.subscription_expires_at else None,
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

    agents = db.query(AgentTemplate).filter(AgentTemplate.tenant_id == tenant_id).all()
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
        today = datetime.now(timezone.utc).date()
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
        "subscription_expires_at": tenant.subscription_expires_at.isoformat() if tenant.subscription_expires_at else None,
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        } if user else None,
        "agents": [
            {
                "id": a.id,
                "name": a.name,
                "agent_type": a.agent_type.value,
                "is_active": a.is_active,
                "prompt_score": a.prompt_score,
                "tone": a.tone,
                "language": a.language,
                "emoji_enabled": a.emoji_enabled,
                "max_response_length": a.max_response_length,
                "custom_prompt_override": a.custom_prompt_override,
                "system_prompt": a.system_prompt,
                "availability_start": a.availability_start,
                "availability_end": a.availability_end,
                "off_hours_message": a.off_hours_message,
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
    tenant.suspended_at = datetime.now(timezone.utc)
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
    tenant.deleted_at = datetime.now(timezone.utc)
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
    now = datetime.now(timezone.utc)

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
