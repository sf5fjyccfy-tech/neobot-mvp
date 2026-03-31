"""
Neo Assistant — Chatbot d'aide contextuel pour le dashboard NeoBot
Endpoint IA dédié, prompt strict : répond uniquement sur NeoBot
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.dependencies import get_current_user
from app.http_client import DeepSeekClient
from app.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/neo-assistant", tags=["neo-assistant"])

# ========== PROMPT SYSTÈME ==========
# Strict : Neo ne parle QUE de NeoBot. Jamais hors scope.
_NEO_SYSTEM_PROMPT = """Tu es Neo, l'assistant IA intégré de NeoBot — une plateforme SaaS d'agents IA conversationnels sur WhatsApp.

TON RÔLE : Aider les utilisateurs du dashboard NeoBot à configurer, comprendre et optimiser leur utilisation de la plateforme.

DOMAINES OÙ TU PEUX AIDER (UNIQUEMENT) :
- Configuration de l'entreprise (profil, secteur, informations business)
- Agents IA : les 5 types (Libre, RDV & Suivi, Support & FAQ, Vente, Qualification), leur configuration, leurs paramètres
- Connexion et gestion WhatsApp (QR code, statut de connexion, sessions)
- Contacts WhatsApp : gestion, exclusions, filtres
- Conversations : lecture, filtres, relecture des échanges
- Abonnements et facturation : formules, limites de messages, essai gratuit, upgrade
- NeoCaisse : paiements intégrés, commissions, reversements Mobile Money
- Analytics et statistiques : interprétation des données du dashboard
- Résolution de problèmes courants : bot qui ne répond pas, QR expiré, messages non envoyés
- Personnalisation du bot : ton, langue, délai de réponse, indicateur de frappe

RÈGLES ABSOLUES :
1. Tu réponds UNIQUEMENT aux questions liées à NeoBot et à l'utilisation du dashboard
2. Si la question est hors sujet, réponds exactement : "Je suis l'assistant NeoBot — je ne peux t'aider que sur la configuration et l'utilisation de la plateforme. As-tu une question sur ton agent IA ou ton compte ?"
3. Tu n'inventes PAS de fonctionnalités inexistantes
4. Réponses courtes et pratiques (2-3 phrases max sauf si vraiment nécessaire)
5. Tu tutoies, tu es direct et efficace, sans jargon inutile
6. Tu réponds dans la langue du message reçu (français par défaut)
7. Tu ne donnes JAMAIS de conseils médicaux, juridiques, financiers généraux ou de code informatique hors contexte NeoBot

PAGE ACTUELLE DE L'UTILISATEUR : {page}
Adapte tes réponses au contexte de cette page si pertinent."""


# ========== SCHEMAS ==========
class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=2000)


class NeoChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    page: Optional[str] = Field(default="dashboard", max_length=50)
    history: Optional[list[ChatMessage]] = Field(default_factory=list, max_length=10)


class NeoChatResponse(BaseModel):
    response: str
    page: str


# ========== ENDPOINT ==========
@router.post("/chat", response_model=NeoChatResponse)
async def neo_chat(
    body: NeoChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Chat avec Neo — l'assistant IA contextuel du dashboard.
    Prompt strict, répond uniquement sur NeoBot.
    Protégé par JWT — un utilisateur non authentifié ne peut pas llm-inject.
    """
    page_clean = (body.page or "dashboard").strip()[:50]

    system_prompt = _NEO_SYSTEM_PROMPT.format(page=page_clean)

    # Construire l'historique — limité à 10 derniers échanges (coût + sécurité)
    messages: list = [{"role": "system", "content": system_prompt}]
    for turn in (body.history or [])[-10:]:
        messages.append({"role": turn.role, "content": turn.content[:2000]})
    messages.append({"role": "user", "content": body.message[:1000]})

    result = await DeepSeekClient.call(
        messages=messages,
        model="deepseek-chat",
        temperature=0.5,   # Plus bas que les agents clients : réponses plus stables et factuelles
        max_tokens=250,
    )

    if "error" in result:
        logger.error(f"Neo assistant DeepSeek error: {result['error']}")
        raise HTTPException(
            status_code=503,
            detail="Service temporairement indisponible. Réessaie dans quelques secondes.",
        )

    try:
        response_text = result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        logger.error(f"Neo assistant unexpected DeepSeek response: {result}")
        raise HTTPException(status_code=503, detail="Réponse IA invalide")

    return NeoChatResponse(response=response_text, page=page_clean)
