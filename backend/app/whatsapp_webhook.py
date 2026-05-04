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
    """Vérifie la signature HMAC si configurée — jamais bloquant.
    Le webhook est interne (VPS → Render), la signature est optionnelle.
    """
    if not WEBHOOK_SECRET:
        return True

    signature = request.headers.get("x-webhook-signature")
    if not signature:
        logger.debug("Webhook sans signature — accepté (WHATSAPP_WEBHOOK_SECRET configuré mais VPS n'envoie pas de signature)")
        return True

    expected = _compute_webhook_signature(message, WEBHOOK_SECRET)
    if not hmac.compare_digest(signature, expected):
        logger.warning("Signature webhook incorrecte — accepté quand même (API interne)")
    return True

# ===== Models =====

class WhatsAppMessage(BaseModel):
    """Incoming message from WhatsApp service"""
    tenant_id: Optional[int] = None
    from_: Optional[str] = None  # Phone number
    reply_jid: Optional[str] = None  # JID exact de l'expéditeur
    to: Optional[str] = None     # Bot number (optional)
    text: str
    senderName: str
    messageKey: dict
    timestamp: int
    isMedia: bool = False
    fromMe: bool = False  # True = message envoyé par le propriétaire depuis son téléphone

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
            
            # ✅ STEP 3: OBTENIR CONVERSATION HISTORY (3 échanges max, 400 chars/msg)
            conversation_history = None
            if db and conversation_id:
                try:
                    # 20 messages = 10 échanges → contexte suffisant pour éviter les répétitions
                    raw_messages = db.query(Message).filter(
                        Message.conversation_id == conversation_id
                    ).order_by(Message.id.desc()).limit(20).all()

                    conversation_history = []
                    for msg in reversed(raw_messages):
                        conversation_history.append({
                            "role": "user" if msg.direction == "incoming" else "assistant",
                            "content": (msg.content or "")[:500]
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
                max_tokens = min(active_agent.max_response_length or 300, 350)

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
                max_tokens = 200
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


# ── Bot payment detection helpers ─────────────────────────────────────────────

import re as _re_pay
_EMAIL_RE = _re_pay.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b')
_PAYMENT_KW = [
    "j'ai payé", "j'ai envoyé", "j'ai transféré", "j'ai effectué",
    "paiement fait", "c'est fait", "c'est envoyé", "i paid", "payment done",
    "payé", "transféré", "virement fait", "envoi effectué", "transaction faite",
    "j ai payé", "j ai envoyé", "j ai transféré", "jai payé", "jai envoyé",
]

_NEOBOT_ADMIN_PHONE = "237694256267"  # Numéro personnel Tim — notif paiement

def _extract_email(text: str):
    m = _EMAIL_RE.search(text)
    return m.group(0).lower() if m else None

def _message_has_payment_keyword(text: str) -> bool:
    low = text.lower()
    return any(kw in low for kw in _PAYMENT_KW)

def _has_payment_context(conversation_id: int, db) -> bool:
    try:
        msgs = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.direction == "incoming",
        ).order_by(Message.id.desc()).limit(12).all()
        for msg in msgs:
            low = msg.content.lower()
            if any(kw in low for kw in _PAYMENT_KW):
                return True
        return False
    except Exception:
        return False

async def _notify_admin_payment_whatsapp(
    customer_name: str,
    customer_phone: str,
    message_text: str,
    admin_phone: str = None,
) -> None:
    """Envoie une notification WhatsApp à l'admin propriétaire quand un client dit 'payé'.
    Toujours envoyé via la session NéoBot (tenant 1) pour éviter les boucles.
    admin_phone : numéro perso du propriétaire du tenant (différent du bot).
    """
    target_phone = admin_phone or _NEOBOT_ADMIN_PHONE
    try:
        whatsapp_service_url = os.getenv('WHATSAPP_SERVICE_URL', 'http://localhost:3001')
        now = datetime.utcnow().strftime('%d/%m/%Y à %Hh%M')
        notif = (
            f"💰 PAIEMENT SIGNALÉ\n\n"
            f"👤 {customer_name}\n"
            f"📞 +{customer_phone}\n"
            f"💬 \"{message_text[:120]}\"\n"
            f"🕐 {now} UTC\n\n"
            f"→ Vérifier le paiement et livrer le produit/service"
        )
        client = get_http_client()
        await client.post(
            f"{whatsapp_service_url}/api/whatsapp/tenants/1/send-message",
            json={"to": target_phone, "message": notif},
            timeout=10,
        )
        logger.info(f"✅ Notif paiement envoyée à {target_phone} pour client {customer_phone}")
    except Exception as e:
        logger.warning(f"Notif paiement WhatsApp échouée (non-bloquant): {e}")


async def _notify_hot_lead_whatsapp(
    owner_phone: str,
    customer_name: str,
    customer_phone: str,
    outcome: str,
) -> None:
    """Notifie le propriétaire d'un tenant quand l'IA détecte un lead chaud."""
    _outcome_labels = {
        "vente": "💳 Vente probable",
        "vente_conclue": "✅ Vente conclue",
        "rdv_pris": "📅 RDV confirmé",
        "lead_qualifié": "🔥 Lead qualifié",
    }
    label = _outcome_labels.get(outcome, f"🔔 {outcome}")
    try:
        whatsapp_service_url = os.getenv('WHATSAPP_SERVICE_URL', 'http://localhost:3001')
        now = datetime.utcnow().strftime('%d/%m/%Y à %Hh%M')
        msg = (
            f"{label} !\n\n"
            f"👤 {customer_name}\n"
            f"📞 +{customer_phone}\n"
            f"🕐 {now} UTC\n\n"
            f"→ Ouvrez la conversation dans votre dashboard NéoBot"
        )
        client = get_http_client()
        await client.post(
            f"{whatsapp_service_url}/api/whatsapp/tenants/1/send-message",
            json={"to": owner_phone, "message": msg},
            timeout=10,
        )
        logger.info(f"✅ Notif lead chaud ({outcome}) envoyée à {owner_phone}")
    except Exception as e:
        logger.warning(f"Notif lead chaud WhatsApp échouée (non-bloquant): {e}")


async def _record_bot_payment(conversation_id: int, customer_name: str,
                               customer_phone: str, customer_email: str, db) -> None:
    try:
        from .models import PaymentEvent
        from .services.email_service import send_internal_alert
        import secrets as _secrets
        from datetime import timedelta as _td

        # Idempotence — ne pas créer deux fois pour le même numéro
        existing = db.query(PaymentEvent).filter(
            PaymentEvent.customer_phone == customer_phone,
            PaymentEvent.status == "bot_pending",
        ).first()
        if existing:
            logger.info(f"PaymentEvent bot déjà enregistré pour {customer_phone} (ref={existing.neo_ref})")
            return

        txid = f"bot_{customer_phone}_{int(datetime.utcnow().timestamp())}"

        # Référence NEO-YYYY-NNNN séquentielle
        from .routers.neopay import _generate_neo_ref, _build_confirm_email
        neo_ref = _generate_neo_ref(db)
        confirm_token = _secrets.token_urlsafe(32)
        confirm_expires = datetime.utcnow() + _td(days=7)

        event = PaymentEvent(
            transaction_id=txid,
            provider="bot_whatsapp",
            payment_link_id=None,
            tenant_id=1,
            plan="BASIC",
            amount=20000,
            currency="XAF",
            payment_method="mobile_money",
            status="bot_pending",
            customer_email=customer_email,
            customer_phone=customer_phone,
            payment_metadata={"customer_name": customer_name, "conversation_id": conversation_id},
            neo_ref=neo_ref,
            confirm_token=confirm_token,
            confirm_token_expires_at=confirm_expires,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(event)
        db.commit()

        confirm_url = f"https://neobot-ai.com/api/neopay/confirm-payment?token={confirm_token}"
        body = _build_confirm_email(
            neo_ref=neo_ref,
            customer_name=customer_name,
            customer_email=customer_email,
            plan_label="Essential",
            amount=20000,
            payment_method="mobile_money",
            customer_phone=customer_phone,
            confirm_url=confirm_url,
        )
        await send_internal_alert(
            subject=f"💰 Paiement bot — {neo_ref} — {customer_name} ({customer_phone})",
            body=body,
        )
        logger.info(f"✅ PaymentEvent bot créé {neo_ref} pour {customer_email} ({customer_phone})")
    except Exception as _e:
        logger.error(f"_record_bot_payment failed: {_e}", exc_info=True)


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

        # ── Message du propriétaire (fromMe=true) ────────────────────────────
        # Le propriétaire a écrit manuellement depuis son téléphone WhatsApp.
        # Sauvegarder le message, activer human_takeover, NE PAS répondre avec l'IA.
        if message.fromMe:
            logger.info(f"👤 Message fromMe pour conv {phone} (tenant {tenant_id}) — human_takeover activé")
            try:
                conversation, _ = await save_message_to_db(
                    phone=phone,
                    sender_name="Propriétaire",
                    text=message.text,
                    direction="outgoing",
                    tenant_id=tenant_id,
                    db=db,
                    is_ai=False,
                )
                # Activer human_takeover sur cette conversation
                human_state = db.query(ConversationHumanState).filter(
                    ConversationHumanState.conversation_id == conversation.id
                ).first()
                if not human_state:
                    human_state = ConversationHumanState(
                        conversation_id=conversation.id,
                        human_active=True,
                        last_human_message_at=datetime.utcnow(),
                    )
                    db.add(human_state)
                else:
                    human_state.human_active = True
                    human_state.last_human_message_at = datetime.utcnow()
                db.commit()
            except Exception as e:
                logger.error(f"Erreur sauvegarde message fromMe: {e}")
            return {"status": "ok", "reason": "owner_message_saved"}

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

        # Fetch agent settings — lecture DB fraîche pour respecter les toggles en temps réel
        active_agent = AgentService.get_active_agent(tenant_id, db)

        # Vérification is_active : si l'agent est désactivé (ou inexistant), ne pas répondre
        if not active_agent or not active_agent.is_active:
            logger.info(f"🔇 Agent désactivé ou absent pour tenant {tenant_id} — réponse IA ignorée")
            return {"status": "skipped", "reason": "agent_disabled"}

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
        
        # ── Détection paiement — tous les tenants ──────────────────────────
        if _message_has_payment_keyword(message.text):
            from .models import Tenant as _Tenant
            _tenant_obj = db.query(_Tenant).filter(_Tenant.id == tenant_id).first()
            # Numéro perso du propriétaire (≠ numéro bot) pour recevoir la notif
            _admin_phone = (_tenant_obj.phone if _tenant_obj else None) or _NEOBOT_ADMIN_PHONE
            await _notify_admin_payment_whatsapp(
                customer_name=message.senderName,
                customer_phone=phone,
                message_text=message.text,
                admin_phone=_admin_phone,
            )
            if tenant_id == 1:
                # Logique PaymentEvent spécifique NéoBot — paiement d'un futur abonné
                _email = _extract_email(message.text)
                if not _email:
                    _email = _extract_email(" ".join(
                        m.content for m in db.query(Message).filter(
                            Message.conversation_id == conversation.id,
                            Message.direction == "incoming",
                        ).order_by(Message.id.desc()).limit(12).all()
                    ))
                if _email:
                    await _record_bot_payment(
                        conversation_id=conversation.id,
                        customer_name=message.senderName,
                        customer_phone=phone,
                        customer_email=_email,
                        db=db,
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
            from .models import Tenant as _TenantOutcome

            _prev_outcome = conversation.outcome_type
            update_conversation_outcome(
                conversation_id=conversation.id,
                agent_type=str(active_agent.agent_type),
                ai_response=response_text,
                db=db,
            )
            db.refresh(conversation)
            _new_outcome = conversation.outcome_type

            # Notifier le propriétaire si un lead chaud vient d'être détecté
            _HOT_OUTCOMES = {"vente", "vente_conclue", "rdv_pris", "lead_qualifié"}
            if _new_outcome in _HOT_OUTCOMES and _prev_outcome not in _HOT_OUTCOMES:
                _t = db.query(_TenantOutcome).filter(_TenantOutcome.id == tenant_id).first()
                _owner_phone = _t.phone if _t else None
                if _owner_phone:
                    background_tasks.add_task(
                        _notify_hot_lead_whatsapp,
                        owner_phone=_owner_phone,
                        customer_name=message.senderName,
                        customer_phone=phone,
                        outcome=_new_outcome,
                    )

        # INCREMENT USAGE: 1 for incoming message + 1 for outgoing message = 2 total
        UsageTrackingService.increment_whatsapp_usage(tenant_id, 2, db)
        
        # UPDATE OVERAGE COST: Recalculate based on new usage
        from .services.overage_pricing_service import OveragePricingService
        OveragePricingService.update_overage_cost(tenant_id, db)
        
        # Détecter les produits avec images mentionnés dans la réponse IA
        # Règle : 1 seule photo par produit par conversation (pas de spam)
        products_with_images = []
        try:
            biz_config = db.query(TenantBusinessConfig).filter(
                TenantBusinessConfig.tenant_id == tenant_id
            ).first()
            if biz_config and biz_config.products_services:
                prods = biz_config.products_services if isinstance(biz_config.products_services, list) else []

                # Produits déjà cités dans les messages IA précédents → photo déjà envoyée
                already_sent: set[str] = set()
                prev_ai_msgs = db.query(Message).filter(
                    Message.conversation_id == conversation.id,
                    Message.direction == "outgoing",
                    Message.is_ai == True,
                ).order_by(Message.id.desc()).limit(30).all()
                for prev_msg in prev_ai_msgs:
                    for p in prods:
                        if isinstance(p, dict) and p.get('name'):
                            if p['name'].lower() in (prev_msg.content or '').lower():
                                already_sent.add(p['name'].lower())

                for p in prods:
                    if isinstance(p, dict) and p.get('image_url') and p.get('name'):
                        if p['name'].lower() in response_text.lower():
                            if p['name'].lower() not in already_sent:
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

        # 503 = WA non connecté (reconnexion en cours).
        # La reconnexion Baileys prend ~10s, donc on tente 4 fois avec backoff :
        # 5s → 12s → 20s → 30s (couvre jusqu'à ~67s de fenêtre de reconnexion).
        if response.status_code == 503:
            retry_delays = [5, 12, 20, 30]
            sent = False
            for attempt, wait in enumerate(retry_delays, start=1):
                logger.warning(f"WA 503 tenant {tenant_id} — retry {attempt}/{len(retry_delays)} dans {wait}s")
                await asyncio.sleep(wait)
                retry_response = await client.post(
                    f"{whatsapp_service_url}/api/whatsapp/tenants/{tenant_id}/send-message",
                    json={"to": phone, "message": text},
                    timeout=25,
                )
                if retry_response.status_code == 200:
                    logger.info(f"✅ Message envoyé à {phone} après retry {attempt} (délai cumulé)")
                    sent = True
                    break
                elif retry_response.status_code != 503:
                    logger.error(f"Erreur inattendue retry {attempt}: {retry_response.status_code} — {retry_response.text}")
                    break
            if not sent:
                logger.error(f"Message définitivement perdu après {len(retry_delays)} retries pour tenant {tenant_id} → {phone}")
            return

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

    # Ne mettre à jour le nom du client que pour les messages entrants (incoming)
    # Les messages outgoing (IA ou propriétaire) ne doivent pas écraser le nom du client
    if direction == "incoming" and sender_name and conversation.customer_name != sender_name:
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
