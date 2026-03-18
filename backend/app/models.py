"""
MODÈLES NÉOBOT OPTIMISÉS - Version robuste sans dépendances circulaires
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum
from .database import Base

# ========== ENUMS ==========

class AgentType(str, enum.Enum):
    """Types d'agents disponibles pour chaque tenant"""
    LIBRE         = "libre"           # Template vierge — le client prompt lui-même
    RDV           = "rdv"             # Gestionnaire de rendez-vous
    SUPPORT       = "support"         # Support client polyvalent
    FAQ           = "faq"             # Question/Réponse
    VENTE         = "vente"           # Closeur pro
    QUALIFICATION = "qualification"   # Qualificateur d'offre
    # NOTIFICATION supprimé — fonctions redistribuées sur RDV/VENTE/SUPPORT

class KnowledgeSourceType(str, enum.Enum):
    URL       = "url"
    PDF       = "pdf"
    YOUTUBE   = "youtube"
    FAQ       = "faq"
    TEXT      = "text"

class PlanType(str, enum.Enum):
    NEOBOT    = "NEOBOT"    # Plan admin/plateforme
    BASIC     = "BASIC"     # Renommé Essential en affichage (valeur DB inchangée)
    STANDARD  = "STANDARD"  # Gelé — renommé Business en affichage
    PRO       = "PRO"       # Gelé — renommé Enterprise en affichage

class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    PENDING = "pending"
    CLOSED = "closed"
    ARCHIVED = "archived"

class BusinessType(str, enum.Enum):
    """Types de business supportés par NéoBot"""
    NEOBOT = "neobot"         # NéoBot se vend lui-même
    RESTAURANT = "restaurant"
    ECOMMERCE = "ecommerce"
    TRAVEL = "travel"
    SALON = "salon"
    FITNESS = "fitness"
    CONSULTING = "consulting"
    CUSTOM = "custom"

# ========== PLAN LIMITS ==========
PLAN_LIMITS = {
    PlanType.NEOBOT: {
        "name": "NéoBot Admin",
        "display_name": "NéoBot",
        "available": False,
        "price_fcfa": 0,
        "whatsapp_messages": -1,
        "channels": -1,
        "max_agents": -1,
        "max_knowledge_sources": -1,
        "allowed_source_types": ["text", "pdf", "url", "youtube"],
        "can_generate_prompt_ai": True,
        "response_delay_configurable": True,
        "test_credits_per_session": 20,
        "outbound_triggers": ["rdv_reminder", "order_followup", "subscription_expiry", "promo"],
        "analytics_days": -1,
        "features": ["Tout accès", "Support prioritaire"],
        "trial_days": 0,
    },
    PlanType.BASIC: {
        "name": "Essential",
        "display_name": "Essential",
        "available": True,
        "price_fcfa": 20000,
        "whatsapp_messages": 2000,           # 2 000 messages/mois
        "channels": 1,
        "max_agents": 1,                     # 1 seul agent actif
        "max_knowledge_sources": 3,          # 3 sources max
        "allowed_source_types": ["text", "pdf"],  # Pas d'URL ni YouTube
        "can_generate_prompt_ai": True,
        "response_delay_configurable": True,
        "test_credits_per_session": 20,
        "outbound_triggers": ["rdv_reminder"],   # Rappels RDV seulement
        "analytics_days": 30,
        "features": [
            "1 agent IA actif",
            "2 000 messages/mois",
            "Types d'agents : Libre, RDV, Support, FAQ, Vente, Qualification",
            "Sources : Texte + PDF (3 max)",
            "Génération prompt par IA",
            "Délai de réponse configurable",
            "Rappels RDV automatiques",
            "Dashboard 30 jours",
            "20 messages de test par session",
            "Essai gratuit 14 jours",
        ],
        "trial_days": 14,
    },
    PlanType.STANDARD: {
        "name": "Business",
        "display_name": "Business",
        "available": False,                  # Gelé — bientôt disponible
        "price_fcfa": 50000,
        "whatsapp_messages": 5000,
        "channels": 3,
        "max_agents": 3,
        "max_knowledge_sources": 10,
        "allowed_source_types": ["text", "pdf", "url", "youtube"],
        "can_generate_prompt_ai": True,
        "response_delay_configurable": True,
        "test_credits_per_session": 20,
        "outbound_triggers": ["rdv_reminder", "order_followup", "promo"],
        "analytics_days": 30,
        "features": [
            "3 agents IA actifs",
            "5 000 messages/mois",
            "Tous les types d'agents",
            "Sources : Texte + PDF + URL + YouTube (10 max)",
            "Génération prompt par IA",
            "Rappels RDV + Suivi commande + Promos ciblées",
            "Dashboard 30 jours",
            "Support email prioritaire",
        ],
        "trial_days": 7,
    },
    PlanType.PRO: {
        "name": "Enterprise",
        "display_name": "Enterprise",
        "available": False,                  # Gelé — bientôt disponible
        "price_fcfa": 90000,
        "whatsapp_messages": -1,             # Illimité
        "channels": -1,
        "max_agents": -1,
        "max_knowledge_sources": -1,
        "allowed_source_types": ["text", "pdf", "url", "youtube"],
        "can_generate_prompt_ai": True,
        "response_delay_configurable": True,
        "test_credits_per_session": 20,
        "outbound_triggers": ["rdv_reminder", "order_followup", "subscription_expiry", "promo"],
        "analytics_days": 90,
        "features": [
            "Agents illimités",
            "Messages illimités",
            "Tous les types d'agents",
            "Sources illimitées (Texte + PDF + URL + YouTube)",
            "Expiration abonnement + Tous les sortants",
            "Dashboard 90 jours + Export",
            "Support dédié WhatsApp",
        ],
        "trial_days": 0,
    },
}

