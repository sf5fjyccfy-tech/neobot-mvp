"""
NeopPay — Orchestrateur de paiement NeoBot.
Décide quel provider utiliser, gère les payment links, active les abonnements,
gère le retry automatique des webhooks échoués.

Règle absolue : L'activation d'abonnement ne se fait QUE via webhook vérifié.
"""
import asyncio
import logging
import os
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

import sentry_sdk
from sqlalchemy.orm import Session

from ..models import (
    PaymentLink,
    PaymentEvent,
    WebhookEvent,
    Tenant,
    Subscription,
    PlanType,
    PLAN_LIMITS,
)
from . import korapay_service
from .email_service import send_internal_alert, send_payment_confirmation

logger = logging.getLogger(__name__)

# ─── Constantes ───────────────────────────────────────────────────────────────

WEBHOOK_MAX_ATTEMPTS = 12           # Max tentatives sur 1h (toutes les 5 min)
WEBHOOK_RETRY_INTERVAL_SEC = 300    # 5 minutes entre chaque retry
WEBHOOK_ALERT_AFTER_SEC = 3600      # Alerte Sentry + Brevo après 1h d'échec


def _get_frontend_url() -> str:
    return os.environ.get("FRONTEND_URL", "https://neobot.app")


def _get_backend_url() -> str:
    return os.environ.get("BACKEND_URL", os.environ.get("WHATSAPP_BACKEND_URL", "https://api.neobot.app"))


# ─── Routing provider ─────────────────────────────────────────────────────────

def _choose_provider(country: str, payment_method: str) -> str:
    """
    Provider unique : Korapay.
    CamPay suspendu — documents en attente.
    """
    return "korapay"


# ─── Création d'un payment link ───────────────────────────────────────────────

