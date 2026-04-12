"""
Router NeopPay — Endpoints de paiement NeoBot.

Endpoints publics (pas d'auth) :
  GET  /api/neopay/payment-links/{token}   — Info d'un lien de paiement
  POST /api/neopay/payment-links/{token}/initiate — Lancer un paiement

Endpoints authentifiés (JWT tenant) :
  POST /api/neopay/payment-links           — Créer un lien de paiement

Webhooks providers (pas d'auth JWT — vérification HMAC obligatoire) :
  POST /api/neopay/webhooks/korapay        — Webhook Korapay
  POST /api/neopay/webhooks/campay         — Webhook CamPay

Endpoints superadmin :
  GET  /api/neopay/payments                — Historique paiements
  GET  /api/neopay/webhooks                — Historique webhooks
"""
import logging
import re
import uuid as _uuid
from typing import Optional
from datetime import datetime

import sentry_sdk
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_superadmin_user
from app.models import PaymentLink, PaymentEvent, WebhookEvent, Tenant, PlanType, PLAN_LIMITS
from app.services import neopay_service, korapay_service, campay_service
from app.services.email_service import send_internal_alert
from app.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/neopay", tags=["neopay"])


# ─── Schémas ─────────────────────────────────────────────────────────────────

class CreatePaymentLinkRequest(BaseModel):
    plan: str   # BASIC | STANDARD | PRO


class InitiatePaymentRequest(BaseModel):
    payment_method: str          # "card" | "mobile_money"
    customer_email: EmailStr
    customer_name: str
    customer_phone: Optional[str] = None
    country: str = "CM"


class PreparePaymentRequest(BaseModel):
    """Pour Korapay Inline Checkout (JS SDK) : prépare le PaymentEvent sans appeler l'API Korapay."""
    payment_method: str = "card"  # "card" | "mobile_money"
    customer_email: EmailStr
    customer_name: str
    customer_phone: Optional[str] = None
    country: str = "CM"


# ─── GET /api/neopay/payment-links/{token} ───────────────────────────────────

@router.get("/payment-links/{token}", summary="Informations d'un lien de paiement")
def get_payment_link(token: str, db: Session = Depends(get_db)):
    """
    Endpoint public — utilisé par la page /pay/[token] du frontend.
    Retourne les infos nécessaires pour afficher le récap commande.
    """
    link = neopay_service.get_payment_link(db, token)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lien de paiement introuvable ou expiré"
        )

    tenant = db.query(Tenant).filter(Tenant.id == link.tenant_id).first()

    return {
        "token": link.token,
        "plan": link.plan,
        "amount": link.amount,
        "currency": link.currency,
        "status": link.status,
        "expires_at": link.expires_at.isoformat(),
        "tenant_name": tenant.name if tenant else "",
        "tenant_email": tenant.email if tenant else "",
    }


# ─── POST /api/neopay/payment-links ──────────────────────────────────────────

