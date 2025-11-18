"""
NéoBot - Version Simple et Stable
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

app = FastAPI(title="NéoBot API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes essentielles
@app.get("/")
def root():
    return {"message": "NéoBot API", "status": "running", "version": "2.0.0"}

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/whatsapp/status")
def whatsapp_status():
    return {"status": "connected", "service": "baileys", "ready": True}

# Route message WhatsApp simplifiée
class MessageRequest(BaseModel):
    phone: str
    message: str

@app.post("/api/tenants/{tenant_id}/whatsapp/message")
async def receive_whatsapp(tenant_id: int, request: MessageRequest):
    """Version simplifiée du message WhatsApp"""
    
    # Réponses de fallback basiques
    fallback_responses = {
        "restaurant": {
            "salut": "👋 Bonjour ! Bienvenue chez notre restaurant. Comment puis-je vous aider ?",
            "menu": "🍽️ Nous avons ndolé, poulet DG, poisson braisé...",
            "prix": "💰 Nos plats vont de 2000 à 5000 FCFA",
            "default": "🍴 Bienvenue ! Dites-moi ce que vous cherchez."
        },
        "boutique": {
            "salut": "👋 Bonjour ! Bienvenue dans notre boutique.",
            "default": "🛍️ Nous avons vêtements, chaussures, accessoires..."
        }
    }
    
    message_lower = request.message.lower()
    
    # Détection basique
    if any(word in message_lower for word in ["salut", "bonjour", "hello"]):
        response = fallback_responses["restaurant"]["salut"]
    elif any(word in message_lower for word in ["menu", "manger", "plat"]):
        response = fallback_responses["restaurant"]["menu"]
    elif any(word in message_lower for word in ["prix", "combien", "coûte"]):
        response = fallback_responses["restaurant"]["prix"]
    elif "ndol" in message_lower:
        response = "🍽️ Notre ndolé est à 2500 FCFA. Un vrai délice !"
    elif "poulet dg" in message_lower:
        response = "🍗 Le poulet DG est à 3500 FCFA. Très populaire !"
    else:
        response = fallback_responses["restaurant"]["default"]
    
    return {"response": response, "source": "fallback_simple"}
