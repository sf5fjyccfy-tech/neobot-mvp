"""
NÉOBOT - Backend principal robuste et production-ready
Version: 1.0.0
"""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import httpx

# Imports locaux
from .database import get_db, init_db, Base, engine
from .models import Tenant, Conversation, Message
from .whatsapp_webhook import router as whatsapp_router

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger .env
load_dotenv()

# ========== APP CREATION ==========
app = FastAPI(
    title="NÉOBOT",
    version="1.0.0",
    description="WhatsApp Bot Assistant avec IA"
)

# ========== INCLUDE ROUTERS ==========
app.include_router(whatsapp_router)

# ========== CORS MIDDLEWARE ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== STARTUP/SHUTDOWN ==========
@app.on_event("startup")
async def startup():
    """Initialiser la DB au démarrage"""
    try:
        init_db()
        logger.info("✅ Application démarrée")
    except Exception as e:
        logger.error(f"❌ Erreur startup: {e}")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup au shutdown"""
    logger.info("🛑 Application arrêtée")

# ========== HEALTH CHECKS ==========
@app.get("/health")
async def health():
    """Health check simple"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/health")
async def api_health(db: Session = Depends(get_db)):
    """Health check avec vérification DB"""
    try:
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"DB Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }, 503

# ========== ROOT ENDPOINT ==========
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🚀 NÉOBOT API v1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/docs")
async def docs():
    """Documentation API"""
    return {
        "endpoints": {
            "health": "GET /health",
            "tenants": "GET /api/tenants",
            "whatsapp": "POST /api/whatsapp/message",
            "conversations": "GET /api/conversations/{tenant_id}"
        }
    }

# ========== TENANT ENDPOINTS ==========
@app.get("/api/tenants")
async def list_tenants(db: Session = Depends(get_db)):
    """Lister tous les tenants"""
    tenants = db.query(Tenant).all()
    return {
        "count": len(tenants),
        "tenants": [
            {
                "id": t.id,
                "name": t.name,
                "email": t.email,
                "plan": t.plan,
                "whatsapp_connected": t.whatsapp_connected
            }
            for t in tenants
        ]
    }

