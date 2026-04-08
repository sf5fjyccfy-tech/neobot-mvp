"""
Service d'envoi d'emails transactionnels via Brevo (ex-Sendinblue).

Tous les templates sont définis en HTML inline — aucune dépendance
aux templates Brevo externes. Design on-brand NeoBot :
fond #0a0a0a, accent orange #FF4D00, teal #00E5CC, logo SVG inline.

Fonctions exposées :
  send_welcome_email(...)
  send_confirmation_email(...)
  send_password_reset_email(...)
  send_payment_confirmation(...)
  send_subscription_expiry_warning(...)
  send_inactivity_reminder(...)
  send_internal_alert(...)
"""

import os
import base64
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
FRONTEND_URL   = os.getenv("FRONTEND_URL", "http://localhost:3002")

if not BREVO_API_KEY:
    logger.warning("⚠️  BREVO_API_KEY non défini — emails transactionnels désactivés")


# ─── Logo NeoBot — SVG encodé en base64 ───────────────────────────────────────
# Compatible Gmail web, Gmail Android, Apple Mail, Samsung Mail.
# Fallback : le texte "NEOBOT" reste toujours visible même si l'image ne charge pas.
_SVG_LOGO = (
    '<svg width="52" height="57" viewBox="0 0 100 110" fill="none" '
    'xmlns="http://www.w3.org/2000/svg">'
    '<path d="M48 6 C30 6 14 20 12 40 L12 58 C14 70 22 80 34 84 L34 94 '
    'L62 94 L62 84 C74 80 82 70 86 58 L86 42 C84 22 68 6 48 6 Z" '
    'stroke="#00E5CC" stroke-width="4" fill="none" stroke-linejoin="round"/>'
    '<path d="M46 22 C58 16 72 24 74 38 C76 52 64 62 52 62 C40 62 30 52 '
    '30 40 C30 28 36 26 46 22 Z" stroke="#00E5CC" stroke-width="3" fill="none"/>'
    '<line x1="86" y1="38" x2="96" y2="38" stroke="#00E5CC" '
    'stroke-width="2.5" stroke-linecap="round"/>'
    '<circle cx="97" cy="38" r="4.5" stroke="#00E5CC" stroke-width="2.5" fill="none"/>'
    '<path d="M12 52 C8 50 7 44 10 38 C12 34 14 30 14 30" '
    'stroke="#00E5CC" stroke-width="2.5" fill="none" stroke-linecap="round"/>'
    '<line x1="34" y1="84" x2="62" y2="84" stroke="#00E5CC" '
    'stroke-width="2.5" stroke-linecap="round"/>'
    '<line x1="40" y1="84" x2="40" y2="94" stroke="#00E5CC" '
    'stroke-width="2.5" stroke-linecap="round"/>'
    '<line x1="56" y1="84" x2="56" y2="94" stroke="#00E5CC" '
    'stroke-width="2.5" stroke-linecap="round"/>'
    '<circle cx="46" cy="42" r="4" fill="#00E5CC"/>'
    '</svg>'
)
_LOGO = (
    "data:image/svg+xml;base64,"
    + base64.b64encode(_SVG_LOGO.encode("utf-8")).decode("ascii")
)


# ─── Helpers HTML (table-based layout pour clients email) ──────────────────────

def _accent_bar(color: str = "#FF4D00") -> str:
    """Barre de couleur 3px en haut de la carte."""
    return (
        f'<tr><td height="3" bgcolor="{color}" '
        f'style="background-color:{color};height:3px;font-size:0;line-height:0;">'
        f'&nbsp;</td></tr>'
    )


