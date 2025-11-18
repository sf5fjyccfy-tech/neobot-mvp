from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Conversation, Message, Tenant
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/tenants/{tenant_id}/conversations/recent")
async def get_recent_conversations(tenant_id: int, db: Session = Depends(get_db)):
    """Récupérer les conversations et messages récents"""
    
    # Vérifier que le tenant existe
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")
    
    # Conversations des dernières 24h
    yesterday = datetime.utcnow() - timedelta(hours=24)
    
    recent_conversations = db.query(Conversation).filter(
        Conversation.tenant_id == tenant_id,
        Conversation.last_message_at >= yesterday
    ).order_by(Conversation.last_message_at.desc()).limit(10).all()
    
    # Messages récents pour l'activité
    recent_messages = []
    for conv in recent_conversations[:5]:  # Limiter à 5 conversations
        last_message = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at.desc()).first()
        
        if last_message:
            recent_messages.append({
                "customer_phone": conv.customer_phone,
                "content": last_message.content,
                "created_at": last_message.created_at.isoformat(),
                "direction": last_message.direction,
                "is_ai": last_message.is_ai
            })
    
    return {
        "conversations": [
            {
                "id": conv.id,
                "customer_phone": conv.customer_phone,
                "customer_name": conv.customer_name,
                "last_message_at": conv.last_message_at.isoformat(),
                "status": conv.status
            } for conv in recent_conversations
        ],
        "recent_messages": recent_messages,
        "total_active": len([c for c in recent_conversations if c.status == "active"])
    }
