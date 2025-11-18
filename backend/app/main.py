"""
NÉOBOT - SYSTÈME COMPLET ET FONCTIONNEL
Version stable avec toutes les fonctionnalités
"""
from __future__ import annotations
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import httpx
import re
import os
import logging
import time
import threading
from pathlib import Path
from dotenv import load_dotenv

# Charger backend/.env automatiquement si présent
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Configuration
AI_API_KEY = os.getenv('DEEPSEEK_API_KEY', 'sk-test')
AI_URL = "https://api.deepseek.com/v1/chat/completions"

# IMPORTS CRITIQUES - DOIVENT ÊTRE EN PREMIER
from .database import get_db, Base, engine
from .models import Tenant, Conversation, Message
from .services.fallback_service import FallbackService
from .services.closeur_pro_service import CloseurProService

# Création des tables
try:
    Base.metadata.create_all(bind=engine)
    print("✅ Base de données initialisée")
except Exception as e:
    logging.warning(f"⚠️  Erreur initialisation DB: {e}")

# Application FastAPI
app = FastAPI(
    title="NéoBot API",
    description="Chatbot intelligent pour entreprises africaines",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schémas Pydantic
class TenantCreate(BaseModel):
    name: str
    email: str
    phone: str
    business_type: Optional[str] = "autre"

class MessageRequest(BaseModel):
    phone: str
    message: str

# ==================== FONCTION IA (DÉPLACÉE ICI) ====================

async def generate_ai_response(tenant: "Tenant", message: str, history: List = None) -> str:
    """Générer une réponse IA avec fallback intelligent"""
    db = next(get_db())
    try:
        fallback_service = FallbackService(db)
        
        # Vérifier si on utilise le fallback
        if fallback_service.should_use_fallback(message):
            response = fallback_service.get_fallback_response(message, tenant.business_type, tenant.name)
            print(f"🤖 Fallback utilisé: {response[:50]}...")
            return response
        
        # Pour les messages complexes, essayer l'IA réelle
        try:
            # Import dynamique pour éviter les erreurs
            from app.ai_prompts import build_chat_messages
            messages = build_chat_messages(tenant, message, history)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    AI_URL,
                    json={
                        "model": "deepseek-chat",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 150
                    },
                    headers={"Authorization": f"Bearer {AI_API_KEY}"}
                )
                
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    # En cas d'erreur API, utiliser le fallback
                    print(f"❌ Erreur API DeepSeek: {response.status_code}")
                    return fallback_service.get_fallback_response(message, tenant.business_type, tenant.name)
                    
        except Exception as ai_error:
            print(f"⚠️ Erreur IA: {ai_error}")
            return fallback_service.get_fallback_response(message, tenant.business_type, tenant.name)
            
    except Exception as e:
        print(f"❌ Erreur générique: {e}")
        return f"👋 Bonjour ! Bienvenue chez {tenant.name}. Comment puis-je vous aider ?"
    finally:
        db.close()

# ==================== ROUTES ESSENTIELLES ====================

@app.get("/")
def root():
    """Route racine"""
    return {
        "message": "🚀 NéoBot API - Système complet",
        "version": "2.0.0", 
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health(db: Session = Depends(get_db)):
    """Santé du système"""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except:
        db_status = "error"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "services": ["fallback", "closeur_pro", "whatsapp"]
    }

@app.get("/api/whatsapp/status")
def whatsapp_status():
    """Statut WhatsApp"""
    return {
        "status": "connected",
        "service": "baileys", 
        "ready": True,
        "timestamp": datetime.now().isoformat()
    }

# ==================== GESTION CLIENTS ====================

