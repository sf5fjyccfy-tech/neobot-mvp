"""
Service Claude Haiku — analyse automatique des erreurs Sentry pour le debugging interne NeoBot.

Claude Haiku 4.5 est UNIQUEMENT utilisé ici pour l'analyse d'erreurs.
DeepSeek reste l'IA des agents NeoBot pour les clients WhatsApp.

Prompt caching Anthropic activé : économie ~90% sur le prompt système
(même prompt pour toutes les analyses → mis en cache par Anthropic).
"""
import json
import logging
import os
from typing import Optional

import sentry_sdk

logger = logging.getLogger(__name__)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# Prompt système partagé pour toutes les analyses — mis en cache par Anthropic.
# Le cache se déclenche automatiquement dès que le bloc est identique entre appels.
_SYSTEM_PROMPT = """Tu es un expert en debugging Python/FastAPI et Node.js/Baileys. Tu analyses des erreurs capturées par Sentry dans NeoBot, un assistant conversationnel WhatsApp + SaaS avec :
- Backend FastAPI Python
- Frontend Next.js 14
- Service WhatsApp Node.js/Baileys
- Base PostgreSQL
- Paiements via Korapay/CamPay (module NeopPay)
- Agents IA : DeepSeek API pour les réponses clients WhatsApp

Réponds UNIQUEMENT en JSON valide sans markdown ni bloc de code. Le JSON doit contenir exactement ces clés :
{
  "severite": "critique ou haute ou moyenne",
  "cause_probable": "explication claire en français, 2-3 phrases maximum",
  "impact": "ce que ça casse concrètement pour les utilisateurs",
  "solution": "étapes précises numérotées pour corriger",
  "fichiers_concernes": ["liste des fichiers à modifier"],
  "necessite_intervention": true ou false,
  "prompt_agent": "prompt complet prêt à envoyer à GitHub Copilot dans VSCode pour corriger le bug, avec contexte NeoBot inclus. null si pas nécessaire",
  "titre_issue": "titre court pour GitHub Issue (50 chars max)",
  "labels": ["bug", "critique ou haute ou moyenne", "backend ou frontend ou whatsapp"]
}"""


async def analyze_sentry_error(
    error_message: str,
    stack_trace: str,
    service: str,
    occurrences_24h: int,
    first_seen: str,
    last_seen: str,
    sentry_url: Optional[str] = None,
) -> Optional[dict]:
    """
    Envoie une erreur Sentry à Claude Haiku pour analyse.

    Returns:
        dict avec les clés: severite, cause_probable, impact, solution,
        fichiers_concernes, necessite_intervention, prompt_agent,
        titre_issue, labels
        None si l'API échoue ou la clé est absente.
    """
    if not ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY non défini — analyse Claude désactivée")
        return None

    try:
        import anthropic
    except ImportError:
        logger.error("Package 'anthropic' non installé — lancez: pip install anthropic")
        return None

    user_content = f"""Erreur Sentry capturée dans NeoBot :

**Service :** {service}
**Occurrences (24h) :** {occurrences_24h}
**Première vue :** {first_seen}
**Dernière vue :** {last_seen}
{f"**Lien Sentry :** {sentry_url}" if sentry_url else ""}

**Message d'erreur :**
{error_message}

**Stack trace :**
{stack_trace}

Analyse cette erreur et retourne le JSON demandé."""

    try:
        client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

        response = await client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    # Prompt caching : économise 90% sur les tokens système
                    # (même contenu → Anthropic ne le retraite pas)
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_content}],
        )

        raw_text = response.content[0].text.strip()

        # Nettoyer si Claude a quand même mis du markdown malgré la consigne
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        raw_text = raw_text.strip()

        analysis = json.loads(raw_text)
        logger.info(
            "Claude analyse — service: %s, sévérité: %s, intervention: %s",
            service, analysis.get("severite"), analysis.get("necessite_intervention")
        )
        return analysis

    except json.JSONDecodeError as exc:
        logger.error("Claude n'a pas retourné de JSON valide: %s", exc)
        sentry_sdk.capture_exception(exc)
        return None
    except Exception as exc:
        logger.error("Erreur appel Claude: %s", exc)
        sentry_sdk.capture_exception(exc)
        return None
