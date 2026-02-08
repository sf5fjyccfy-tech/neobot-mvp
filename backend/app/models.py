"""
MODÈLES NÉOBOT OPTIMISÉS - Version robuste sans dépendances circulaires
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
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

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    customer_phone = Column(String(50), nullable=False)
    customer_name = Column(String(255), nullable=True)
    channel = Column(String(50), default="whatsapp")
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    
    # Relations (en utilisant des strings)
    tenant = relationship("Tenant", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")
    
    # Si ConversationState existe, la relation est optionnelle
    # state = relationship("ConversationState", back_populates="conversation", uselist=False)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    content = Column(Text, nullable=False)
    direction = Column(String(20), nullable=False)
    is_ai = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")

# ========== MODÈLES OPTIONNELS ==========
# Si ConversationState n'est pas essentiel, on peut le commenter
# class ConversationState(Base):
#     __tablename__ = "conversation_states"
#     
#     id = Column(Integer, primary_key=True, index=True)
#     conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
#     state_type = Column(String(50), default="initial")
#     metadata = Column(Text, nullable=True)
#     created_at = Column(DateTime, default=datetime.utcnow)
#     
#     conversation = relationship("Conversation", back_populates="state")