def _cta(label: str, url: str, bg: str = "#FF4D00") -> str:
    """Bouton CTA centré."""
    return (
        f'<table role="presentation" cellpadding="0" cellspacing="0" '
        f'style="margin:0 auto;">'
        f'<tr><td align="center" bgcolor="{bg}" '
        f'style="background-color:{bg};border-radius:8px;">'
        f'<a href="{url}" target="_blank" '
        f'style="display:inline-block;padding:13px 34px;'
        f'font-family:Arial,Helvetica,sans-serif;font-size:14px;font-weight:700;'
        f'color:#ffffff;text-decoration:none;border-radius:8px;'
        f'letter-spacing:0.02em;">{label}</a>'
        f'</td></tr></table>'
    )


def _stat_td(value: str, label: str) -> str:
    """Cellule statistique pour la bande basse des cartes."""
    return (
        f'<td align="center" style="padding:16px 8px;'
        f'font-family:Arial,Helvetica,sans-serif;">'
        f'<div style="font-size:18px;font-weight:800;color:#00E5CC;line-height:1;">'
        f'{value}</div>'
        f'<div style="font-size:11px;color:#444444;margin-top:3px;">{label}</div>'
        f'</td>'
    )


def _sep_td() -> str:
    """Séparateur vertical entre stats."""
    return (
        '<td width="1" bgcolor="#1e1e1e" '
        'style="background-color:#1e1e1e;font-size:0;line-height:0;">&nbsp;</td>'
    )


def _wrap(card_rows: str) -> str:
    """
    Wrapper HTML complet pour tout email NeoBot.
    Inclut : fond sombre, logo NeoBot, carte principale, footer légal.
    """
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="color-scheme" content="dark light">
  <title>NeoBot</title>
</head>
<body style="margin:0;padding:0;background-color:#0a0a0a;" bgcolor="#0a0a0a">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       bgcolor="#0a0a0a" style="background-color:#0a0a0a;">
  <tr><td align="center" style="padding:28px 16px 48px;">

    <!-- Logo NeoBot -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="max-width:560px;width:100%;margin-bottom:16px;">
      <tr><td align="center" style="padding:0;">
        <img src="{_LOGO}" width="48" height="53" alt="NeoBot"
             style="display:block;border:0;outline:none;margin:0 auto 8px;">
        <div style="font-family:Arial Black,Arial,sans-serif;font-size:17px;
                    font-weight:900;letter-spacing:0.22em;color:#f0f0f0;line-height:1;">
          NEO<span style="color:#00E5CC;">BOT</span>
        </div>
      </td></tr>
    </table>

    <!-- Carte principale -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           bgcolor="#131313"
           style="max-width:560px;width:100%;background-color:#131313;
                  border-radius:14px;border:1px solid #222222;overflow:hidden;">
      {card_rows}
    </table>

    <!-- Footer légal -->
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="max-width:560px;width:100%;margin-top:20px;">
      <tr><td align="center"
              style="font-family:Arial,Helvetica,sans-serif;font-size:11px;
                     color:#3a3a3a;line-height:1.8;padding:0 16px;">
        NeoBot &middot; L'IA WhatsApp pour les businesses africains<br>
        <a href="{FRONTEND_URL}" style="color:#3a3a3a;text-decoration:none;">neobot-ai.com</a>
        &nbsp;&middot;&nbsp;
        <a href="{FRONTEND_URL}/legal" style="color:#3a3a3a;text-decoration:none;">Confidentialité</a>
        &nbsp;&middot;&nbsp;
        <a href="mailto:contact@neobot-ai.com" style="color:#3a3a3a;text-decoration:none;">Support</a>
      </td></tr>
    </table>

  </td></tr>
