"""
Endpoint demo public — visiteurs de la landing page testent NéoBot en direct.

Sécurité :
- Public par conception (aucun token requis) — rate limit par IP
- Prompt système chargé depuis la DB (tenant configuré par DEMO_TENANT_ID)
  ou fallback hard codé si absent — non injectable par le client
- Sessions en mémoire uniquement (pas de DB, pas de PII persisté)
- Max 5 échanges / session, messages tronqués à 480 chars en entrée
- Max 200 tokens / réponse (coût maîtrisé)

Dette technique :
- Session store in-memory = ne survit pas au redémarrage / multi-instance.
  À remplacer par Redis si on scale avant 6 mois.
- Le prompt est mis en cache au premier appel (recharge au redémarrage uniquement).
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from ..limiter import limiter
from ..http_client import DeepSeekClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/demo", tags=["demo"])

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
# ID du tenant NeoBot admin dont on charge l'agent pour la démo.
DEMO_TENANT_ID = int(os.getenv("DEMO_TENANT_ID", "13"))

# ── Config ────────────────────────────────────────────────────────────────
_SESSION_TTL_MINUTES = 30
_MAX_EXCHANGES = 5       # messages visiteur max par session
_MAX_INPUT_CHARS = 480
_DAILY_CALL_LIMIT = 100  # plafond global journalier pour toute la démo

# ── Session store in-memory ───────────────────────────────────────────────
# { session_id: { messages: [...], created_at: datetime, count: int } }
_SESSIONS: Dict[str, dict] = {}
# ── Compteur global journalier (reset à minuit UTC) ───────────────────────
_daily_calls: int = 0
_daily_reset_date: Optional[str] = None   # "YYYY-MM-DD"
# ── Cache du prompt (chargé une seule fois par démarrage) ─────────────────
_cached_system_prompt: Optional[str] = None


# ── Prompt fallback — si l'agent DB n'existe pas encore ────────────────
_FALLBACK_SYSTEM_PROMPT = """\
Tu es NéoBot, l'assistant IA commercial de NeoBot — la première plateforme d'agents IA WhatsApp pour les PME africaines.
Tu parles à un visiteur qui teste le produit en direct. Ton rôle : convaincre avec honnêteté et guider vers l'essai gratuit.

PRODUIT :
NeoBot = ton WhatsApp répond automatiquement 24h/24, 7j/7. Configuration sans code, opérationnel en 30 minutes.

TYPES D'AGENTS : Libre (polyvalent), RDV & Suivi (médecins/salons), Support & FAQ (e-commerce/SAV), Vente (boutiques/restaurants), Qualification (agences B2B).

PLANS :
- Essential : 20 000 FCFA/mois — 1 agent, 2 500 messages/mois, sources PDF+Texte, analytics 30j, rappels RDV
- Business : 50 000 FCFA/mois (bientôt) — 3 agents, 5 000 messages/mois
- Enterprise : 100 000 FCFA/mois (bientôt) — illimité, analytics 90j, support WhatsApp dédié
- Essai gratuit : 14 jours, toutes fonctionnalités, aucune CB requise → neobot-ai.com/register

PAIEMENT : Orange Money 640748907 ou MTN MoMo 673745429 (DIMANI BALLA). Annulation à tout moment.

MARCHÉS : Cameroun, Côte d'Ivoire, Sénégal, toute l'Afrique francophone.
Secteurs : restaurants, boutiques, cliniques, pharmacies, agences immo, auto-écoles, hôtels, salons.

OBJECTIONS :
"Trop cher" → 8 FCFA/message, 1 client converti = rentabilisé. Essai 14j gratuit sans risque.
"Pas tech" → Aucun code, 30 minutes chrono, même interface que WhatsApp.
"Mon équipe suffit" → Le bot répond la nuit/week-end, l'équipe se concentre sur les vraies ventes.