# ========== MODÈLES PRINCIPAUX ==========
class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    business_type = Column(String(100), default="autre")
    plan = Column(SQLEnum(PlanType), default=PlanType.BASIC, nullable=False)
    
    whatsapp_provider = Column(String(50), default="WASENDER_API")
    whatsapp_connected = Column(Boolean, default=False)
    
    messages_used = Column(Integer, default=0)
    messages_limit = Column(Integer, default=2000)
    
    is_trial = Column(Boolean, default=True)
    trial_ends_at = Column(DateTime, nullable=True)

    def get_plan_config(self):
        """Obtenir la configuration du plan"""
        return PLAN_LIMITS.get(self.plan, PLAN_LIMITS[PlanType.BASIC])

    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations (utilisant des strings pour éviter les imports circulaires)
    conversations = relationship("Conversation", back_populates="tenant")
    users = relationship("User", back_populates="tenant")

class User(Base):
    """Utilisateurs de la plateforme NéoBot"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="user")  # "user", "admin", "owner"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    tenant = relationship("Tenant", back_populates="users")

# ========== CONTACTS ==========
class Contact(Base):
    """Contacts gérés par chaque tenant (Phone, name, settings)"""
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    name = Column(String(255), nullable=True)
    
    # Whitelist/Blacklist
    is_whitelisted = Column(Boolean, default=False)
    is_blacklisted = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    first_contact_date = Column(DateTime, default=datetime.utcnow)
    last_contact_date = Column(DateTime, default=datetime.utcnow)
    message_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('tenant_id', 'phone', name='uq_contact_phone'),
    )

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    customer_phone = Column(String(50), nullable=False)
    customer_name = Column(String(255), nullable=True)
    channel = Column(String(50), default="whatsapp")
    status = Column(String(50), default="active")  # active, escalated, closed, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations (en utilisant des strings)
    tenant = relationship("Tenant", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    escalations = relationship("Escalation", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    content = Column(Text, nullable=False)
    direction = Column(String(20), nullable=False)
    is_ai = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")

# ========== NOUVEAUX MODÈLES: BUSINESS INTELLIGENCE ==========

class BusinessTypeModel(Base):
    """Types de business supportés (Restaurant, E-commerce, etc)"""
    __tablename__ = "business_types"
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(50), unique=True, nullable=False)  # "restaurant", "ecommerce"
    name = Column(String(100), nullable=False)              # "Restaurant", "E-commerce"
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)               # emoji or icon name
    created_at = Column(DateTime, default=datetime.utcnow)
    
    configs = relationship("TenantBusinessConfig", back_populates="business_type")

class TenantBusinessConfig(Base):
    """Configuration personnalisée par tenant (ses produits, ton, focus)"""
    __tablename__ = "tenant_business_config"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    business_type_id = Column(Integer, ForeignKey("business_types.id"), nullable=False)
    
    # Infos spécifiques au business du client
    company_name = Column(String(255), nullable=True)           # "La Saveur Restaurant"
    company_description = Column(Text, nullable=True)
    
    # Produits/Services en JSON
    products_services = Column(JSON, nullable=True)            # [{"name": "Pizza", "price": 5000}...]
    
    # Configuration IA
    tone = Column(String(50), nullable=True)                   # "Friendly", "Professional"
    selling_focus = Column(String(255), nullable=True)         # "Quality", "Price", "Service"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    business_type = relationship("BusinessTypeModel", back_populates="configs")
    contexts = relationship("ConversationContext", back_populates="config")

class ConversationContext(Base):
    """Contexte amélioré pour chaque conversation"""
    __tablename__ = "conversation_context"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, unique=True)
    config_id = Column(Integer, ForeignKey("tenant_business_config.id"), nullable=True)
    
    # Infos client
    client_name = Column(String(255), nullable=True)           # "Patrick"
    client_previous_interest = Column(JSON, nullable=True)    # {"interested_in": ["Pizza", "Pasta"]}
    conversation_stage = Column(String(50), nullable=True)     # "discovery", "consideration", "closing"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    config = relationship("TenantBusinessConfig", back_populates="contexts")

# ========== WHATSAPP INTEGRATION ==========
class WhatsAppSession(Base):
    """Enregistre les sessions WhatsApp par tenant (pour Baileys multi-device)"""
    __tablename__ = "whatsapp_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    whatsapp_phone = Column(String(50), nullable=False, unique=True, index=True)  # "221780123456"
    
    # Baileys session metadata
    baileys_session_file = Column(Text, nullable=True)  # JSON path or encoded data
    is_connected = Column(Boolean, default=False)
    last_connected_at = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tenant = relationship("Tenant", foreign_keys=[tenant_id])

# ========== USAGE TRACKING ==========
class UsageTracking(Base):
    """Suivi de l'utilisation mensuelle par tenant"""
    __tablename__ = "usage_tracking"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    month_year = Column(String(7), nullable=False, index=True)  # "2026-02"
    
    whatsapp_messages_used = Column(Integer, default=0)
    other_platform_messages_used = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('tenant_id', 'month_year', name='uq_tenant_month'),
    )

