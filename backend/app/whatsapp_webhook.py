"""
🧠 WhatsApp Webhook Handler for NéoBot Backend
Receives messages from WhatsApp service and processes them
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from pydantic import BaseModel, field_validator
from datetime import datetime, timedelta
from typing import Optional
import random
import httpx
import os
import logging
from app.services.http_client import get_http_client
import hmac
import hashlib
import sentry_sdk
from sqlalchemy.orm import Session
from sqlalchemy import func

# Imports locaux
import asyncio
from app.database import get_db
from app.models import Conversation, Message, ConversationHumanState, TenantBusinessConfig
from app.services.business_kb_service import BusinessKBService
from app.services.contact_filter_service import ContactFilterService
from app.services.agent_service import AgentService

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(tags=["webhooks"])

WEBHOOK_SECRET = os.getenv("WHATSAPP_WEBHOOK_SECRET") or os.getenv("WHATSAPP_SECRET_KEY") or ""
APP_ENV = os.getenv("APP_ENV", "development")


def _compute_webhook_signature(message: "WhatsAppMessage", secret: str) -> str:
    """Build deterministic signature from key message fields."""
    payload = f"{message.from_}|{message.text}|{message.timestamp}"
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _is_valid_webhook_signature(request: Request, message: "WhatsAppMessage") -> bool:
    """Validate HMAC signature.
    - Si WEBHOOK_SECRET est défini : signature obligatoire (dev + prod).
    - Si WEBHOOK_SECRET absent ET env=development : permissif (service interne).
    - Si WEBHOOK_SECRET absent ET env=production : rejette tout — configuration requise.
    """
    if not WEBHOOK_SECRET:
        if APP_ENV == "production":
            logger.error("CRITIQUE: WHATSAPP_WEBHOOK_SECRET non défini en production — toutes les requêtes rejetées")
            return False
        # Dev sans secret configuré : permissif (Baileys local ne signe pas)
        return True

    signature = request.headers.get("x-webhook-signature")
    if not signature:
        return False

    expected = _compute_webhook_signature(message, WEBHOOK_SECRET)
    return hmac.compare_digest(signature, expected)

# ===== Models =====

class WhatsAppMessage(BaseModel):
    """Incoming message from WhatsApp service"""
    tenant_id: Optional[int] = None
    from_: Optional[str] = None  # Phone number
    reply_jid: Optional[str] = None  # JID exact de l'expéditeur (ex: 221XXXXXXX@s.whatsapp.net ou @lid)
    to: Optional[str] = None     # Bot number (optional)
    text: str
    senderName: str
    messageKey: dict
    timestamp: int
    isMedia: bool = False

    @field_validator('text', mode='before')
    @classmethod
    def truncate_text(cls, v: str) -> str:
        """Limiter le texte entrant à 4096 chars — prévient les injections massives."""
        if v and len(v) > 4096:
            return v[:4096]
        return v


class WhatsAppResponse(BaseModel):
    """Response to send back"""
    to: str
    text: str


# ===== Brain (Simple Orchestrator) =====

class BrainOrchestrator:
    """
    Pattern matching + DeepSeek with Business Context enrichment
    Now uses tenant business configuration for intelligent responses
    """
    
    def __init__(self):
        # ⚠️ DISABLED: Patterns are now handled by Intent Classifier + Sales Prompt Generator
        # Keep empty dict to maintain compatibility but don't use it
        self.patterns = {}
        
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.deepseek_url = 'https://api.deepseek.com/v1/chat/completions'
    
    async def process(self, message: str, sender_name: str, db: Session = None, tenant_id: int = 1, conversation_id: int = None) -> str:
        """
        Process incoming message and return response
        Now supports business context enrichment
        
        Args:
            message: User message
            sender_name: Sender name
            db: Database session (optional)
            tenant_id: Tenant ID (default 1 for testing)
            conversation_id: Conversation ID (for context)
        """
        logger.info(f"Processing message from {sender_name}: {message}")
        
        # Normalize message
        normalized = message.lower().strip()
        
        # Check patterns (still support pattern matching as first line)
        for keyword, handler in self.patterns.items():
            if keyword in normalized:
                response = handler(sender_name)
                logger.info(f"Matched pattern '{keyword}': {response}")
                return response
        
        # No pattern matched → call DeepSeek with business context
        logger.info(f"No pattern matched, calling DeepSeek with context")
        response = await self._call_deepseek(message, sender_name, db, tenant_id, conversation_id)
        return response
    
    # ===== Pattern Handlers =====
    
    def _handle_pricing(self, sender_name: str) -> str:
        """Handle pricing inquiry"""
        return """💰 *Plan Essential — NéoBot*

