"""
Endpoint demo public — visiteurs de la landing page testent en direct.

Sécurité :
- Public par conception (aucun token requis) — rate limit par IP
- Prompt système verrouillé côté serveur, non injectable par le client
- Sessions en mémoire uniquement (pas de DB, pas de PII persisté)
- Max 5 échanges / session, messages tronqués à 480 chars en entrée
- Max 200 tokens / réponse (coût maîtrisé)

Dette technique :
- Session store in-memory = ne survit pas au redémarrage / multi-instance.
  À remplacer par Redis si on scale avant 6 mois.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field

from ..limiter import limiter
from ..http_client import DeepSeekClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/demo", tags=["demo"])

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# ── Config ────────────────────────────────────────────────────────────────
_SESSION_TTL_MINUTES = 30
_MAX_EXCHANGES = 5       # messages visiteur max par session
_MAX_INPUT_CHARS = 480

# ── Session store in-memory ───────────────────────────────────────────────
# { session_id: { messages: [...], created_at: datetime, count: int } }
_SESSIONS: Dict[str, dict] = {}


def _cleanup_expired() -> None:
    """Nettoie les sessions expirées. Appelé à chaque requête (coût O(n) négligeable à MVP)."""
    cutoff = datetime.utcnow() - timedelta(minutes=_SESSION_TTL_MINUTES)
    expired = [sid for sid, s in _SESSIONS.items() if s["created_at"] < cutoff]
    for sid in expired:
        del _SESSIONS[sid]


# ── Prompt système — verrouillé serveur ──────────────────────────────────
# NéoBot joue son propre rôle : il répond aux visiteurs de la landing page
# qui veulent comprendre le produit, les tarifs, comment démarrer.
_SYSTEM_PROMPT = """\
Tu es NéoBot, un agent IA WhatsApp conçu pour les PME africaines.
Tu parles directement à un visiteur de ta landing page qui découvre le produit.
Ton rôle : convaincre avec honnêteté, répondre aux questions produit, et guider
vers l'essai gratuit.

Informations produit :
- NéoBot connecte un agent IA à WhatsApp Business d'une PME
- L'agent répond automatiquement 24h/24 aux clients (vente, RDV, support, FAQ, qualification)
- Configuration sans code : formulaire + prompt IA généré automatiquement
- Délai d'installation : moins de 30 minutes
- Plan unique : Essential — 20 000 FCFA/mois, 2 500 messages/mois, 1 agent actif
- Essai gratuit 14 jours, aucune carte bancaire requise
- Langues : français, anglais, dialectes locaux selon la configuration
- Clients cibles : restaurants, boutiques, agences, cliniques, auto-écoles, artisans
- Disponible au Cameroun, Côte d'Ivoire, Sénégal, et toute l'Afrique francophone

Règles absolues :
- Réponds en 1 à 3 phrases maximum, style WhatsApp naturel et direct
- Tu peux utiliser un emoji si c'est naturel, pas plus de 1-2 par message
- Si on te demande quelque chose hors de ta connaissance, dis-le honnêtement
- Ne promets jamais de fonctionnalités qui n'existent pas dans la liste ci-dessus
- Si le visiteur semble intéressé, invite-le à démarrer l'essai gratuit (/signup)
- Reste chaleureux mais va droit au but — les visiteurs sont sur mobile\
"""


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

    # Fenêtre de contexte : system + 10 derniers messages (5 échanges max de toute façon)
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + session["messages"][-10:]

    client = DeepSeekClient(api_key=DEEPSEEK_API_KEY)
    try:
        reply = await client.call(messages, temperature=0.72, max_tokens=200)
    except Exception as exc:
        logger.error("Demo chat DeepSeek error: %s", exc)
        # Rembourse le quota — l'échange n'a pas abouti
        session["count"] -= 1
        session["messages"].pop()  # retire le message utilisateur non traité
        raise HTTPException(status_code=502, detail="Erreur lors de la génération de la réponse")

    session["messages"].append({"role": "assistant", "content": reply})

    return DemoChatResponse(
        reply=reply,
        exchange_count=session["count"],
        max_exchanges=_MAX_EXCHANGES,
    )
