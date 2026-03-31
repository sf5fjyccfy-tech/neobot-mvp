"""
Service Korapay — Provider de paiement primaire NeopPay.
Gère : création de charges (Mobile Money + Carte), vérification HMAC des webhooks.

Clés lues UNIQUEMENT depuis les variables d'environnement.
Jamais de données bancaires (carte, CVV) stockées ou loggées.
"""
import hashlib
import hmac
import os
import logging
from typing import Optional
import httpx
import sentry_sdk

logger = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────

KORAPAY_BASE_URL = "https://api.korapay.com/merchant/api/v1"


def _get_secret_key() -> str:
    key = os.environ.get("KORAPAY_SECRET_KEY", "")
    if not key:
        raise RuntimeError("KORAPAY_SECRET_KEY manquante dans les variables d'environnement")
    return key


def _get_public_key() -> str:
    key = os.environ.get("KORAPAY_PUBLIC_KEY", "")
    if not key:
        raise RuntimeError("KORAPAY_PUBLIC_KEY manquante dans les variables d'environnement")
    return key


def _get_encryption_key() -> str:
    key = os.environ.get("KORAPAY_ENCRYPTION_KEY", "")
    if not key:
        raise RuntimeError("KORAPAY_ENCRYPTION_KEY manquante dans les variables d'environnement")
    return key


# ─── Vérification HMAC (webhook) ──────────────────────────────────────────────

def verify_korapay_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Vérifie la signature HMAC-SHA512 d'un webhook Korapay.
    Le header attendu est : X-Korapay-Signature
    La clé de signature est l'encryption key Korapay.

    Rejette TOUTE requête dont la signature ne correspond pas.
    Toute tentative invalide est loggée via Sentry.
    """
    if not signature_header:
        logger.warning("Webhook Korapay reçu sans signature")
        sentry_sdk.capture_message(
            "Korapay webhook sans signature X-Korapay-Signature",
            level="warning"
        )
        return False

    try:
        encryption_key = _get_encryption_key()
        expected = hmac.new(
            encryption_key.encode("utf-8"),
            raw_body,
            hashlib.sha512
        ).hexdigest()

        # Comparaison en temps constant pour éviter timing attacks
        valid = hmac.compare_digest(expected.lower(), signature_header.lower())
        if not valid:
            logger.warning("Signature Korapay invalide — potentielle tentative d'injection")
            sentry_sdk.capture_message(
                "Korapay webhook : signature HMAC invalide",
                level="warning",
                extras={"signature_received": signature_header[:20] + "..."}
            )
        return valid
    except Exception as exc:
        logger.error("Erreur lors de la vérification de signature Korapay: %s", exc)
        sentry_sdk.capture_exception(exc)
        return False


# ─── Initialisation d'une charge ──────────────────────────────────────────────

async def initialize_charge(
    *,
    reference: str,
    amount: int,
    currency: str,
    customer_email: str,
    customer_name: str,
    redirect_url: str,
    notification_url: str,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Crée une charge Korapay (checkout unifié carte + Mobile Money).
    Retourne la réponse brute du provider.

    Args:
        reference:        Référence unique côté NeoBot (payment_link.token)
        amount:           Montant en unité de devise (ex: 20000 pour 20 000 XAF)
        currency:         Code devise ISO 4217 (ex: XAF, NGN, GHS)
        customer_email:   Email du client
        customer_name:    Nom du client
        redirect_url:     URL de redirection après paiement
        notification_url: URL du webhook NeopPay
        metadata:         Données custom (plan, tenant_id, etc.)

    Raises:
        httpx.HTTPStatusError: Si l'API Korapay renvoie une erreur HTTP
        RuntimeError: Si les clés d'environnement sont manquantes
    """
    payload = {
        # Korapay limite la reference à 50 chars — on tronque le token (256-bit entropy
        # réduit à ~200 bits, toujours unique pour nos volumétries)
        "reference": reference[:50],
        "amount": amount,
        "currency": currency,
        "redirect_url": redirect_url,
        "notification_url": notification_url,
        "customer": {
            "email": customer_email,
            "name": customer_name,
        },
    }
    if metadata:
        payload["metadata"] = metadata

    headers = {
        "Authorization": f"Bearer {_get_secret_key()}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{KORAPAY_BASE_URL}/charges/initialize",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    logger.info("Korapay charge créée — ref: %s, amount: %s %s", reference, amount, currency)
    return data


# ─── Vérification du statut d'une transaction ─────────────────────────────────

async def verify_transaction(reference: str) -> dict:
    """
    Vérifie le statut d'une transaction Korapay via l'API (pour réconciliation).
    Utilisé en fallback si le webhook n'est pas reçu dans les temps.

    Returns:
        dict avec au moins les clés : status, amount, currency, reference
    """
    headers = {
        "Authorization": f"Bearer {_get_secret_key()}",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{KORAPAY_BASE_URL}/charges/{reference}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


# ─── Extraction des données d'un webhook Korapay ─────────────────────────────

def extract_webhook_data(payload: dict) -> dict:
    """
    Normalise le payload webhook Korapay vers notre format interne.
    Korapay envoie : event, data.reference, data.amount, data.status, data.customer

    Returns:
        {
          webhook_id:       str (data.reference — unique par transaction)
          event_type:       str (ex: "charge.completed")
          transaction_id:   str
          amount:           int
          currency:         str
          status:           str (korapay raw status)
          customer_email:   str | None
          metadata:         dict | None
        }
    """
    data = payload.get("data", {})
    return {
        "webhook_id":     data.get("reference", ""),
        "event_type":     payload.get("event", "unknown"),
        "transaction_id": data.get("reference", ""),
        "amount":         data.get("amount", 0),
        "currency":       data.get("currency", "XAF"),
        "status":         data.get("status", "unknown"),
        "customer_email": data.get("customer", {}).get("email"),
        "metadata":       data.get("metadata"),
    }
