# Fichier: app/services/whatsapp_service.py

# Ceci est un simple mock asynchrone pour satisfaire l'appel dans dual_mode_engine.py
# Il ne fait rien d'autre que d'attendre pour simuler l'envoi d'un message.

import asyncio
from typing import Dict, Any

async def send_whatsapp_message(phone: str, message: str) -> Dict[str, Any]:
    """Simule l'envoi d'un message via l'API WhatsApp."""
    print(f"DEBUG: TENTATIVE D'ENVOI WHATSAPP vers {phone} avec contenu: '{message[:30]}...'")
    await asyncio.sleep(0.1) # Simuler le délai réseau
    return {"status": "success", "message_id": "mock_123"}

