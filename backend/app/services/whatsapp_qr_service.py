"""
Service WhatsApp QR Code Management
Communique avec le service WhatsApp Node.js (port 3001) pour gérer les QR codes.
"""

import os
import httpx
import logging
import base64
import io
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import qrcode
from sqlalchemy.orm import Session

from app.models import WhatsAppSessionQR, Tenant

logger = logging.getLogger(__name__)

WHATSAPP_SERVICE_URL = os.getenv("WHATSAPP_SERVICE_URL", "http://whatsapp:3001")
QR_CACHE_TTL_SECONDS = 5  # Cache local pendant 5 sec pour éviter surcharge

# Cache en mémoire pour les réponses QR — déduplicates les polls frontend
_qr_response_cache: Dict[int, tuple[Dict[str, Any], datetime]] = {}


def _generate_qr_image_from_raw(qr_raw: str) -> str:
    """
    Génère une image PNG base64 à partir des données brutes qrRaw de Baileys.
    
    La qrRaw est une string délimitée par des virgules contenant les données du QR.
    On les utilise comme contenu directement pour générer le PNG.
    """
    try:
        # Générer un QR code avec la qrRaw comme contenu
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_raw)
        qr.make(fit=True)
        
        # Générer l'image PNG
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convertir en base64
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        img_base64 = base64.b64encode(img_bytes.getvalue()).decode("utf-8")
        
        # Retourner comme data URL
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        logger.error(f"Error generating QR image from raw: {e}")
        return None

