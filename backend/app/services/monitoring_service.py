"""
Service monitoring crédits API — DeepSeek + Anthropic.

Vérifie les soldes toutes les heures, stocke l'historique en DB,
déclenche les alertes par email (et WhatsApp si critique),
active/désactive le mode dégradé NeoBot automatiquement.
"""
import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import httpx
import sentry_sdk
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import ApiCredit
from .email_service import send_internal_alert, SENDER_EMAIL, SENDER_NAME

logger = logging.getLogger(__name__)

# ─── Config ──────────────────────────────────────────────────────────────────

DEEPSEEK_API_KEY   = os.getenv("DEEPSEEK_API_KEY", "")
ANTHROPIC_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
ADMIN_WHATSAPP     = os.getenv("ADMIN_WHATSAPP", "")
ALERT_EMAIL        = os.getenv("NEOPAY_ALERT_EMAIL", "neobot561@gmail.com")

# Seuils DeepSeek (USD)
DS_GREEN   = 5.0
DS_ORANGE  = 2.0
DS_RED     = 0.50
DS_CRITICAL = 0.10   # mode dégradé activé sous ce seuil

# Seuils Anthropic (USD)
AN_GREEN   = 2.0
AN_ORANGE  = 0.50
AN_RED     = 0.10
AN_CRITICAL = 0.02

# Taux de conversion USD → FCFA (approximatif, à maintenir à jour)
USD_TO_FCFA = 620.0


# ─── Récupération des soldes ──────────────────────────────────────────────────

async def fetch_deepseek_balance() -> Optional[float]:
    """
    Récupère le solde DeepSeek.
    GET https://api.deepseek.com/user/balance
    Retourne le solde en USD, ou None si erreur.
    """
    if not DEEPSEEK_API_KEY:
        logger.warning("DEEPSEEK_API_KEY non défini")
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.deepseek.com/user/balance",
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json()
            # Format DeepSeek : {"balance_infos": [{"currency": "USD", "total_balance": "8.42", ...}]}
            for info in data.get("balance_infos", []):
                if info.get("currency") == "USD":
                    return float(info.get("total_balance", 0))
            # Fallback : essayer balance directement
            return float(data.get("balance", 0))
    except Exception as exc:
        logger.error("Erreur fetch DeepSeek balance: %s", exc)
        sentry_sdk.capture_exception(exc)
        return None


async def fetch_anthropic_usage() -> Optional[float]:
    """
    Estime les crédits Anthropic restants via l'API usage.
    L'API usage retourne la consommation — on calcule le solde par différence.
    Retourne une estimation en USD, ou None si erreur.

    Note : Anthropic ne fournit pas d'endpoint de solde direct.
    On utilise /v1/organizations/{org_id}/usage ou on interroge les
    informations de facturation disponibles via l'API.
    """
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY non défini")
        return None

    try:
        # Anthropic fournit un endpoint beta pour le solde de crédit
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.anthropic.com/v1/usage",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "anthropic-beta": "usage-2024-10-01",
                },
                params={"limit": 1},
            )
            if resp.status_code == 200:
                data = resp.json()
                # Format possible : {"credits_remaining": 4.21}
                credits = data.get("credits_remaining") or data.get("balance")
                if credits is not None:
                    return float(credits)

            # Si l'endpoint ne retourne pas de solde direct,
            # on tente /v1/account pour les informations de compte
            resp2 = await client.get(
                "https://console.anthropic.com/api/usage_metrics",
                headers={"x-api-key": ANTHROPIC_API_KEY},
            )
            if resp2.status_code == 200:
                data2 = resp2.json()
                return float(data2.get("credits_remaining", -1))

            # En dernier recours, retourner -1 (inconnu) pour afficher
            # dans le dashboard "solde non disponible" plutôt que de crasher
            logger.warning(
                "Solde Anthropic non récupérable (status %s) — "
                "vérifier l'endpoint dans la console Anthropic",
                resp.status_code,
            )
            return -1.0
    except Exception as exc:
        logger.error("Erreur fetch Anthropic usage: %s", exc)
        sentry_sdk.capture_exception(exc)
        return None


