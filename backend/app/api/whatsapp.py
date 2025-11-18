"""
Endpoints API pour la gestion WhatsApp
"""
from fastapi import APIRouter, HTTPException
from app.services.whatsapp_service import whatsapp_service

router = APIRouter()

@router.get("/whatsapp/status")
async def get_whatsapp_status():
    """Obtenir le statut de connexion WhatsApp"""
    try:
        status = await whatsapp_service.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/whatsapp/start")
async def start_whatsapp():
    """Démarrer la connexion WhatsApp"""
    try:
        result = await whatsapp_service.start_whatsapp()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/whatsapp/disconnect")
async def disconnect_whatsapp():
    """Déconnecter WhatsApp"""
    try:
        result = await whatsapp_service.disconnect()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
