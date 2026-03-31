#!/usr/bin/env python3
"""
Crée les 4 templates email NeoBot dans Brevo via l'API REST.
Utilise la clé BREVO_API_KEY depuis .env (ou env variable directe).

Usage :
  source /home/tim/neobot-mvp/.venv/bin/activate
  cd /home/tim/neobot-mvp/backend
  python scripts/create_brevo_templates.py

Résultat : affiche les IDs des templates créés à enregistrer dans .env
  BREVO_TPL_WELCOME=X
  BREVO_TPL_PAYMENT=X
  BREVO_TPL_EXPIRY=X
  BREVO_TPL_INACTIVITY=X
"""

import os
import sys
import json
import httpx

# ─── Charger .env si disponible ───────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
if not BREVO_API_KEY:
    print("❌  BREVO_API_KEY absent. Configure-le dans backend/.env")
    sys.exit(1)

SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "contact@neobot-ai.com")
SENDER_NAME  = os.getenv("BREVO_SENDER_NAME", "NeoBot")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://neobot-ai.com")

HEADERS = {
    "accept":       "application/json",
    "content-type": "application/json",
    "api-key":      BREVO_API_KEY,
}

# ─── Composants HTML partagés ─────────────────────────────────────────────────

def _header(title: str, subtitle: str = "") -> str:
    return f"""
    <!-- LOGO + HEADER -->
    <tr>
      <td style="background:linear-gradient(135deg,#FF4D00 0%,#FF7A40 100%);
                 padding:36px 40px;text-align:center;border-radius:12px 12px 0 0;">
        <table cellpadding="0" cellspacing="0" style="margin:0 auto 18px;">
          <tr>
            <td style="background:rgba(0,0,0,0.25);border-radius:10px;padding:8px 16px;">
              <!-- Logo SVG inline -->
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                   style="vertical-align:middle;margin-right:8px;"
                   xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="11" stroke="#fff" stroke-width="1.5"/>
                <path d="M8 9h8M8 12h5M8 15h7" stroke="#fff" stroke-width="1.5"
                      stroke-linecap="round"/>
              </svg>
              <span style="color:#fff;font-family:Arial,sans-serif;font-weight:900;
                           font-size:18px;letter-spacing:2px;vertical-align:middle;">
                NEOBOT
              </span>
            </td>
          </tr>
        </table>
        <h1 style="color:#fff;margin:0;font-size:22px;font-weight:800;
                   font-family:Arial,sans-serif;line-height:1.3;">
          {title}
        </h1>
        {"<p style='color:rgba(255,255,255,0.82);margin:8px 0 0;font-size:14px;font-family:Arial,sans-serif;'>" + subtitle + "</p>" if subtitle else ""}
      </td>
    </tr>"""


def _footer() -> str:
    return f"""
    <!-- FOOTER -->
    <tr>
      <td style="padding:22px 40px;border-top:1px solid #2a2a2a;text-align:center;
                 background:#141414;border-radius:0 0 12px 12px;">
        <p style="margin:0 0 8px;color:#444;font-size:12px;font-family:Arial,sans-serif;">
          NéoBot · Agents IA WhatsApp pour les entreprises africaines
        </p>
        <p style="margin:0;font-size:11px;font-family:Arial,sans-serif;">
          <a href="{FRONTEND_URL}/legal?tab=cgu"
             style="color:#555;text-decoration:none;">CGU</a>
          &nbsp;·&nbsp;
          <a href="{FRONTEND_URL}/legal?tab=confidentialite"
             style="color:#555;text-decoration:none;">Confidentialité</a>
          &nbsp;·&nbsp;
          <a href="{FRONTEND_URL}/legal?tab=mentions"
             style="color:#555;text-decoration:none;">Mentions légales</a>
          &nbsp;·&nbsp;
          <a href="{{{{ unsubscribeUrl }}}}"
             style="color:#555;text-decoration:none;">Se désinscrire</a>
        </p>
        <p style="margin:8px 0 0;color:#333;font-size:10px;font-family:Arial,sans-serif;">
          contact@neobot-ai.com · Yaoundé, Cameroun
        </p>
      </td>
    </tr>"""


def _wrap(content: str) -> str:
    """Enroule le contenu dans le layout email de base."""
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <meta name="color-scheme" content="dark">
  <title>NeoBot</title>
