"""
NÉOBOT - Backend principal robuste et production-ready
Version: 1.0.0
"""
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from contextlib import asynccontextmanager
import logging
import os
from dotenv import load_dotenv
import httpx

# Imports locaux
from .database import get_db, init_db, Base, engine
from .models import Tenant, Conversation, Message
from .whatsapp_webhook import router as whatsapp_router
from .routers.tenant_business import router as tenant_business_router
from .routers.business import router as business_router
from .routers.auth import router as auth_router
from .routers.whatsapp import router as whatsapp_sessions_router
from .routers.usage import router as usage_router
from .routers.overage import router as overage_router
from .routers.analytics import router as analytics_router
from .routers.subscription import router as subscription_router
from .routers.setup import router as setup_router
from .routers.whatsapp_qr import router as whatsapp_qr_router
from .routers.contacts import router as contacts_router
from .routers.tenant_settings import router as tenant_settings_router
from .routers.human_detection import router as human_detection_router
from .routers.agents import router as agents_router
from .services.business_kb_service import BusinessKBService
from .http_client import close_http_client

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger .env
load_dotenv()

# ========== STARTUP/SHUTDOWN ==========
async def _startup_tasks():
    """Initialiser la DB au démarrage"""
    try:
        init_db()

        # Initialiser les types de business
        db = next(get_db())
        BusinessKBService.initialize_business_types(db)

        # Auto-configurer le tenant 1 comme NéoBot si pas encore configuré
        from app.models import TenantBusinessConfig, BusinessTypeModel
        import json

        existing_config = db.query(TenantBusinessConfig).filter(
            TenantBusinessConfig.tenant_id == 1
        ).first()

        if not existing_config:
            neobot_type = db.query(BusinessTypeModel).filter(
                BusinessTypeModel.slug == "neobot"
            ).first()

            if neobot_type:
                new_config = TenantBusinessConfig(
                    tenant_id=1,
                    business_type_id=neobot_type.id,
                    company_name="NéoBot",
                    company_description="Plateforme d'automatisation WhatsApp avec IA",
                    tone="Professional, Friendly, Expert",
                    selling_focus="Automatisation, Efficacité, Scaling",
                    products_services=json.dumps([
                        {
                            "name": "NéoBot Starter",
                            "price": 20000,
                            "description": "500 messages/mois + Support"
                        },
                        {
                            "name": "NéoBot Pro",
                            "price": 50000,
                            "description": "Messages illimités + Analytics + API"
                        },
                        {
                            "name": "NéoBot Enterprise",
                            "price": 100000,
                            "description": "Tout illimité + Support prioritaire"
                        }
                    ])
                )
                db.add(new_config)
                db.commit()
                logger.info("✅ NéoBot tenant configuration initialized")

        logger.info("✅ Application démarrée")
    except Exception as e:
        logger.error(f"❌ Erreur startup: {e}")


async def _shutdown_tasks():
    """Cleanup au shutdown"""
    await close_http_client()
    logger.info("🛑 Application arrêtée")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await _startup_tasks()
    try:
        yield
    finally:
        await _shutdown_tasks()


# ========== APP CREATION ==========
app = FastAPI(
    title="NÉOBOT",
    version="1.0.0",
    description="WhatsApp Bot Assistant avec IA",
    lifespan=lifespan,
)

# ========== INCLUDE ROUTERS ==========
app.include_router(auth_router)
app.include_router(whatsapp_router)
app.include_router(whatsapp_sessions_router)
app.include_router(usage_router)
app.include_router(overage_router)
app.include_router(analytics_router)
app.include_router(subscription_router)
app.include_router(setup_router)
app.include_router(whatsapp_qr_router)
app.include_router(contacts_router)
app.include_router(tenant_settings_router)
app.include_router(human_detection_router)
app.include_router(tenant_business_router)
app.include_router(business_router)
app.include_router(agents_router)

# ========== CORS MIDDLEWARE ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # Development frontend
        "http://127.0.0.1:3000",      # Development frontend
        "https://app.votre-domaine.com",  # Production frontend (change this)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)

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
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"DB Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
        )

# ========== ROOT ENDPOINT ==========
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🚀 NÉOBOT API v1.0.0",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/api/docs-info")
async def docs_info():
    """Informations rapides sur les endpoints API."""
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
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(e),
                "response": "Désolé, une erreur s'est produite."
            }
        )

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
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handler personnalisé pour les erreurs HTTP"""
    detail = getattr(exc, "detail", str(exc))
    status_code = getattr(exc, "status_code", 500)
    return JSONResponse(
        status_code=status_code,
        content={
            "error": detail,
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
