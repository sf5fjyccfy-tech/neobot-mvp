from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import enum
import os
from cryptography.fernet import Fernet

# Générer clé de chiffrement
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    
cipher = Fernet(ENCRYPTION_KEY.encode())

class PlanType(enum.Enum):
    BASIQUE = "basique"
    STANDARD = "standard"
    PRO = "pro"

class WhatsAppProvider(enum.Enum):
    WASENDER_API = "wasender_api"
    WHATSAPP_BUSINESS_API = "whatsapp_business_api"

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    business_type = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    plan = Column(Enum(PlanType), default=PlanType.BASIQUE)
    
    messages_limit = Column(Integer, default=1000)
    messages_used = Column(Integer, default=0)
    
    whatsapp_provider = Column(Enum(WhatsAppProvider), default=WhatsAppProvider.WASENDER_API)
    whatsapp_connected = Column(Boolean, default=False)
    whatsapp_config = Column(Text, nullable=True)
    
    is_trial = Column(Boolean, default=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    conversations = relationship("Conversation", back_populates="tenant")
    
    def get_plan_config(self):
        plan_configs = {
            PlanType.BASIQUE: {
                "name": "Basique",
                "price_fcfa": 20000,
                "messages_limit": 1000,
                "trial_days": 3,
                "features": ["WhatsApp QR", "IA basique", "Support email"],
                "whatsapp_provider": WhatsAppProvider.WASENDER_API,
                "requires_client_tokens": False
            },
            PlanType.STANDARD: {
                "name": "Standard",
                "price_fcfa": 50000,
                "messages_limit": 1500,
                "trial_days": 5,
                "features": ["WhatsApp Business API", "IA avancée", "Support prioritaire"],
                "whatsapp_provider": WhatsAppProvider.WHATSAPP_BUSINESS_API,
                "requires_client_tokens": True
            },
            PlanType.PRO: {
                "name": "Pro",
                "price_fcfa": 90000,
                "messages_limit": 3000,
                "trial_days": 7,
                "features": ["Multi-canaux", "API complète", "Support dédié"],
                "whatsapp_provider": WhatsAppProvider.WHATSAPP_BUSINESS_API,
                "requires_client_tokens": True
            }
        }
        return plan_configs.get(self.plan, plan_configs[PlanType.BASIQUE])
    
    def set_whatsapp_tokens(self, access_token: str, phone_number_id: str):
        """Chiffrer et sauvegarder les tokens WhatsApp"""
        import json
        data = {
            "access_token": access_token,
            "phone_number_id": phone_number_id
        }
        encrypted = cipher.encrypt(json.dumps(data).encode())
        self.whatsapp_config = encrypted.decode()
        self.whatsapp_connected = True
    
    def get_whatsapp_tokens(self):
        """Déchiffrer et récupérer les tokens"""
        if not self.whatsapp_config:
            return None, None
        
        try:
            import json
            decrypted = cipher.decrypt(self.whatsapp_config.encode())
            data = json.loads(decrypted.decode())
            return data.get("access_token"), data.get("phone_number_id")
        except:
            return None, None
    
    def clear_whatsapp_tokens(self):
        """Supprimer les tokens"""
        self.whatsapp_config = None
        self.whatsapp_connected = False
    
    def has_valid_whatsapp_config(self):
        """Vérifier si la config WhatsApp est valide"""
        if self.plan == PlanType.BASIQUE:
            return True  # Pas besoin de tokens pour plan Basique
        
        access_token, phone_number_id = self.get_whatsapp_tokens()
        return bool(access_token and phone_number_id)

class WhatsAppSession(Base):
    __tablename__ = "whatsapp_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), unique=True)
    
    qr_code = Column(Text, nullable=True)
    is_connected = Column(Boolean, default=False)
    phone_number = Column(String(20), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    connected_at = Column(DateTime(timezone=True), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    customer_phone = Column(String(20), nullable=False)
    customer_name = Column(String(100), nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_message_at = Column(DateTime(timezone=True), server_default=func.now())
    
    tenant = relationship("Tenant", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    content = Column(Text, nullable=False)
    direction = Column(String(10), nullable=False)
    is_ai = Column(Boolean, default=False)
    message_type = Column(String(20), default="text")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    conversation = relationship("Conversation", back_populates="messages")
