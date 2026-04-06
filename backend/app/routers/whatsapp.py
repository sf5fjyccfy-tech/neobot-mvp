"""
WhatsApp Router - Gestion des sessions et QR codes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import asyncio
import logging
import os
import httpx

from app.database import get_db
from app.dependencies import verify_tenant_access
from app.models import WhatsAppSession, Tenant, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["whatsapp"])

WHATSAPP_SERVICE_URL = os.getenv("WHATSAPP_SERVICE_URL", "http://localhost:3001")
WHATSAPP_SERVICE_TIMEOUT = float(os.getenv("WHATSAPP_SERVICE_TIMEOUT", "15"))

# ========== SCHEMAS ==========

class WhatsAppSessionResponse(BaseModel):
    id: int
    tenant_id: int
    whatsapp_phone: str
    is_connected: bool
    last_connected_at: datetime | None
    failed_attempts: int
    
    model_config = ConfigDict(from_attributes=True)

class WhatsAppQRResponse(BaseModel):
    tenant_id: int
    status: str  # "awaiting_scan", "connected", "error"
    qr_code: str | None  # Base64 encoded QR code image or empty
    phone: str | None
    message: str

class CreateSessionRequest(BaseModel):
    whatsapp_phone: str

# ========== UTILITY FUNCTIONS ==========

def get_tenant_from_phone(phone: str, db: Session) -> int | None:
    """
    Map un numéro WhatsApp à un tenant_id
    Retourne l'ID du tenant ou None si pas trouvé
    """
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.whatsapp_phone == phone
    ).first()
    
    if not session:
        return None
    
    return session.tenant_id

def get_tenant_phone(tenant_id: int, db: Session) -> str | None:
    """
    Map un tenant_id à son numéro WhatsApp
    """
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        return None
    
    return session.whatsapp_phone

# ========== ENDPOINTS ==========

@router.get("/{tenant_id}/whatsapp/session", response_model=WhatsAppSessionResponse | None)
async def get_whatsapp_session(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access),
):
    """Récupère la session WhatsApp actuelle du tenant."""
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pas de session WhatsApp pour ce tenant"
        )
    
    return session

@router.post("/{tenant_id}/whatsapp/session")
async def create_whatsapp_session(
    tenant_id: int,
    body: CreateSessionRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access),
):
    """
    Crée une nouvelle session WhatsApp pour un tenant
    """
    whatsapp_phone = body.whatsapp_phone
    # Vérifier que le tenant existe
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant non trouvé"
        )
    
    # Vérifier qu'il n'existe pas déjà une session
    existing = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce tenant a déjà une session WhatsApp"
        )
    
    # Vérifier que le phone n'est pas utilisé par un autre tenant
    phone_in_use = db.query(WhatsAppSession).filter(
        WhatsAppSession.whatsapp_phone == whatsapp_phone
    ).first()
    
    if phone_in_use:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce numéro WhatsApp est déjà utilisé"
        )
    
    # Créer la session
    new_session = WhatsAppSession(
        tenant_id=tenant_id,
        whatsapp_phone=whatsapp_phone,
        is_connected=False,
        failed_attempts=0,
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    logger.info(f"✅ WhatsApp session created for tenant {tenant_id}: {whatsapp_phone}")
    
    return {
        "id": new_session.id,
        "tenant_id": new_session.tenant_id,
        "whatsapp_phone": new_session.whatsapp_phone,
        "is_connected": new_session.is_connected,
    }

@router.get("/{tenant_id}/whatsapp/qr", response_model=WhatsAppQRResponse)
async def get_whatsapp_qr(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access),
):
    """
    Récupère le QR code pour authentifier WhatsApp
    
    Flow:
    1. Si pas de session: Retourner message "créer une session d'abord"
    2. Si session existe + is_connected: Retourner status "connecté"
    3. Si session existe + !is_connected: Retourner QR code à scanner
    
    Intégré avec le service WhatsApp/Baileys pour récupérer le vrai QR code.
    """
    # Vérifier que le tenant existe
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant non trouvé"
        )
    
    # Chercher la session WhatsApp
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        return WhatsAppQRResponse(
            tenant_id=tenant_id,
            status="error",
            qr_code=None,
            phone=None,
            message="Aucune session WhatsApp créée. Veuillez d'abord connecter un numéro."
        )
    
    service_qr_url = f"{WHATSAPP_SERVICE_URL}/api/whatsapp/tenants/{tenant_id}/qr"
    service_connect_url = f"{WHATSAPP_SERVICE_URL}/api/whatsapp/tenants/{tenant_id}/connect"

    try:
        async with httpx.AsyncClient(timeout=WHATSAPP_SERVICE_TIMEOUT) as client:
            # 1) Read current QR state
            qr_resp = await client.get(service_qr_url)
            qr_resp.raise_for_status()
            qr_payload = qr_resp.json()

            has_qr = bool(qr_payload.get("hasQR"))
            is_connected = bool(qr_payload.get("connected"))
            state = qr_payload.get("state", "unknown")
            qr_image = qr_payload.get("qrImageDataUrl")

            # 2) If not connected, no QR yet, and NOT in an active pairing/init flow
            # → demander au service d'initialiser la connexion et repolled une fois
            # Ne pas déclencher POST /connect pendant state='initializing' pour éviter
            # d'interférer avec un code de pairing en cours de génération.
            if not is_connected and not has_qr and state not in ('initializing',):
                logger.info(f"🔄 No QR yet for tenant {tenant_id}, requesting connect")
                connect_resp = await client.post(service_connect_url)
                connect_resp.raise_for_status()

                qr_resp = await client.get(service_qr_url)
                qr_resp.raise_for_status()
                qr_payload = qr_resp.json()

                has_qr = bool(qr_payload.get("hasQR"))
                is_connected = bool(qr_payload.get("connected"))
                state = qr_payload.get("state", state)
                qr_image = qr_payload.get("qrImageDataUrl")

        # Sync DB ↔ service réel — le service fait autorité sur la connexion live
        if is_connected and not session.is_connected:
            session.is_connected = True
            session.last_connected_at = datetime.utcnow()
            session.failed_attempts = 0
            db.commit()
        elif not is_connected and session.is_connected:
            # DB dit "connecté" mais le service dit "non" (ex: redémarrage Render).
            # Rectifier la DB pour débloquer l'UI — sinon l'utilisateur ne peut plus
            # accéder au formulaire de re-jumelage.
            session.is_connected = False
            db.commit()
            logger.info(f"DB desync fixed for tenant {tenant_id}: marked disconnected")

        if is_connected:
            return WhatsAppQRResponse(
                tenant_id=tenant_id,
                status="connected",
                qr_code=None,
                phone=session.whatsapp_phone,
                message=f"✅ Connecté: {session.whatsapp_phone}",
            )

        if has_qr and qr_image:
            return WhatsAppQRResponse(
                tenant_id=tenant_id,
                status="awaiting_scan",
                qr_code=qr_image,
                phone=session.whatsapp_phone,
                message=f"QR prêt. Scannez pour connecter {session.whatsapp_phone}",
            )

        return WhatsAppQRResponse(
            tenant_id=tenant_id,
            status="awaiting_scan",
            qr_code=None,
            phone=session.whatsapp_phone,
            message=f"Connexion en cours ({state}). Le QR sera disponible sous peu.",
        )

    except httpx.HTTPStatusError as e:
        logger.error(
            f"WhatsApp service HTTP error for tenant {tenant_id}: "
            f"{e.response.status_code} {e.response.text}"
        )
        # Fallback sur la DB si le service est temporairement indisponible
        if session.is_connected:
            return WhatsAppQRResponse(
                tenant_id=tenant_id,
                status="connected",
                qr_code=None,
                phone=session.whatsapp_phone,
                message=f"✅ Connecté: {session.whatsapp_phone}",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Service WhatsApp indisponible temporairement"
        )
    except httpx.RequestError as e:
        logger.error(f"WhatsApp service request error for tenant {tenant_id}: {str(e)}")
        # Fallback sur la DB — ne pas bloquer l'UI si le service est down
        if session.is_connected:
            return WhatsAppQRResponse(
                tenant_id=tenant_id,
                status="connected",
                qr_code=None,
                phone=session.whatsapp_phone,
                message=f"✅ Connecté: {session.whatsapp_phone}",
            )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible de joindre le service WhatsApp"
        )


class PairingCodeRequest(BaseModel):
    phone_number: str  # ex: "22612345678" — format international sans +


@router.post("/{tenant_id}/whatsapp/request-pairing-code")
async def request_pairing_code(
    tenant_id: int,
    body: PairingCodeRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access),
):
    """
    Alternative au QR : génère un code à 8 chiffres à entrer dans l'app WhatsApp.
    Meilleur quand le QR est inaccessible (rate-limit, pas de caméra, connexion distante).
    Instructions: WA > ⋮ > Appareils connectés > Associer un appareil > Associer avec un numéro
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant non trouvé")

    phone = body.phone_number.replace("+", "").replace(" ", "").replace("-", "")
    if not phone.isdigit() or not (7 <= len(phone) <= 15):
        raise HTTPException(status_code=422, detail="Numéro invalide — format international sans +, ex: 22612345678")

    async def _call_wa_service() -> httpx.Response:
        async with httpx.AsyncClient(timeout=40.0) as client:
            return await client.post(
                f"{WHATSAPP_SERVICE_URL}/api/whatsapp/tenants/{tenant_id}/request-pairing-code",
                json={"phone_number": phone},
            )

    try:
        resp = await _call_wa_service()
    except httpx.RequestError as e:
        # Connexion refusée = cold start Render. Un seul retry après 5s.
        logger.info(f"WA service cold start, retry après 5s: {e}")
        await asyncio.sleep(5)
        try:
            resp = await _call_wa_service()
        except httpx.RequestError as e2:
            logger.error(f"WA service inaccessible: {e2}")
            raise HTTPException(status_code=503, detail="Service WhatsApp inaccessible — réessayez dans 1 minute")

    # 429 : rate limit Meta — renvoyer tel quel avec wait_seconds dans le body pour le frontend
    if resp.status_code == 429:
        wa_data = resp.json()
        return JSONResponse(
            status_code=429,
            content={
                "error": wa_data.get("error", "Trop de tentatives — attendez avant de réessayer"),
                "wait_seconds": wa_data.get("wait_seconds", 65),
            },
        )

    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail=f"Erreur service WhatsApp: {resp.text}")

    data = resp.json()

    if data.get("status") == "already_connected":
        return {"status": "already_connected", "message": "WhatsApp déjà connecté"}

    return {
        "status": "code_generated",
        "code": data.get("code"),
        "instructions": data.get("instructions"),
        "phone": phone,
    }


