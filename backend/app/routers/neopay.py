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
import secrets
import uuid as _uuid
from typing import Optional
from datetime import datetime, timedelta

import sentry_sdk
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, get_superadmin_user
from app.models import PaymentLink, PaymentEvent, WebhookEvent, Tenant, PlanType, PLAN_LIMITS
from app.services import neopay_service, korapay_service, campay_service
from app.services.email_service import send_internal_alert
from app.limiter import limiter

_FRONTEND_URL = "https://neobot-ai.com"
_ADMIN_URL    = f"{_FRONTEND_URL}/admin"


def _generate_neo_ref(db: Session) -> str:
    """Génère une référence NEO-YYYY-NNNN séquentielle et unique."""
    year = datetime.utcnow().year
    prefix = f"NEO-{year}-"
    existing = db.query(PaymentEvent.neo_ref).filter(
        PaymentEvent.neo_ref.like(f"{prefix}%")
    ).all()
    max_n = 0
    for (ref,) in existing:
        if ref:
            try:
                n = int(ref[len(prefix):])
                if n > max_n:
                    max_n = n
            except (ValueError, TypeError):
                pass
    return f"{prefix}{max_n + 1:04d}"


def _build_confirm_email(
    neo_ref: str,
    customer_name: str,
    customer_email: str,
    plan_label: str,
    amount: int,
    payment_method: str,
    customer_phone: str,
    confirm_url: str,
) -> str:
    """Construit le corps de l'email admin avec 2 boutons."""
    method_label = "Orange Money" if "om" in payment_method.lower() else (
        "MTN MoMo" if "momo" in payment_method.lower() or "mtn" in payment_method.lower() else payment_method
    )
    verify_account = "Vérifiez votre compte Orange Money" if "om" in payment_method.lower() else (
        "Vérifiez votre compte MTN MoMo" if "mtn" in payment_method.lower() or "momo" in payment_method.lower()
        else "Vérifiez le paiement"
    )
    now = datetime.utcnow().strftime("%d/%m/%Y à %Hh%M")
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 NOUVEAU PAIEMENT — {neo_ref}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Client      : {customer_name or '—'}\n"
        f"Email       : {customer_email or '—'}\n"
        f"Plan        : {plan_label} — {amount:,} XAF/mois\n"
        f"Moyen       : {method_label}\n"
        f"N° paiement : {customer_phone or '—'}\n"
        f"Date        : {now} UTC\n\n"
        f"🔍 {verify_account} pour le numéro {customer_phone}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ CONFIRMER — activation immédiate :\n"
        f"{confirm_url}\n\n"
        f"⚙️  OUVRIR LE PANEL ADMIN :\n"
        f"{_ADMIN_URL}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )

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
    payment_method: str = "om_manual"  # om_manual | momo_manual

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

    # G\u00e9n\u00e9rer ref NEO + token de confirmation 1-clic
    neo_ref = _generate_neo_ref(db)
    confirm_token = secrets.token_urlsafe(32)
    confirm_expires = datetime.utcnow() + timedelta(days=7)

    event = PaymentEvent(
        transaction_id=transaction_id,
        provider="om_manual",
        tenant_id=current_user.tenant_id,
        plan=plan_key,
        amount=amount,
        currency="XAF",
        payment_method=body.payment_method if hasattr(body, "payment_method") else "mobile_money",
        status="pending",
        customer_email=current_user.email,
        customer_phone=body.customer_phone,
        payment_metadata={"customer_name": current_user.full_name or ""},
        neo_ref=neo_ref,
        confirm_token=confirm_token,
        confirm_token_expires_at=confirm_expires,
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    plan_label = plan_config.get("display_name", plan_key)
    confirm_url = f"{_FRONTEND_URL}/api/neopay/confirm-payment?token={confirm_token}"
    try:
        await send_internal_alert(
            subject=f"\ud83d\udcb0 Paiement OM en attente \u2014 {neo_ref} \u2014 {current_user.full_name or current_user.email}",
            body=_build_confirm_email(
                neo_ref=neo_ref,
                customer_name=current_user.full_name or "\u2014",
                customer_email=current_user.email,
                plan_label=plan_label,
                amount=amount,
                payment_method=event.payment_method or "mobile_money",
                customer_phone=body.customer_phone,
                confirm_url=confirm_url,
            ),
        )
    except Exception as alert_exc:
        logger.warning("Alerte email OM non envoy\u00e9e : %s", alert_exc)

    return {
        "status": "pending",
        "event_id": event.id,
        "neo_ref": neo_ref,
        "message": f"Demande {neo_ref} enregistr\u00e9e. Votre abonnement sera activ\u00e9 dans les 24h apr\u00e8s v\u00e9rification.",
    }


# ─── GET /api/neopay/confirm-payment — Activation 1-clic depuis email ─────────

@router.get("/confirm-payment", summary="Confirmer un paiement via lien email (sans login)")
async def confirm_payment_by_token(token: str, db: Session = Depends(get_db)):
    """
    Endpoint public — lien reçu par email admin.
    Valide le token, active le compte du client, consume le token (usage unique).
    Retourne une page HTML de confirmation.
    """
    if not token or len(token) < 10:
        return HTMLResponse(_confirm_html("❌ Lien invalide", "Ce lien de confirmation est invalide.", error=True))

    event = db.query(PaymentEvent).filter(
        PaymentEvent.confirm_token == token,
        PaymentEvent.confirmed_at == None,
    ).first()

    if not event:
        return HTMLResponse(_confirm_html(
            "❌ Lien déjà utilisé ou invalide",
            "Ce lien a déjà été utilisé ou n'existe pas.",
            error=True,
        ))

    if event.confirm_token_expires_at and event.confirm_token_expires_at < datetime.utcnow():
        return HTMLResponse(_confirm_html(
            "⏰ Lien expiré",
            f"Ce lien a expiré. Référence : {event.neo_ref or event.transaction_id}. Approuvez manuellement depuis le panel admin.",
            error=True,
        ))

    try:
        await neopay_service.approve_manual_payment(db, event.id)
    except Exception as exc:
        logger.error("confirm_payment_by_token: erreur approve event %s: %s", event.id, exc)
        return HTMLResponse(_confirm_html(
            "⚠️ Erreur lors de l'activation",
            f"Le compte n'a pas pu être activé automatiquement. Approuvez manuellement depuis le panel admin. Réf : {event.neo_ref or '—'}",
            error=True,
        ))

    # Consommer le token — usage unique
    event.confirmed_at = datetime.utcnow()
    event.confirm_token = None
    event.status = "confirmed"
    db.commit()

    neo = event.neo_ref or "—"
    email = event.customer_email or "—"
    logger.info("✅ Paiement %s confirmé via lien email (event_id=%s)", neo, event.id)

    return HTMLResponse(_confirm_html(
        f"✅ Compte activé — {neo}",
        f"Le compte a été activé avec succès.<br>Un email de bienvenue a été envoyé à <strong>{email}</strong>.",
        neo_ref=neo,
        admin_url=_ADMIN_URL,
    ))


def _confirm_html(title: str, message: str, error: bool = False, neo_ref: str = "", admin_url: str = "") -> str:
    color = "#ef4444" if error else "#22c55e"
    extra = ""
    if admin_url:
        extra = f'<p style="margin-top:24px"><a href="{admin_url}" style="background:#6366f1;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;font-weight:600;">⚙️ Ouvrir le panel admin</a></p>'
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>NéoBot — {title}</title>
  <style>body{{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;display:flex;align-items:center;justify-content:center;min-height:100vh;margin:0}}
  .card{{background:#1e293b;border:1px solid {color}40;border-radius:16px;padding:40px;max-width:480px;width:90%;text-align:center}}
  h1{{color:{color};font-size:1.6rem;margin-bottom:16px}}
  p{{color:#94a3b8;line-height:1.6}}
  .ref{{font-size:1.1rem;font-weight:700;color:#f1f5f9;margin:16px 0}}
  </style>
</head>
<body>
  <div class="card">
    <h1>{title}</h1>
    <p>{message}</p>
    {"<p class='ref'>Référence : " + neo_ref + "</p>" if neo_ref else ""}
    {extra}
  </div>
</body>
</html>"""


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


def _fmt_dt(dt) -> str | None:
    if dt is None:
        return None
    try:
        from datetime import timezone as _tz
        if hasattr(dt, 'utcoffset') and dt.utcoffset() is not None:
            dt = dt.astimezone(_tz.utc).replace(tzinfo=None)
    except Exception:
        pass
    return dt.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'


# ─── GET /api/neopay/bot-orders — Commandes WhatsApp en attente ───────────────

@router.get("/bot-orders", summary="Commandes WhatsApp bot en attente (superadmin)")
def list_bot_orders(db: Session = Depends(get_db), _=Depends(get_superadmin_user)):
    try:
        events = (
            db.query(PaymentEvent)
            .filter(PaymentEvent.status == "bot_pending")
            .order_by(PaymentEvent.created_at.desc())
            .all()
        )
        result = []
        for e in events:
            try:
                meta = e.payment_metadata if isinstance(e.payment_metadata, dict) else {}
                result.append({
                    "id": e.id,
                    "transaction_id": e.transaction_id or "—",
                    "neo_ref": getattr(e, "neo_ref", None) or "—",
                    "customer_name": meta.get("customer_name", "—"),
                    "customer_email": e.customer_email or "—",
                    "customer_phone": e.customer_phone or "—",
                    "plan": e.plan,
                    "amount": e.amount,
                    "currency": e.currency,
                    "created_at": _fmt_dt(e.created_at),
                })
            except Exception as row_err:
                logger.warning("bot-orders: erreur sérialisation event id=%s: %s", getattr(e, "id", "?"), row_err)
        return result
    except Exception as exc:
        logger.error("bot-orders: erreur liste: %s", exc, exc_info=True)
        return []


@router.post("/bot-orders/{order_id}/mark-done", summary="Marquer commande bot comme traitée (superadmin)")
def mark_bot_order_done(order_id: int, db: Session = Depends(get_db), _=Depends(get_superadmin_user)):
    event = db.query(PaymentEvent).filter(
        PaymentEvent.id == order_id,
        PaymentEvent.status == "bot_pending",
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Commande introuvable ou déjà traitée")
    event.status = "confirmed"
    event.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "done", "id": order_id}


@router.delete("/bot-orders/{order_id}", summary="Annuler commande bot (superadmin)")
def cancel_bot_order(order_id: int, db: Session = Depends(get_db), _=Depends(get_superadmin_user)):
    event = db.query(PaymentEvent).filter(
        PaymentEvent.id == order_id,
        PaymentEvent.status == "bot_pending",
    ).first()
    if not event:
        raise HTTPException(status_code=404, detail="Commande introuvable")
    event.status = "cancelled"
    event.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "cancelled"}


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
