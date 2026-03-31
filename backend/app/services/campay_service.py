"""
Service CamPay — Provider secondaire NeopPay (Mobile Money Cameroun).
Gère : MTN Mobile Money + Orange Money Cameroun.

⚠️  PRODUCTION DÉSACTIVÉE — CamPay exige une URL de site web valide.
    Dès que neobot.app est hébergé et le domaine actif :
    1. Créer un compte CamPay production sur https://campay.net
    2. Renseigner CAMPAY_USERNAME, CAMPAY_PASSWORD dans .env
    3. Passer CAMPAY_PRODUCTION=true dans .env

    En attendant : sandbox only, jamais de vraies transactions.
"""
import os
import hashlib
import hmac
import logging
from typing import Optional
import httpx
import sentry_sdk

logger = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────

CAMPAY_SANDBOX_URL    = "https://demo.campay.net/api"
CAMPAY_PRODUCTION_URL = "https://api.campay.net/api"


def _is_production() -> bool:
    """
    CamPay ne passe en production QUE si le flag est explicitement 'true'
    ET que les credentials de production sont présents.
    """
    flag = os.environ.get("CAMPAY_PRODUCTION", "false").lower()
    if flag != "true":
        return False
    # Double-check : on ne passe pas en prod sans token
    return bool(os.environ.get("CAMPAY_USERNAME") and os.environ.get("CAMPAY_PASSWORD"))


def _get_base_url() -> str:
    return CAMPAY_PRODUCTION_URL if _is_production() else CAMPAY_SANDBOX_URL


def _get_username() -> str:
    key = os.environ.get("CAMPAY_USERNAME", "")
    if not key:
        raise RuntimeError("CAMPAY_USERNAME manquant dans les variables d'environnement")
    return key


def _get_password() -> str:
    key = os.environ.get("CAMPAY_PASSWORD", "")
    if not key:
        raise RuntimeError("CAMPAY_PASSWORD manquant dans les variables d'environnement")
    return key


# ─── Authentification CamPay (token Bearer) ──────────────────────────────────

async def _get_access_token() -> str:
    """
    Obtient un token d'accès CamPay via username/password.
    Le token expire — à obtenir à chaque appel (ou mettre en cache si besoin perf).
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{_get_base_url()}/user/token/",
            data={
                "username": _get_username(),
                "password": _get_password(),
            },
        )
        response.raise_for_status()
        data = response.json()
        token = data.get("token")
        if not token:
            raise RuntimeError("CamPay n'a pas retourné de token d'accès")
        return token


# ─── Création d'une collecte Mobile Money ────────────────────────────────────

async def initialize_collection(
    *,
    reference: str,
    amount: int,
    currency: str = "XAF",
    phone_number: str,
    description: str,
    redirect_url: str,
    webhook_url: str,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Déclenche une collecte Mobile Money via CamPay.
    Supporte MTN Mobile Money et Orange Money Cameroun.

    Args:
        reference:    Référence unique NeoBot (payment_link.token)
        amount:       Montant en XAF
        phone_number: Numéro de téléphone du payeur (format: 6XXXXXXXX)
        description:  Description affichée sur le prompt paiement
        webhook_url:  URL de callback NeopPay

    ⚠️  En mode sandbox, les transactions ne sont pas réelles.
    """
    if _is_production():
        logger.warning("CamPay initialisé en mode PRODUCTION")
    else:
        logger.info("CamPay : requête sandbox (aucune transaction réelle)")

    token = await _get_access_token()
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
    }

    payload = {
        "amount": str(amount),
        "currency": currency,
        "from": phone_number,
        "description": description,
        "external_reference": reference,
        "redirect_url": redirect_url,
        "webhook": webhook_url,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{_get_base_url()}/collect/",
            json=payload,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

    logger.info(
        "CamPay collection initiée — ref: %s, mode: %s",
        reference,
        "production" if _is_production() else "sandbox"
    )
    return data


# ─── Vérification du statut d'une transaction ─────────────────────────────────

async def verify_transaction(reference: str) -> dict:
    """Vérifie le statut d'une transaction CamPay (réconciliation)."""
    token = await _get_access_token()
    headers = {"Authorization": f"Token {token}"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{_get_base_url()}/transaction/{reference}/",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


# ─── Vérification de signature webhook CamPay ────────────────────────────────

def verify_campay_signature(raw_body: bytes, signature_header: str) -> bool:
    """
    Vérifie la signature du webhook CamPay.
    CamPay utilise HMAC-SHA256 avec le mot de passe comme clé.

    TODO: Confirmer le mécanisme exact de signature CamPay lors de l'activation
    production (la doc sandbox est moins précise sur ce point).
    """
    if not signature_header:
        logger.warning("Webhook CamPay reçu sans signature")
        sentry_sdk.capture_message(
            "CamPay webhook sans signature",
            level="warning"
        )
        return False

    try:
        password = _get_password()
        expected = hmac.new(
            password.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()

        valid = hmac.compare_digest(expected.lower(), signature_header.lower())
        if not valid:
            logger.warning("Signature CamPay invalide")
            sentry_sdk.capture_message("CamPay webhook : signature invalide", level="warning")
        return valid
    except Exception as exc:
        logger.error("Erreur vérification signature CamPay: %s", exc)
        sentry_sdk.capture_exception(exc)
        return False


# ─── Extraction des données d'un webhook CamPay ──────────────────────────────

def extract_webhook_data(payload: dict) -> dict:
    """
    Normalise le payload webhook CamPay vers notre format interne.

    Returns:
        {
          webhook_id:       str (reference)
          event_type:       str ("collection.completed" | "collection.failed")
          transaction_id:   str
          amount:           int
          currency:         str
          status:           str (CamPay raw status)
          customer_phone:   str | None
          metadata:         dict | None
        }
    """
    status = payload.get("status", "unknown")
    event_type = (
        "collection.completed" if status == "SUCCESSFUL"
        else "collection.failed" if status == "FAILED"
        else "collection.pending"
    )
    return {
        "webhook_id":      payload.get("reference", payload.get("external_reference", "")),
        "event_type":      event_type,
        "transaction_id":  payload.get("reference", payload.get("external_reference", "")),
        "amount":          int(payload.get("amount", 0)),
        "currency":        payload.get("currency", "XAF"),
        "status":          status,
        "customer_phone":  payload.get("operator_reference", None),
        "metadata":        None,
    }