✅ 20 000 FCFA/mois
   • 2 500 messages WhatsApp/mois
   • 1 agent IA actif
   • Sources Texte + PDF
   • Dashboard Analytics 30 jours
   • Support par email

🎁 Essai gratuit 14 jours — aucune carte requise
D'autres formules arrivent bientôt.

Voulez-vous activer? Répondez "ACTIVER"
"""
    
    def _handle_help(self, sender_name: str) -> str:
        """Show help menu"""
        return """📋 *Menu NéoBot*

Tapez un mot-clé:
   📌 *prix* - Voir nos tarifs
   🆘 *aide* - Ce menu
   🎁 *demo* - Voir une démo
   
Ou posez n'importe quelle question!
"""
    
    def _handle_demo(self, sender_name: str) -> str:
        """Send demo response"""
        return f"""🎬 *Démo NéoBot*

Bonjour {sender_name}! 👋

Je suis NéoBot, un assistant WhatsApp alimenté par l'IA.
Je peux:
   ✅ Répondre à vos questions
   ✅ Afficher le menu produits
   ✅ Traiter les commandes
   ✅ Vous aider 24/7

Prêt à commencer? 🚀
"""
    
    def _handle_greeting(self, sender_name: str) -> str:
        """Handle greeting"""
        return f"""Bonjour {sender_name}! 👋

Bienvenue chez NéoBot!

Tapez:
   *prix* - Voir nos tarifs
   *aide* - Voir le menu
   
