"""
Router Conversations — Listing et détail des conversations/messages par tenant
Endpoints:
  GET /api/tenants/{tenant_id}/conversations
  GET /api/tenants/{tenant_id}/conversations/{conv_id}/messages
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, case
from typing import Optional

from app.database import get_db
from app.models import Conversation, Message, User
from app.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["conversations"])


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
