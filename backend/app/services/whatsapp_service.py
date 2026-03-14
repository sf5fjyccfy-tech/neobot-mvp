import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


async def send_whatsapp_message(phone: str, message: str) -> Dict[str, Any]:
    """Fallback async sender used when direct WhatsApp provider is unavailable."""
    await asyncio.sleep(0.1)
    logger.info("Mock WhatsApp send to %s", phone)
    return {"status": "success", "message_id": "mock_123"}


class WhatsAppService:
    """Minimal async service contract used by legacy API routes."""

    async def get_status(self) -> Dict[str, Any]:
        return {
            "status": "connected",
            "provider": "mock",
            "message": "WhatsApp mock service active"
        }

    async def start_whatsapp(self) -> Dict[str, Any]:
        await asyncio.sleep(0.05)
        return {
            "status": "started",
            "provider": "mock",
            "message": "Mock WhatsApp session started"
        }

    async def disconnect(self) -> Dict[str, Any]:
        await asyncio.sleep(0.05)
        return {
            "status": "disconnected",
            "provider": "mock",
            "message": "Mock WhatsApp session disconnected"
        }


whatsapp_service = WhatsAppService()