# ========== OVERAGE PRICING ==========
class Overage(Base):
    """Suivi des dépassements de quota et coûts supplémentaires"""
    __tablename__ = "overages"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    month_year = Column(String(7), nullable=False, index=True)  # "2026-02"
    
    messages_over = Column(Integer, default=0)  # Nombre de messages au-delà de la limite
    cost_fcfa = Column(Integer, default=0)      # Coût en FCFA
    
    is_billed = Column(Boolean, default=False)  # Facturé ou pas?
    billed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('tenant_id', 'month_year', name='uq_overage_tenant_month'),
    )

# ========== SUBSCRIPTION MANAGEMENT ==========
class Subscription(Base):
    """Tracks subscription plans, trial periods, and billing information"""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    
    # Plan information
    plan = Column(String(50), nullable=False)  # "basique", "standard", "pro"
    status = Column(String(50), default="active")  # "active", "paused", "cancelled"
    
    # Trial information
    is_trial = Column(Boolean, default=True)
    trial_start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    trial_end_date = Column(DateTime, nullable=False)
    
    # Subscription dates
    subscription_start_date = Column(DateTime, default=datetime.utcnow)
    subscription_end_date = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Billing information
    next_billing_date = Column(DateTime, nullable=True)
    last_billing_date = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tenant = relationship("Tenant", foreign_keys=[tenant_id])

# ========== ESCALATION MANAGEMENT ==========
class Escalation(Base):
    """Tickets d'escalade vers support humain"""
    __tablename__ = "escalations"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    reason = Column(String(100), nullable=False)  # frustrated, complex, payment, technical, request_human, max_attempts
    status = Column(String(50), default="pending")  # pending, assigned, resolved, closed
    assigned_agent = Column(String(100), nullable=True)  # Nom de l'agent
    
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    # Relation
    conversation = relationship("Conversation", back_populates="escalations")