@router.post("/payment-links", summary="Créer un lien de paiement")
def create_payment_link(
    body: CreatePaymentLinkRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Crée un lien de paiement pour le tenant authentifié.
    URL retournée : {FRONTEND_URL}/pay/{token}
    """
    try:
        link = neopay_service.create_payment_link(
            db,
            tenant_id=current_user.tenant_id,
            plan=body.plan,
        )
        pay_url = f"{neopay_service._get_frontend_url()}/pay/{link.token}"
        return {
            "token": link.token,
            "payment_url": pay_url,
            "plan": link.plan,
            "amount": link.amount,
            "currency": link.currency,
            "expires_at": link.expires_at.isoformat(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ─── POST /api/neopay/payment-links/{token}/initiate ─────────────────────────

@router.post("/payment-links/{token}/initiate", summary="Lancer le paiement")
async def initiate_payment(
    token: str,
    body: InitiatePaymentRequest,
    db: Session = Depends(get_db),
):
    """
    Lance le paiement pour un lien donné.
    Choisit le provider selon le pays + mode paiement.
    Retourne l'URL checkout ou le code USSD Mobile Money.

    Endpoint public — pas d'authentification JWT requise
    (le token du lien est le secret, valable 24h).
    """
    try:
        result = await neopay_service.initiate_payment(
            db,
            token=token,
            payment_method=body.payment_method,
            customer_email=body.customer_email,
            customer_name=body.customer_name,
            customer_phone=body.customer_phone,
            country=body.country,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        logger.error("Erreur initiation paiement token=%s: %s", token[:8], exc)
        sentry_sdk.capture_exception(exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Erreur temporaire du service de paiement. Veuillez réessayer."
        )


# ─── POST /api/neopay/payment-links/{token}/prepare ──────────────────────────

@router.post("/payment-links/{token}/prepare", summary="Préparer le paiement (Korapay Inline)")
def prepare_payment(
    token: str,
    body: PreparePaymentRequest,
    db: Session = Depends(get_db),
):
    """
    Prépare un PaymentEvent en DB sans appeler l'API Korapay.
    Utilisé par le SDK Korapay Inline Checkout (client-side JS) :
    le client reçoit reference + public_key et initialise le checkout directement.

    Endpoint public — le token du lien est le secret, valable 24h.
    """
    try:
        result = neopay_service.prepare_payment(
            db,
            token=token,
            payment_method=body.payment_method,
            customer_email=body.customer_email,
            customer_name=body.customer_name,
            customer_phone=body.customer_phone,
            country=body.country,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ─── POST /api/neopay/webhooks/korapay ───────────────────────────────────────

@router.post("/webhooks/korapay", summary="Webhook Korapay")
async def webhook_korapay(request: Request, db: Session = Depends(get_db)):
    """
    Reçoit et traite les webhooks Korapay.
    Vérification HMAC obligatoire — toute requête non signée → 401.

    L'activation de l'abonnement ne se fait QUE depuis cet endpoint,
    après vérification de signature réussie.
    """
    raw_body = await request.body()
    signature = request.headers.get("x-korapay-signature", "")

    # ── Vérification HMAC — AVANT tout traitement ────────────────────────────
    if not korapay_service.verify_korapay_signature(raw_body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature invalide"
        )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON invalide")

    extracted = korapay_service.extract_webhook_data(payload)
    webhook_id = extracted.get("webhook_id", "")

    if not webhook_id:
        logger.warning("Webhook Korapay sans référence — payload ignoré")
        return {"status": "ignored"}

    # Traitement asynchrone (idempotent)
    await neopay_service.process_webhook(
        db,
        provider="korapay",
        webhook_id=webhook_id,
        event_type=extracted["event_type"],
        raw_payload=payload,
        extracted=extracted,
    )

    # Korapay exige un 200 pour ne pas retenter (idempotence gérée en DB)
    return {"status": "ok"}


# ─── POST /api/neopay/webhooks/campay ────────────────────────────────────────

@router.post("/webhooks/campay", summary="Webhook CamPay")
async def webhook_campay(request: Request, db: Session = Depends(get_db)):
    """
    Reçoit et traite les webhooks CamPay.
    Vérification de signature obligatoire.

    ⚠️  CamPay est en mode sandbox — les transactions ne sont pas réelles
    tant que CAMPAY_PRODUCTION=false.
    """
    raw_body = await request.body()
    signature = request.headers.get("x-campay-signature", "")

    # ── Vérification signature ───────────────────────────────────────────────
    if not campay_service.verify_campay_signature(raw_body, signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature invalide"
        )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="JSON invalide")

    extracted = campay_service.extract_webhook_data(payload)
    webhook_id = extracted.get("webhook_id", "")

    if not webhook_id:
        return {"status": "ignored"}

    await neopay_service.process_webhook(
        db,
        provider="campay",
        webhook_id=webhook_id,
        event_type=extracted["event_type"],
        raw_payload=payload,
        extracted=extracted,
    )

    return {"status": "ok"}


# ─── Orange Money Manuel ─────────────────────────────────────────────────────

class OmPaymentRequestBody(BaseModel):
    plan: str = "BASIC"
    customer_phone: str

    @field_validator('customer_phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        digits = v.replace(' ', '').replace('-', '')
        if not re.match(r'^6\d{8}$', digits):
            raise ValueError('Numéro invalide — format attendu : 6XXXXXXXX (9 chiffres, commençant par 6)')
        return digits


@router.post("/om-request", summary="Demande paiement Orange Money manuel")
@limiter.limit("3/hour")  # Limite 3 demandes/heure — évite spam inbox admin
async def create_om_request(
    request: Request,
    body: OmPaymentRequestBody,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Enregistre une demande de paiement Orange Money manuel.
    Crée un PaymentEvent 'pending' et alerte l'admin par email.
    L'activation est déclenchée manuellement via /api/neopay/om-approve/{event_id}.
    """
    _ALIASES = {"ESSENTIAL": "BASIC", "BUSINESS": "STANDARD", "ENTERPRISE": "PRO"}
    plan_key = _ALIASES.get(body.plan.upper(), body.plan.upper())

    try:
        plan_config = PLAN_LIMITS.get(PlanType(plan_key))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Plan inconnu : {body.plan}")

    if not plan_config:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Plan {plan_key} non disponible")

    transaction_id = f"om_manual_{_uuid.uuid4().hex}"
    amount = plan_config.get("price_fcfa", 20000)

    event = PaymentEvent(
        transaction_id=transaction_id,
        provider="om_manual",
        tenant_id=current_user.tenant_id,
        plan=plan_key,
        amount=amount,
        currency="XAF",
        payment_method="mobile_money",
        status="pending",
        customer_email=current_user.email,
        customer_phone=body.customer_phone,
        payment_metadata={"customer_name": current_user.full_name or ""},
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    try:
        _nom = current_user.full_name or "\u2014"
        await send_internal_alert(
            subject=f"\U0001f4b0 Paiement OM en attente \u2014 {current_user.full_name or current_user.email}",
            body=(
                f"Tenant ID  : {current_user.tenant_id}\n"
                f"Plan       : {plan_key} ({amount:,} XAF)\n"
                f"T\u00e9l\u00e9phone  : {body.customer_phone}\n"
                f"Email      : {current_user.email}\n"
                f"Nom        : {_nom}\n"
                f"Event ID   : {event.id}\n"
                f"Transaction: {transaction_id}\n\n"
                f"\u2192 Pour approuver :\n"
                f"POST /api/neopay/om-approve/{event.id}"
            ),
        )
    except Exception as alert_exc:
        logger.warning("Alerte email OM non envoy\u00e9e : %s", alert_exc)

    return {
        "status": "pending",
        "event_id": event.id,
        "message": "Demande enregistr\u00e9e. Votre abonnement sera activ\u00e9 dans les 24h apr\u00e8s v\u00e9rification.",
    }


@router.post("/om-approve/{event_id}", summary="Approuver un paiement OM (superadmin)")
async def approve_om_payment(
    event_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_superadmin_user),
):
    """
    Active manuellement l'abonnement d'un client dont le paiement OM a \u00e9t\u00e9 v\u00e9rifi\u00e9.
    D\u00e9clenche la m\u00eame logique d'activation que les webhooks provider.
    Idempotent \u2014 sans risque si appel\u00e9 deux fois.
    """
    try:
        result = await neopay_service.approve_manual_payment(db, event_id)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ─── GET /api/neopay/payments — Superadmin ───────────────────────────────────

@router.get("/payments", summary="Historique paiements (superadmin)")
def list_payments(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _=Depends(get_superadmin_user),
):
    """Liste tous les PaymentEvents — superadmin uniquement."""
    payments = (
        db.query(PaymentEvent)
        .order_by(PaymentEvent.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(PaymentEvent).count()
    return {
        "total": total,
        "payments": [
            {
                "id": p.id,
                "transaction_id": p.transaction_id,
                "provider": p.provider,
                "tenant_id": p.tenant_id,
                "plan": p.plan,
                "amount": p.amount,
                "currency": p.currency,
                "payment_method": p.payment_method,
                "status": p.status,
                "customer_email": p.customer_email,
                "created_at": p.created_at.isoformat(),
            }
            for p in payments
        ],
    }


# ─── GET /api/neopay/webhook-events — Superadmin ─────────────────────────────

@router.get("/webhook-events", summary="Historique webhooks (superadmin)")
def list_webhook_events(
    status_filter: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    _=Depends(get_superadmin_user),
):
    """Liste les WebhookEvents — superadmin uniquement. Utile pour le debug."""
    query = db.query(WebhookEvent).order_by(WebhookEvent.created_at.desc())
    if status_filter:
        query = query.filter(WebhookEvent.status == status_filter)
    events = query.limit(limit).all()

    return [
        {
            "id": e.id,
            "webhook_id": e.webhook_id,
            "provider": e.provider,
            "event_type": e.event_type,
            "status": e.status,
            "attempts": e.attempts,
            "last_attempt_at": e.last_attempt_at.isoformat() if e.last_attempt_at else None,
            "processed_at": e.processed_at.isoformat() if e.processed_at else None,
            "error_detail": e.error_detail,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


# ─── POST /api/neopay/payment-links/generate — Auto à l'inscription ──────────

@router.post(
    "/generate-for-tenant/{tenant_id}",
    summary="Générer un lien de paiement pour un tenant (superadmin)",
)
def generate_for_tenant(
    tenant_id: int,
    body: CreatePaymentLinkRequest,
    db: Session = Depends(get_db),
    _=Depends(get_superadmin_user),
):
    """
    Génère un lien de paiement pour un tenant spécifique.
    Utilisé par l'admin ou automatiquement à l'inscription.
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant introuvable")

    try:
        link = neopay_service.create_payment_link(db, tenant_id=tenant_id, plan=body.plan)
        pay_url = f"{neopay_service._get_frontend_url()}/pay/{link.token}"
        return {
            "token": link.token,
            "payment_url": pay_url,
            "plan": link.plan,
            "amount": link.amount,
            "currency": link.currency,
            "expires_at": link.expires_at.isoformat(),
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