class MarkConnectedBody(BaseModel):
    phone: str | None = None


@router.post("/{tenant_id}/whatsapp/session/mark-connected")
async def mark_whatsapp_connected(
    tenant_id: int,
    body: MarkConnectedBody = MarkConnectedBody(),
    db: Session = Depends(get_db),
    x_internal_token: str | None = Header(default=None),
):
    """Appelé par le service WhatsApp interne après authentification Baileys."""
    _key = os.getenv("INTERNAL_API_KEY", "")
    if not _key or x_internal_token != _key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session WhatsApp non trouvée"
        )
    
    session.is_connected = True
    session.last_connected_at = datetime.utcnow()
    session.failed_attempts = 0
    # Mettre à jour le numéro si Baileys le fournit (vrai JID extrait des creds)
    if body.phone and body.phone.strip():
        session.whatsapp_phone = body.phone.strip()
    
    db.commit()
    db.refresh(session)
    
    logger.info(f"✅ WhatsApp session marked as connected for tenant {tenant_id}: {session.whatsapp_phone}")
    
    return {
        "status": "success",
        "message": f"Session connectée: {session.whatsapp_phone}"
    }

@router.post("/{tenant_id}/whatsapp/session/mark-disconnected")
async def mark_whatsapp_disconnected(
    tenant_id: int,
    db: Session = Depends(get_db),
    x_internal_token: str | None = Header(default=None),
):
    """Appelé par le service WhatsApp interne quand connexion perdue."""
    _key = os.getenv("INTERNAL_API_KEY", "")
    if not _key or x_internal_token != _key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session WhatsApp non trouvée"
        )
    
    session.is_connected = False
    session.failed_attempts += 1
    
    db.commit()
    
    logger.warning(f"⚠️  WhatsApp session disconnected for tenant {tenant_id}")
    
    return {
        "status": "disconnected",
        "failed_attempts": session.failed_attempts
    }

