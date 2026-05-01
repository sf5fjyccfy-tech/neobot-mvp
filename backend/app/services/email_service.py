"""
Service d'envoi d'emails transactionnels via Brevo.

Design : fond blanc, typographie noire, accents orange #FF4D00 et teal #00E5CC.
Logo hébergé sur le CDN NeoBot (compatible tous clients email dont Gmail).
Layout table-based email-safe, max-width 560px, mobile-first.

Fonctions :
  send_welcome_email(...)
  send_confirmation_email(...)
  send_password_reset_email(...)
  send_payment_confirmation(...)
  send_subscription_expiry_warning(...)
  send_inactivity_reminder(...)
  send_internal_alert(...)
"""

import os
import re
import html as _esc
import logging

import httpx
import sentry_sdk
from datetime import date

logger = logging.getLogger(__name__)

# ─── Configuration ─────────────────────────────────────────────────────────────
BREVO_API_KEY  = os.getenv("BREVO_API_KEY", "")
BREVO_API_URL  = "https://api.brevo.com/v3/smtp/email"
SENDER_EMAIL   = os.getenv("BREVO_SENDER_EMAIL", "contact@neobot-ai.com")
SENDER_NAME    = os.getenv("BREVO_SENDER_NAME", "NeoBot")
REPLY_TO_EMAIL = os.getenv("BREVO_REPLY_TO", "contact@neobot-ai.com")
FRONTEND_URL   = os.getenv("FRONTEND_URL", "https://neobot-ai.com")

# Logo PNG hébergé — compatible Gmail web, Android, Apple Mail, Samsung Mail
LOGO_URL = f"{FRONTEND_URL}/logo-email.png"

if not BREVO_API_KEY:
    logger.warning("BREVO_API_KEY non défini — emails transactionnels désactivés")


# ─── Composants HTML réutilisables ─────────────────────────────────────────────

def _header(label: str, color: str = "#FF4D00") -> str:
    """En-tête de carte : barre colorée + logo NeoBot + titre de section."""
    return (
        # Barre accent
        f'<tr><td height="3" bgcolor="{color}" '
        f'style="background-color:{color};height:3px;font-size:0;line-height:0;">&nbsp;</td></tr>'
        # Logo + nom
        f'<tr><td align="center" bgcolor="#ffffff" '
        f'style="background-color:#ffffff;padding:28px 36px 20px;border-bottom:1px solid #f0f0f0;">'
        f'<img src="{LOGO_URL}" width="44" height="48" alt="NeoBot" border="0" '
        f'style="display:block;margin:0 auto 10px;">'
        f'<div style="font-family:Arial Black,Arial,Helvetica,sans-serif;font-size:15px;'
        f'font-weight:900;letter-spacing:0.22em;color:#111111;">'
        f'NEO<span style="color:#00BFA5;">BOT</span>'
        f'</div>'
        f'<div style="margin-top:12px;display:inline-block;padding:4px 14px;'
        f'background-color:{color}1a;border-radius:20px;">'
        f'<span style="font-family:Arial,Helvetica,sans-serif;font-size:11px;'
        f'font-weight:700;color:{color};letter-spacing:0.08em;text-transform:uppercase;">'
        f'{label}</span>'
        f'</div>'
        f'</td></tr>'
    )


def _cta(label: str, url: str, color: str = "#FF4D00") -> str:
    """Bouton CTA centré — fond coloré, texte blanc."""
    return (
        f'<table role="presentation" cellpadding="0" cellspacing="0" '
        f'style="margin:0 auto;">'
        f'<tr><td align="center" bgcolor="{color}" '
        f'style="background-color:{color};border-radius:7px;">'
        f'<a href="{url}" target="_blank" '
        f'style="display:inline-block;padding:13px 32px;'
        f'font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;'
        f'color:#ffffff;text-decoration:none;border-radius:7px;">{label}</a>'
        f'</td></tr></table>'
    )


