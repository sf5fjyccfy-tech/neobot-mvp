"""
Service d'envoi d'emails transactionnels via Brevo (ex-Sendinblue).
Utilise l'API REST Brevo v3 avec httpx (déjà dans les dépendances).

Fonctions exposées :
  - send_welcome_email(to_email, user_name, tenant_name, trial_end_date, trial_days)
  - send_password_reset_email(to_email, reset_link)
  - send_confirmation_email(to_email, confirmation_link)
  - send_payment_confirmation(tenant_email, tenant_name, plan, amount, currency)
  - send_subscription_expiry_warning(to_email, user_name, plan_name, days_left, expiry_date, renewal_price, currency)
  - send_inactivity_reminder(to_email, user_name, agent_name, plan_name, inactive_days, total_conversations)
  - send_internal_alert(subject, body)

Templates Brevo (IDs dans .env) :
  BREVO_TPL_WELCOME=1    Bienvenue après inscription
  BREVO_TPL_PAYMENT=2    Confirmation paiement
  BREVO_TPL_EXPIRY=3     Abonnement expire bientôt
  BREVO_TPL_INACTIVITY=4 Relance inactivité
"""

import os
import logging
import sentry_sdk
import httpx
from datetime import date

logger = logging.getLogger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
BREVO_API_KEY      = os.getenv("BREVO_API_KEY", "")
BREVO_API_URL      = "https://api.brevo.com/v3/smtp/email"
SENDER_EMAIL       = os.getenv("BREVO_SENDER_EMAIL", "contact@neobot-ai.com")
SENDER_NAME        = os.getenv("BREVO_SENDER_NAME", "NeoBot")
REPLY_TO_EMAIL     = os.getenv("BREVO_REPLY_TO", "contact@neobot-ai.com")
FRONTEND_URL       = os.getenv("FRONTEND_URL", "http://localhost:3002")

# IDs des templates Brevo
TPL_WELCOME     = int(os.getenv("BREVO_TPL_WELCOME",     "1"))
TPL_PAYMENT     = int(os.getenv("BREVO_TPL_PAYMENT",     "2"))
TPL_EXPIRY      = int(os.getenv("BREVO_TPL_EXPIRY",      "3"))
TPL_INACTIVITY  = int(os.getenv("BREVO_TPL_INACTIVITY",  "4"))

if not BREVO_API_KEY:
    logger.warning(
        "⚠️  BREVO_API_KEY non défini — les emails transactionnels seront désactivés"
    )


# ─── Helpers internes ─────────────────────────────────────────────────────────

async def _send(payload: dict) -> bool:
    """
    Appel HTTP vers l'API Brevo.
    Retourne True si succès (2xx), False sinon.
    Capture toute exception dans Sentry.
    """
    if not BREVO_API_KEY:
        logger.warning("Email non envoyé : BREVO_API_KEY absent.")
        return False

    # Inject replyTo automatiquement si non présent
    if REPLY_TO_EMAIL and "replyTo" not in payload:
        payload["replyTo"] = {"email": REPLY_TO_EMAIL}

    headers = {
        "accept":       "application/json",
        "content-type": "application/json",
        "api-key":      BREVO_API_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(BREVO_API_URL, json=payload, headers=headers)

        if response.is_success:
            logger.info(
                f"✅ Email envoyé → {payload.get('to', [{}])[0].get('email', '?')} "
                f"[{response.status_code}]"
            )
            return True
        else:
            logger.error(
                f"❌ Brevo erreur {response.status_code}: {response.text[:300]}"
            )
            sentry_sdk.capture_message(
                f"Brevo email failed: {response.status_code}",
                level="error",
                extras={"response_body": response.text[:300], "to": payload.get("to")},
            )
            return False

    except httpx.TimeoutException:
        logger.error("❌ Brevo timeout — email non envoyé")
        sentry_sdk.capture_message("Brevo API timeout", level="warning")
        return False

    except Exception as exc:
        logger.error(f"❌ Brevo exception inattendue: {exc}")
        sentry_sdk.capture_exception(exc)
        return False


# ─── Emails transactionnels ───────────────────────────────────────────────────

async def send_welcome_email(
    to_email: str,
    user_name: str,
    tenant_name: str,
    trial_end_date: date | None = None,
    trial_days: int = 14,
) -> bool:
    """
    Envoyé après chaque inscription réussie. Utilise le template Brevo TPL_WELCOME.
    """
    trial_end_str = trial_end_date.strftime("%d/%m/%Y") if trial_end_date else ""
    payload = {
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email, "name": user_name}],
        "replyTo":     {"email": REPLY_TO_EMAIL},
        "templateId":  TPL_WELCOME,
        "params": {
            "USER_NAME":      user_name,
            "TENANT_NAME":    tenant_name,
            "TRIAL_DAYS":     str(trial_days),
            "TRIAL_END_DATE": trial_end_str,
            "DASHBOARD_URL":  f"{FRONTEND_URL}/dashboard",
            "DEMO_URL":       f"{FRONTEND_URL}/#demo",
        },
    }
    return await _send(payload)