class WhatsAppQRService:
    """Gestion QR codes pour connexion WhatsApp via Baileys"""

    @staticmethod
    async def get_qr_for_tenant(
        tenant_id: int,
        db: Session,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Récupère le QR code pour un tenant.
        
        OPTIMISATION: Cache en mémoire 5s pour réduire les requêtes DB lors du polling frontend.
        Chaque requête frontend poll le QR toutes les 5s — sans cache, ça crève le pool.
        
        Args:
            tenant_id: ID du tenant
            db: Session database
            force_refresh: Forcer la génération d'un nouveau QR (ignore le cache)
        
        Returns:
            {
                "tenant_id": 1,
                "status": "waiting_qr" | "connected" | "disconnected",
                "qr_code": "data:image/png;base64,..." | None,
                "expires_in": 120,
                "message": "Scan le code QR avec WhatsApp",
                "phone": "+237... ou None",
                "connected": False | True,
                "timestamp": "2026-04-18T..."
            }
        """
        # ✅ CHECK CACHE — Si un résultat existe et n'a pas expiré, le retourner
        # Cela réduit drastiquement les requêtes DB lors du polling frontend
        if not force_refresh and tenant_id in _qr_response_cache:
            cached_response, cache_time = _qr_response_cache[tenant_id]
            if (datetime.utcnow() - cache_time).total_seconds() < QR_CACHE_TTL_SECONDS:
                logger.debug(f"✅ QR cache hit (in-memory) for tenant {tenant_id}")
                return cached_response
            else:
                # Cache expiré, le nettoyer
                del _qr_response_cache[tenant_id]
        
        # Vérifier que le tenant existe
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Vérifier le cache DB : y a-t-il un QR valide et non expiré ?
        if not force_refresh:
            existing_qr = (
                db.query(WhatsAppSessionQR)
                .filter(
                    WhatsAppSessionQR.tenant_id == tenant_id,
                    WhatsAppSessionQR.status == "pending",
                    WhatsAppSessionQR.qr_expires_at > datetime.utcnow()
                )
                .order_by(WhatsAppSessionQR.qr_generated_at.desc())
                .first()
            )
            if existing_qr and existing_qr.qr_code_data:
                logger.debug(f"✅ QR cache hit (DB) for tenant {tenant_id}")
                expires_in = int(
                    (existing_qr.qr_expires_at - datetime.utcnow()).total_seconds()
                )
                result = {
                    "tenant_id": tenant_id,
                    "status": "waiting_qr",
                    "qr_code": existing_qr.qr_code_data,
                    "expires_in": max(1, expires_in),
                    "message": "Scannez ce code QR avec WhatsApp",
                    "phone": existing_qr.phone_number,
                    "connected": False,
                    "timestamp": datetime.utcnow().isoformat(),
                }
                # Mettre en cache mémoire
                _qr_response_cache[tenant_id] = (result, datetime.utcnow())
                return result

        # Pas de QR valide en cache → appeler le service WhatsApp
        # IMPORTANT: D'abord appeler /connect pour initialiser la session si nécessaire
        # Ensuite, récupérer le QR code
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # 1. POST /connect pour initialiser si pas encore fait
                logger.debug(f"Initializing session for tenant {tenant_id}...")
                try:
                    connect_resp = await client.post(
                        f"{WHATSAPP_SERVICE_URL}/api/whatsapp/tenants/{tenant_id}/connect",
                        json={},
                        timeout=10.0
                    )
                    # Ne pas raise ici — le service peut être en train de générer le QR
                    logger.debug(f"Connect response: {connect_resp.status_code}")
                except httpx.TimeoutException:
                    logger.debug(f"Connect request timed out (service generating QR)")
                except httpx.HTTPError as e:
                    logger.debug(f"Connect request error: {e}")
                
                # 2. GET QR — le service doit maintenant l'avoir généré
                logger.debug(f"Fetching QR for tenant {tenant_id}...")
                response = await client.get(
                    f"{WHATSAPP_SERVICE_URL}/api/whatsapp/tenants/{tenant_id}/qr",
                    headers={"Accept": "application/json"},
                    timeout=15.0
                )
                response.raise_for_status()
                wa_data = response.json()
        except httpx.TimeoutException:
            logger.error(f"WhatsApp service timeout for tenant {tenant_id}")
            raise RuntimeError("WhatsApp service timeout — veuillez réessayer")
        except httpx.HTTPError as e:
            logger.error(f"WhatsApp service error for tenant {tenant_id}: {e}")
            raise RuntimeError("Service WhatsApp indisponible — veuillez réessayer")

        # Valider les données du service WhatsApp
        qr_image_data = wa_data.get("qrImageDataUrl")
        qr_raw = wa_data.get("qrRaw")
        
        # Si le service n'a pas encore généré l'image, on la génère nous-mêmes
        if not qr_image_data and qr_raw:
            logger.debug(f"Generating QR image from qrRaw for tenant {tenant_id}")
            qr_image_data = _generate_qr_image_from_raw(qr_raw)
        
        if not qr_image_data:
            logger.warn(f"No QR data available for tenant {tenant_id} (qrImageDataUrl={bool(wa_data.get('qrImageDataUrl'))}, qrRaw={bool(wa_data.get('qrRaw'))})")
            raise RuntimeError("Impossible de générer le QR — veuillez réessayer")

        # Sauvegarder en DB
        now = datetime.utcnow()
        qr_expires = now + timedelta(minutes=2)  # QR valide 2 min
        
        session_qr = WhatsAppSessionQR(
            tenant_id=tenant_id,
            session_id=f"tenant_{tenant_id}_{now.timestamp()}",
            qr_code_data=wa_data.get("qrImageDataUrl"),
            status="pending",
            qr_generated_at=now,
            qr_expires_at=qr_expires,
            phone_number=wa_data.get("phone"),
        )
        db.add(session_qr)
        try:
            db.commit()
            db.refresh(session_qr)
        except Exception as e:
            db.rollback()
            logger.error(f"DB error saving QR for tenant {tenant_id}: {e}")
            # Continuer quand même — retourner le QR même si pas en DB

        result = {
            "tenant_id": tenant_id,
            "status": wa_data.get("state", "waiting_qr"),
            "qr_code": wa_data.get("qrImageDataUrl"),
            "expires_in": 120,
            "message": wa_data.get("message", "Scannez ce code QR avec WhatsApp"),
            "phone": wa_data.get("phone"),
            "connected": wa_data.get("connected", False),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # ✅ Mettre en cache mémoire pour réduire les requêtes DB pendant le polling
        _qr_response_cache[tenant_id] = (result, datetime.utcnow())
        
        return result

    @staticmethod
    async def get_connection_status(tenant_id: int, db: Session) -> Dict[str, Any]:
        """
        Récupère le statut de connexion WhatsApp actuel.
        
        Returns:
            {
                "status": "disconnected" | "waiting_qr" | "connected",
                "phone": "+237..." | None,
                "connected_since": "2026-04-18T..." | None
            }
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{WHATSAPP_SERVICE_URL}/api/whatsapp/status",
                    headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                wa_status = response.json()
        except httpx.HTTPError as e:
            logger.error(f"WhatsApp status check failed for tenant {tenant_id}: {e}")
            return {
                "status": "disconnected",
                "phone": None,
                "connected_since": None,
                "error": "Service WhatsApp indisponible"
            }

        return {
            "status": wa_status.get("state", "disconnected"),
            "phone": wa_status.get("connectedPhone"),
            "connected_since": wa_status.get("connectedAt"),
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def mark_qr_as_used(tenant_id: int, db: Session) -> None:
        """Marquer tous les QR codes d'un tenant comme "utilisés" après connexion réussie"""
        try:
            pending_qrs = db.query(WhatsAppSessionQR).filter(
                WhatsAppSessionQR.tenant_id == tenant_id,
                WhatsAppSessionQR.status == "pending"
            ).all()
            
            for qr in pending_qrs:
                qr.status = "connected"
                qr.connected_at = datetime.utcnow()
            
            db.commit()
            logger.info(f"Marked {len(pending_qrs)} QR codes as used for tenant {tenant_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error marking QR as used for tenant {tenant_id}: {e}")