# ========== PHASE 8M: BAILEYS + FEATURES ==========

# 1. WhatsApp QR Code Sessions
class WhatsAppSessionQR(Base):
    """Gestion QR codes Baileys avec expiration"""
    __tablename__ = "whatsapp_session_qrs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    phone_number = Column(String(50), nullable=True)  # NULL avant connexion
    
    # QR Code
    qr_code_data = Column(Text, nullable=True)  # Base64 image
    status = Column(String(50), default="pending")  # pending, connected, expired, disconnected
    
    # Dates
    qr_generated_at = Column(DateTime, default=datetime.utcnow)
    qr_expires_at = Column(DateTime, nullable=True)  # 2 min après generation
    connected_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    session_expires_at = Column(DateTime, nullable=True)  # 30 jours après connexion
    
    # Session data
    session_data = Column(Text, nullable=True)  # Données Baileys chiffrées
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 2. Contact Settings - Whitelist/Blacklist
class ContactSetting(Base):
    """Whitelist/Blacklist: contrôle si IA répond à ce contact"""
    __tablename__ = "contact_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    phone_number = Column(String(50), nullable=False)
    
    # Contrôle IA
    ai_enabled = Column(Boolean, default=True)  # True = IA répond, False = ignoré
    
    # Metadata
    contact_name = Column(String(255), nullable=True)
    message_count = Column(Integer, default=0)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('tenant_id', 'phone_number', name='uq_contact_setting'),
    )


# 3. Human Intervention State - Détécte intervention humain
class ConversationHumanState(Base):
    """Suivi l'état: humain intervenu, IA pause, etc."""
    __tablename__ = "conversation_human_states"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, unique=True, index=True)
    
    # État IA
    human_active = Column(Boolean, default=False)  # Humain en train de répondre?
    ai_paused_at = Column(DateTime, nullable=True)  # Quand IA pausée
    last_human_message_at = Column(DateTime, nullable=True)  # Dernier message humain
    
    # Metadata
    detection_confidence = Column(Integer, default=0)  # 0-100%
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 4. Tenant Settings - Configuration délai réponse
class TenantSettings(Base):
    """Configuration tenant: délai réponse, etc."""
    __tablename__ = "tenant_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, unique=True, index=True)
    
    # Délai de réponse
    response_delay_seconds = Column(Integer, default=30)  # 0, 15, 30, 60, 120
    
    # Overrides par contact (JSON)
    contact_delays = Column(JSON, nullable=True)  # {"237666123456": 0, "237777777777": 60}
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 5. Queued Messages - Messages en attente de délai
class QueuedMessage(Base):
    """Messages en queue en attente d'envoi (après délai)"""
    __tablename__ = "queued_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    phone_number = Column(String(50), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Message
    response_text = Column(Text, nullable=False)
    
    # Envoi
    send_at = Column(DateTime, nullable=False, index=True)  # Quand envoyer
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Retry
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ========== SYSTÈME D'AGENTS (NOUVELLE FEATURE) ==========