# ─── Calcul du niveau d'alerte ────────────────────────────────────────────────

def _get_alert_level(balance: float, provider: str) -> str:
    """Retourne 'green' | 'orange' | 'red' | 'critical' selon le solde."""
    if balance < 0:
        return "unknown"
    if provider == "deepseek":
        if balance > DS_GREEN:   return "green"
        if balance > DS_ORANGE:  return "orange"
        if balance > DS_RED:     return "red"
        return "critical"
    else:  # anthropic
        if balance > AN_GREEN:   return "green"
        if balance > AN_ORANGE:  return "orange"
        if balance > AN_RED:     return "red"
        return "critical"


def _days_remaining(balance: float, daily_avg: float) -> Optional[int]:
    if daily_avg <= 0 or balance < 0:
        return None
    return int(balance / daily_avg)


# ─── Calcul de la consommation moyenne ────────────────────────────────────────

def get_daily_avg(db: Session, provider: str, days: int = 7) -> float:
    """
    Calcule la consommation journalière moyenne sur les N derniers jours.
    Compare le premier et dernier solde connu sur la période.
    """
    since = datetime.utcnow() - timedelta(days=days)
    records = (
        db.query(ApiCredit)
        .filter(ApiCredit.provider == provider, ApiCredit.checked_at >= since)
        .order_by(ApiCredit.checked_at)
        .all()
    )
    if len(records) < 2:
        return 0.0
    oldest = records[0].balance_usd
    newest = records[-1].balance_usd
    elapsed_days = (records[-1].checked_at - records[0].checked_at).total_seconds() / 86400
    if elapsed_days < 0.01:
        return 0.0
    consumed = oldest - newest
    return max(0.0, consumed / elapsed_days)


def get_history(db: Session, provider: str, days: int = 30) -> list:
    """Retourne l'historique des soldes pour le graphique frontend."""
    since = datetime.utcnow() - timedelta(days=days)
    records = (
        db.query(ApiCredit)
        .filter(ApiCredit.provider == provider, ApiCredit.checked_at >= since)
        .order_by(ApiCredit.checked_at)
        .all()
    )
    return [
        {
            "date": r.checked_at.strftime("%Y-%m-%d %H:%M"),
            "balance_usd": float(r.balance_usd),
            "is_degraded": r.is_degraded,
        }
        for r in records
    ]


def get_latest_balance(db: Session, provider: str) -> Optional[ApiCredit]:
    return (
        db.query(ApiCredit)
        .filter(ApiCredit.provider == provider)
        .order_by(ApiCredit.checked_at.desc())
        .first()
    )


# ─── Mode dégradé DeepSeek ────────────────────────────────────────────────────

DEGRADED_MODE_ACTIVE = False   # Flag in-process — persisté en DB aussi


def is_degraded_mode() -> bool:
    """Retourne True si NeoBot doit être en mode dégradé (DeepSeek vide)."""
    return DEGRADED_MODE_ACTIVE


def _set_degraded_mode(active: bool) -> None:
    global DEGRADED_MODE_ACTIVE
    if DEGRADED_MODE_ACTIVE != active:
        DEGRADED_MODE_ACTIVE = active
        if active:
            logger.critical("🔴 MODE DÉGRADÉ ACTIVÉ — DeepSeek solde critique")
            sentry_sdk.capture_message("NeoBot mode dégradé activé — DeepSeek solde critique", level="critical")
        else:
            logger.info("✅ MODE DÉGRADÉ DÉSACTIVÉ — DeepSeek rechargé")
            sentry_sdk.capture_message("NeoBot mode dégradé désactivé — DeepSeek rechargé", level="info")


# ─── Alertes ──────────────────────────────────────────────────────────────────

# Tracking des dernières alertes (in-process, pour limiter les spams)
_last_alert_sent: dict[str, datetime] = {}
ALERT_COOLDOWN_HOURS = {"green": 999, "orange": 6, "red": 2, "critical": 1, "unknown": 6}


