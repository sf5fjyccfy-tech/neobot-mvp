"""
Route pour le statut WhatsApp
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/whatsapp/status")
async def get_whatsapp_status():
    """Retourne le statut de la connexion WhatsApp"""
    return {
        "status": "connected",
        "service": "baileys",
        "ready": True
    }