def create_payment_link(
    db: Session,
    *,
    tenant_id: int,
    plan: str,
) -> PaymentLink:
    """
    Génère un lien de paiement unique valide 24h.
    URL publique : {FRONTEND_URL}/pay/{token}

    Le token est un hex 32 octets (256 bits d'entropie — non devinable).
    """
    plan_config = PLAN_LIMITS.get(PlanType(plan.upper()))
    if not plan_config:
        raise ValueError(f"Plan inconnu : {plan}")

    # Korapay traite en NGN — on utilise le prix NGN (converti depuis XAF)
    amount = plan_config.get("price_ngn", 0)
    if amount <= 0:
        raise ValueError(f"Plan {plan} non facturable (prix 0 ou interne)")

    token = secrets.token_hex(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)

    link = PaymentLink(
        token=token,
        tenant_id=tenant_id,
        plan=plan.upper(),
        amount=amount,
        currency="NGN",
        status="pending",
        expires_at=expires_at,
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    logger.info("Payment link créé — tenant %s, plan %s, token %s", tenant_id, plan, token[:8] + "...")
    return link


def get_payment_link(db: Session, token: str) -> Optional[PaymentLink]:
    """Récupère un lien de paiement par token. Retourne None si introuvable ou expiré."""
    link = db.query(PaymentLink).filter(PaymentLink.token == token).first()
    if not link:
        return None

    # Marquer comme expiré si dépassé
    if link.status == "pending" and link.expires_at < datetime.utcnow():
        link.status = "expired"
        db.commit()
        return None

    return link


# ─── Initiation d'un paiement ─────────────────────────────────────────────────

async def initiate_payment(
    db: Session,
    *,
    token: str,
    payment_method: str,   # "card" | "mobile_money"
    customer_email: str,
    customer_name: str,
    customer_phone: Optional[str] = None,
    country: str = "CM",
) -> dict:
    """
    Initie un paiement pour un payment link donné.
    Choisit le provider selon le contexte (pays + mode paiement).
    Crée un PaymentEvent avec status "initiated".

    Returns:
        { checkout_url: str, provider: str, reference: str }
    """
    link = get_payment_link(db, token)
    if not link:
        raise ValueError("Lien de paiement introuvable ou expiré")
    if link.status != "pending":
        raise ValueError(f"Lien de paiement déjà {link.status}")

    provider = _choose_provider(country, payment_method)
    # Korapay limite les références à 50 chars — on tronque ici pour que
    # PaymentEvent.transaction_id corresponde exactement à ce que Korapay
    # renvoie dans le webhook (sinon l'activation abonnement ne se déclenche pas)
    reference = link.token[:50]

    # Gérer le retry : si un event "failed" existe sur ce token, on le supprime
    # avant de recréer (UNIQUE constraint sur transaction_id).
    # Si "paid", on rejette — paiement déjà effectué.
    existing_event = db.query(PaymentEvent).filter(PaymentEvent.transaction_id == reference).first()
    if existing_event:
        if existing_event.status == "paid":
            raise ValueError("Ce paiement a déjà été effectué avec succès")
        # Pour tout autre statut (failed, initiated, pending), on supprime pour permettre le retry
        db.delete(existing_event)
        db.flush()

    # Créer l'événement de paiement en DB
    event = PaymentEvent(
        transaction_id=reference,
        provider=provider,
        payment_link_id=link.id,
        tenant_id=link.tenant_id,
        plan=link.plan,
        amount=link.amount,
        currency=link.currency,
        payment_method=payment_method,
        status="initiated",
        customer_email=customer_email,
        customer_phone=customer_phone,
        payment_metadata={"country": country},
    )
    db.add(event)
    db.commit()

    notification_url = f"{_get_backend_url()}/api/neopay/webhooks/{provider}"
    redirect_url = f"{_get_frontend_url()}/pay/{token}/callback"

    # ── Appel provider ────────────────────────────────────────────────────────
    try:
        if provider == "korapay":
            result = await korapay_service.initialize_charge(
                reference=reference,
                amount=link.amount,
                currency=link.currency,
                customer_email=customer_email,
                customer_name=customer_name,
                redirect_url=redirect_url,
                notification_url=notification_url,
                metadata={"plan": link.plan, "tenant_id": link.tenant_id, "payment_link_id": link.id},
            )
            checkout_url = result.get("data", {}).get("checkout_url") or result.get("data", {}).get("payment_url", "")

        else:
            raise ValueError(f"Provider non supporté : {provider}")

        event.status = "pending"
        db.commit()

        return {"checkout_url": checkout_url, "provider": provider, "reference": reference}

    except Exception as exc:
        logger.error("Échec initiation paiement %s via %s: %s", reference, provider, exc)
        sentry_sdk.capture_exception(exc)

        # Alerte Sentry + email sur erreur Korapay
        await send_internal_alert(
            subject="⚠️ NeopPay — Erreur Korapay",
            body=f"Référence: {reference}\nTenant: {link.tenant_id}\nErreur: {exc}"
        )

        event.status = "failed"
        event.failure_reason = str(exc)
        db.commit()
        raise


# ─── Traitement d'un webhook entrant ─────────────────────────────────────────

async def process_webhook(
    db: Session,
    *,
    provider: str,
    webhook_id: str,
    event_type: str,
    raw_payload: dict,
    extracted: dict,
) -> bool:
    """
    Traite un webhook entrant avec idempotence stricte.
    Crée un WebhookEvent en DB, active l'abonnement si le paiement est confirmé.

    Returns:
        True si traité avec succès, False si erreur (déclenche retry)
    """
    # ── Idempotence : déjà traité ? ───────────────────────────────────────────
    existing = db.query(WebhookEvent).filter(
        WebhookEvent.webhook_id == webhook_id
    ).first()

    if existing and existing.status in ("processed", "skipped"):
        logger.info("Webhook déjà traité — id: %s, status: %s", webhook_id, existing.status)
        return True

    # ── Enregistrement en DB ──────────────────────────────────────────────────
    if not existing:
        wh_event = WebhookEvent(
            webhook_id=webhook_id,
            provider=provider,
            event_type=event_type,
            status="pending",
            raw_payload=raw_payload,
            attempts=0,
        )
        db.add(wh_event)
        db.commit()
        db.refresh(wh_event)
    else:
        wh_event = existing

    wh_event.attempts += 1
    wh_event.last_attempt_at = datetime.utcnow()
    db.commit()

    # ── Traitement métier ─────────────────────────────────────────────────────
    try:
        raw_status = extracted.get("status", "")
        is_success = (provider == "korapay" and raw_status in ("success", "successful"))

        if is_success:
            transaction_id = extracted["transaction_id"]
            await _activate_subscription_from_payment(db, transaction_id=transaction_id, provider=provider)

        wh_event.status = "processed"
        wh_event.processed_at = datetime.utcnow()
        db.commit()
        return True

    except Exception as exc:
        logger.error("Échec traitement webhook %s: %s", webhook_id, exc)
        sentry_sdk.capture_exception(exc)
        wh_event.status = "failed"
        wh_event.error_detail = str(exc)
        db.commit()
        return False


# ─── Activation d'abonnement ─────────────────────────────────────────────────

async def _activate_subscription_from_payment(
    db: Session,
    *,
    transaction_id: str,
    provider: str,
) -> None:
    """
    Active l'abonnement d'un tenant après confirmation d'un paiement réussi.
    UNIQUEMENT appelée depuis process_webhook — jamais via endpoint direct.

    Met à jour :
    - payment_event.status → "confirmed"
    - payment_link.status  → "paid"
    - tenant.plan, tenant.is_trial, tenant.trial_ends_at
    - subscription.plan, subscription.status, subscription.is_trial
    """
    payment = db.query(PaymentEvent).filter(
        PaymentEvent.transaction_id == transaction_id
    ).first()

    if not payment:
        logger.warning("PaymentEvent introuvable pour transaction %s — pas d'activation", transaction_id)
        return

    if payment.status == "confirmed":
        logger.info("Paiement %s déjà confirmé — idempotence", transaction_id)
        return

    # Mettre à jour l'événement paiement
    payment.status = "confirmed"
    payment.provider_raw_status = "confirmed"

    # Mettre à jour le payment link
    if payment.payment_link_id:
        link = db.query(PaymentLink).filter(PaymentLink.id == payment.payment_link_id).first()
        if link:
            link.status = "paid"
            link.paid_at = datetime.utcnow()

    # ── Activer le plan sur le Tenant ─────────────────────────────────────────
    tenant = db.query(Tenant).filter(Tenant.id == payment.tenant_id).first()
    if not tenant:
        raise ValueError(f"Tenant {payment.tenant_id} introuvable")

    plan_key = payment.plan.upper()
    plan_config = PLAN_LIMITS.get(PlanType(plan_key))
    if not plan_config:
        raise ValueError(f"Plan {plan_key} inconnu lors de l'activation")

    old_plan = tenant.plan
    tenant.plan = PlanType(plan_key)
    tenant.is_trial = False
    tenant.trial_ends_at = None
    tenant.messages_limit = plan_config["whatsapp_messages"] if plan_config["whatsapp_messages"] > 0 else 999999

    # ── Mettre à jour la Subscription ────────────────────────────────────────
    subscription = db.query(Subscription).filter(Subscription.tenant_id == payment.tenant_id).first()
    now = datetime.utcnow()
    if subscription:
        subscription.plan = plan_key.lower()
        subscription.status = "active"
        subscription.is_trial = False
        subscription.subscription_start_date = now
        subscription.next_billing_date = now + timedelta(days=30)
        subscription.last_billing_date = now
    else:
        # Créer la subscription si elle n'existe pas
        subscription = Subscription(
            tenant_id=payment.tenant_id,
            plan=plan_key.lower(),
            status="active",
            is_trial=False,
            trial_start_date=now,
            trial_end_date=now,
            subscription_start_date=now,
            next_billing_date=now + timedelta(days=30),
            last_billing_date=now,
            auto_renew=True,
        )
        db.add(subscription)

    db.commit()

    logger.info(
        "✅ Abonnement activé — tenant %s: %s → %s (provider: %s, ref: %s)",
        payment.tenant_id, old_plan, plan_key, provider, transaction_id
    )

    # ── Notifications ─────────────────────────────────────────────────────────
    await send_payment_confirmation(
        tenant_email=tenant.email,
        tenant_name=tenant.name,
        plan=plan_config["display_name"],
        amount=payment.amount,
        currency=payment.currency,
    )


# ─── Retry automatique des webhooks échoués ──────────────────────────────────

async def retry_failed_webhooks(db: Session) -> int:
    """
    Rejoue les webhooks en status "failed" ou "pending" depuis trop longtemps.
    Appelé par le scheduler toutes les 5 minutes.
    Après WEBHOOK_MAX_ATTEMPTS : alerte Sentry + email Brevo.

    Returns:
        Nombre de webhooks retentés
    """
    cutoff = datetime.utcnow() - timedelta(seconds=WEBHOOK_RETRY_INTERVAL_SEC)

    pending_webhooks = db.query(WebhookEvent).filter(
        WebhookEvent.status.in_(["pending", "failed"]),
        WebhookEvent.attempts < WEBHOOK_MAX_ATTEMPTS,
        # Ne retry que les webhooks dont la dernière tentative date d'au moins RETRY_INTERVAL
        (WebhookEvent.last_attempt_at == None) |
        (WebhookEvent.last_attempt_at < cutoff),
    ).all()

    retried = 0
    for wh in pending_webhooks:
        logger.info("Retry webhook %s (tentative %d)", wh.webhook_id, wh.attempts + 1)

        # Extraire les données normalisées depuis le payload stocké
        if wh.provider == "korapay":
            extracted = korapay_service.extract_webhook_data(wh.raw_payload)
        else:
            continue

        success = await process_webhook(
            db,
            provider=wh.provider,
            webhook_id=wh.webhook_id,
            event_type=wh.event_type,
            raw_payload=wh.raw_payload,
            extracted=extracted,
        )
        if success:
            retried += 1

    # ── Alerter pour les webhooks qui ont dépassé le maximum de tentatives ────
    dead_webhooks = db.query(WebhookEvent).filter(
        WebhookEvent.status == "failed",
        WebhookEvent.attempts >= WEBHOOK_MAX_ATTEMPTS,
        WebhookEvent.error_detail != None,
        # Alerter une seule fois — marquer "skipped" après alerte
    ).all()

    for wh in dead_webhooks:
        logger.error(
            "Webhook %s échec définitif après %d tentatives — alerte déclenchée",
            wh.webhook_id, wh.attempts
        )
        sentry_sdk.capture_message(
            f"NeopPay — Webhook mort après {wh.attempts} tentatives",
            level="error",
            extras={
                "webhook_id": wh.webhook_id,
                "provider": wh.provider,
                "event_type": wh.event_type,
                "last_error": wh.error_detail,
            }
        )
        await send_internal_alert(
            subject=f"🔴 NeopPay — Webhook mort ({wh.provider})",
            body=(
                f"Webhook ID: {wh.webhook_id}\n"
                f"Provider: {wh.provider}\n"
                f"Type: {wh.event_type}\n"
                f"Tentatives: {wh.attempts}\n"
                f"Dernière erreur: {wh.error_detail}\n"
                f"Créé le: {wh.created_at}"
            ),
        )
        # Marquer pour ne plus alerter
        wh.status = "skipped"
        db.commit()

    return retried