</table>
</body>
</html>"""


# ─── Transport HTTP Brevo ──────────────────────────────────────────────────────

async def _send(payload: dict) -> bool:
    """
    Appel HTTP vers l'API Brevo v3.
    Retourne True si succès (2xx), False sinon.
    Capture toute exception dans Sentry.
    """
    if not BREVO_API_KEY:
        logger.warning("Email non envoyé : BREVO_API_KEY absent.")
        return False

    if REPLY_TO_EMAIL and "replyTo" not in payload:
        payload["replyTo"] = {"email": REPLY_TO_EMAIL}

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
            logger.info("✅ Email envoyé → %s [%s]", to_addr, r.status_code)
            return True

        logger.error("❌ Brevo %s : %s", r.status_code, r.text[:300])
        sentry_sdk.capture_message(
            f"Brevo email failed: {r.status_code}",
            level="error",
            extras={"response_body": r.text[:300], "to": payload.get("to")},
        )
        return False

    except httpx.TimeoutException:
        logger.error("❌ Brevo timeout — email non envoyé")
        sentry_sdk.capture_message("Brevo API timeout", level="warning")
        return False
    except Exception as exc:
        logger.error("❌ Brevo exception inattendue : %s", exc)
        sentry_sdk.capture_exception(exc)
        return False


# ─── 1. Email de bienvenue ─────────────────────────────────────────────────────

async def send_welcome_email(
    to_email: str,
    user_name: str,
    tenant_name: str,
    trial_end_date: date | None = None,
    trial_days: int = 14,
) -> bool:
    trial_end_str = trial_end_date.strftime("%d/%m/%Y") if trial_end_date else ""
    date_line = (
        f"jusqu'au <strong style='color:#FF7A40;'>{trial_end_str}</strong>"
        if trial_end_str
        else f"pendant {trial_days} jours"
    )

    card = f"""
    {_accent_bar("#FF4D00")}

    <tr><td style="padding:32px 36px 0;font-family:Arial,Helvetica,sans-serif;">
      <div style="font-size:11px;font-weight:700;color:#00E5CC;letter-spacing:0.1em;
                  text-transform:uppercase;margin-bottom:10px;">
        &#10022; Compte activé
      </div>
      <h1 style="margin:0 0 10px;font-size:24px;font-weight:800;color:#f0f0f0;
                 line-height:1.25;font-family:Arial Black,Arial,sans-serif;">
        Bienvenue, {_esc.escape(user_name)}&nbsp;!
      </h1>
      <p style="margin:0 0 28px;font-size:14px;color:#777777;line-height:1.7;">
        Ton espace <strong style="color:#cccccc;">{_esc.escape(tenant_name)}</strong> est prêt.<br>
        Ton essai gratuit est actif — {date_line}.
      </p>
    </td></tr>

    <!-- Étapes de démarrage -->
    <tr><td style="padding:0 36px 28px;font-family:Arial,Helvetica,sans-serif;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">

        <tr><td style="padding:12px 0;border-bottom:1px solid #1c1c1c;">
          <table role="presentation" cellpadding="0" cellspacing="0"><tr>
            <td width="30" height="30" bgcolor="#FF4D00"
                style="background-color:#FF4D00;border-radius:50%;
                       text-align:center;vertical-align:middle;">
              <span style="font-size:13px;font-weight:800;color:#ffffff;
                           font-family:Arial,sans-serif;">1</span>
            </td>
            <td style="padding-left:12px;font-size:13px;color:#bbbbbb;
                       font-family:Arial,Helvetica,sans-serif;">
              Connecte ton numéro WhatsApp Business
            </td>
          </tr></table>
        </td></tr>

        <tr><td style="padding:12px 0;border-bottom:1px solid #1c1c1c;">
          <table role="presentation" cellpadding="0" cellspacing="0"><tr>
            <td width="30" height="30"
                style="background-color:#1a1a1a;border:1px solid #FF4D00;
                       border-radius:50%;text-align:center;vertical-align:middle;">
              <span style="font-size:13px;font-weight:800;color:#FF4D00;
                           font-family:Arial,sans-serif;">2</span>
            </td>
            <td style="padding-left:12px;font-size:13px;color:#bbbbbb;
                       font-family:Arial,Helvetica,sans-serif;">
              Configure ton premier agent IA (Libre, Vente, RDV&hellip;)
            </td>
          </tr></table>
        </td></tr>

        <tr><td style="padding:12px 0;">
          <table role="presentation" cellpadding="0" cellspacing="0"><tr>
            <td width="30" height="30"
                style="background-color:#1a1a1a;border:1px solid #2a2a2a;
                       border-radius:50%;text-align:center;vertical-align:middle;">
              <span style="font-size:13px;font-weight:800;color:#444444;
                           font-family:Arial,sans-serif;">3</span>
            </td>
            <td style="padding-left:12px;font-size:13px;color:#555555;
                       font-family:Arial,Helvetica,sans-serif;">
              Ton agent répond 24h/24 à ta place
            </td>
          </tr></table>
        </td></tr>

      </table>
    </td></tr>

    <!-- CTA -->
    <tr><td align="center" style="padding:0 36px 32px;">
      {_cta("Configurer mon agent &rarr;", f"{FRONTEND_URL}/dashboard")}
      <p style="margin:16px 0 0;font-size:12px;color:#444444;text-align:center;
                font-family:Arial,Helvetica,sans-serif;">
        Des questions&nbsp;? Réponds directement à cet email.
      </p>
    </td></tr>

    <!-- Bande stats basse -->
    <tr><td bgcolor="#0d0d0d"
           style="background-color:#0d0d0d;border-top:1px solid #1c1c1c;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr>
          {_stat_td(f"{trial_days}j", "Essai gratuit")}
          {_sep_td()}
          {_stat_td("24/7", "Disponibilité")}
          {_sep_td()}
          {_stat_td("5", "Types d'agents")}
        </tr>
      </table>
    </td></tr>
    """

    html = _wrap(card)
    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email, "name": user_name}],
        "replyTo":     {"email": REPLY_TO_EMAIL},
        "subject":     f"Bienvenue sur NeoBot — ton essai de {trial_days} jours commence maintenant",
        "htmlContent": html,
    })


# ─── 2. Confirmation d'adresse email ──────────────────────────────────────────

async def send_confirmation_email(to_email: str, confirmation_link: str) -> bool:
    card = f"""
    {_accent_bar("#00E5CC")}

    <tr><td style="padding:40px 36px 36px;font-family:Arial,Helvetica,sans-serif;
                   text-align:center;">
      <div style="font-size:40px;line-height:1;margin-bottom:16px;">&#9993;</div>
      <h1 style="margin:0 0 12px;font-size:22px;font-weight:800;color:#f0f0f0;
                 font-family:Arial Black,Arial,sans-serif;">
        Confirmez votre adresse email
      </h1>
      <p style="margin:0 0 28px;font-size:14px;color:#777777;line-height:1.7;
                max-width:380px;margin-left:auto;margin-right:auto;">
        Cliquez sur le bouton ci-dessous pour activer votre compte NeoBot.<br>
        Ce lien est valable <strong style="color:#00E5CC;">24 heures</strong>.
      </p>
      {_cta("Confirmer mon adresse email &rarr;", confirmation_link, "#00E5CC")}
      <p style="margin:20px 0 0;font-size:12px;color:#3a3a3a;
                font-family:Arial,Helvetica,sans-serif;">
        Si vous n'avez pas créé de compte NeoBot, ignorez cet email.
      </p>
    </td></tr>
    """

    html = _wrap(card)
    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email}],
        "subject":     "Confirmez votre adresse email — NeoBot",
        "htmlContent": html,
    })


# ─── 3. Réinitialisation mot de passe ─────────────────────────────────────────

async def send_password_reset_email(to_email: str, reset_link: str) -> bool:
    card = f"""
    {_accent_bar("#FF4D00")}

    <tr><td style="padding:40px 36px 36px;font-family:Arial,Helvetica,sans-serif;
                   text-align:center;">
      <div style="font-size:40px;line-height:1;margin-bottom:16px;">&#128272;</div>
      <h1 style="margin:0 0 12px;font-size:22px;font-weight:800;color:#f0f0f0;
                 font-family:Arial Black,Arial,sans-serif;">
        Réinitialisation du mot de passe
      </h1>
      <p style="margin:0 0 6px;font-size:14px;color:#777777;line-height:1.7;
                max-width:380px;margin-left:auto;margin-right:auto;">
        Vous avez demandé à réinitialiser votre mot de passe NeoBot.
      </p>
      <p style="margin:0 0 28px;font-size:13px;color:#555555;
                font-family:Arial,Helvetica,sans-serif;">
        Ce lien expire dans <strong style="color:#FF7A40;">1 heure</strong>.
      </p>
      {_cta("Réinitialiser mon mot de passe &rarr;", reset_link)}
      <p style="margin:20px 0 4px;font-size:12px;color:#3a3a3a;
                font-family:Arial,Helvetica,sans-serif;">
        Si vous n'avez pas fait cette demande, votre compte est en sécurité.
      </p>
      <p style="margin:0;font-size:10px;color:#252525;word-break:break-all;
                font-family:Arial,Helvetica,sans-serif;">
        <a href="{reset_link}" style="color:#252525;">{reset_link[:90]}...</a>
      </p>
    </td></tr>
    """

    html = _wrap(card)
    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email}],
        "subject":     "Réinitialisation de votre mot de passe NeoBot",
        "htmlContent": html,
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
        ("Plan", f'<strong style="color:#00E5CC;">{_esc.escape(plan)}</strong>'),
        ("Montant", f'<strong style="color:#f0f0f0;">{amount:,} {currency}</strong>'),
    ]
    if reference:
        rows_data.append(("Référence", _esc.escape(reference)))
    if payment_date:
        rows_data.append(("Date de paiement", _esc.escape(payment_date)))
    if next_renewal:
        rows_data.append(("Prochain renouvellement", _esc.escape(next_renewal)))
    if messages_limit:
        rows_data.append(("Messages inclus", f"{_esc.escape(messages_limit)}/mois"))

    detail_rows_html = "".join(
        f'<tr>'
        f'<td style="padding:10px 0;border-bottom:1px solid #1a1a1a;'
        f'font-size:13px;color:#666666;font-family:Arial,Helvetica,sans-serif;">{k}</td>'
        f'<td style="padding:10px 0;border-bottom:1px solid #1a1a1a;'
        f'font-size:13px;text-align:right;font-family:Arial,Helvetica,sans-serif;">{v}</td>'
        f'</tr>'
        for k, v in rows_data
    )

    card = f"""
    {_accent_bar("#22c55e")}

    <tr><td style="padding:32px 36px 8px;font-family:Arial,Helvetica,sans-serif;">
      <div style="font-size:11px;font-weight:700;color:#22c55e;letter-spacing:0.1em;
                  text-transform:uppercase;margin-bottom:10px;">
        &#10003; Paiement confirmé
      </div>
      <h1 style="margin:0 0 8px;font-size:24px;font-weight:800;color:#f0f0f0;
                 font-family:Arial Black,Arial,sans-serif;">
        Merci, {_esc.escape(tenant_name)}&nbsp;!
      </h1>
      <p style="margin:0 0 24px;font-size:14px;color:#777777;line-height:1.7;">
        Votre abonnement est activé. Votre agent IA est opérationnel.
      </p>
    </td></tr>

    <!-- Récap commande -->
    <tr><td style="padding:0 36px 28px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
        <tr><td bgcolor="#0d0d0d"
               style="background-color:#0d0d0d;border-radius:8px;
                      border:1px solid #1e1e1e;padding:4px 16px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            {detail_rows_html}
          </table>
        </td></tr>
      </table>
    </td></tr>

    <!-- CTA -->
    <tr><td align="center" style="padding:0 36px 36px;">
      {_cta("Voir mon dashboard &rarr;", f"{FRONTEND_URL}/dashboard", "#22c55e")}
    </td></tr>
    """

    html = _wrap(card)
    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": tenant_email, "name": tenant_name}],
        "replyTo":     {"email": REPLY_TO_EMAIL},
        "subject":     f"Paiement confirmé — Abonnement NeoBot {plan}",
        "htmlContent": html,
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
        accent = "#ef4444"
        badge  = "&#128680; EXPIRE DEMAIN"
        subj   = "🚨 Urgent — Votre abonnement NeoBot expire demain"
    elif days_left <= 3:
        accent = "#f97316"
        badge  = f"&#9888; EXPIRE DANS {days_left} JOURS"
        subj   = f"⚠️ Votre abonnement NeoBot expire dans {days_left} jours"
    else:
        accent = "#f59e0b"
        badge  = f"&#128197; EXPIRE DANS {days_left} JOURS"
        subj   = f"Votre abonnement NeoBot expire dans {days_left} jours"

    card = f"""
    {_accent_bar(accent)}

    <tr><td style="padding:32px 36px 28px;font-family:Arial,Helvetica,sans-serif;">
      <div style="font-size:11px;font-weight:700;color:{accent};
                  letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">
        {badge}
      </div>
      <h1 style="margin:0 0 10px;font-size:22px;font-weight:800;color:#f0f0f0;
                 font-family:Arial Black,Arial,sans-serif;">
        Votre abonnement expire bientôt
      </h1>
      <p style="margin:0 0 20px;font-size:14px;color:#777777;line-height:1.7;">
        Bonjour {_esc.escape(user_name)}, votre plan
        <strong style="color:#cccccc;">{_esc.escape(plan_name)}</strong>
        expire le <strong style="color:{accent};">{_esc.escape(expiry_date)}</strong>.
      </p>

      <!-- Montant renouvellement -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="margin-bottom:24px;">
        <tr><td bgcolor="#0d0d0d"
               style="background-color:#0d0d0d;border-radius:8px;
                      border:1px solid #1e1e1e;padding:16px 20px;">
          <div style="font-size:12px;color:#555555;margin-bottom:4px;
                      font-family:Arial,Helvetica,sans-serif;">Renouvellement à</div>
          <div style="font-size:22px;font-weight:800;color:#00E5CC;
                      font-family:Arial Black,Arial,sans-serif;">
            {renewal_price:,} {currency}
          </div>
        </td></tr>
      </table>

      {_cta("Renouveler maintenant &rarr;", f"{FRONTEND_URL}/billing", accent)}
      <p style="margin:16px 0 0;font-size:12px;color:#444444;text-align:center;
                font-family:Arial,Helvetica,sans-serif;">
        Sans renouvellement, votre agent s'arrêtera automatiquement.
      </p>
    </td></tr>
    """

    html = _wrap(card)
    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email, "name": user_name}],
        "replyTo":     {"email": REPLY_TO_EMAIL},
        "subject":     subj,
        "htmlContent": html,
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
    {_accent_bar("#00E5CC")}

    <tr><td style="padding:32px 36px 28px;font-family:Arial,Helvetica,sans-serif;">
      <div style="font-size:11px;font-weight:700;color:#00E5CC;
                  letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px;">
        &#128164; Agent en pause
      </div>
      <h1 style="margin:0 0 10px;font-size:22px;font-weight:800;color:#f0f0f0;
                 font-family:Arial Black,Arial,sans-serif;">
        Ton agent t'attend, {_esc.escape(user_name)}
      </h1>
      <p style="margin:0 0 20px;font-size:14px;color:#777777;line-height:1.7;">
        Ton agent <strong style="color:#cccccc;">{_esc.escape(agent_name)}</strong>
        n'a reçu aucune conversation depuis
        <strong style="color:#FF4D00;">{inactive_days} jours</strong>.
      </p>

      <!-- Stats activité -->
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
             style="margin-bottom:24px;">
        <tr><td bgcolor="#0d0d0d"
               style="background-color:#0d0d0d;border-radius:8px;
                      border:1px solid #1e1e1e;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            <tr>
              {_stat_td(str(total_conversations), "conversations totales")}
              {_sep_td()}
              {_stat_td(f"{inactive_days}j", "sans activité")}
            </tr>
          </table>
        </td></tr>
      </table>

      <p style="margin:0 0 24px;font-size:13px;color:#555555;line-height:1.6;">
        Vérifie que ton numéro WhatsApp est bien connecté
        et que ton agent est actif sur le dashboard.
      </p>
      {_cta("Réactiver mon agent &rarr;", f"{FRONTEND_URL}/dashboard")}
    </td></tr>
    """

    html = _wrap(card)
    return await _send({
        "sender":      {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "to":          [{"email": to_email, "name": user_name}],
        "replyTo":     {"email": REPLY_TO_EMAIL},
        "subject":     f"Ton agent NeoBot n'a pas répondu depuis {inactive_days} jours",
        "htmlContent": html,
    })


# ─── 7. NeoAlert — alerte interne admin ───────────────────────────────────────

async def send_internal_alert(subject: str, body: str) -> bool:
    """
    Email d'alerte technique pour les events critiques (crédits API, paiements, etc.).
    Envoyé à NEOPAY_ALERT_EMAIL. Design minimaliste fonctionnel, logo NeoAlert.
    """
    alert_email = os.getenv("NEOPAY_ALERT_EMAIL", "")
    if not alert_email:
        logger.warning("NEOPAY_ALERT_EMAIL non défini — alerte ignorée : %s", subject)
        return False

    env_label = os.getenv("APP_ENV", "development").upper()
    safe_subj = _esc.escape(subject)
    safe_body = _esc.escape(body)

    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"><title>NeoAlert</title></head>
<body style="margin:0;padding:0;background-color:#060606;" bgcolor="#060606">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       bgcolor="#060606" style="background-color:#060606;">
  <tr><td align="center" style="padding:28px 16px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="max-width:600px;width:100%;">

      <!-- Header NeoAlert -->
      <tr><td bgcolor="#0e0e0e"
             style="background-color:#0e0e0e;border-radius:12px 12px 0 0;
                    border:1px solid #1e1e1e;border-bottom:none;padding:18px 24px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td>
              <img src="{_LOGO}" width="28" height="31" alt="NeoBot"
                   style="display:inline-block;vertical-align:middle;
                          margin-right:8px;border:0;">
              <span style="font-family:Arial Black,Arial,sans-serif;font-size:13px;
                           font-weight:900;color:#f0f0f0;letter-spacing:0.18em;
                           vertical-align:middle;">
                NEO<span style="color:#00E5CC;">ALERT</span>
              </span>
            </td>
            <td align="right">
              <span style="font-family:Arial,Helvetica,sans-serif;font-size:11px;
                           color:#333333;letter-spacing:0.05em;">{env_label}</span>
            </td>
          </tr>
        </table>
      </td></tr>

      <!-- Barre accent -->
      <tr><td height="2" bgcolor="#FF4D00"
             style="background-color:#FF4D00;height:2px;font-size:0;line-height:0;"
             >&nbsp;</td></tr>

      <!-- Titre alerte -->
      <tr><td bgcolor="#0e0e0e"
             style="background-color:#0e0e0e;border:1px solid #1e1e1e;
                    border-top:none;border-bottom:none;padding:18px 24px 12px;">
        <div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;
                    font-weight:700;color:#FF4D00;">{safe_subj}</div>
      </td></tr>

      <!-- Corps technique -->
      <tr><td bgcolor="#080808"
             style="background-color:#080808;border:1px solid #1e1e1e;
                    border-top:none;border-radius:0 0 12px 12px;
                    padding:16px 24px 24px;">
        <pre style="margin:0;font-family:'Courier New',Courier,monospace;
                    font-size:12px;color:#7a7a7a;line-height:1.7;
                    white-space:pre-wrap;word-break:break-all;">{safe_body}</pre>
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