</head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#0a0a0a;min-height:100vh;">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#1a1a1a;border-radius:12px;
                      max-width:600px;width:100%;
                      box-shadow:0 4px 40px rgba(255,77,0,0.12);">
          {content}
        </table>
        <p style="margin:20px 0 0;color:#2a2a2a;font-size:11px;font-family:Arial,sans-serif;">
          © 2026 NéoBot — DIMANI BALLA TIM PATRICK, Yaoundé, Cameroun
        </p>
      </td>
    </tr>
  </table>
</body>
</html>"""


# ─── Template 1 — Bienvenue ────────────────────────────────────────────────────

T1_HTML = _wrap(
    _header("Bienvenue sur NéoBot 🤖", "Votre agent IA WhatsApp est prêt à démarrer")
    + """
    <!-- BODY -->
    <tr>
      <td style="padding:36px 40px;color:#e0e0e0;font-size:15px;line-height:1.75;
                 font-family:Arial,sans-serif;">

        <p style="margin:0 0 20px;">
          Bonjour <strong style="color:#fff;">{{ params.USER_NAME }}</strong>,
        </p>
        <p style="margin:0 0 16px;color:#bbb;">
          Bienvenue sur <strong style="color:#FF7A40;">NéoBot</strong> ! Votre compte
          <strong style="color:#fff;">{{ params.TENANT_NAME }}</strong> est activé.
          Votre essai gratuit de
          <strong style="color:#FF7A40;">{{ params.TRIAL_DAYS }} jours</strong>
          commence dès maintenant — sans carte bancaire.
        </p>

        <!-- Badges plan -->
        <table cellpadding="0" cellspacing="0" style="margin:20px 0;">
          <tr>
            <td style="background:rgba(255,77,0,0.1);border:1px solid rgba(255,77,0,0.25);
                       border-radius:6px;padding:6px 14px;">
              <span style="color:#FF7A40;font-size:13px;font-weight:700;">
                ✅ Essai gratuit · {{ params.TRIAL_DAYS }} jours
              </span>
            </td>
          </tr>
        </table>

        <p style="margin:0 0 8px;color:#999;font-size:14px;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.5px;">
          Commencez en 3 étapes :
        </p>
        <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr>
            <td style="padding:10px 0;border-bottom:1px solid #252525;vertical-align:top;">
              <span style="color:#FF7A40;font-weight:700;font-size:22px;margin-right:14px;
                           vertical-align:middle;">1</span>
              <span style="color:#ccc;font-size:14px;vertical-align:middle;">
                Connectez votre numéro WhatsApp via le dashboard
              </span>
            </td>
          </tr>
          <tr>
            <td style="padding:10px 0;border-bottom:1px solid #252525;vertical-align:top;">
              <span style="color:#FF7A40;font-weight:700;font-size:22px;margin-right:14px;
                           vertical-align:middle;">2</span>
              <span style="color:#ccc;font-size:14px;vertical-align:middle;">
                Configurez votre agent IA (type, personnalité, base de connaissance)
              </span>
            </td>
          </tr>
          <tr>
            <td style="padding:10px 0;vertical-align:top;">
              <span style="color:#FF7A40;font-weight:700;font-size:22px;margin-right:14px;
                           vertical-align:middle;">3</span>
              <span style="color:#ccc;font-size:14px;vertical-align:middle;">
                Testez votre bot en lui envoyant un message WhatsApp
              </span>
            </td>
          </tr>
        </table>

        <!-- CTA principal -->
        <div style="text-align:center;margin:32px 0 24px;">
          <a href="{{ params.DASHBOARD_URL }}"
             style="background:linear-gradient(135deg,#FF4D00 0%,#FF7A40 100%);
                    color:#fff;text-decoration:none;padding:15px 40px;
                    border-radius:8px;font-weight:700;font-size:15px;
                    display:inline-block;letter-spacing:0.3px;">
            Accéder à mon dashboard →
          </a>
        </div>

        <!-- CTA secondaire démo -->
        <div style="text-align:center;margin:0 0 28px;">
          <a href="{{ params.DEMO_URL }}"
             style="color:#FF7A40;text-decoration:none;font-size:13px;
                    border-bottom:1px solid rgba(255,122,64,0.3);padding-bottom:2px;">
            Voir une démo WhatsApp en direct →
          </a>
        </div>

        <p style="margin:0;color:#555;font-size:12px;line-height:1.6;">
          Des questions ? Répondez à cet email — notre équipe vous répond sous 24h.
          <br>Essai se terminant le : <strong style="color:#777;">{{ params.TRIAL_END_DATE }}</strong>
        </p>
      </td>
    </tr>
    """ + _footer()
)

# ─── Template 2 — Confirmation paiement ──────────────────────────────────────

T2_HTML = _wrap(
    _header("Paiement confirmé ✅", "Votre abonnement NéoBot est maintenant actif")
    + """
    <tr>
      <td style="padding:36px 40px;color:#e0e0e0;font-size:15px;line-height:1.75;
                 font-family:Arial,sans-serif;">

        <p style="margin:0 0 20px;">
          Bonjour <strong style="color:#fff;">{{ params.USER_NAME }}</strong>,
        </p>
        <p style="margin:0 0 24px;color:#bbb;">
          Votre paiement a été traité avec succès. Le plan
          <strong style="color:#00E5CC;">{{ params.PLAN_NAME }}</strong>
          est maintenant actif sur votre compte.
        </p>

        <!-- Récapitulatif paiement -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#111;border:1px solid #252525;border-radius:10px;
                      margin:0 0 28px;overflow:hidden;">
          <tr>
            <td colspan="2"
                style="padding:12px 18px;background:#1f1f1f;
                       font-size:12px;color:#666;font-weight:700;
                       text-transform:uppercase;letter-spacing:0.5px;
                       border-bottom:1px solid #252525;">
              Récapitulatif
            </td>
          </tr>
          <tr>
            <td style="padding:13px 18px;color:#888;font-size:14px;
                       border-bottom:1px solid #1e1e1e;">Plan activé</td>
            <td style="padding:13px 18px;text-align:right;font-weight:700;
                       color:#00E5CC;font-size:14px;
                       border-bottom:1px solid #1e1e1e;">{{ params.PLAN_NAME }}</td>
          </tr>
          <tr>
            <td style="padding:13px 18px;color:#888;font-size:14px;
                       border-bottom:1px solid #1e1e1e;">Montant payé</td>
            <td style="padding:13px 18px;text-align:right;font-weight:700;
                       color:#fff;font-size:14px;
                       border-bottom:1px solid #1e1e1e;">
              {{ params.AMOUNT }} {{ params.CURRENCY }}
            </td>
          </tr>
          <tr>
            <td style="padding:13px 18px;color:#888;font-size:14px;
                       border-bottom:1px solid #1e1e1e;">Référence</td>
            <td style="padding:13px 18px;text-align:right;color:#555;
                       font-size:12px;font-family:monospace;
                       border-bottom:1px solid #1e1e1e;">{{ params.REFERENCE }}</td>
          </tr>
          <tr>
            <td style="padding:13px 18px;color:#888;font-size:14px;
                       border-bottom:1px solid #1e1e1e;">Date de paiement</td>
            <td style="padding:13px 18px;text-align:right;color:#ccc;
                       font-size:14px;border-bottom:1px solid #1e1e1e;">
              {{ params.PAYMENT_DATE }}
            </td>
          </tr>
          <tr>
            <td style="padding:13px 18px;color:#888;font-size:14px;">
              Prochain renouvellement
            </td>
            <td style="padding:13px 18px;text-align:right;font-weight:700;
                       color:#FF7A40;font-size:14px;">{{ params.NEXT_RENEWAL }}</td>
          </tr>
        </table>

        <!-- Fonctionnalités débloquées -->
        <p style="margin:0 0 12px;color:#999;font-size:13px;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.5px;">
          Fonctionnalités actives sur {{ params.PLAN_NAME }} :
        </p>
        <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr>
            <td style="padding:7px 0;color:#bbb;font-size:13px;">
              <span style="color:#00E5CC;margin-right:8px;">✓</span>
              {{ params.MESSAGES_LIMIT }} messages/mois
            </td>
          </tr>
          <tr>
            <td style="padding:7px 0;color:#bbb;font-size:13px;">
              <span style="color:#00E5CC;margin-right:8px;">✓</span>
              Agents IA illimités
            </td>
          </tr>
          <tr>
            <td style="padding:7px 0;color:#bbb;font-size:13px;">
              <span style="color:#00E5CC;margin-right:8px;">✓</span>
              Analytics avancés
            </td>
          </tr>
          <tr>
            <td style="padding:7px 0;color:#bbb;font-size:13px;">
              <span style="color:#00E5CC;margin-right:8px;">✓</span>
              Support prioritaire
            </td>
          </tr>
        </table>

        <!-- CTA -->
        <div style="text-align:center;margin:28px 0 24px;">
          <a href="{{ params.DASHBOARD_URL }}"
             style="background:linear-gradient(135deg,#FF4D00 0%,#FF7A40 100%);
                    color:#fff;text-decoration:none;padding:15px 40px;
                    border-radius:8px;font-weight:700;font-size:15px;
                    display:inline-block;">
            Accéder à mon dashboard →
          </a>
        </div>

        <p style="margin:0;color:#555;font-size:12px;">
          Besoin d'une facture ou d'un justificatif ? Répondez à cet email.
        </p>
      </td>
    </tr>
    """ + _footer()
)

# ─── Template 3 — Abonnement expire bientôt ──────────────────────────────────

T3_HTML = _wrap(
    _header("⏳ Votre abonnement expire dans {{ params.DAYS_LEFT }} jours",
            "Renouvelez maintenant pour ne pas perdre votre accès")
    + """
    <tr>
      <td style="padding:36px 40px;color:#e0e0e0;font-size:15px;line-height:1.75;
                 font-family:Arial,sans-serif;">

        <p style="margin:0 0 20px;">
          Bonjour <strong style="color:#fff;">{{ params.USER_NAME }}</strong>,
        </p>

        <!-- Alerte bannière -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:rgba(255,77,0,0.08);
                      border:1px solid rgba(255,77,0,0.3);
                      border-radius:8px;margin:0 0 24px;">
          <tr>
            <td style="padding:16px 20px;">
              <p style="margin:0;color:#FF7A40;font-size:14px;font-weight:700;">
                ⚠️  Expiration le {{ params.EXPIRY_DATE }}
              </p>
              <p style="margin:6px 0 0;color:#bbb;font-size:13px;">
                Votre plan <strong style="color:#fff;">{{ params.PLAN_NAME }}</strong>
                expire dans <strong style="color:#FF4D00;">{{ params.DAYS_LEFT }} jours</strong>.
              </p>
            </td>
          </tr>
        </table>

        <p style="margin:0 0 16px;color:#bbb;">
          Si vous ne renouvelez pas avant cette date :
        </p>

        <!-- Conséquences -->
        <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #222;color:#888;font-size:13px;">
              <span style="color:#FF4D00;margin-right:8px;font-weight:700;">✗</span>
              Votre agent IA WhatsApp sera mis en pause
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #222;color:#888;font-size:13px;">
              <span style="color:#FF4D00;margin-right:8px;font-weight:700;">✗</span>
              Vos contacts ne recevront plus de réponses automatiques
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;border-bottom:1px solid #222;color:#888;font-size:13px;">
              <span style="color:#FF4D00;margin-right:8px;font-weight:700;">✗</span>
              Vos données seront conservées 30 jours puis supprimées
            </td>
          </tr>
          <tr>
            <td style="padding:8px 0;color:#888;font-size:13px;">
              <span style="color:#00E5CC;margin-right:8px;font-weight:700;">✓</span>
              Le renouvellement conserve toutes vos configurations et données
            </td>
          </tr>
        </table>

        <!-- Récap plan actuel -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#111;border:1px solid #252525;border-radius:8px;
                      margin:0 0 28px;">
          <tr>
            <td style="padding:12px 18px;color:#888;font-size:14px;
                       border-bottom:1px solid #1e1e1e;">Plan actuel</td>
            <td style="padding:12px 18px;text-align:right;color:#FF7A40;
                       font-weight:700;font-size:14px;
                       border-bottom:1px solid #1e1e1e;">{{ params.PLAN_NAME }}</td>
          </tr>
          <tr>
            <td style="padding:12px 18px;color:#888;font-size:14px;">
              Tarif renouvellement
            </td>
            <td style="padding:12px 18px;text-align:right;color:#fff;
                       font-weight:700;font-size:14px;">
              {{ params.RENEWAL_PRICE }} {{ params.CURRENCY }}/mois
            </td>
          </tr>
        </table>

        <!-- CTA -->
        <div style="text-align:center;margin:28px 0 16px;">
          <a href="{{ params.RENEWAL_URL }}"
             style="background:linear-gradient(135deg,#FF4D00 0%,#FF7A40 100%);
                    color:#fff;text-decoration:none;padding:15px 40px;
                    border-radius:8px;font-weight:700;font-size:15px;
                    display:inline-block;">
            Renouveler mon abonnement →
          </a>
        </div>

        <p style="margin:0;color:#555;font-size:12px;text-align:center;">
          Renouvellement en 2 minutes · Paiement sécurisé Mobile Money / Carte
        </p>
      </td>
    </tr>
    """ + _footer()
)

# ─── Template 4 — Relance inactivité ─────────────────────────────────────────

T4_HTML = _wrap(
    _header("NeoBot vous attend 👋", "Vous n'avez pas utilisé votre agent depuis {{ params.INACTIVE_DAYS }} jours")
    + """
    <tr>
      <td style="padding:36px 40px;color:#e0e0e0;font-size:15px;line-height:1.75;
                 font-family:Arial,sans-serif;">

        <p style="margin:0 0 20px;">
          Bonjour <strong style="color:#fff;">{{ params.USER_NAME }}</strong>,
        </p>
        <p style="margin:0 0 24px;color:#bbb;">
          Nous avons remarqué que votre agent IA
          <strong style="color:#fff;">{{ params.AGENT_NAME }}</strong>
          n'a pas reçu de conversations depuis <strong style="color:#FF7A40;">
          {{ params.INACTIVE_DAYS }} jours</strong>.
          Votre bot est prêt — il ne manque plus que vos clients.
        </p>

        <!-- Stats compte -->
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:#111;border:1px solid #252525;border-radius:10px;
                      margin:0 0 28px;overflow:hidden;">
          <tr>
            <td colspan="2"
                style="padding:10px 18px;background:#1a1a1a;font-size:11px;
                       color:#555;font-weight:700;text-transform:uppercase;
                       letter-spacing:0.5px;border-bottom:1px solid #222;">
              Votre compte
            </td>
          </tr>
          <tr>
            <td style="padding:12px 18px;color:#777;font-size:13px;
                       border-bottom:1px solid #1a1a1a;">Agent configuré</td>
            <td style="padding:12px 18px;text-align:right;color:#fff;
                       font-size:13px;border-bottom:1px solid #1a1a1a;">
              {{ params.AGENT_NAME }}
            </td>
          </tr>
          <tr>
            <td style="padding:12px 18px;color:#777;font-size:13px;
                       border-bottom:1px solid #1a1a1a;">Plan actif</td>
            <td style="padding:12px 18px;text-align:right;color:#FF7A40;
                       font-weight:700;font-size:13px;
                       border-bottom:1px solid #1a1a1a;">{{ params.PLAN_NAME }}</td>
          </tr>
          <tr>
            <td style="padding:12px 18px;color:#777;font-size:13px;">
              Conversations total
            </td>
            <td style="padding:12px 18px;text-align:right;color:#ccc;font-size:13px;">
              {{ params.TOTAL_CONVERSATIONS }}
            </td>
          </tr>
        </table>

        <!-- Tips -->
        <p style="margin:0 0 12px;color:#999;font-size:13px;font-weight:700;
                  text-transform:uppercase;letter-spacing:0.5px;">
          3 façons d'activer votre bot dès aujourd'hui :
        </p>
        <table width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr>
            <td style="padding:10px 14px;background:#111;border-radius:6px;
                       margin-bottom:8px;display:block;border-left:3px solid #FF4D00;">
              <span style="color:#FF7A40;font-weight:700;font-size:13px;">
                💬 Partagez votre numéro WhatsApp
              </span>
              <p style="margin:4px 0 0;color:#777;font-size:13px;">
                Ajoutez votre numéro dans vos signatures email, profils sociaux et carte de visite.
              </p>
            </td>
          </tr>
          <tr><td style="height:8px;"></td></tr>
          <tr>
            <td style="padding:10px 14px;background:#111;border-radius:6px;
                       border-left:3px solid #FF7A40;">
              <span style="color:#FF7A40;font-weight:700;font-size:13px;">
                📚 Enrichissez la base de connaissance
              </span>
              <p style="margin:4px 0 0;color:#777;font-size:13px;">
                Ajoutez vos FAQ, tarifs, horaires — votre bot répondra à 80% des questions.
              </p>
            </td>
          </tr>
          <tr><td style="height:8px;"></td></tr>
          <tr>
            <td style="padding:10px 14px;background:#111;border-radius:6px;
                       border-left:3px solid #00E5CC;">
              <span style="color:#00E5CC;font-weight:700;font-size:13px;">
                🚀 Testez le bot vous-même
              </span>
              <p style="margin:4px 0 0;color:#777;font-size:13px;">
                Envoyez un message à votre propre numéro connecté et voyez la magie opérer.
              </p>
            </td>
          </tr>
        </table>

        <!-- CTA -->
        <div style="text-align:center;margin:28px 0 24px;">
          <a href="{{ params.DASHBOARD_URL }}"
             style="background:linear-gradient(135deg,#FF4D00 0%,#FF7A40 100%);
                    color:#fff;text-decoration:none;padding:15px 40px;
                    border-radius:8px;font-weight:700;font-size:15px;
                    display:inline-block;">
            Accéder à mon dashboard →
          </a>
        </div>

        <p style="margin:0;color:#555;font-size:12px;text-align:center;">
          Besoin d'aide pour configurer votre agent ?
          <a href="mailto:contact@neobot-ai.com"
             style="color:#FF4D00;text-decoration:none;">
            Contactez-nous
          </a>
        </p>
      </td>
    </tr>
    """ + _footer()
)


# ─── Définition des templates ─────────────────────────────────────────────────

TEMPLATES = [
    {
        "name":    "NeoBot — Bienvenue après inscription",
        "subject": "Bienvenue sur NeoBot 🤖 — votre essai de {{ params.TRIAL_DAYS }} jours commence !",
        "html":    T1_HTML,
        "tag":     "BREVO_TPL_WELCOME",
    },
    {
        "name":    "NeoBot — Confirmation paiement",
        "subject": "Paiement confirmé — NeoBot {{ params.PLAN_NAME }} activé ✅",
        "html":    T2_HTML,
        "tag":     "BREVO_TPL_PAYMENT",
    },
    {
        "name":    "NeoBot — Abonnement expire bientôt",
        "subject": "⏳ Votre abonnement NeoBot expire dans {{ params.DAYS_LEFT }} jours",
        "html":    T3_HTML,
        "tag":     "BREVO_TPL_EXPIRY",
    },
    {
        "name":    "NeoBot — Relance inactivité",
        "subject": "NeoBot vous attend 👋 — votre agent IA est prêt",
        "html":    T4_HTML,
        "tag":     "BREVO_TPL_INACTIVITY",
    },
]


# ─── Création via l'API Brevo ─────────────────────────────────────────────────

def create_template(name: str, subject: str, html: str) -> int | None:
    """Crée un template Brevo et retourne son ID."""
    payload = {
        "templateName": name,
        "subject":      subject,
        "htmlContent":  html,
        "sender":       {"name": SENDER_NAME, "email": SENDER_EMAIL},
        "isActive":     True,
        "replyTo":      SENDER_EMAIL,
        "toField":      "{{ contact.FIRSTNAME }} {{ contact.LASTNAME }}",
    }
    try:
        response = httpx.post(
            "https://api.brevo.com/v3/smtp/templates",
            json=payload,
            headers=HEADERS,
            timeout=15.0,
        )
        if response.is_success:
            data = response.json()
            return data.get("id")
        else:
            print(f"  ❌ Erreur {response.status_code}: {response.text[:200]}")
            return None
    except Exception as exc:
        print(f"  ❌ Exception: {exc}")
        return None


def main():
    print("=" * 55)
    print("  NeoBot — Création des templates Brevo")
    print("=" * 55)
    print(f"  Expéditeur : {SENDER_NAME} <{SENDER_EMAIL}>")
    print(f"  API Key    : {BREVO_API_KEY[:12]}...")
    print("=" * 55)

    results = {}

    for tpl in TEMPLATES:
        print(f"\n📧 Création : {tpl['name']}")
        template_id = create_template(tpl["name"], tpl["subject"], tpl["html"])
        if template_id:
            results[tpl["tag"]] = template_id
            print(f"  ✅ Créé avec l'ID : {template_id}")
        else:
            print(f"  ❌ Échec de création")

    print("\n" + "=" * 55)
    print("  Résultat — à ajouter dans backend/.env :")
    print("=" * 55)
    for env_key, tpl_id in results.items():
        print(f"  {env_key}={tpl_id}")

    print("\n" + "=" * 55)
    created = len(results)
    total   = len(TEMPLATES)
    print(f"  {created}/{total} templates créés avec succès")
    if created == total:
        print("  ✅ Tous les templates sont prêts dans Brevo")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