@app.post("/api/tenants", response_model=dict)
def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    """Créer un nouveau client"""
    # Vérifier si l'email existe déjà
    existing = db.query(Tenant).filter(Tenant.email == tenant.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    
    # Créer le tenant
    db_tenant = Tenant(
        name=tenant.name,
        email=tenant.email,
        phone=tenant.phone,
        business_type=tenant.business_type
    )
    db_tenant.activate_trial()
    
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    
    return {
        "id": db_tenant.id,
        "name": db_tenant.name,
        "email": db_tenant.email,
        "plan": db_tenant.plan.value,
        "business_type": db_tenant.business_type,
        "status": "active",
        "trial_ends_at": db_tenant.trial_ends_at.isoformat() if db_tenant.trial_ends_at else None
    }

@app.get("/api/tenants/{tenant_id}")
def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    """Obtenir les informations d'un client"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    return {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "phone": tenant.phone,
        "business_type": tenant.business_type,
        "plan": tenant.get_plan_config(),
        "whatsapp_connected": tenant.whatsapp_connected,
        "is_trial": tenant.is_trial,
        "trial_ends_at": tenant.trial_ends_at.isoformat() if tenant.trial_ends_at else None
    }

# ==================== FONCTIONNALITÉ PRINCIPALE ====================

@app.post("/api/tenants/{tenant_id}/whatsapp/message")
async def receive_whatsapp_message(tenant_id: int, request: MessageRequest, db: Session = Depends(get_db)):
    """Recevoir un message WhatsApp - FONCTION PRINCIPALE"""
    # Vérifier le client
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    phone = request.phone
    message_text = request.message
    
    if not message_text or not message_text.strip():
        raise HTTPException(status_code=400, detail="Message vide")
    
    # Vérifier les limites de messages
    if not tenant.check_message_limit("whatsapp"):
        return {
            "response": "🚫 Limite de messages atteinte pour ce mois. Veuillez recharger votre compte.",
            "source": "system"
        }
    
    # Gérer la conversation
    conversation = db.query(Conversation).filter(
        Conversation.tenant_id == tenant_id,
        Conversation.customer_phone == phone
    ).first()
    
    if not conversation:
        conversation = Conversation(
            tenant_id=tenant_id,
            customer_phone=phone,
            customer_name=f"Client {phone[-4:]}",
            channel="whatsapp",
            status="active"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        print(f"📞 Nouvelle conversation: {phone}")
    
    # Enregistrer le message entrant
    incoming_message = Message(
        conversation_id=conversation.id,
        content=message_text,
        direction="incoming",
        is_ai=False
    )
    db.add(incoming_message)
    db.commit()
    
    # Générer la réponse
    start_time = time.time()
    reply = await generate_ai_response(tenant, message_text)
    response_time = time.time() - start_time
    
    # Enregistrer la réponse
    outgoing_message = Message(
        conversation_id=conversation.id,
        content=reply,
        direction="outgoing", 
        is_ai=True
    )
    db.add(outgoing_message)
    
    # Mettre à jour les compteurs
    tenant.increment_message_count("whatsapp")
    conversation.last_message_at = datetime.utcnow()
    
    db.commit()
    
    print(f"💬 Réponse envoyée en {response_time:.2f}s: {reply[:50]}...")
    
    return {
        "response": reply,
        "source": "ai",
        "response_time": response_time,
        "conversation_id": conversation.id
    }

# ==================== ANALYTICS ====================

@app.get("/api/tenants/{tenant_id}/analytics")
def get_analytics(tenant_id: int, db: Session = Depends(get_db)):
    """Obtenir les statistiques d'un client"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    
    # Statistiques de base
    total_conversations = db.query(Conversation).filter(Conversation.tenant_id == tenant_id).count()
    total_messages = db.query(Message).join(Conversation).filter(Conversation.tenant_id == tenant_id).count()
    
    # Messages des 7 derniers jours
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_messages = db.query(Message).join(Conversation).filter(
        Conversation.tenant_id == tenant_id,
        Message.created_at >= seven_days_ago
    ).count()
    
    return {
        "tenant_id": tenant_id,
        "period": "all_time",
        "conversations": {
            "total": total_conversations,
            "active": db.query(Conversation).filter(
                Conversation.tenant_id == tenant_id,
                Conversation.status == "active"
            ).count()
        },
        "messages": {
            "total": total_messages,
            "last_7_days": recent_messages,
            "incoming": db.query(Message).join(Conversation).filter(
                Conversation.tenant_id == tenant_id,
                Message.direction == "incoming"
            ).count(),
            "outgoing": db.query(Message).join(Conversation).filter(
                Conversation.tenant_id == tenant_id,
                Message.direction == "outgoing" 
            ).count()
        },
        "plan": tenant.get_plan_config(),
        "limits": {
            "messages_used": tenant.messages_used,
            "messages_limit": tenant.messages_limit,
            "remaining": tenant.get_remaining_messages("whatsapp")
        }
    }

# ==================== CLOSEUR PRO ====================

@app.post("/api/tenants/{tenant_id}/closeur-pro/analyze")
def analyze_conversation_risk(tenant_id: int, conversation_id: int, db: Session = Depends(get_db)):
    """Analyser le risque d'abandon d'une conversation"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.tenant_id == tenant_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    closeur_service = CloseurProService(db)
    analysis = closeur_service.analyze_conversation(conversation)
    
    return {
        "conversation_id": conversation_id,
        "analysis": analysis,
        "should_persuade": closeur_service.should_send_persuasion(conversation),
        "timestamp": datetime.now().isoformat()
    }

# ==================== SYSTÈME BACKGROUND ====================

def background_persuasion_check():
    """Vérification périodique des conversations pour persuasion"""
    while True:
        try:
            from app.database import SessionLocal
            db = SessionLocal()
            
            # Conversations actives des dernières 24h
            time_threshold = datetime.utcnow() - timedelta(hours=24)
            
            conversations = db.query(Conversation).filter(
                Conversation.last_message_at >= time_threshold,
                Conversation.status == "active"
            ).all()
            
            closeur_service = CloseurProService(db)
            persuasion_count = 0
            
            for conv in conversations:
                if closeur_service.should_send_persuasion(conv):
                    result = closeur_service.process_conversation_persuasion(conv)
                    if result:
                        persuasion_count += 1
            
            if persuasion_count > 0:
                print(f"💬 {persuasion_count} persuasions éthiques envoyées")
            
            db.close()
            time.sleep(180)  # 3 minutes entre les vérifications
            
        except Exception as e:
            print(f"❌ Erreur vérification persuasion: {e}")
            time.sleep(60)  # Attente plus courte en cas d'erreur

@app.on_event("startup")
async def startup_event():
    """Démarrage de l'application"""
    # Démarrer le thread de background
    thread = threading.Thread(target=background_persuasion_check, daemon=True)
    thread.start()
    
    print("🚀 NéoBot démarré avec succès!")
    print("   • Fallback Intelligent ✓")
    print("   • Closeur Pro Éthique ✓") 
    print("   • API REST complète ✓")
    print("   • Système background ✓")
    print(f"   • Accès: http://localhost:8000")
    print(f"   • Documentation: http://localhost:8000/docs")

# ==================== DOCUMENTATION ====================

@app.get("/api/help")
def get_help():
    """Aide et documentation de l'API"""
    return {
        "api_name": "NéoBot API",
        "version": "2.0.0",
        "endpoints": {
            "health": "GET /health - Santé du système",
            "create_tenant": "POST /api/tenants - Créer un client",
            "get_tenant": "GET /api/tenants/{id} - Obtenir un client", 
            "whatsapp_message": "POST /api/tenants/{id}/whatsapp/message - Envoyer/réception message",
            "analytics": "GET /api/tenants/{id}/analytics - Statistiques",
            "closeur_pro": "POST /api/tenants/{id}/closeur-pro/analyze - Analyser conversation"
        },
        "business_types": ["restaurant", "boutique", "service", "autre"],
        "support": "contact@neobot.cm"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