def _footer() -> str:
    """Pied de page légal NeoBot."""
    return (
        f'<tr><td bgcolor="#f9f9f9" '
        f'style="background-color:#f9f9f9;border-top:1px solid #eeeeee;'
        f'padding:20px 36px;text-align:center;">'
        f'<p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:11px;'
        f'color:#999999;line-height:1.8;">'
        f'NeoBot &middot; L\'IA WhatsApp pour les businesses africains<br>'
        f'<a href="{FRONTEND_URL}" style="color:#999999;text-decoration:none;">neobot-ai.com</a>'
        f'&nbsp;&middot;&nbsp;'
        f'<a href="{FRONTEND_URL}/legal" style="color:#999999;text-decoration:none;">Confidentialit&eacute;</a>'
        f'&nbsp;&middot;&nbsp;'
        f'<a href="mailto:contact@neobot-ai.com" style="color:#999999;text-decoration:none;">Support</a>'
        f'</p>'
        f'</td></tr>'
    )


def _wrap(card_rows: str) -> str:
    """Wrapper HTML complet pour tout email NeoBot — fond blanc, max 560px."""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>NeoBot</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f4f4;" bgcolor="#f4f4f4">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       bgcolor="#f4f4f4" style="background-color:#f4f4f4;">
  <tr><td align="center" style="padding:28px 16px 48px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           bgcolor="#ffffff"
           style="max-width:560px;width:100%;background-color:#ffffff;
                  border-radius:10px;border:1px solid #e8e8e8;
                  overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);">
      {card_rows}
      {_footer()}
    </table>
  </td></tr>