class AgentTemplate(Base):
    """
    Template d'agent IA configuré par le tenant.
    Chaque tenant peut avoir plusieurs agents (un actif à la fois).
    """
    __tablename__ = "agent_templates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Identité de l'agent
    name = Column(String(255), nullable=False)                          # "Mon Bot Vente"
    agent_type = Column(SQLEnum(AgentType), nullable=False, default=AgentType.LIBRE)
    description = Column(Text, nullable=True)
    
    # Prompt système (couche 2 — modifiable par le tenant)
    system_prompt = Column(Text, nullable=True)                         # Prompt pré-défini du type
    custom_prompt_override = Column(Text, nullable=True)               # Prompt libre saisi par le tenant
    
    # Personnalité
    tone = Column(String(100), default="Friendly, Professional")        # "Friendly", "Expert", etc.
    language = Column(String(10), default="fr")                         # "fr", "en", "ar"
    emoji_enabled = Column(Boolean, default=True)
    max_response_length = Column(Integer, default=400)                  # Tokens max
    
    # Délai de réponse (simule un comportement humain)
    # "immediate" = 0s, "natural" = 2-4s, "human" = 5-12s, "slow" = 15-30s
    response_delay = Column(String(20), default="natural")
    typing_indicator = Column(Boolean, default=True)                   # Afficher "est en train d'écrire..."

    # Disponibilité horaire
    availability_start = Column(String(5), nullable=True)              # "08:00"
    availability_end = Column(String(5), nullable=True)                # "22:00"
    off_hours_message = Column(Text, nullable=True)                    # Message hors horaires
    
    # Score de qualité (calculé automatiquement 0-100)
    prompt_score = Column(Integer, default=0)
    
    # Etat
    is_active = Column(Boolean, default=False)                         # Un seul actif à la fois
    is_default = Column(Boolean, default=False)                        # Template par défaut

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    knowledge_sources = relationship("KnowledgeSource", back_populates="agent", cascade="all, delete-orphan")
    prompt_variables = relationship("PromptVariable", back_populates="agent", cascade="all, delete-orphan")


class KnowledgeSource(Base):
    """
    Sources de connaissance attachées à un agent.
    Le contenu extrait est injecté dans le prompt IA.
    """
    __tablename__ = "knowledge_sources"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agent_templates.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    # Source
    source_type = Column(SQLEnum(KnowledgeSourceType), nullable=False)  # url, pdf, youtube, faq, text
    name = Column(String(255), nullable=True)                           # Nom lisible
    source_url = Column(Text, nullable=True)                            # URL ou lien YouTube
    file_path = Column(Text, nullable=True)                             # Chemin vers le fichier uploadé

    # Contenu extrait (indexé pour injection dans le prompt)
    content_extracted = Column(Text, nullable=True)
    content_preview = Column(Text, nullable=True)                       # 500 premiers chars pour aperçu

    # Sync
    sync_status = Column(String(50), default="pending")                 # pending, synced, error
    sync_error = Column(Text, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("AgentTemplate", back_populates="knowledge_sources")


class PromptVariable(Base):
    """
    Variables substituables dans les prompts : {{nom_entreprise}}, {{lien_catalogue}}, etc.
    Permettent de rendre les prompts dynamiques sans les réécrire.
    """
    __tablename__ = "prompt_variables"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agent_templates.id"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    key = Column(String(100), nullable=False)    # "nom_entreprise"
    value = Column(Text, nullable=True)          # "Le Gourmet Restaurant"
    description = Column(String(255), nullable=True)  # Hint pour l'UI

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agent = relationship("AgentTemplate", back_populates="prompt_variables")

    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('agent_id', 'key', name='uq_agent_variable_key'),
    )


# ========== OUTBOUND TRACKING ==========

class OutboundTracking(Base):
    """
    Suivi des messages sortants par contact.
    Enforcement backend : max 2 messages proactifs par contact, jamais de cold outreach.
    Cold outreach (numéro sans historique) = rejeté avant même d'arriver ici.
    """
    __tablename__ = "outbound_tracking"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    phone_number = Column(String(50), nullable=False, index=True)       # Numéro destinataire

    # Compteur par type de déclencheur
    rdv_outbound_count = Column(Integer, default=0)          # Rappels RDV
    order_outbound_count = Column(Integer, default=0)        # Suivi commande
    subscription_outbound_count = Column(Integer, default=0) # Expiration abonnement
    promo_outbound_count = Column(Integer, default=0)        # Promos ciblées

    # Total global = somme de tous les types
    total_outbound_count = Column(Integer, default=0)        # Max 2 au total

    last_outbound_at = Column(DateTime, nullable=True)
    last_trigger_type = Column(String(50), nullable=True)    # "rdv_reminder", "order_followup", etc.

    # Opt-out : si True, aucun sortant autorisé pour ce contact
    opted_out = Column(Boolean, default=False)
    opted_out_at = Column(DateTime, nullable=True)

    # Fenêtre de reset : les compteurs se remettent à 0 chaque mois
    window_start = Column(DateTime, default=datetime.utcnow)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        __import__('sqlalchemy').UniqueConstraint('tenant_id', 'phone_number', name='uq_outbound_tenant_phone'),
    )
