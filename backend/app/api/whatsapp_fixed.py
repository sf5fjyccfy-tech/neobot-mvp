"""
Endpoint WhatsApp corrigé et robuste
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Tenant, Conversation, Message
from app.services.fallback_service import FallbackService
import json

router = APIRouter()

async def generate_ai_response(tenant, message: str):
    """Version simplifiée de la réponse IA"""
    from app.services.fallback_service import FallbackService
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        fallback_service = FallbackService(db)
        return fallback_service.get_fallback_response(message, tenant.business_type, tenant.name)
    finally:
        db.close()

@router.post("/api/tenants/{tenant_id}/whatsapp/message-fixed")
async def receive_whatsapp_fixed(tenant_id: int, request: dict, db: Session = Depends(get_db)):
    """Endpoint WhatsApp corrigé - gère tous les formats de données"""
    print(f"🔍 WHATSAPP FIXED - Données reçues: {request}")
    
    # Rechercher le message dans différents formats
    message = None
    possible_keys = ['message', 'Message', 'text', 'body', 'content', 'msg']
    
    for key in possible_keys:
        if key in request:
            message = request[key]
            print(f"✅ Message trouvé avec clé '{key}': {message}")
            break
    
    if not message:
        print("❌ Aucun message trouvé dans les données")
        return {"response": "❌ Aucun message reçu", "source": "error"}
    
    if message == "Message" or message == "message":
        print("⚠️  Message générique détecté, probable erreur frontend")
        return {"response": "🤖 Je suis prêt ! Envoyez-moi votre demande (ex: 'je cherche des chaussures')", "source": "help"}
    
    phone = request.get("phone", "+237000000000")
    
    print(f"📞 Conversation: {phone} → {message}")
    
    # Suite du traitement normal...
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(404, "Tenant introuvable")
    
    # Vérifier les limites
    if not tenant.check_message_limit("whatsapp"):
        return {"response": "🚫 Limite de messages atteinte", "source": "error"}
    
    # Gérer conversation
    conv = db.query(Conversation).filter(
        Conversation.tenant_id == tenant_id,
        Conversation.customer_phone == phone
    ).first()
    
    if not conv:
        conv = Conversation(
            tenant_id=tenant_id,
            customer_phone=phone,
            customer_name=f"Client {phone[-4:]}",
            channel="whatsapp",
            status="active"
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    
    # Message entrant
    db.add(Message(
        conversation_id=conv.id,
        content=message,
        direction="incoming",
        is_ai=False
    ))
    db.commit()
    
    # Réponse
    reply = await generate_ai_response(tenant, message)
    
    # Message sortant
    db.add(Message(
        conversation_id=conv.id,
        content=reply,
        direction="outgoing",
        is_ai=True
    ))
    tenant.increment_message_count("whatsapp")
    db.commit()
    
    return {"response": reply, "source": "ai", "original_message": message}