RÈGLES ABSOLUES :
- Réponds en 1 à 3 phrases max, style WhatsApp naturel et direct
- 1 emoji max par message si naturel
- N'invente aucune fonctionnalité inexistante
- Si intéressé → invite à l'essai gratuit sur neobot-ai.com/register
- Réponds dans la langue du message (français par défaut)
- Reste chaleureux, direct, sans jargon technique\
"""


def _load_system_prompt_from_db() -> str:
    """
    Charge le prompt de l'agent du tenant DEMO_TENANT_ID depuis la DB.
    Prend en priorité custom_prompt_override, puis system_prompt.
    Retourne le fallback si aucun agent trouvé ou erreur DB.
    Mis en cache après le premier appel réussi.
    """
    global _cached_system_prompt
    if _cached_system_prompt is not None:
        return _cached_system_prompt

    try:
        from ..database import SessionLocal
        from sqlalchemy import text

        db = SessionLocal()
        try:
            row = db.execute(
                text("""
                    SELECT
                        COALESCE(custom_prompt_override, system_prompt) AS prompt,
                        name
                    FROM agent_templates
                    WHERE tenant_id = :tid
                      AND COALESCE(custom_prompt_override, system_prompt) IS NOT NULL
                      AND COALESCE(custom_prompt_override, system_prompt) != ''
                    ORDER BY id DESC
                    LIMIT 1
                """),
                {"tid": DEMO_TENANT_ID},
            ).fetchone()
        finally:
            db.close()

        if row and row.prompt:
            logger.info(
                "Demo: prompt chargé depuis DB (tenant=%s, agent='%s', %d chars)",
                DEMO_TENANT_ID, row.name, len(row.prompt),
            )
            _cached_system_prompt = row.prompt
        else:
            logger.info(
                "Demo: aucun agent trouvé pour tenant=%s — fallback",
                DEMO_TENANT_ID,
            )
            _cached_system_prompt = _FALLBACK_SYSTEM_PROMPT

    except Exception as exc:
        logger.warning("Demo: erreur chargement prompt DB (%s) — fallback", exc)
        _cached_system_prompt = _FALLBACK_SYSTEM_PROMPT

    return _cached_system_prompt

def _cleanup_expired() -> None:
    """Nettoie les sessions expirées. Appelé à chaque requête (coût O(n) négligeable à MVP)."""
    cutoff = datetime.utcnow() - timedelta(minutes=_SESSION_TTL_MINUTES)
    expired = [sid for sid, s in _SESSIONS.items() if s["created_at"] < cutoff]
    for sid in expired:
        del _SESSIONS[sid]


def _check_daily_limit() -> bool:
    """Retourne True si le plafond journalier est atteint."""
    global _daily_calls, _daily_reset_date
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if _daily_reset_date != today:
        _daily_calls = 0
        _daily_reset_date = today
    return _daily_calls >= _DAILY_CALL_LIMIT


def _increment_daily() -> None:
    global _daily_calls
    _daily_calls += 1


# ── Schémas ───────────────────────────────────────────────────────────────
class DemoChatRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=64, pattern=r'^[a-zA-Z0-9_-]+$')
    message: str = Field(..., min_length=1, max_length=_MAX_INPUT_CHARS)


class DemoChatResponse(BaseModel):
    reply: str
    exchange_count: int
    max_exchanges: int


# ── Route ─────────────────────────────────────────────────────────────────
@router.post("/chat", response_model=DemoChatResponse)
@limiter.limit("8/minute")
async def demo_chat(request: Request, body: DemoChatRequest):
    """
    Chat demo public. Aucune auth. Rate-limited à 8 req/min par IP.
    Retourne 429 si la limite de session est atteinte.
    """
    if not DEEPSEEK_API_KEY:
        raise HTTPException(status_code=503, detail="Service temporairement indisponible")

    if _check_daily_limit():
        raise HTTPException(status_code=429, detail="Démo temporairement indisponible, réessayez demain")

    _cleanup_expired()

    sid = body.session_id
    if sid not in _SESSIONS:
        _SESSIONS[sid] = {
            "messages": [],
            "created_at": datetime.utcnow(),
            "count": 0,
        }

    session = _SESSIONS[sid]

    if session["count"] >= _MAX_EXCHANGES:
        raise HTTPException(status_code=429, detail="Limite de la démo atteinte")

    user_text = body.message[:_MAX_INPUT_CHARS]
    session["messages"].append({"role": "user", "content": user_text})
    session["count"] += 1

    # Fenêtre de contexte : system + 10 derniers messages
    system_prompt = _load_system_prompt_from_db()
    messages = [{"role": "system", "content": system_prompt}] + session["messages"][-10:]

    result = await DeepSeekClient.call(messages, temperature=0.72, max_tokens=200)

    # DeepSeekClient.call() retourne {"error": "..."} en cas d'échec API (pas d'exception)
    if "error" in result:
        logger.error("Demo chat DeepSeek error: %s", result["error"])
        session["count"] -= 1
        session["messages"].pop()
        raise HTTPException(status_code=502, detail="Erreur lors de la génération de la réponse")

    try:
        reply = result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        logger.error("Demo: structure réponse DeepSeek inattendue (%s): %s", exc, result)
        session["count"] -= 1
        session["messages"].pop()
        raise HTTPException(status_code=502, detail="Erreur lors de la génération de la réponse")

    session["messages"].append({"role": "assistant", "content": reply})
    _increment_daily()

    return DemoChatResponse(
        reply=reply,
        exchange_count=session["count"],
        max_exchanges=_MAX_EXCHANGES,
    )


# ── Reset cache prompt (appelé après modification de l'agent dans le dashboard) ──
@router.post("/reload-prompt")
async def reload_demo_prompt():
    """Force le rechargement du prompt depuis la DB (après modification de l'agent)."""
    global _cached_system_prompt
    _cached_system_prompt = None
    new_prompt = _load_system_prompt_from_db()
    source = "fallback" if new_prompt == _FALLBACK_SYSTEM_PROMPT else "db"
    return {"status": "ok", "prompt_chars": len(new_prompt), "source": source}
