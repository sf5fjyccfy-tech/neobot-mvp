"""
NÉOBOT - Backend principal robuste et production-ready
Version: 1.0.0
"""
from fastapi import FastAPI, HTTPException, Request, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from contextlib import asynccontextmanager
import logging
import os
import asyncio
from dotenv import load_dotenv
import httpx
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Imports locaux
from .database import get_db, init_db, Base, engine, SessionLocal
from .models import Tenant, Conversation, Message, User
from .dependencies import get_superadmin_user
from .middleware_security import SecurityHeadersMiddleware
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
from .routers.admin import router as admin_router
from .routers.conversations import router as conversations_router
from .routers.neo_assistant import router as neo_assistant_router
from .routers.neopay import router as neopay_router
from .routers.sentry_webhook import router as sentry_webhook_router
from .routers.monitoring import router as monitoring_router
from .routers.demo import router as demo_router
from .services import neopay_service
from .services import monitoring_service
from .services.email_service import send_internal_alert
from .services.business_kb_service import BusinessKBService
from .http_client import close_http_client
from .middleware_subscription import SubscriptionMiddleware
from .limiter import limiter

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Classe définie ici, appliquée dans _startup_tasks APRÈS que uvicorn a appelé
# dictConfig() — sans ça, uvicorn écrase le filtre au démarrage.
class _SuppressASGIExceptionLog(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "Exception in ASGI application" not in record.getMessage()

# Charger .env — cherche d'abord backend/.env, puis racine du projet
load_dotenv()
load_dotenv(dotenv_path="/home/tim/neobot-mvp/.env", override=False)

# ========== SENTRY ==========
_sentry_dsn = os.getenv("SENTRY_DSN")
if _sentry_dsn and not _sentry_dsn.startswith("REMPLACER"):
    sentry_sdk.init(
        dsn=_sentry_dsn,
        environment=os.getenv("APP_ENV", "development"),
        traces_sample_rate=0.2 if os.getenv("APP_ENV") == "production" else 1.0,
        integrations=[
            FastApiIntegration(),
            SqlalchemyIntegration(),
        ],
        # Filtrer les 4xx sauf 401/403 (attaques à monitor) et sauf 429 (rate limit)
        before_send=lambda event, hint: None if (
            hint.get("exc_info") and
            isinstance(hint["exc_info"][1], HTTPException) and
            400 <= hint["exc_info"][1].status_code < 500 and
            hint["exc_info"][1].status_code not in (401, 403)
        ) else event,
    )
    logger.info("✅ Sentry initialisé")
else:
    logger.warning("⚠️  SENTRY_DSN non défini — monitoring Sentry désactivé")

# ========== STARTUP/SHUTDOWN ==========
async def _startup_tasks():
    """Initialiser la DB au démarrage"""
    # Appliqué ICI car uvicorn appelle logging.config.dictConfig() avant ce point,
    # ce qui efface tout filtre posé au chargement du module.
    _f = _SuppressASGIExceptionLog()
    logging.getLogger("uvicorn.error").addFilter(_f)
    for _h in logging.root.handlers:  # couvre la propagation vers root
        _h.addFilter(_f)

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
                    company_description="Plateforme SaaS africaine d'automatisation WhatsApp par IA — PME africaines, réponses 24h/24 7j/7",
                    tone="Professional, Friendly, Expert, Persuasif",
                    selling_focus="Automatisation WhatsApp, gain de clients, disponibilité 24h/24",
                    products_services=json.dumps([
                        {
                            "name": "Essential",
                            "price": 20000,
                            "description": "2 500 messages/mois — 1 agent IA — Sources Texte + PDF — Essai 14j gratuit",
                            "features": [
                                "2 500 messages WhatsApp/mois",
                                "1 agent IA actif",
                                "Sources de connaissance : Texte + PDF (3 max)",
                                "Génération de prompt par IA",
                                "Délai de réponse configurable",
                                "Rappels RDV automatiques",
                                "Dashboard Analytics 30 jours",
                                "Support par email",
                                "Essai gratuit 14 jours — aucune carte bancaire requise"
                            ]
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


async def _retry_webhooks_loop():
    """Background task : retente les webhooks échoués toutes les 5 min."""
    loop = asyncio.get_event_loop()
    while True:
        await asyncio.sleep(300)  # 5 minutes
        db = SessionLocal()
        try:
            await loop.run_in_executor(None, neopay_service.retry_failed_webhooks, db)
        except Exception as exc:
            import sentry_sdk as _sentry
            _sentry.capture_exception(exc)
            logger.error(f"❌ retry_webhooks_loop error: {exc}")
        finally:
            db.close()


async def _credits_check_loop():
    """Vérifie les balances API DeepSeek + Anthropic toutes les heures."""
    while True:
        await asyncio.sleep(3600)  # 1h
        db = SessionLocal()
        try:
            await monitoring_service.check_and_store_credits(db)
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            logger.error(f"❌ credits_check_loop error: {exc}")
        finally:
            db.close()


async def _morning_summary_loop():
    """Envoie un résumé des alertes Sentry ouvertes à 8h UTC chaque jour."""
    from datetime import datetime as _dt, timezone as _tz
    while True:
        now = _dt.now(_tz.utc)
        # Prochain 8h00 UTC
        target = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if now >= target:
            # On est déjà passé 8h aujourd'hui — attendre demain
            from datetime import timedelta as _td
            target += _td(days=1)
        await asyncio.sleep((target - now).total_seconds())
        db = SessionLocal()
        try:
            await monitoring_service.send_morning_summary(db)
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            logger.error(f"❌ morning_summary_loop error: {exc}")
        finally:
            db.close()


async def _db_cleanup_loop():
    """
    Cron hebdomadaire : dimanche à 3h UTC.
    - Archive les conversations de plus de 6 mois dans conversations_archive
    - Log la taille actuelle de la base Neon
    - Envoie une alerte email si la base dépasse 400 MB (limite Neon free : 512 MB)
    """
    from datetime import datetime as _dt, timezone as _tz, timedelta as _td
    while True:
        now = _dt.now(_tz.utc)
        # Prochain dimanche 3h00 UTC
        days_until_sunday = (6 - now.weekday()) % 7  # 6 = dimanche
        next_run = now.replace(hour=3, minute=0, second=0, microsecond=0) + _td(days=days_until_sunday)
        if next_run <= now:
            next_run += _td(weeks=1)
        await asyncio.sleep((next_run - now).total_seconds())

        db = SessionLocal()
        try:
            # 1. Créer la table d'archive si elle n'existe pas
            db.execute(text("""
                CREATE TABLE IF NOT EXISTS conversations_archive (
                    id             INTEGER,
                    tenant_id      INTEGER,
                    customer_phone VARCHAR(50),
                    customer_name  VARCHAR(255),
                    channel        VARCHAR(50),
                    status         VARCHAR(50),
                    created_at     TIMESTAMP,
                    last_message_at TIMESTAMP,
                    outcome_type   VARCHAR(50),
                    outcome_detected_at TIMESTAMP,
                    archived_at    TIMESTAMPTZ DEFAULT NOW()
                )
            """))
            db.commit()

            # 2. Copier les conversations de plus de 6 mois (sans supprimer — safe pour MVP)
            result = db.execute(text("""
                INSERT INTO conversations_archive
                    (id, tenant_id, customer_phone, customer_name, channel, status,
                     created_at, last_message_at, outcome_type, outcome_detected_at, archived_at)
                SELECT id, tenant_id, customer_phone, customer_name, channel, status,
                       created_at, last_message_at, outcome_type, outcome_detected_at, NOW()
                FROM conversations
                WHERE created_at < NOW() - INTERVAL '6 months'
                  AND id NOT IN (SELECT id FROM conversations_archive WHERE id IS NOT NULL)
            """))
            db.commit()
            archived_count = result.rowcount
            logger.info(f"✅ DB cleanup : {archived_count} conversations archivées")

            # 3. Mesurer la taille de la base
            size_result = db.execute(text(
                "SELECT pg_database_size(current_database()) AS bytes"
            )).fetchone()
            size_mb = round(size_result.bytes / (1024 * 1024), 1) if size_result else 0
            logger.info(f"📊 Taille base Neon : {size_mb} MB")

            # 4. Alerte si on approche de la limite
            alert_email = os.getenv("NEOPAY_ALERT_EMAIL", "neobot561@gmail.com")
            if size_mb > 400:
                await send_internal_alert(
                    subject=f"⚠️ NéoBot — Base de données à {size_mb} MB (limite : 512 MB)",
                    body=(
                        f"La base de données Neon atteint {size_mb} MB.\n\n"
                        f"Conversations archivées ce cycle : {archived_count}\n\n"
                        f"Action requise : supprimer les anciennes données ou migrer vers un plan supérieur.\n"
                        f"Limite Neon free tier : 512 MB."
                    )
                )
                logger.warning(f"⚠️ Alerte taille DB envoyée : {size_mb} MB > 400 MB")
            else:
                logger.info(f"✅ Taille DB OK : {size_mb} MB / 512 MB")

        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            logger.error(f"❌ db_cleanup_loop error: {exc}")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await _startup_tasks()
    retry_task    = asyncio.create_task(_retry_webhooks_loop())
    credits_task  = asyncio.create_task(_credits_check_loop())
    morning_task  = asyncio.create_task(_morning_summary_loop())
    cleanup_task  = asyncio.create_task(_db_cleanup_loop())
    try:
        yield
    finally:
        retry_task.cancel()
        credits_task.cancel()
        morning_task.cancel()
        cleanup_task.cancel()
        await _shutdown_tasks()


# ========== APP CREATION ==========
app = FastAPI(
    title="NÉOBOT",
    version="1.0.0",
    description="WhatsApp Bot Assistant avec IA",
    lifespan=lifespan,
)

# Rate limiting via slowapi — identifie les clients par IP
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Handler global pour les exceptions non gérées (500)
# CRITIQUE : sans ça, les 500 passent par ServerErrorMiddleware (plus externe que
# CORSMiddleware) → réponse sans headers CORS → erreur "Access-Control-Allow-Origin manquant".
# En enregistrant ce handler ICI, l'exception est capturée par ExceptionMiddleware
# de FastAPI (qui est DANS le stack CORSMiddleware) → CORS headers ajoutés correctement.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception [%s %s]: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur. Veuillez réessayer."},
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
app.include_router(admin_router)
app.include_router(conversations_router)
app.include_router(neo_assistant_router)
app.include_router(neopay_router)
app.include_router(sentry_webhook_router)
app.include_router(monitoring_router)
app.include_router(demo_router)

# ========== CORS MIDDLEWARE ==========
# Note : les middlewares Starlette s'exécutent dans l'ordre inverse d'ajout.
# CORS doit être ajouté EN DERNIER pour être exécuté EN PREMIER (traite les OPTIONS avant subscription check).
app.add_middleware(GZipMiddleware, minimum_size=500)
app.add_middleware(SubscriptionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600,
)
# SecurityHeadersMiddleware en dernier = plus externe = s'exécute en premier
# Ajoute les headers de sécurité sur TOUTES les réponses, y compris les erreurs CORS
app.add_middleware(SecurityHeadersMiddleware)

# ========== HEALTH CHECKS ==========
@app.get("/health")
async def health():
    """Health check simple"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.head("/health")
async def health_head():
    """HEAD /health — UptimeRobot et autres monitors utilisent HEAD"""
    return Response(status_code=200)

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


@app.get("/api/service-health")
async def service_health():
    """Proxy public vers le health check du service WhatsApp — utilisé par la page /status."""
    whatsapp_url = os.getenv("WHATSAPP_SERVICE_URL", "http://localhost:3001")
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(f"{whatsapp_url}/health")
            data = resp.json()
            return JSONResponse(status_code=resp.status_code, content=data)
    except httpx.TimeoutException:
        return JSONResponse(status_code=503, content={"status": "down", "detail": "timeout"})
    except Exception as exc:
        return JSONResponse(status_code=503, content={"status": "down", "detail": str(exc)})

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

# ========== DEBUG SENTRY (superadmin uniquement, désactivé en production) ==========
@app.get("/debug-sentry")
async def debug_sentry(_: User = Depends(get_superadmin_user)):
    """Déclenche une erreur intentionnelle pour valider l'intégration Sentry.
    Accessible aux superadmins uniquement et désactivé en production."""
    if os.getenv("APP_ENV", "development") == "production":
        raise HTTPException(status_code=403, detail="Endpoint debug désactivé en production")
    raise ValueError("Test Sentry NéoBot Backend — this is intentional")

# ========== TENANT ENDPOINTS (superadmin only) ==========
@app.get("/api/tenants")
async def list_tenants(db: Session = Depends(get_db), _: User = Depends(get_superadmin_user)):
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
async def get_tenant(tenant_id: int, db: Session = Depends(get_db), _: User = Depends(get_superadmin_user)):
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
async def create_tenant(data: dict, db: Session = Depends(get_db), _: User = Depends(get_superadmin_user)):
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
    # Forwarder les headers de l'exception (ex. WWW-Authenticate sur 401)
    exc_headers = getattr(exc, "headers", None) or {}
    return JSONResponse(
        status_code=status_code,
        content={
            "error": detail,
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        },
        headers=exc_headers,
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handler générique pour les erreurs"""
    import traceback as _tb
    tb = _tb.format_exc()
    logger.error(f"❌ Erreur non gérée: {exc}\n{tb}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Une erreur interne est survenue.",
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