</table>
</body>
</html>"""


# ─── Transport HTTP ────────────────────────────────────────────────────────────

async def _send(payload: dict) -> bool:
    if not BREVO_API_KEY:
        logger.warning("Email non envoyé : BREVO_API_KEY absent.")
        return False

    if REPLY_TO_EMAIL and "replyTo" not in payload:
        payload["replyTo"] = {"email": REPLY_TO_EMAIL}

    # Génère automatiquement une version text/plain si absente (corrige MIME_HTML_ONLY)
    if "htmlContent" in payload and "textContent" not in payload:
        html_body = payload["htmlContent"]
        text = re.sub(r'<style[^>]*>.*?</style>', '', html_body, flags=re.DOTALL)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&middot;', '·', text)
        text = re.sub(r'&[a-z]+;', '', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text.strip())
        payload["textContent"] = text

    headers = {
        "accept":       "application/json",
        "content-type": "application/json",
        "api-key":      BREVO_API_KEY,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(BREVO_API_URL, json=payload, headers=headers)

        if r.is_success:
            to_addr = payload.get("to", [{}])[0].get("email", "?")
            logger.info("Email envoyé -> %s [%s]", to_addr, r.status_code)
            return True

        logger.error("Brevo %s : %s", r.status_code, r.text[:300])
        sentry_sdk.capture_message(
            f"Brevo email failed: {r.status_code}",
            level="error",
            extras={"response_body": r.text[:300], "to": payload.get("to")},
        )
        return False

    except httpx.TimeoutException:
        logger.error("Brevo timeout — email non envoyé")
        sentry_sdk.capture_message("Brevo API timeout", level="warning")
        return False
    except Exception as exc:
        logger.error("Brevo exception : %s", exc)
        sentry_sdk.capture_exception(exc)
        return False


# ─── 1. Bienvenue ──────────────────────────────────────────────────────────────

async def send_welcome_email(
    to_email: str,
    user_name: str,
    tenant_name: str,
    trial_end_date: date | None = None,
    trial_days: int = 14,
) -> bool:
    trial_end_str = trial_end_date.strftime("%d/%m/%Y") if trial_end_date else ""
    date_line = (
        f"jusqu'au <strong>{trial_end_str}</strong>"
        if trial_end_str
        else f"pendant {trial_days}&nbsp;jours"
    )

    card = f"""
    {_header("Compte activ&eacute;")}

    <tr><td style="padding:32px 36px 8px;">
      <h1 style="margin:0 0 8px;font-family:Arial Black,Arial,sans-serif;
                 font-size:22px;font-weight:900;color:#111111;">
        Bienvenue, {_esc.escape(user_name)}&nbsp;!
      </h1>
      <p style="margin:0 0 24px;font-family:Arial,Helvetica,sans-serif;
                font-size:14px;color:#555555;line-height:1.7;">
        Ton espace <strong>{_esc.escape(tenant_name)}</strong> est pr&ecirc;t.
        Ton essai gratuit <strong>Plan Essential</strong> est actif {date_line}.
      </p>
    </td></tr>

    <!-- 3 etapes -->
    <tr><td style="padding:0 36px 28px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid #f0f0f0;border-radius:8px;overflow:hidden;">

        <tr bgcolor="#fafafa" style="background-color:#fafafa;">
          <td width="48" align="center" style="padding:14px 0 14px 16px;">
            <div style="width:28px;height:28px;border-radius:50%;
                        background-color:#FF4D00;text-align:center;line-height:28px;">
              <span style="font-family:Arial,sans-serif;font-size:13px;
                           font-weight:800;color:#ffffff;">1</span>
            </div>
          </td>
          <td style="padding:14px 16px;border-bottom:1px solid #f0f0f0;
                     font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#333333;">
            <strong>Connecte ton num&eacute;ro WhatsApp Business</strong>
          </td>
        </tr>

        <tr bgcolor="#ffffff" style="background-color:#ffffff;">
          <td width="48" align="center" style="padding:14px 0 14px 16px;">
            <div style="width:28px;height:28px;border-radius:50%;
                        background-color:#f0f0f0;border:2px solid #FF4D00;
                        text-align:center;line-height:24px;">
              <span style="font-family:Arial,sans-serif;font-size:13px;
                           font-weight:800;color:#FF4D00;">2</span>
            </div>
          </td>
          <td style="padding:14px 16px;border-bottom:1px solid #f0f0f0;
                     font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#333333;">
            Configure ton premier agent IA (Libre, Vente, RDV&hellip;)
          </td>
        </tr>

        <tr bgcolor="#fafafa" style="background-color:#fafafa;">
          <td width="48" align="center" style="padding:14px 0 14px 16px;">
            <div style="width:28px;height:28px;border-radius:50%;
                        background-color:#f0f0f0;text-align:center;line-height:28px;">
              <span style="font-family:Arial,sans-serif;font-size:13px;
                           font-weight:800;color:#bbbbbb;">3</span>
            </div>
          </td>
          <td style="padding:14px 16px;
                     font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#aaaaaa;">
            Ton agent r&eacute;pond 24h/24 &agrave; ta place
          </td>
        </tr>

      </table>
    </td></tr>

    <!-- CTA -->
    <tr><td align="center" style="padding:0 36px 32px;">
      {_cta("Configurer mon agent", f"{FRONTEND_URL}/agent")}
      <p style="margin:14px 0 0;font-family:Arial,Helvetica,sans-serif;
                font-size:12px;color:#999999;text-align:center;">
        Des questions&nbsp;? R&eacute;ponds directement &agrave; cet email.
      </p>
    </td></tr>

    <!-- Recap plan -->
    <tr><td bgcolor="#f9f9f9"
           style="background-color:#f9f9f9;border-top:1px solid #f0f0f0;
                  padding:16px 36px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td align="center" style="padding:8px;
              font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#888888;">
            <strong style="display:block;font-size:16px;color:#FF4D00;
                           font-weight:800;">{trial_days}&nbsp;jours</strong>
            Essai gratuit
          </td>
          <td width="1" bgcolor="#e8e8e8"
              style="background-color:#e8e8e8;font-size:0;">&nbsp;</td>
          <td align="center" style="padding:8px;
              font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#888888;">
            <strong style="display:block;font-size:16px;color:#FF4D00;
                           font-weight:800;">24h/24</strong>
            Disponibilit&eacute;
          </td>
          <td width="1" bgcolor="#e8e8e8"
              style="background-color:#e8e8e8;font-size:0;">&nbsp;</td>
          <td align="center" style="padding:8px;
              font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#888888;">
            <strong style="display:block;font-size:16px;color:#FF4D00;
                           font-weight:800;">5</strong>
            Types d'agents
          </td>
        </tr>
      </table>
    </td></tr>
    """

    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email, "name": user_name}],
        "replyTo":     {"email": REPLY_TO_EMAIL},
        "subject":     f"Bienvenue sur NeoBot — ton essai de {trial_days} jours commence maintenant",
        "htmlContent": _wrap(card),
    })


# ─── 2. Confirmation d'adresse email ──────────────────────────────────────────

async def send_confirmation_email(to_email: str, confirmation_link: str) -> bool:
    card = f"""
    {_header("Confirmation d'adresse email", "#00BFA5")}

    <tr><td style="padding:32px 36px 8px;text-align:center;">
      <h1 style="margin:0 0 12px;font-family:Arial Black,Arial,sans-serif;
                 font-size:22px;font-weight:900;color:#111111;">
        Confirmez votre adresse email
      </h1>
      <p style="margin:0 0 8px;font-family:Arial,Helvetica,sans-serif;
                font-size:14px;color:#555555;line-height:1.7;
                max-width:400px;margin-left:auto;margin-right:auto;">
        Cliquez sur le bouton ci-dessous pour activer votre compte NeoBot.
      </p>
      <p style="margin:0 0 28px;font-family:Arial,Helvetica,sans-serif;
                font-size:13px;color:#888888;">
        Ce lien est valable <strong>24&nbsp;heures</strong>.
      </p>
      {_cta("Confirmer mon adresse email", confirmation_link, "#00BFA5")}
      <p style="margin:20px 0 0;font-family:Arial,Helvetica,sans-serif;
                font-size:12px;color:#bbbbbb;">
        Si vous n'avez pas cr&eacute;&eacute; de compte NeoBot, ignorez cet email.
      </p>
    </td></tr>
    <tr><td height="32" style="font-size:0;">&nbsp;</td></tr>
    """

    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email}],
        "subject":     "Confirmez votre adresse email — NeoBot",
        "htmlContent": _wrap(card),
    })


# ─── 3. Réinitialisation mot de passe ─────────────────────────────────────────

async def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    card = f"""
    {_header("S&eacute;curit&eacute; du compte")}

    <tr><td style="padding:32px 36px 8px;text-align:center;">
      <h1 style="margin:0 0 12px;font-family:Arial Black,Arial,sans-serif;
                 font-size:22px;font-weight:900;color:#111111;">
        R&eacute;initialisation du mot de passe
      </h1>
      <p style="margin:0 0 8px;font-family:Arial,Helvetica,sans-serif;
                font-size:14px;color:#555555;line-height:1.7;
                max-width:400px;margin-left:auto;margin-right:auto;">
        Vous avez demand&eacute; &agrave; r&eacute;initialiser votre mot de passe NeoBot.
      </p>
      <p style="margin:0 0 28px;font-family:Arial,Helvetica,sans-serif;
                font-size:13px;color:#888888;">
        Ce lien est valable <strong>1&nbsp;heure</strong>.
        Apr&egrave;s expiration, recommencez depuis la page de connexion.
      </p>
      {_cta("R&eacute;initialiser mon mot de passe", reset_link)}
      <p style="margin:20px 0 4px;font-family:Arial,Helvetica,sans-serif;
                font-size:12px;color:#bbbbbb;">
        Si vous n'avez pas fait cette demande, votre compte est s&eacute;curis&eacute;.
        Ignorez cet email.
      </p>
    </td></tr>
    <tr><td height="32" style="font-size:0;">&nbsp;</td></tr>
    """

    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email}],
        "subject":     "Réinitialisation de votre mot de passe — NeoBot",
        "htmlContent": _wrap(card),
    })


# ─── 4. Confirmation de paiement ──────────────────────────────────────────────

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
    rows_data = [
        ("Plan", f"<strong>{_esc.escape(plan)}</strong>"),
        ("Montant pay&eacute;", f"<strong>{amount:,}&nbsp;{_esc.escape(currency)}</strong>"),
    ]
    if reference:
        rows_data.append(("R&eacute;f&eacute;rence", _esc.escape(reference)))
    if payment_date:
        rows_data.append(("Date de paiement", _esc.escape(payment_date)))
    if next_renewal:
        rows_data.append(("Prochain renouvellement", _esc.escape(next_renewal)))
    if messages_limit:
        rows_data.append(("Messages inclus", f"{_esc.escape(messages_limit)}&nbsp;/&nbsp;mois"))

    detail_rows = "".join(
        f'<tr>'
        f'<td style="padding:11px 16px;border-bottom:1px solid #f5f5f5;'
        f'font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#777777;">{k}</td>'
        f'<td style="padding:11px 16px;border-bottom:1px solid #f5f5f5;'
        f'font-family:Arial,Helvetica,sans-serif;font-size:13px;color:#111111;'
        f'text-align:right;">{v}</td>'
        f'</tr>'
        for k, v in rows_data
    )

    card = f"""
    {_header("Paiement confirm&eacute;", "#22a05d")}

    <tr><td style="padding:28px 36px 8px;">
      <h1 style="margin:0 0 8px;font-family:Arial Black,Arial,sans-serif;
                 font-size:22px;font-weight:900;color:#111111;">
        Merci, {_esc.escape(tenant_name)}&nbsp;!
      </h1>
      <p style="margin:0 0 20px;font-family:Arial,Helvetica,sans-serif;
                font-size:14px;color:#555555;line-height:1.7;">
        Votre abonnement est activ&eacute;. Votre agent IA est op&eacute;rationnel.
      </p>
    </td></tr>

    <!-- Recap paiement -->
    <tr><td style="padding:0 36px 28px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid #e8e8e8;border-radius:8px;overflow:hidden;">
        {detail_rows}
      </table>
    </td></tr>

    <tr><td align="center" style="padding:0 36px 32px;">
      {_cta("Voir mon abonnement", f"{FRONTEND_URL}/billing", "#22a05d")}
    </td></tr>
    """

    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": tenant_email, "name": tenant_name}],
        "replyTo":     {"email": REPLY_TO_EMAIL},
        "subject":     f"Paiement confirmé — NeoBot {plan}",
        "htmlContent": _wrap(card),
    })


# ─── 5. Alerte expiration abonnement ──────────────────────────────────────────

async def send_subscription_expiry_warning(
    to_email: str,
    user_name: str,
    plan_name: str,
    days_left: int,
    expiry_date: str,
    renewal_price: int,
    currency: str = "XAF",
) -> bool:
    if days_left <= 1:
        accent = "#e53e3e"
        label  = "EXPIRE DEMAIN"
        subj   = "Urgent — Votre abonnement NeoBot expire demain"
    elif days_left <= 3:
        accent = "#dd6b20"
        label  = f"EXPIRE DANS {days_left} JOURS"
        subj   = f"Votre abonnement NeoBot expire dans {days_left} jours"
    else:
        accent = "#d69e2e"
        label  = f"EXPIRE DANS {days_left} JOURS"
        subj   = f"Votre abonnement NeoBot expire dans {days_left} jours"

    card = f"""
    {_header(label, accent)}

    <tr><td style="padding:28px 36px 8px;">
      <h1 style="margin:0 0 8px;font-family:Arial Black,Arial,sans-serif;
                 font-size:22px;font-weight:900;color:#111111;">
        Votre abonnement expire bient&ocirc;t
      </h1>
      <p style="margin:0 0 20px;font-family:Arial,Helvetica,sans-serif;
                font-size:14px;color:#555555;line-height:1.7;">
        Bonjour <strong>{_esc.escape(user_name)}</strong>, votre plan
        <strong>{_esc.escape(plan_name)}</strong>
        expire le <strong style="color:{accent};">{_esc.escape(expiry_date)}</strong>.
        Sans renouvellement, votre agent s'arr&ecirc;tera automatiquement.
      </p>
    </td></tr>

    <!-- Montant renouvellement -->
    <tr><td style="padding:0 36px 24px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid #e8e8e8;border-radius:8px;">
        <tr>
          <td style="padding:16px 20px;font-family:Arial,Helvetica,sans-serif;">
            <div style="font-size:12px;color:#888888;margin-bottom:4px;">
              Montant du renouvellement
            </div>
            <div style="font-size:24px;font-weight:800;color:#111111;
                        font-family:Arial Black,Arial,sans-serif;">
              {renewal_price:,}&nbsp;<span style="font-size:16px;">{_esc.escape(currency)}</span>
              <span style="font-size:13px;font-weight:400;color:#888888;">/mois</span>
            </div>
          </td>
        </tr>
      </table>
    </td></tr>

    <tr><td align="center" style="padding:0 36px 32px;">
      {_cta("Renouveler mon abonnement", f"{FRONTEND_URL}/billing", accent)}
    </td></tr>
    """

    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email, "name": user_name}],
        "replyTo":     {"email": REPLY_TO_EMAIL},
        "subject":     subj,
        "htmlContent": _wrap(card),
    })


# ─── 6. Relance inactivité ─────────────────────────────────────────────────────

async def send_inactivity_reminder(
    to_email: str,
    user_name: str,
    agent_name: str,
    plan_name: str,
    inactive_days: int,
    total_conversations: int = 0,
) -> bool:
    card = f"""
    {_header("Agent en pause", "#00BFA5")}

    <tr><td style="padding:28px 36px 8px;">
      <h1 style="margin:0 0 8px;font-family:Arial Black,Arial,sans-serif;
                 font-size:22px;font-weight:900;color:#111111;">
        Ton agent t'attend, {_esc.escape(user_name)}
      </h1>
      <p style="margin:0 0 12px;font-family:Arial,Helvetica,sans-serif;
                font-size:14px;color:#555555;line-height:1.7;">
        Ton agent <strong>{_esc.escape(agent_name)}</strong> n'a re&ccedil;u aucune
        conversation depuis <strong style="color:#FF4D00;">{inactive_days}&nbsp;jours</strong>.
      </p>
      <p style="margin:0 0 20px;font-family:Arial,Helvetica,sans-serif;
                font-size:13px;color:#888888;line-height:1.6;">
        V&eacute;rifie que ton num&eacute;ro WhatsApp est bien connect&eacute;
        et que ton agent est actif.
      </p>
    </td></tr>

    <!-- Stats activité -->
    <tr><td style="padding:0 36px 24px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid #e8e8e8;border-radius:8px;overflow:hidden;">
        <tr bgcolor="#f9f9f9" style="background-color:#f9f9f9;">
          <td align="center" style="padding:16px 8px;
              font-family:Arial,Helvetica,sans-serif;">
            <strong style="display:block;font-size:20px;color:#111111;">{total_conversations}</strong>
            <span style="font-size:11px;color:#999999;">conversations totales</span>
          </td>
          <td width="1" bgcolor="#e8e8e8"
              style="background-color:#e8e8e8;font-size:0;">&nbsp;</td>
          <td align="center" style="padding:16px 8px;
              font-family:Arial,Helvetica,sans-serif;">
            <strong style="display:block;font-size:20px;color:#FF4D00;">{inactive_days}j</strong>
            <span style="font-size:11px;color:#999999;">sans activit&eacute;</span>
          </td>
        </tr>
      </table>
    </td></tr>

    <tr><td align="center" style="padding:0 36px 32px;">
      {_cta("R&eacute;activer mon agent", f"{FRONTEND_URL}/agent", "#00BFA5")}
    </td></tr>
    """

    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email, "name": user_name}],
        "replyTo":     {"email": REPLY_TO_EMAIL},
        "subject":     f"Ton agent NeoBot est inactif depuis {inactive_days} jours",
        "htmlContent": _wrap(card),
    })


# ─── 7. NeoAlert — alerte interne admin ───────────────────────────────────────

async def send_internal_alert(subject: str, body: str) -> bool:
    """
    Alerte technique interne (crédits API, paiements, incidents).
    Envoyé à NEOPAY_ALERT_EMAIL. Design minimaliste fonctionnel.
    """
    alert_email = os.getenv("NEOPAY_ALERT_EMAIL", "neobot561@gmail.com")
    if not alert_email:
        logger.warning("NEOPAY_ALERT_EMAIL non défini — alerte ignorée : %s", subject)
        return False

    env_label = os.getenv("APP_ENV", "development").upper()
    safe_subj = _esc.escape(subject)
    safe_body = _esc.escape(body)

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>NeoAlert</title></head>
<body style="margin:0;padding:0;background-color:#f4f4f4;" bgcolor="#f4f4f4">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       bgcolor="#f4f4f4" style="background-color:#f4f4f4;">
  <tr><td align="center" style="padding:28px 16px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           bgcolor="#ffffff"
           style="max-width:600px;width:100%;background-color:#ffffff;
                  border-radius:10px;border:1px solid #e8e8e8;">

      <!-- Header NeoAlert -->
      <tr><td height="3" bgcolor="#FF4D00"
             style="background-color:#FF4D00;height:3px;font-size:0;
                    border-radius:10px 10px 0 0;">&nbsp;</td></tr>

      <tr><td style="padding:20px 28px;border-bottom:1px solid #f0f0f0;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td>
              <img src="{LOGO_URL}" width="28" height="31" alt="NeoBot" border="0"
                   style="display:inline-block;vertical-align:middle;margin-right:8px;">
              <span style="font-family:Arial Black,Arial,Helvetica,sans-serif;
                           font-size:13px;font-weight:900;letter-spacing:0.18em;
                           color:#111111;vertical-align:middle;">
                NEO<span style="color:#00BFA5;">ALERT</span>
              </span>
            </td>
            <td align="right">
              <span style="font-family:Arial,Helvetica,sans-serif;font-size:11px;
                           color:#bbbbbb;letter-spacing:0.05em;">{env_label}</span>
            </td>
          </tr>
        </table>
      </td></tr>

      <!-- Titre alerte -->
      <tr><td style="padding:16px 28px 8px;">
        <div style="font-family:Arial Black,Arial,sans-serif;font-size:16px;
                    font-weight:900;color:#FF4D00;">{safe_subj}</div>
      </td></tr>

      <!-- Corps technique -->
      <tr><td style="padding:4px 28px 24px;">
        <pre style="margin:0;font-family:'Courier New',Courier,monospace;
                    font-size:12px;color:#444444;line-height:1.7;
                    background-color:#f8f8f8;border:1px solid #eeeeee;
                    border-radius:6px;padding:14px 16px;
                    white-space:pre-wrap;word-break:break-all;">{safe_body}</pre>
      </td></tr>

      <!-- Footer -->
      <tr><td bgcolor="#f9f9f9"
             style="background-color:#f9f9f9;border-top:1px solid #eeeeee;
                    padding:14px 28px;border-radius:0 0 10px 10px;
                    text-align:center;">
        <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:11px;
                  color:#bbbbbb;">NeoBot &middot; Alerte interne</p>
      </td></tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""

    return await _send({
        "sender":      {"name": "NeoAlert", "email": SENDER_EMAIL},
        "to":          [{"email": alert_email}],
        "subject":     subject,
        "htmlContent": html_content,
    })


async def send_custom_broadcast(
    to_email: str,
    to_name: str,
    subject: str,
    body: str,
) -> bool:
    """
    Email broadcast superadmin — envoi personnalisé à un client.
    body est du texte brut, converti en HTML sécurisé (XSS-safe via _esc.escape).
    Appelé en boucle par POST /api/admin/broadcast-email.
    """
    safe_name = _esc.escape(to_name)
    safe_subject = _esc.escape(subject)
    safe_body = _esc.escape(body).replace("\n", "<br>")
    accent = "#00E5CC"

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>{safe_subject}</title></head>
<body style="margin:0;padding:0;background-color:#f4f4f4;" bgcolor="#f4f4f4">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#f4f4f4"
       style="background-color:#f4f4f4;">
  <tr><td align="center" style="padding:28px 16px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" bgcolor="#ffffff"
           style="max-width:560px;width:100%;background-color:#ffffff;border-radius:10px;
                  border:1px solid #e8e8e8;">
      <tr><td height="4" bgcolor="{accent}"
             style="background-color:{accent};height:4px;font-size:0;
                    border-radius:10px 10px 0 0;">&nbsp;</td></tr>
      <tr><td style="padding:24px 28px 16px;">
        <img src="{LOGO_URL}" width="28" height="31" alt="NeoBot" border="0"
             style="display:inline-block;vertical-align:middle;margin-right:8px;">
        <span style="font-family:Arial Black,Arial,Helvetica,sans-serif;font-size:13px;
                     font-weight:900;letter-spacing:0.18em;color:#111111;
                     vertical-align:middle;">NEOBOT</span>
      </td></tr>
      <tr><td style="padding:8px 28px 16px;">
        <div style="font-family:Arial Black,Arial,sans-serif;font-size:18px;
                    font-weight:900;color:#111111;line-height:1.3;">{safe_subject}</div>
      </td></tr>
      <tr><td style="padding:0 28px 24px;">
        <div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;color:#444444;
                    line-height:1.7;">{safe_body}</div>
      </td></tr>
      {_footer()}
    </table>
  </td></tr>
</table>
</body>
</html>"""

    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email, "name": to_name}],
        "subject":     subject,
        "htmlContent": html_content,
    })