def _should_send_alert(provider: str, level: str) -> bool:
    if level == "green":
        return False
    key = f"{provider}:{level}"
    last = _last_alert_sent.get(key)
    if not last:
        return True
    cooldown_h = ALERT_COOLDOWN_HOURS.get(level, 2)
    return (datetime.utcnow() - last).total_seconds() > cooldown_h * 3600


async def _send_credits_alert(
    provider: str, balance: float, level: str, daily_avg: float, days_left: Optional[int]
) -> None:
    """Envoie l'email d'alerte crédits + WhatsApp si critique."""
    icons = {"orange": "🟡", "red": "🔴", "critical": "⛔"}
    labels = {"deepseek": "DeepSeek API", "anthropic": "Anthropic Claude"}
    recharge_urls = {
        "deepseek": "https://platform.deepseek.com/billing",
        "anthropic": "https://console.anthropic.com/settings/plans",
    }
    icon = icons.get(level, "⚠️")
    provider_label = labels.get(provider, provider)
    recharge_url = recharge_urls.get(provider, "#")
    days_txt = f"~{days_left} jours" if days_left else "durée inconnue"
    fcfa = int(balance * USD_TO_FCFA)

    subject = f"{icon} {provider_label} solde bas — Il reste ${balance:.2f} ({days_txt})"
    body = f"""
<h2 style="color:#FF4D00;">{icon} Solde bas — {provider_label}</h2>
<table style="font-family:monospace;border-collapse:collapse;width:100%;">
  <tr><td style="padding:6px 12px;color:#aaa;">Solde actuel</td>
      <td style="padding:6px 12px;color:#fff;font-weight:bold;">${balance:.4f} USD ({fcfa:,} FCFA)</td></tr>
  <tr><td style="padding:6px 12px;color:#aaa;">Consommation/jour</td>
      <td style="padding:6px 12px;color:#fff;">${daily_avg:.4f} USD</td></tr>
  <tr><td style="padding:6px 12px;color:#aaa;">Estimation restante</td>
      <td style="padding:6px 12px;color:#FF4D00;font-weight:bold;">{days_txt}</td></tr>
  <tr><td style="padding:6px 12px;color:#aaa;">Niveau</td>
      <td style="padding:6px 12px;color:#FF4D00;">{level.upper()}</td></tr>
</table>
<p style="margin-top:24px;">
  <a href="{recharge_url}"
     style="background:#FF4D00;color:#fff;padding:12px 24px;border-radius:8px;
            text-decoration:none;font-weight:bold;display:inline-block;">
    Recharger {provider_label} →
  </a>
</p>
"""
    await send_internal_alert(subject=subject, body=body)
    _last_alert_sent[f"{provider}:{level}"] = datetime.utcnow()

    # WhatsApp admin si critique DeepSeek (NeoBot serait mort sans ça)
    if level == "critical" and provider == "deepseek" and ADMIN_WHATSAPP:
        await _send_whatsapp_alert(
            f"⛔ CRITIQUE NeoBot — DeepSeek à ${balance:.2f} seulement. "
            f"Rechargez maintenant : https://platform.deepseek.com/billing"
        )


async def _send_whatsapp_alert(message: str) -> None:
    """Envoie une alerte WhatsApp au numéro admin via le service WhatsApp NeoBot."""
    try:
        whatsapp_backend = os.getenv("WHATSAPP_BACKEND_URL", "http://localhost:3001")
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{whatsapp_backend}/send-message",
                json={"phone": ADMIN_WHATSAPP, "message": message},
            )
    except Exception as exc:
        logger.warning("Alerte WhatsApp admin non envoyée: %s", exc)


# ─── Vérification complète (appelée par le cron) ──────────────────────────────