@app.get("/api/tenants/{tenant_id}")
async def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    """Récupérer un tenant"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "plan": tenant.plan.value,
        "whatsapp_connected": tenant.whatsapp_connected,
        "messages_used": tenant.messages_used,
        "messages_limit": tenant.messages_limit
    }

@app.post("/api/tenants")
async def create_tenant(data: dict, db: Session = Depends(get_db)):
    """Créer un nouveau tenant"""
    try:
        tenant = Tenant(
            name=data.get("name"),
            email=data.get("email"),
            phone=data.get("phone"),
            business_type=data.get("business_type", "autre")
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        
        logger.info(f"✅ Tenant créé: {tenant.name} (ID: {tenant.id})")
        return {
            "success": True,
            "tenant_id": tenant.id,
            "message": "Tenant créé"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur création tenant: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ========== WHATSAPP WEBHOOK ==========
@app.post("/api/whatsapp/message")
async def whatsapp_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook WhatsApp: recevoir les messages et générer des réponses
    """
    try:
        data = await request.json()
        phone = data.get("from")
        message_text = data.get("message")
        tenant_id = data.get("tenant_id", 1)
        
        logger.info(f"📨 Message reçu de {phone}: {message_text}")
        
        # Vérifier le tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return {"error": "Tenant not found"}, 404
        
        # Créer/récupérer la conversation
        conversation = db.query(Conversation).filter(
            Conversation.tenant_id == tenant_id,
            Conversation.customer_phone == phone
        ).first()
        
        if not conversation:
            conversation = Conversation(
                tenant_id=tenant_id,
                customer_phone=phone,
                customer_name=f"Client {phone[-4:]}"
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            logger.info(f"📝 Conversation créée: {conversation.id}")
        
        # Sauvegarder le message entrant
        incoming_msg = Message(
            conversation_id=conversation.id,
            content=message_text,
            direction="incoming",
            is_ai=False
        )
        db.add(incoming_msg)
        
        # Générer la réponse IA
        ai_response = await get_ai_response(message_text, tenant.name)
        
        # Sauvegarder la réponse
        outgoing_msg = Message(
            conversation_id=conversation.id,
            content=ai_response,
            direction="outgoing",
            is_ai=True
        )
        db.add(outgoing_msg)
        
        # Mettre à jour les métriques
        tenant.messages_used += 2
        conversation.last_message_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"✅ Réponse générée: {ai_response[:50]}...")
        
        return {
            "status": "ok",
            "phone": phone,
            "message": message_text,
            "response": ai_response,
            "conversation_id": conversation.id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erreur webhook: {e}")
        return {
            "status": "error",
            "error": str(e),
            "response": "Désolé, une erreur s'est produite."
        }, 500

# ========== CONVERSATION ENDPOINTS ==========
@app.get("/api/conversations/{tenant_id}")
async def get_conversations(tenant_id: int, db: Session = Depends(get_db)):
    """Lister les conversations d'un tenant"""
    conversations = db.query(Conversation).filter(
        Conversation.tenant_id == tenant_id
    ).all()
    
    return {
        "tenant_id": tenant_id,
        "count": len(conversations),
        "conversations": [
            {
                "id": c.id,
                "customer_phone": c.customer_phone,
                "customer_name": c.customer_name,
                "status": c.status,
                "messages": len(c.messages),
                "last_message": c.last_message_at.isoformat()
            }
            for c in conversations
        ]
    }

@app.get("/api/messages/{conversation_id}")
async def get_messages(conversation_id: int, db: Session = Depends(get_db)):
    """Récupérer les messages d'une conversation"""
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()
    
    return {
        "conversation_id": conversation_id,
        "count": len(messages),
        "messages": [
            {
                "id": m.id,
                "content": m.content,
                "direction": m.direction,
                "is_ai": m.is_ai,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }

# ========== IA INTEGRATION ==========
async def get_ai_response(message: str, business_name: str = "NéoBot") -> str:
    """
    Générer une réponse IA via DeepSeek
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        logger.warning("⚠️ DEEPSEEK_API_KEY not set, using fallback")
        return get_fallback_response(message, business_name)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"Tu es l'assistant de {business_name}. Réponds en français, sois courtois et concis (max 2 phrases)."
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 150
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                ai_response = data['choices'][0]['message']['content']
                logger.info(f"🤖 IA réponse générée")
                return ai_response
            else:
                logger.warning(f"⚠️ DeepSeek API error: {response.status_code}")
                return get_fallback_response(message, business_name)
                
    except Exception as e:
        logger.error(f"❌ Erreur IA: {e}")
        return get_fallback_response(message, business_name)

def get_fallback_response(message: str, business_name: str = "NéoBot") -> str:
    """
    Réponse de fallback quand l'IA ne répond pas
    """
    msg_lower = message.lower()
    
    if any(word in msg_lower for word in ["bonjour", "salut", "hello", "hi"]):
        return f"👋 Bonjour ! Bienvenue chez {business_name}. Comment puis-je vous aider ?"
    elif any(word in msg_lower for word in ["prix", "tarif", "coût", "combien"]):
        return f"💰 Pour plus d'informations sur nos tarifs, veuillez nous contacter directement."
    elif any(word in msg_lower for word in ["horaire", "ouvert", "ferme"]):
        return f"🕐 Pour connaître nos horaires, veuillez nous contacter."
    elif any(word in msg_lower for word in ["merci", "thank"]):
        return f"😊 De rien ! Avez-vous autre chose ?"
    else:
        return f"✅ Merci pour votre message ! Notre équipe vous répondra rapidement."

# ========== ERROR HANDLERS ==========
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler personnalisé pour les erreurs HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler générique pour les erreurs"""
    logger.error(f"❌ Erreur non gérée: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ========== RUN APP ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", 8000)),
        reload=os.getenv("BACKEND_RELOAD", "true").lower() == "true"
    )