Ou posez votre question!
"""
    
    # ===== DeepSeek with Intent Filtering + Sales Questions =====
    
    async def _call_deepseek(self, user_message: str, sender_name: str, db: Session = None, tenant_id: int = 1, conversation_id: int = None) -> str:
        """
        Call DeepSeek API with:
        1. Intent Classification (rejette hors-sujet)
        2. RAG Context (vraies données)
        3. Sales Questions (questions pertinentes)
        4. PHASE 7F: Escalade, Mémoire, CRM
        """
        if not self.deepseek_api_key:
            logger.warning("DeepSeek API key not configured")
            return "Je ne peux pas répondre à cette question en ce moment. Essayez: prix, aide, demo"
        
        try:
            # 🚨 PHASE 7F STEP 1: ESCALADE DETECTION
            from .services.escalation_service import EscalationService, EscalationReason
            
            escalation_reason = EscalationService.detect_escalation_trigger(
                user_message, 
                conversation_id, 
                db
            )
            
            if escalation_reason:
                # Créer le ticket d'escalade
                EscalationService.create_escalation_ticket(
                    conversation_id,
                    escalation_reason,
                    db
                )
                
                # Retourner le message d'escalade
                response = EscalationService.generate_escalation_response(escalation_reason)
                logger.info(f"🚨 ESCALADE: {escalation_reason} - Conversation {conversation_id}")
                return response
            
            # 🧠 PHASE 7F STEP 2: MÉMOIRE - Récupérer historique
            from .services.conversation_memory_service import ConversationMemoryService
            from .services.crm_service import CRMService
            from .models import Conversation
            
            # Get conversation for phone number
            conversation = db.query(Conversation).filter_by(id=conversation_id).first() if conversation_id else None
            phone_number = conversation.customer_phone if conversation else "unknown"
            
            history = ConversationMemoryService.get_conversation_history(
                phone_number, 
                tenant_id, 
                db, 
                limit=5
            )
            history_text = ConversationMemoryService.format_history_for_prompt(history)
            
            # 👤 PHASE 7F STEP 3: CRM - Récupérer profil client
            customer_info = ConversationMemoryService.extract_customer_info(history)
            
            # Update conversation with name if extracted
            if customer_info["name"] and conversation:
                CRMService.update_conversation_metadata(
                    conversation.id, 
                    db, 
                    customer_name=customer_info["name"]
                )
            
            customer_context = CRMService.get_customer_summary(conversation_id if conversation_id else 1, db)
            
            # ✅ STEP 1: INTENT CLASSIFICATION
            from .services.intent_classifier import classify_intent
            from .services.ai_service_rag import generate_ai_response_with_db
            from .services.knowledge_base_service import KnowledgeBaseService
            from .models import Tenant
            
            logger.info(f"🔍 Classifying intent for message: '{user_message[:80]}'")
            
            # Récupérer le vrai business type du tenant
            tenant = db.query(Tenant).filter_by(id=tenant_id).first()
            business_type = tenant.business_type if tenant else "neobot"
            
            # Classifier le message avec le vrai business type
            classification = classify_intent(user_message, business_type=business_type)
            is_relevant = classification.get("is_relevant", True)
            intent = classification.get("intent", "general_inquiry")
            category = classification.get("category", "unknown")
            redirect_msg = classification.get("redirect_message")
            
            # Si HORS-SUJET = rejeter et rediriger
            if not is_relevant:
                logger.warning(f"⚠️ OUT-OF-SCOPE detected: {category}")
                return redirect_msg or "Comment puis-je vous aider avec NéoBot?"
            
            logger.info(f"✅ PERTINENT - Intent: {intent}, Category: {category}")
            
            # ✅ STEP 2: RÉCUPÉRER LES DONNÉES MÉTIER POUR LES QUESTIONS
            profile = KnowledgeBaseService.get_tenant_profile(db, tenant_id)
            if not profile:
                profile = KnowledgeBaseService.create_default_neobot_profile(db, tenant_id)
            
            business_data = {
                "company_name": profile.get('company_name', 'NéoBot'),
                "tone": profile.get('tone', 'Professional'),
                "products_services": profile.get('products_services', [])
            }
            
            # ✅ STEP 3: OBTENIR CONVERSATION HISTORY
            conversation_history = None
            if db and conversation_id:
                try:
                    messages = db.query(Message).filter(
                        Message.conversation_id == conversation_id
                    ).order_by(Message.id.desc()).limit(5).all()
                    
                    conversation_history = []
                    for msg in reversed(messages):
                        conversation_history.append({
                            "role": "user" if msg.direction == "incoming" else "assistant",
                            "content": msg.content
                        })
                except Exception as e:
                    logger.warning(f"Could not get conversation history: {e}")
            
            # ✅ STEP 4: CONSTRUIRE LE PROMPT — agent actif ou fallback SalesPromptGenerator
            from .services.agent_service import AgentService, build_agent_system_prompt
            from .services.sales_prompt_generator import SalesPromptGenerator
            from .services.http_client import DeepSeekClient

            active_agent = AgentService.get_active_agent(tenant_id, db)

            if active_agent:
                # Mode AGENT : utiliser le prompt système de l'agent configuré
                system_prompt = build_agent_system_prompt(active_agent, db)
                max_tokens = active_agent.max_response_length or 500

                # CRM uniquement — history_text est déjà dans conversation_history[:-1]
                # l'injecter ici aussi causerait une duplication → bot qui répète
                enriched_context = CRMService.get_customer_history_context(conversation_id if conversation_id else 1, db)

                messages = []
                messages.append({"role": "system", "content": system_prompt})
                if conversation_history:
                    messages.extend(conversation_history[:-1])  # historique sauf dernier
                if enriched_context.strip():
                    messages.append({"role": "user", "content": f"[Contexte client]\n{enriched_context.strip()}\n\n[Message]\n{user_message}"})
                else:
                    messages.append({"role": "user", "content": user_message})

                logger.info(f"🤖 Using agent '{active_agent.name}' (type={active_agent.agent_type}, score={active_agent.prompt_score})")

            else:
                # Mode FALLBACK : SalesPromptGenerator (comportement original)
                # Même raison : conversation_history est déjà passé à generate(), history_text serait dupliqué
                enriched_context = CRMService.get_customer_history_context(conversation_id if conversation_id else 1, db)

                sales_prompt = SalesPromptGenerator.generate(
                    message=user_message,
                    intent=intent,
                    category=category,
                    business_data=business_data,
                    conversation_history=conversation_history,
                    extra_context=enriched_context,
                )
                messages = [{"role": "user", "content": sales_prompt}]
                max_tokens = 500
                logger.info(f"📝 No active agent — fallback SalesPromptGenerator (intent={intent})")

            # ✅ STEP 5: APPELER DEEPSEEK
            http_client = DeepSeekClient(api_key=self.deepseek_api_key)
            response = await http_client.call(
                messages=messages,
                temperature=0.7,
                max_tokens=max_tokens,
            )

            logger.info(f"✅ DeepSeek response: {response[:100]}...")
            return response
        
        except Exception as e:
            import traceback
            logger.error(f"Error in advanced response: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return "Je rencontre une petite difficulté. Réessayez ou tapez: prix, aide, demo"


# Create global brain instance
brain = BrainOrchestrator()


# ===== Webhook Endpoint =====

@router.post("/api/v1/webhooks/whatsapp")
@router.post("/webhooks/whatsapp", include_in_schema=False)
async def whatsapp_webhook(request: Request, message: WhatsAppMessage, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Receive messages from WhatsApp service
    Process with business context and send response asynchronously
    """
    try:
        if not _is_valid_webhook_signature(request, message):
            logger.warning("Invalid webhook signature", extra={"path": str(request.url.path)})
            sentry_sdk.capture_message(
                "Webhook signature invalide détectée — possible attaque",
                level="warning",
                extras={"path": str(request.url.path), "ip": request.client.host if request.client else "unknown"},
            )
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

        logger.info(f"📨 Received message from {message.senderName}: {message.text}")
        
        # Extract phone number (remove country code if needed)
        phone = message.from_ or ""
        if phone.startswith('+'):
            phone = phone[1:]
        
        # Resolve tenant context: tenant_id from service is authoritative.
        from .services.whatsapp_mapping_service import WhatsAppMappingService
        from .services.usage_tracking_service import UsageTrackingService
        tenant_id = message.tenant_id

        if not tenant_id and message.to:
            tenant_id = WhatsAppMappingService.get_tenant_from_phone(message.to, db)

        if not tenant_id:
            tenant_id = WhatsAppMappingService.get_tenant_from_phone(phone, db)
        
        if not tenant_id:
            logger.warning(f"⚠️  Phone {phone} not mapped to any tenant. Message ignored.")
            return {"status": "error", "message": "Phone not registered"}
        
        logger.info(f"✅ Phone {phone} mapped to tenant {tenant_id}")
        
        # CHECK QUOTA before processing message
        if UsageTrackingService.check_quota_exceeded(tenant_id, db):
            logger.warning(f"⚠️  Tenant {tenant_id} has exceeded quota. Message rejected.")
            return {
                "status": "error",
                "message": "Quota dépassé. Veuillez renouveler votre plan."
            }
        
        # Check per-customer guardrails (daily/monthly)
        if is_daily_limit_reached(phone, tenant_id=tenant_id, db=db):
            logger.warning(f"⚠️  Daily customer limit reached for {phone} (tenant {tenant_id})")
            return {
                "status": "error",
                "message": "Limite journaliere atteinte pour ce client.",
            }

        if is_monthly_limit_reached(phone, tenant_id=tenant_id, db=db):
            logger.warning(f"⚠️  Monthly customer limit reached for {phone} (tenant {tenant_id})")
            return {
                "status": "error",
                "message": "Limite mensuelle atteinte pour ce client.",
            }

        # Save incoming message (create conversation if needed)
        conversation, incoming_msg = await save_message_to_db(
            phone=phone,
            sender_name=message.senderName,
            text=message.text,
            direction="incoming",
            tenant_id=tenant_id,
            db=db,
            is_ai=False,
        )
        logger.info(f"✅ Saved incoming message {incoming_msg.id}")

        # Check contact blacklist — AI disabled for this contact?
        if not ContactFilterService.is_ai_enabled_for_contact(tenant_id, phone, db):
            logger.info(f"🚫 IA désactivée pour {phone} (tenant {tenant_id}) — réponse ignorée")
            return {"status": "skipped", "reason": "ai_disabled_for_contact"}

        # Check human takeover — pause manuelle (indéfinie) ou temporaire (30 min) ?
        human_state = db.query(ConversationHumanState).filter(
            ConversationHumanState.conversation_id == conversation.id
        ).first()
        if human_state and human_state.human_active:
            if human_state.last_human_message_at is None:
                # Pause manuelle indéfinie (toggle) — respecter sans limite de temps
                logger.info(f"🔇 Bot en pause manuelle conv {conversation.id} — opérateur doit reprendre manuellement")
                return {"status": "skipped", "reason": "human_takeover"}
            pause_window = timedelta(minutes=30)
            if (datetime.utcnow() - human_state.last_human_message_at) < pause_window:
                logger.info(f"🔇 Bot en pause temporaire conv {conversation.id} — opérateur actif depuis {human_state.last_human_message_at}")
                return {"status": "skipped", "reason": "human_takeover"}
            else:
                # Pause temporaire expirée — réactiver le bot automatiquement
                human_state.human_active = False
                db.commit()
                logger.info(f"🔄 Pause temporaire expirée conv {conversation.id} — bot réactivé")

        # Fetch agent settings (delay + typing) before generating response
        active_agent = AgentService.get_active_agent(tenant_id, db)
        response_delay = active_agent.response_delay if active_agent else "natural"
        typing_indicator = active_agent.typing_indicator if active_agent else True
        
        # Process message with brain (now with business context)
        response_text = await brain.process(
            message.text,
            message.senderName,
            db=db,
            tenant_id=tenant_id,
            conversation_id=conversation.id
        )
        
        # Save outgoing message to database
        _, outgoing_msg = await save_message_to_db(
            phone=phone,
            sender_name=message.senderName,
            text=response_text,
            direction="outgoing",
            tenant_id=tenant_id,
            db=db,
            is_ai=True,
        )
        logger.info(f"✅ Saved outgoing message {outgoing_msg.id}")
        
        # DETECT OUTCOME: analyser la réponse IA pour détecter un résultat métier
        if active_agent:
            from .services.outcome_detector import update_conversation_outcome
            update_conversation_outcome(
                conversation_id=conversation.id,
                agent_type=str(active_agent.agent_type),
                ai_response=response_text,
                db=db,
            )

        # INCREMENT USAGE: 1 for incoming message + 1 for outgoing message = 2 total
        UsageTrackingService.increment_whatsapp_usage(tenant_id, 2, db)
        
        # UPDATE OVERAGE COST: Recalculate based on new usage
        from .services.overage_pricing_service import OveragePricingService
        OveragePricingService.update_overage_cost(tenant_id, db)
        
        # Détecter les produits avec images mentionnés dans la réponse IA
        products_with_images = []
        try:
            biz_config = db.query(TenantBusinessConfig).filter(
                TenantBusinessConfig.tenant_id == tenant_id
            ).first()
            if biz_config and biz_config.products_services:
                prods = biz_config.products_services if isinstance(biz_config.products_services, list) else []
                for p in prods:
                    if isinstance(p, dict) and p.get('image_url') and p.get('name'):
                        if p['name'].lower() in response_text.lower():
                            products_with_images.append(p)
        except Exception as img_err:
            logger.debug(f"Product image detection failed (non-blocking): {img_err}")

        # Send response in background — utiliser reply_jid si dispo (JID exact de l'expéditeur)
        background_tasks.add_task(
            send_whatsapp_response,
            tenant_id=tenant_id,
            phone=message.reply_jid or phone,
            text=response_text,
            response_delay=response_delay,
            typing_indicator=typing_indicator,
            products_with_images=products_with_images,
        )
        
        return {
            "status": "received",
            "phone": phone,
            "sender": message.senderName,
            "conversation_id": conversation.id,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ===== Background Task =====

# Mapping délai de réponse → plage (min, max) en secondes.
# Délai variable = pattern humain. Délai fixe = pattern bot détectable par WA.
_DELAY_MAP = {
    "immediate": (0, 0),
    "instant":   (0, 0),
    "natural":   (2, 5),
    "human":     (4, 9),
    "slow":      (9, 16),
}


def _compute_delay(response_delay: Optional[str], response_text: str) -> float:
    """
    Calcule un délai de réponse humain :
    - Plage de base selon le mode configuré (natural/human/slow)
    - Jitter proportionnel à la longueur du texte (lire + taper prend plus de temps)
    - Variation aléatoire pour éviter tout pattern détectable
    """
    mode = response_delay or "natural"
    min_s, max_s = _DELAY_MAP.get(mode, (2, 5))
    if min_s == 0 and max_s == 0:
        return 0.0
    # +0.5s par tranche de 100 caractères, plafonné à +4s
    length_bonus = min(len(response_text) / 100 * 0.5, 4.0)
    base = random.uniform(min_s, max_s)
    return round(base + length_bonus, 2)


async def send_whatsapp_response(
    tenant_id: int,
    phone: str,
    text: str,
    response_delay: Optional[str] = "natural",
    typing_indicator: bool = True,
    products_with_images: Optional[list] = None,
):
    """
    Send response via WhatsApp service.
    Simulates typing delay before sending if configured.
    Delay is randomized (human jitter) to avoid bot detection by WhatsApp.
    Runs in background (non-blocking).
    """
    try:
        whatsapp_service_url = os.getenv('WHATSAPP_SERVICE_URL', 'http://localhost:3001')
        delay_secs = _compute_delay(response_delay, text)
        # Réutiliser le client HTTP global poolé — pas de nouvelle connexion TCP à chaque message
        client = get_http_client()

        # Envoyer l'indicateur de frappe puis attendre le délai configuré
        if typing_indicator and delay_secs > 0:
            try:
                await client.post(
                    f"{whatsapp_service_url}/api/whatsapp/tenants/{tenant_id}/typing",
                    json={"to": phone},
                    timeout=5,
                )
            except Exception as typing_err:
                # Non bloquant — le message s'envoie quand même
                logger.debug(f"Typing indicator failed (non-blocking): {typing_err}")
            await asyncio.sleep(delay_secs)

        response = await client.post(
            f"{whatsapp_service_url}/api/whatsapp/tenants/{tenant_id}/send-message",
            json={"to": phone, "message": text},
            timeout=25,  # 10s était trop court sur connexion lente / free tier
        )

        # Backward compatibility with older service contracts.
        if response.status_code == 404:
            response = await client.post(
                f"{whatsapp_service_url}/send",
                json={"to": phone, "text": text},
                timeout=25,
            )

        # 503 = WA non connecté (reconnexion en cours) → retry unique après 5s.
        # Couvre le cas où le socket Baileys se reconnecte après un 515 et que
        # le message arrive dans la fenêtre de 3-5s de transition.
        if response.status_code == 503:
            logger.warning(f"WA 503 for tenant {tenant_id} (not connected) — waiting 5s and retrying")
            await asyncio.sleep(5)
            response = await client.post(
                f"{whatsapp_service_url}/api/whatsapp/tenants/{tenant_id}/send-message",
                json={"to": phone, "message": text},
                timeout=25,
            )

        if response.status_code == 200:
            logger.info(f"✅ Message sent to {phone} (delay={delay_secs}s, typing={typing_indicator})")
        else:
            logger.error(f"Failed to send message: {response.status_code} — {response.text}")

        # Envoyer les images produits détectées (non-bloquant — best effort)
        if products_with_images:
            for product in products_with_images:
                try:
                    img_response = await client.post(
                        f"{whatsapp_service_url}/api/whatsapp/tenants/{tenant_id}/send-image",
                        json={
                            "to": phone,
                            "imageBase64": product["image_url"],
                            "caption": product.get("name", ""),
                            "mimetype": "image/jpeg",
                        },
                        timeout=20,
                    )
                    if img_response.status_code == 200:
                        logger.info(f"✅ Product image sent for '{product.get('name')}' to {phone}")
                    else:
                        logger.warning(f"Product image send failed ({img_response.status_code}) for '{product.get('name')}'")
                except Exception as img_err:
                    logger.warning(f"Product image send error for '{product.get('name')}': {img_err}")

    except Exception as e:
        logger.error(f"Error sending WhatsApp response: {str(e)}")


# ===== Utils =====

# In-process lock par (tenant_id, phone) — sérialise la création de conversation
# entre deux requêtes simultanées du même expéditeur (ex: retry webhook + original).
# Single-process sur Render free tier → asyncio.Lock est suffisant.
# La dict grossit au rythme des numéros uniques, négligeable en mémoire à l'échelle MVP.
_conversation_locks: dict[tuple[int, str], asyncio.Lock] = {}


def _get_conversation_lock(tenant_id: int, phone: str) -> asyncio.Lock:
    key = (tenant_id, phone)
    if key not in _conversation_locks:
        _conversation_locks[key] = asyncio.Lock()
    return _conversation_locks[key]


async def save_message_to_db(
    phone: str,
    sender_name: str,
    text: str,
    direction: str,
    tenant_id: int,
    db: Session,
    is_ai: bool = False,
):
    """
    Save message for a tenant/customer pair and create conversation when missing.
    """
    # Verrouillage par (tenant_id, phone) : évite la race condition SELECT→INSERT
    # qui créerait deux conversations dupliquées si deux messages arrivent en parallèle.
    async with _get_conversation_lock(tenant_id, phone):
        conversation = db.query(Conversation).filter(
            Conversation.tenant_id == tenant_id,
            Conversation.customer_phone == phone,
        ).order_by(Conversation.id.desc()).first()

        if not conversation:
            conversation = Conversation(
                tenant_id=tenant_id,
                customer_phone=phone,
                customer_name=sender_name,
                channel="whatsapp",
                status="active",
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            logger.info(f"✅ Created new conversation {conversation.id} for {phone}")

    # Keep customer name fresh if we receive a better value later.
    if sender_name and conversation.customer_name != sender_name:
        conversation.customer_name = sender_name

    message = Message(
        conversation_id=conversation.id,
        content=text,
        direction=direction,
        is_ai=is_ai,
    )
    db.add(message)
    conversation.last_message_at = datetime.utcnow()
    db.commit()
    db.refresh(message)

    return conversation, message


def is_daily_limit_reached(phone: str, tenant_id: int, db: Session) -> bool:
    """
    Check per-customer daily incoming message limit.

    Env override:
    - WHATSAPP_CUSTOMER_DAILY_LIMIT (default: 200)
    """
    daily_limit = int(os.getenv("WHATSAPP_CUSTOMER_DAILY_LIMIT", "200"))
    if daily_limit <= 0:
        return False

    start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    count = db.query(func.count(Message.id)).join(
        Conversation, Message.conversation_id == Conversation.id
    ).filter(
        Conversation.tenant_id == tenant_id,
        Conversation.customer_phone == phone,
        Message.direction == "incoming",
        Message.created_at >= start_of_day,
    ).scalar() or 0

    return count >= daily_limit


def is_monthly_limit_reached(phone: str, tenant_id: int, db: Session) -> bool:
    """
    Check per-customer monthly incoming message limit.

    Env override:
    - WHATSAPP_CUSTOMER_MONTHLY_LIMIT (default: 2000)
    """
    monthly_limit = int(os.getenv("WHATSAPP_CUSTOMER_MONTHLY_LIMIT", "2000"))
    if monthly_limit <= 0:
        return False

    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    count = db.query(func.count(Message.id)).join(
        Conversation, Message.conversation_id == Conversation.id
    ).filter(
        Conversation.tenant_id == tenant_id,
        Conversation.customer_phone == phone,
        Message.direction == "incoming",
        Message.created_at >= start_of_month,
    ).scalar() or 0

    return count >= monthly_limit