async def check_and_store_credits(db: Session) -> dict:
    """
    Vérifie les soldes DeepSeek + Anthropic, stocke en DB, envoie les alertes.
    Appelé toutes les heures depuis le background loop dans main.py.

    Returns:
        dict avec les résultats pour les deux providers.
    """
    results = {}

    # ── DeepSeek ─────────────────────────────────────────────────────────────
    ds_balance = await fetch_deepseek_balance()
    if ds_balance is not None:
        ds_daily = get_daily_avg(db, "deepseek")
        ds_level = _get_alert_level(ds_balance, "deepseek")
        ds_days  = _days_remaining(ds_balance, ds_daily)

        # Mode dégradé automatique
        _set_degraded_mode(ds_balance < DS_CRITICAL and ds_balance >= 0)

        credit = ApiCredit(
            provider="deepseek",
            balance_usd=ds_balance,
            is_degraded=is_degraded_mode(),
            checked_at=datetime.utcnow(),
        )
        db.add(credit)

        if _should_send_alert("deepseek", ds_level):
            await _send_credits_alert("deepseek", ds_balance, ds_level, ds_daily, ds_days)

        results["deepseek"] = {
            "balance_usd": ds_balance,
            "level": ds_level,
            "daily_avg": ds_daily,
            "days_remaining": ds_days,
            "is_degraded": is_degraded_mode(),
        }
        logger.info("DeepSeek balance: $%.4f | level: %s | days: %s", ds_balance, ds_level, ds_days)

    # ── Anthropic ────────────────────────────────────────────────────────────
    an_balance = await fetch_anthropic_usage()
    if an_balance is not None:
        an_daily = get_daily_avg(db, "anthropic")
        an_level = _get_alert_level(an_balance, "anthropic")
        an_days  = _days_remaining(an_balance, an_daily)

        credit_an = ApiCredit(
            provider="anthropic",
            balance_usd=an_balance,
            is_degraded=False,
            checked_at=datetime.utcnow(),
        )
        db.add(credit_an)

        if _should_send_alert("anthropic", an_level):
            await _send_credits_alert("anthropic", an_balance, an_level, an_daily, an_days)

        results["anthropic"] = {
            "balance_usd": an_balance,
            "level": an_level,
            "daily_avg": an_daily,
            "days_remaining": an_days,
        }
        logger.info("Anthropic balance: $%.4f | level: %s | days: %s", an_balance, an_level, an_days)

    db.commit()
    return results


async def send_morning_summary(db: Session) -> None:
    """
    Email récapitulatif envoyé à 8h si des Issues Sentry non résolues persistent.
    """
    from ..models import SentryAlert
    open_alerts = db.query(SentryAlert).filter(SentryAlert.status == "open").count()
    if open_alerts == 0:
        return

    ds_latest  = get_latest_balance(db, "deepseek")
    an_latest  = get_latest_balance(db, "anthropic")
    ds_bal     = f"${ds_latest.balance_usd:.4f}" if ds_latest else "N/A"
    an_bal     = f"${an_latest.balance_usd:.4f}" if an_latest else "N/A"

    subject = f"📋 NeoBot — Récap matinal : {open_alerts} issue(s) Sentry en cours"
    body = f"""
<h2>Récapitulatif matinal NeoBot — {datetime.utcnow().strftime('%d/%m/%Y')}</h2>
<p>🔴 <strong>{open_alerts} issue(s)</strong> Sentry non résolues.</p>
<p>
  <a href="https://sentry.io" style="color:#FF4D00;">Voir dans Sentry →</a>
  &nbsp;&nbsp;
  <a href="https://github.com/{os.getenv('GITHUB_REPO_BACKEND','')}/issues"
     style="color:#FF4D00;">Voir les Issues GitHub →</a>
</p>
<hr>
<h3>Crédits API</h3>
<table style="font-family:monospace;">
  <tr><td>DeepSeek :</td><td><strong>{ds_bal}</strong></td></tr>
  <tr><td>Anthropic :</td><td><strong>{an_bal}</strong></td></tr>
</table>
"""
    await send_internal_alert(subject=subject, body=body)
