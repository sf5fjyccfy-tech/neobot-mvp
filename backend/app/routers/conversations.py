"""
Router Conversations — Listing et détail des conversations/messages par tenant
Endpoints:
  GET  /api/tenants/{tenant_id}/conversations
  GET  /api/tenants/{tenant_id}/conversations/{conv_id}/messages
  POST /api/tenants/{tenant_id}/conversations/{conv_id}/send
  POST /api/tenants/{tenant_id}/conversations/{conv_id}/toggle-bot
"""
import os
import httpx
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, case
from typing import Optional

from app.database import get_db
from app.models import Conversation, Message, User, ConversationHumanState
from app.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["conversations"])

WHATSAPP_SERVICE_URL = os.getenv("WHATSAPP_SERVICE_URL", "http://localhost:3001")
INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY", "")
# Durée (minutes) pendant laquelle le bot reste silencieux après un message manuel
BOT_PAUSE_MINUTES = 30


def _check_tenant_access(tenant_id: int, current_user: User) -> None:
    """Vérifie que l'utilisateur a accès au tenant demandé."""
    if current_user.is_superadmin:
        return  # superadmin voit tout
    if current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Accès refusé à ce tenant")


@router.get("/{tenant_id}/conversations")
async def list_conversations(
    tenant_id: int,
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Liste les conversations du tenant, triées par dernier message.
    Inclut le dernier message de chaque conversation.
    """
    _check_tenant_access(tenant_id, current_user)
    try:
        q = db.query(Conversation).filter(Conversation.tenant_id == tenant_id)
        if status:
            q = q.filter(Conversation.status == status)
        convs = q.order_by(desc(Conversation.last_message_at)).offset(offset).limit(limit).all()

        conv_ids = [c.id for c in convs]

        # Requête 2 : agrégats en une passe (1 COUNT total + 1 COUNT incoming par conv)
        counts_rows = (
            db.query(
                Message.conversation_id,
                func.count(Message.id).label("total"),
                func.sum(case((Message.direction == "incoming", 1), else_=0)).label("incoming"),
            )
            .filter(Message.conversation_id.in_(conv_ids))
            .group_by(Message.conversation_id)
            .all()
        ) if conv_ids else []
        counts = {r.conversation_id: r for r in counts_rows}

        # Requête 3 : dernier message par conversation (JOIN sur max created_at)
        last_msg_sq = (
            db.query(
                Message.conversation_id,
                func.max(Message.created_at).label("max_at"),
            )
            .filter(Message.conversation_id.in_(conv_ids))
            .group_by(Message.conversation_id)
            .subquery()
        ) if conv_ids else None

        last_msgs: dict[int, Message] = {}
        if last_msg_sq is not None:
            for m in (
                db.query(Message)
                .join(
                    last_msg_sq,
                    (Message.conversation_id == last_msg_sq.c.conversation_id)
                    & (Message.created_at == last_msg_sq.c.max_at),
                )
                .all()
            ):
                last_msgs[m.conversation_id] = m

        result = []
        for c in convs:
            agg = counts.get(c.id)
            lm = last_msgs.get(c.id)
            result.append({
                "id": c.id,
                "tenant_id": c.tenant_id,
                "customer_phone": c.customer_phone,
                "customer_name": c.customer_name or c.customer_phone,
                "channel": getattr(c, "channel", "whatsapp"),
                "status": c.status or "active",
                "message_count": agg.total if agg else 0,
                "unread": (agg.incoming > 0) if agg else False,
                "last_message": lm.content if lm else "",
                "last_message_direction": lm.direction if lm else None,
                "last_message_is_ai": lm.is_ai if lm else False,
                "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            })

        total = db.query(func.count(Conversation.id)).filter(Conversation.tenant_id == tenant_id).scalar()
        return {"conversations": result, "total": total, "limit": limit, "offset": offset}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ list_conversations tenant={tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la récupération des conversations")


@router.get("/{tenant_id}/conversations/{conv_id}/messages")
async def get_messages(
    tenant_id: int,
    conv_id: int,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les messages d'une conversation, avec direction (incoming/outgoing), is_ai, heure.
    Vérifie que la conversation appartient bien au tenant.
    """
    _check_tenant_access(tenant_id, current_user)
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.tenant_id == tenant_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")

    msgs = (
        db.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "conversation_id": conv_id,
        "customer_phone": conv.customer_phone,
        "customer_name": conv.customer_name or conv.customer_phone,
        "messages": [
            {
                "id": m.id,
                "content": m.content,
                "direction": m.direction,   # "incoming" | "outgoing"
                "is_ai": m.is_ai,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in msgs
        ],
        "total": db.query(Message).filter(Message.conversation_id == conv_id).count(),
    }


# ── Schémas ────────────────────────────────────────────────────────────────

class ManualMessageBody(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)


class ToggleBotBody(BaseModel):
    paused: bool  # True = pause bot, False = reprendre IA


# ── Envoi message manuel (opérateur → client WhatsApp) ─────────────────────

@router.post("/{tenant_id}/conversations/{conv_id}/send")
async def send_manual_message(
    tenant_id: int,
    conv_id: int,
    body: ManualMessageBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Envoie un message manuel depuis l'interface opérateur vers le client WhatsApp.
    - Sauvegarde le message en DB (is_ai=False)
    - Met le bot en pause 30 min (ConversationHumanState)
    - Transmet le message au service WhatsApp
    """
    _check_tenant_access(tenant_id, current_user)
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.tenant_id == tenant_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")

    now = datetime.utcnow()

    # 1. Sauvegarder en DB
    msg = Message(
        conversation_id=conv_id,
        content=body.message,
        direction="outgoing",
        is_ai=False,
    )
    db.add(msg)
    conv.last_message_at = now

    # 2. Pause bot 30 min pour cette conversation
    human_state = db.query(ConversationHumanState).filter(
        ConversationHumanState.conversation_id == conv_id
    ).first()
    if human_state:
        human_state.human_active = True
        human_state.ai_paused_at = now
        human_state.last_human_message_at = now
    else:
        human_state = ConversationHumanState(
            conversation_id=conv_id,
            human_active=True,
            ai_paused_at=now,
            last_human_message_at=now,
        )
        db.add(human_state)

    db.commit()
    db.refresh(msg)

    # 3. Appel au service WhatsApp
    wa_ok = False
    wa_error = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                f"{WHATSAPP_SERVICE_URL}/api/whatsapp/tenants/{tenant_id}/send-message",
                json={"to": conv.customer_phone, "message": body.message},
                headers={"x-api-key": INTERNAL_API_KEY},
            )
            wa_ok = r.status_code == 200
            if not wa_ok:
                wa_error = r.text[:200]
                logger.warning(f"WA send failed ({r.status_code}): {wa_error}")
    except Exception as e:
        wa_error = str(e)
        logger.error(f"WA service unreachable: {e}")

    return {
        "message_id": msg.id,
        "whatsapp_sent": wa_ok,
        "bot_paused_until": (now + timedelta(minutes=BOT_PAUSE_MINUTES)).isoformat(),
        "created_at": msg.created_at.isoformat() if msg.created_at else now.isoformat(),
        **({"wa_error": wa_error} if wa_error else {}),
    }


# ── Toggle pause bot pour une conversation ─────────────────────────────────

@router.post("/{tenant_id}/conversations/{conv_id}/toggle-bot")
async def toggle_bot_pause(
    tenant_id: int,
    conv_id: int,
    body: ToggleBotBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Active ou désactive manuellement le bot pour une conversation.
    paused=True  → bot silencieux (opérateur répond)
    paused=False → bot reprend automatiquement
    """
    _check_tenant_access(tenant_id, current_user)
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.tenant_id == tenant_id,
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")

    now = datetime.utcnow()
    human_state = db.query(ConversationHumanState).filter(
        ConversationHumanState.conversation_id == conv_id
    ).first()

    if human_state:
        human_state.human_active = body.paused
        if body.paused:
            human_state.ai_paused_at = now
            human_state.last_human_message_at = now
    else:
        human_state = ConversationHumanState(
            conversation_id=conv_id,
            human_active=body.paused,
            ai_paused_at=now if body.paused else None,
            last_human_message_at=now if body.paused else None,
        )
        db.add(human_state)

    db.commit()
    return {"bot_paused": body.paused, "conversation_id": conv_id}


# ── Statut du bot pour une conversation ────────────────────────────────────

@router.get("/{tenant_id}/conversations/{conv_id}/bot-state")
async def get_bot_state(
    tenant_id: int,
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retourne si le bot est en pause (opérateur actif) pour cette conversation."""
    _check_tenant_access(tenant_id, current_user)
    human_state = db.query(ConversationHumanState).filter(
        ConversationHumanState.conversation_id == conv_id
    ).first()

    if not human_state or not human_state.human_active:
        return {"bot_paused": False}

    # Vérifier si la pause a expiré
    if human_state.last_human_message_at:
        expired = (datetime.utcnow() - human_state.last_human_message_at) > timedelta(minutes=BOT_PAUSE_MINUTES)
        if expired:
            human_state.human_active = False
            db.commit()
            return {"bot_paused": False}

    return {
        "bot_paused": True,
        "paused_since": human_state.ai_paused_at.isoformat() if human_state.ai_paused_at else None,
    }
