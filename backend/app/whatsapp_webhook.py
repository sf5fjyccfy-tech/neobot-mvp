"""
🧠 WhatsApp Webhook Handler for NéoBot Backend
Receives messages from WhatsApp service and processes them
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import httpx
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

# ===== Models =====

class WhatsAppMessage(BaseModel):
    """Incoming message from WhatsApp service"""
    from_: str = None  # Phone number
    to: str = None     # Bot number (optional)
    text: str
    senderName: str
    messageKey: dict
    timestamp: int
    isMedia: bool = False


class WhatsAppResponse(BaseModel):
    """Response to send back"""
    to: str
    text: str


# ===== Brain (Simple Orchestrator) =====

class BrainOrchestrator:
    """
    Simple pattern matching + DeepSeek fallback
    This is the "intelligence" of the bot
    """
    
    def __init__(self):
        self.patterns = {
            'prix': self._handle_pricing,
            'tarif': self._handle_pricing,
            'coût': self._handle_pricing,
            'aide': self._handle_help,
            'help': self._handle_help,
            'menu': self._handle_help,
            'demo': self._handle_demo,
            'hello': self._handle_greeting,
            'bonjour': self._handle_greeting,
            'hi': self._handle_greeting,
            'salut': self._handle_greeting,
        }
        
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        self.deepseek_url = 'https://api.deepseek.com/v1/chat/completions'
    
    async def process(self, message: str, sender_name: str) -> str:
        """
        Process incoming message and return response
        """
        logger.info(f"Processing message from {sender_name}: {message}")
        
        # Normalize message
        normalized = message.lower().strip()
        
        # Check patterns
        for keyword, handler in self.patterns.items():
            if keyword in normalized:
                response = handler(sender_name)
                logger.info(f"Matched pattern '{keyword}': {response}")
                return response
        
        # No pattern matched → call DeepSeek
        logger.info(f"No pattern matched, calling DeepSeek")
        response = await self._call_deepseek(message, sender_name)
        return response
    
    # ===== Pattern Handlers =====
    
    def _handle_pricing(self, sender_name: str) -> str:
        """Handle pricing inquiry"""
        return """💰 *Tarifs NéoBot*

📱 Plan Starter: 20,000 FCFA/mois
   • 500 messages illimités
   • Support manuel
   • Statistiques de base

🚀 Plus tard: plans supérieurs

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
    
    # ===== DeepSeek Fallback =====
    
    async def _call_deepseek(self, user_message: str, sender_name: str) -> str:
        """
        Call DeepSeek API for custom responses
        Fallback when no pattern matches
        """
        if not self.deepseek_api_key:
            logger.warning("DeepSeek API key not configured")
            return "Je ne peux pas répondre à cette question en ce moment. Essayez: prix, aide, demo"
        
        try:
            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "Vous êtes NéoBot, un assistant WhatsApp IA. Répondez en français, court (max 160 caractères pour SMS), amical."
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 150
            }
            
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.deepseek_url,
                    json=payload,
                    headers=headers,
                    timeout=10
                )
            
            if response.status_code != 200:
                logger.error(f"DeepSeek API error: {response.status_code}")
                return "Je dois vérifier ma mémoire. Essayez: prix, aide, demo"
            
            data = response.json()
            message = data['choices'][0]['message']['content']
            
            logger.info(f"DeepSeek response: {message}")
            return message
        
        except Exception as e:
            logger.error(f"DeepSeek error: {str(e)}")
            return "Je rencontre une petite difficulté. Réessayez ou tapez: prix, aide, demo"


# Create global brain instance
brain = BrainOrchestrator()


# ===== Webhook Endpoint =====

@router.post("/whatsapp")
async def whatsapp_webhook(message: WhatsAppMessage, background_tasks: BackgroundTasks):
    """
    Receive messages from WhatsApp service
    Process and send response asynchronously
    """
    try:
        logger.info(f"📨 Received message from {message.senderName}: {message.text}")
        
        # Extract phone number (remove country code if needed)
        phone = message.from_
        if phone.startswith('+'):
            phone = phone[1:]
        
        # TODO: Save to database
        # conversation = await save_message_to_db(
        #     phone=phone,
        #     sender_name=message.senderName,
        #     text=message.text,
        #     direction='incoming'
        # )
        
        # Process message with brain
        response_text = await brain.process(message.text, message.senderName)
        
        # Send response in background
        background_tasks.add_task(
            send_whatsapp_response,
            phone=phone,
            text=response_text
        )
        
        return {
            "status": "received",
            "phone": phone,
            "sender": message.senderName,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Background Task =====

async def send_whatsapp_response(phone: str, text: str):
    """
    Send response via WhatsApp service
    Runs in background (non-blocking)
    """
    try:
        whatsapp_service_url = os.getenv(
            'WHATSAPP_SERVICE_URL',
            'http://localhost:3001'
        )
        
        payload = {
            "to": phone,
            "text": text
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{whatsapp_service_url}/send",
                json=payload,
                timeout=10
            )
        
        if response.status_code == 200:
            logger.info(f"✅ Message sent to {phone}")
        else:
            logger.error(f"Failed to send message: {response.status_code}")
            logger.error(response.text)
    
    except Exception as e:
        logger.error(f"Error sending WhatsApp response: {str(e)}")


# ===== Utils =====

async def save_message_to_db(phone: str, sender_name: str, text: str, direction: str):
    """
    TODO: Implement database saving
    - Find or create Conversation
    - Add Message to conversation
    - Track message count for billing
    """
    pass


def is_daily_limit_reached(phone: str) -> bool:
    """
    TODO: Check if customer has reached daily message limit
    """
    return False


def is_monthly_limit_reached(phone: str) -> bool:
    """
    TODO: Check if customer has reached monthly message limit
    """
    return False