async def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    """
    Envoyé quand l'utilisateur demande une réinitialisation de mot de passe.
    Le lien expire dans 1 heure côté backend.
    """
    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0f0f0f;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0f0f;">
    <tr><td align="center" style="padding:40px 20px;">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#1a1a1a;border-radius:12px;overflow:hidden;max-width:600px;width:100%;">
        <tr>
          <td style="background:linear-gradient(135deg,#FF4D00,#FF7A40);padding:32px;text-align:center;">
            <h1 style="color:#fff;margin:0;font-size:24px;font-weight:800;">
              NéoBot — Réinitialisation de mot de passe
            </h1>
          </td>
        </tr>
        <tr>
          <td style="padding:36px 40px;color:#e0e0e0;font-size:15px;line-height:1.7;">
            <p style="margin:0 0 16px;">Vous avez demandé à réinitialiser votre mot de passe NéoBot.</p>
            <p style="margin:0 0 24px;color:#999;">
              Ce lien est valable <strong style="color:#FF7A40;">1 heure</strong>.
              Si vous n'avez pas fait cette demande, ignorez cet email — votre compte reste sécurisé.
            </p>
            <div style="text-align:center;margin:32px 0;">
              <a href="{reset_link}"
                 style="background:linear-gradient(135deg,#FF4D00,#FF7A40);color:#fff;
                        text-decoration:none;padding:14px 36px;border-radius:8px;
                        font-weight:700;font-size:15px;display:inline-block;">
                Réinitialiser mon mot de passe →
              </a>
            </div>
            <p style="margin:0;color:#555;font-size:12px;word-break:break-all;">
              Lien direct : <a href="{reset_link}" style="color:#FF7A40;">{reset_link}</a>
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 40px;border-top:1px solid #2a2a2a;text-align:center;">
            <p style="margin:0;color:#555;font-size:12px;">NéoBot — Automatisation WhatsApp</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    payload = {
        "sender":  {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":      [{"email": to_email}],
        "subject": "🔐 Réinitialisation de votre mot de passe NéoBot",
        "htmlContent": html_content,
    }
    return await _send(payload)


async def send_confirmation_email(to_email: str, confirmation_link: str) -> bool:
    """
    Envoyé pour confirmer l'adresse email d'un utilisateur.
    (Feature à brancher quand la vérification email sera implémentée.)
    """
    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#0f0f0f;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0f0f;">
    <tr><td align="center" style="padding:40px 20px;">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:#1a1a1a;border-radius:12px;overflow:hidden;max-width:600px;width:100%;">
        <tr>
          <td style="background:linear-gradient(135deg,#FF4D00,#FF7A40);padding:32px;text-align:center;">
            <h1 style="color:#fff;margin:0;font-size:24px;font-weight:800;">
              NéoBot — Confirmez votre email
            </h1>
          </td>
        </tr>
        <tr>
          <td style="padding:36px 40px;color:#e0e0e0;font-size:15px;line-height:1.7;">
            <p style="margin:0 0 16px;">
              Cliquez sur le bouton ci-dessous pour confirmer votre adresse email
              et activer votre compte NéoBot.
            </p>
            <div style="text-align:center;margin:32px 0;">
              <a href="{confirmation_link}"
                 style="background:linear-gradient(135deg,#FF4D00,#FF7A40);color:#fff;
                        text-decoration:none;padding:14px 36px;border-radius:8px;
                        font-weight:700;font-size:15px;display:inline-block;">
                Confirmer mon email →
              </a>
            </div>
          </td>
        </tr>
        <tr>
          <td style="padding:20px 40px;border-top:1px solid #2a2a2a;text-align:center;">
            <p style="margin:0;color:#555;font-size:12px;">NéoBot — Automatisation WhatsApp</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""
    payload = {
        "sender":  {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":      [{"email": to_email}],
        "subject": "✅ Confirmez votre adresse email NéoBot",
        "htmlContent": html_content,
    }
    return await _send(payload)


# ─── NeopPay : confirmation paiement ─────────────────────────────────────────

async def send_payment_confirmation(
    tenant_email: str,
    tenant_name: str,
    plan: str,
    amount: int,
    currency: str = "XAF",
    reference: str = "",
    payment_date: str = "",
    next_renewal: str = "",
    messages_limit: str = "",
) -> bool:
    """Email envoyé au client après activation de son abonnement. Utilise TPL_PAYMENT."""
    payload = {
        "sender":     {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":         [{"email": tenant_email, "name": tenant_name}],
        "replyTo":    {"email": REPLY_TO_EMAIL},
        "templateId": TPL_PAYMENT,
        "params": {
            "USER_NAME":      tenant_name,
            "PLAN_NAME":      plan,
            "AMOUNT":         f"{amount:,}",
            "CURRENCY":       currency,
            "REFERENCE":      reference,
            "PAYMENT_DATE":   payment_date,
            "NEXT_RENEWAL":   next_renewal,
            "MESSAGES_LIMIT": messages_limit,
            "DASHBOARD_URL":  f"{FRONTEND_URL}/dashboard",
        },
    }
    return await _send(payload)


# ─── Rappel expiration abonnement ─────────────────────────────────────────────

async def send_subscription_expiry_warning(
    to_email: str,
    user_name: str,
    plan_name: str,
    days_left: int,
    expiry_date: str,
    renewal_price: int,
    currency: str = "XAF",
) -> bool:
    """
    Envoyé automatiquement quand days_left == 7, 3 ou 1.
    Utilise le template Brevo TPL_EXPIRY.
    """
    payload = {
        "sender":     {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":         [{"email": to_email, "name": user_name}],
        "replyTo":    {"email": REPLY_TO_EMAIL},
        "templateId": TPL_EXPIRY,
        "params": {
            "USER_NAME":     user_name,
            "PLAN_NAME":     plan_name,
            "DAYS_LEFT":     str(days_left),
            "EXPIRY_DATE":   expiry_date,
            "RENEWAL_PRICE": f"{renewal_price:,}",
            "CURRENCY":      currency,
            "RENEWAL_URL":   f"{FRONTEND_URL}/billing",
            "DASHBOARD_URL": f"{FRONTEND_URL}/dashboard",
        },
    }
    return await _send(payload)


# ─── Relance inactivité ────────────────────────────────────────────────────────

async def send_inactivity_reminder(
    to_email: str,
    user_name: str,
    agent_name: str,
    plan_name: str,
    inactive_days: int,
    total_conversations: int = 0,
) -> bool:
    """
    Envoyé si aucune conversation depuis N jours (défaut : 5).
    Utilise le template Brevo TPL_INACTIVITY.
    """
    payload = {
        "sender":     {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":         [{"email": to_email, "name": user_name}],
        "replyTo":    {"email": REPLY_TO_EMAIL},
        "templateId": TPL_INACTIVITY,
        "params": {
            "USER_NAME":           user_name,
            "AGENT_NAME":          agent_name,
            "PLAN_NAME":           plan_name,
            "INACTIVE_DAYS":       str(inactive_days),
            "TOTAL_CONVERSATIONS": str(total_conversations),
            "DASHBOARD_URL":       f"{FRONTEND_URL}/dashboard",
        },
    }
    return await _send(payload)


# ─── NeopPay : alerte interne (admin) ────────────────────────────────────────

async def send_internal_alert(subject: str, body: str) -> bool:
    """
    Email d'alerte interne pour les events critiques NeopPay.
    Envoyé à l'adresse admin configurée dans NEOPAY_ALERT_EMAIL.
    """
    alert_email = os.getenv("NEOPAY_ALERT_EMAIL", "")
    if not alert_email:
        logger.warning("NEOPAY_ALERT_EMAIL non défini — alerte interne non envoyée: %s", subject)
        return False

    html_content = f"""
<html><body style="font-family:monospace;background:#111;color:#eee;padding:24px;">
  <h2 style="color:#FF4D00;">{subject}</h2>
  <pre style="background:#0a0a0a;padding:16px;border-radius:8px;color:#ccc;white-space:pre-wrap;">{body}</pre>
  <p style="color:#555;font-size:12px;margin-top:24px;">NeopPay — {os.getenv("APP_ENV","development")}</p>
</body></html>
"""
    payload = {
        "sender":  {"name": f"NeopPay Alert", "email": SENDER_EMAIL},
        "to":      [{"email": alert_email}],
        "subject": subject,
        "htmlContent": html_content,
    }
    return await _send(payload)
