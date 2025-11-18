from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.contact_filter_service import ContactFilterService
from app.services.ai_service import generate_ai_response

router = APIRouter()

@router.post("/whatsapp/message")
async def whatsapp_message(request: Request, db: Session = Depends(get_db)):
    """Webhook pour messages WhatsApp entrants"""
    
    data = await request.json()
    
    phone = data.get("from")
    message = data.get("message")
    tenant_id = data.get("tenant_id")
    
    # Filtrage intelligent
    filter_service = ContactFilterService(db)
    is_business, reason = filter_service.is_business_contact(
        phone, message, tenant_id, "whatsapp"
    )
    
    if not is_business:
        # Message personnel → enregistrer pour notification
        from app.models import PendingMessage
        pending = PendingMessage(
            tenant_id=tenant_id,
            phone=phone,
            message=message,
            channel="whatsapp",
            filter_reason=reason
        )
        db.add(pending)
        db.commit()
        
        return {"status": "filtered", "reason": reason}
    
    # C'est un client → répondre
    ai_response = await generate_ai_response(message, tenant_id)
    
    # Envoyer via Baileys
    # ... (ton code existant)
    
    return {"status": "replied", "response": ai_response}