@router.delete("/{tenant_id}/whatsapp/session")
async def delete_whatsapp_session(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access),
):
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session WhatsApp non trouvée"
        )
    
    db.delete(session)
    db.commit()
    
    logger.info(f"🗑️  WhatsApp session deleted for tenant {tenant_id}")
    
    return {
        "status": "deleted",
        "message": f"Session WhatsApp supprimée pour le tenant {tenant_id}"
    }


@router.post("/{tenant_id}/whatsapp/disconnect")
async def disconnect_whatsapp(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(verify_tenant_access),
):
    """
    Déconnecter WhatsApp — ferme le socket Baileys sans supprimer les creds.
    L'utilisateur peut se reconnecter via QR ou code de couplage.
    """
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.tenant_id == tenant_id
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session WhatsApp non trouvée"
        )

    # Notifier le service Baileys
    service_disconnect_url = f"{WHATSAPP_SERVICE_URL}/api/whatsapp/tenants/{tenant_id}/disconnect"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            await client.post(service_disconnect_url)
    except Exception as e:
        logger.warning(f"Baileys disconnect call failed for tenant {tenant_id}: {e}")

    # Marquer comme déconnecté en DB
    session.is_connected = False
    db.commit()

    logger.info(f"🔴 WhatsApp disconnected for tenant {tenant_id}")

    return {"status": "disconnected", "tenant_id": tenant_id}
