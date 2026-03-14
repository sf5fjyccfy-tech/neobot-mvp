"""
MODÈLES NÉOBOT OPTIMISÉS - Version robuste sans dépendances circulaires
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum
from .database import Base

# ========== ENUMS ==========
class PlanType(str, enum.Enum):
    NEOBOT = "NEOBOT"  # Valeur par défaut pour l'admin
    BASIQUE = "basique"
    STANDARD = "standard"
    PRO = "pro"

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
        "name": "NéoBot",
        "price_fcfa": 0,
        "whatsapp_messages": -1,  # illimité
        "other_platforms_messages": -1,
        "channels": -1,
        "features": ["Tout accès", "Support prioritaire"],
        "trial_days": 0
    },
    PlanType.BASIQUE: {
        "name": "Basique",
        "price_fcfa": 20000,
        "whatsapp_messages": 2000,
        "other_platforms_messages": 4000,
        "channels": 1,
        "features": ["1 canal", "Réponses automatiques", "Dashboard basique"],
        "trial_days": 14
    },
    PlanType.STANDARD: {
        "name": "Standard",
        "price_fcfa": 50000,
        "whatsapp_messages": 2500,
        "other_platforms_messages": -1,  # illimité
        "channels": 3,
        "features": ["3 canaux", "IA avancée", "NÉOBRAIN", "Analytics"],
        "trial_days": 7
    },
    PlanType.PRO: {
        "name": "Pro",
        "price_fcfa": 90000,
        "whatsapp_messages": 4000,
        "other_platforms_messages": -1,  # illimité
        "channels": -1,  # tous
        "features": ["Canaux illimités", "CLOSEUR PRO", "API", "Support dédié"],
        "trial_days": 0
    }
}

# ========== MODÈLES PRINCIPAUX ==========
class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    business_type = Column(String(100), default="autre")
    plan = Column(SQLEnum(PlanType), default=PlanType.BASIQUE, nullable=False)
    
    whatsapp_provider = Column(String(50), default="wasender_api")
    whatsapp_connected = Column(Boolean, default=False)
    
    messages_used = Column(Integer, default=0)
    messages_limit = Column(Integer, default=2000)
    
    is_trial = Column(Boolean, default=True)
    trial_ends_at = Column(DateTime, nullable=True)

    def get_plan_config(self):
        """Obtenir la configuration du plan"""
        return PLAN_LIMITS.get(self.plan, PLAN_LIMITS[PlanType.NEOBOT])

    
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
