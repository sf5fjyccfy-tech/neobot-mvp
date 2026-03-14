"""
Service IA Simple et Fonctionnel
"""
import os
import httpx
from app.ai_prompts import build_chat_messages

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

async def generate_ai_response(tenant, message: str, conversation_history: list = None) -> str:
    """Génère une réponse IA simple et fonctionnelle"""
    try:
        # Construire les messages pour l'IA
        messages = build_chat_messages(tenant, message, conversation_history)
        
        # Appel API DeepSeek
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                DEEPSEEK_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 150
                }
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Merci pour votre message. Notre équipe vous répondra bientôt. (Erreur: {response.status_code})"
                
    except Exception as e:
        print(f"❌ Erreur IA détaillée: {e}")
        return "Merci pour votre message. Notre service IA est temporairement indisponible, mais nous vous répondrons rapidement."
