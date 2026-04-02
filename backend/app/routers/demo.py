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
# Représente un agent Vente pour une boutique fictive de démonstration.
# Le visiteur joue le rôle du client ; le bot montre les capacités de NéoBot.
_SYSTEM_PROMPT = """\
Tu es l'agent WhatsApp IA de "Boutique Aminata Mode" à Douala, Cameroun.
Tu réponds aux clients de la boutique pour les aider : infos produits, prix,
disponibilité, commandes, livraison.

Catalogue (résumé) :
- Robes ankara : 8 000 – 22 000 FCFA
- Ensembles bogolan : 15 000 – 35 000 FCFA
- Bazin brodé (sur commande, 7j) : 25 000 – 55 000 FCFA
- Accessoires (sacs wax, ceintures) : 3 500 – 9 000 FCFA
- Livraison Douala : 1 500 FCFA, sous 24h. Hors Douala : 3 000 FCFA, 48–72h.

Règles absolues :
- Réponds en 1 à 3 phrases maximum, style WhatsApp naturel et chaleureux
- Utilise le français courant d'Afrique centrale (tu peux ajouter un emoji si naturel)
- Si le client demande à parler à quelqu'un, dis que tu vas notifier Aminata immédiatement
- N'invente PAS de produits ou de prix hors catalogue
- Si une question dépasse ta connaissance, propose un rappel ou l'escalade
- Tu représentes la boutique, pas NéoBot — ne mentionne jamais NéoBot\
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
        raise HTTPException(status_code=502, detail="Erreur lors de la génération de la réponse")

    session["messages"].append({"role": "assistant", "content": reply})

    return DemoChatResponse(
        reply=reply,
        exchange_count=session["count"],
        max_exchanges=_MAX_EXCHANGES,
    )
