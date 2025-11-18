from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum
from .database import Base

class PlanType(str, enum.Enum):
    BASIQUE = "basique"
    STANDARD = "standard"
    PRO = "pro"

class WhatsAppProvider(str, enum.Enum):
    WASENDER_API = "wasender_api"
    WHATSAPP_BUSINESS_API = "whatsapp_business_api"

PLAN_LIMITS = {
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
        "other_platforms_messages": -1,
        "channels": 3,
        "features": ["3 canaux", "IA avancée", "NÉOBRAIN", "Analytics"],
        "trial_days": 7
    },
    PlanType.PRO: {
        "name": "Pro",
        "price_fcfa": 90000,
        "whatsapp_messages": 4000,
        "other_platforms_messages": -1,
        "channels": -1,
        "features": ["Canaux illimités", "CLOSEUR PRO", "API", "Support dédié"],
        "trial_days": 0
    }
}

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=False)
    business_type = Column(String(100), default="ecommerce")
    plan = Column(SQLEnum(PlanType), default=PlanType.BASIQUE, nullable=False)
    
    whatsapp_provider = Column(SQLEnum(WhatsAppProvider), default=WhatsAppProvider.WASENDER_API)
    whatsapp_connected = Column(Boolean, default=False)
    
    messages_used = Column(Integer, default=0)
    messages_limit = Column(Integer, default=2000)
    
    is_trial = Column(Boolean, default=True)
    trial_ends_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    conversations = relationship("Conversation", back_populates="tenant", overlaps="conversations")
    products = relationship("Product", back_populates="tenant", overlaps="products")
    transactions = relationship("Transaction", back_populates="tenant", overlaps="transactions")
    
    def get_plan_config(self):
        return PLAN_LIMITS.get(self.plan, PLAN_LIMITS[PlanType.BASIQUE])
    
    def activate_trial(self):
        config = self.get_plan_config()
        trial_days = config.get("trial_days", 14)
        if trial_days > 0:
            self.is_trial = True
            self.trial_ends_at = datetime.utcnow() + timedelta(days=trial_days)
            self.messages_limit = config["whatsapp_messages"]
    
    def check_message_limit(self, channel: str = "whatsapp") -> bool:
        config = self.get_plan_config()
        
        if channel == "whatsapp":
            limit = config["whatsapp_messages"]
        else:
            limit = config["other_platforms_messages"]
        
        if limit == -1:
            return True
        
        return self.messages_used < limit
    
    def increment_message_count(self, channel: str = "whatsapp"):
        self.messages_used += 1
    
    def get_remaining_messages(self, channel: str = "whatsapp") -> int:
        config = self.get_plan_config()
        
        if channel == "whatsapp":
            limit = config["whatsapp_messages"]
        else:
            limit = config["other_platforms_messages"]
        
        if limit == -1:
            return -1
        
        return max(0, limit - self.messages_used)

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
    
    tenant = relationship("Tenant", back_populates="conversations", overlaps="conversations")
    messages = relationship("Message", back_populates="conversation", overlaps="messages")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    content = Column(Text, nullable=False)
    direction = Column(String(20), nullable=False)
    is_ai = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages", overlaps="messages")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, default=0)
    category = Column(String(100), nullable=False)
    images = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("Tenant", back_populates="products", overlaps="products")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    commission_rate = Column(Integer, nullable=False)
    commission_amount = Column(Integer, nullable=False)
    net_amount = Column(Integer, nullable=False)
    payment_reference = Column(String(100), nullable=False)
    customer_phone = Column(String(50), nullable=False)
    tenant_plan = Column(String(50), nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    
    tenant = relationship("Tenant", back_populates="transactions", overlaps="transactions")


