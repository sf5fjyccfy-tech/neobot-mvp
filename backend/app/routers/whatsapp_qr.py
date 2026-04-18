"""
WhatsApp QR Code Endpoints - Production Integration avec Baileys
Récupère les QR codes du service WhatsApp Node.js, gère les sessions.
"""

from fastapi import APIRouter, HTTPException, Depends, Path
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ..database import get_db
from ..models import Tenant
from ..services.whatsapp_qr_service import WhatsAppQRService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["whatsapp"])


# ========== PUBLIC ENDPOINTS (pas d'authentification) ==========

@router.get("/tenants/{tenant_id}/whatsapp/qr", response_model=dict)
async def get_whatsapp_qr(
    tenant_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    """
    Récupère le QR code pour scanner avec WhatsApp.
    
    Endpoint PUBLIC — pas d'authentification requise.
    Vérification simple: tenant existe.
    
    Returns:
    {
        "tenant_id": 1,
        "status": "waiting_qr" | "connected",
        "qr_code": "data:image/png;base64,...",
        "expires_in": 120,
        "message": "Scannez ce code QR avec WhatsApp",
        "phone": "+237... ou null",
        "connected": false,
        "timestamp": "2026-04-18T..."
    }
    """
    logger.info(f"🔵 [PUBLIC QR] tenant_id={tenant_id}")
    try:
        logger.info(f"Calling WhatsAppQRService...")
        result = await WhatsAppQRService.get_qr_for_tenant(
            tenant_id=tenant_id,
            db=db,
            force_refresh=False
        )
        logger.info(f"✅ QR result: status={result.get('status')}")
        return result
    except ValueError as e:
        logger.warning(f"Invalid tenant {tenant_id}: {e}")
        raise HTTPException(status_code=404, detail="Tenant not found")
    except RuntimeError as e:
        logger.error(f"WhatsApp service error for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting QR for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@router.get("/tenants/{tenant_id}/whatsapp/status", response_model=dict)
async def get_whatsapp_status(
    tenant_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    """
    Récupère le statut de connexion WhatsApp.
    
    Endpoint PUBLIC — pas d'authentification requise.
    Utilisé par le polling du frontend.
    
    Returns:
    {
        "status": "disconnected" | "waiting_qr" | "connected",
        "phone": "+237... ou null",
        "connected_since": "2026-04-18T..." ou null,
        "timestamp": "2026-04-18T..."
    }
    """
    try:
        result = await WhatsAppQRService.get_connection_status(
            tenant_id=tenant_id,
            db=db
        )
        return result
    except ValueError as e:
        logger.warning(f"Invalid tenant {tenant_id}: {e}")
        raise HTTPException(status_code=404, detail="Tenant not found")
    except Exception as e:
        logger.error(f"Error getting WhatsApp status for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")


@router.post("/tenants/{tenant_id}/whatsapp/refresh-qr", response_model=dict)
async def refresh_whatsapp_qr(
    tenant_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
):
    """
    Force la génération d'un nouveau QR code.
    
    Endpoint PUBLIC — utilisé quand l'utilisateur a attendu trop longtemps
    et le QR a expiré (2 min).
    
    Returns: Same as get_whatsapp_qr
    """
    try:
        result = await WhatsAppQRService.get_qr_for_tenant(
            tenant_id=tenant_id,
            db=db,
            force_refresh=True
        )
        logger.info(f"QR refresh triggered for tenant {tenant_id}")
        return result
    except ValueError as e:
        logger.warning(f"Invalid tenant {tenant_id}: {e}")
        raise HTTPException(status_code=404, detail="Tenant not found")
    except RuntimeError as e:
        logger.error(f"WhatsApp service error on refresh for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Error refreshing QR for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Erreur serveur")
