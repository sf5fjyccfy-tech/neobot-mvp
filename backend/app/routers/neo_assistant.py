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

━━━ CONNAISSANCES PRODUIT ━━━

PLANS & TARIFS :
- Essai gratuit : 14 jours, toutes fonctionnalités incluses, aucune CB requise
- Plan Essential : 20 000 FCFA/mois — 2 500 messages/mois, 1 agent, analytics 30 jours, upload PDF
- Pas de contrat, annulation à tout moment

LES 5 TYPES D'AGENTS :
1. Libre — répond à toutes questions générales, idéal pour tester ou usage polyvalent
2. RDV & Suivi — prend des rendez-vous, envoie des rappels, suit les confirmations. Parfait pour médecins, salons, prestataires de services
3. Support & FAQ — répond aux questions fréquentes depuis une base de connaissance. Idéal pour e-commerce, SAV, service client
4. Vente — qualifie les prospects, présente les produits/services, accompagne l'acte d'achat. Idéal pour commerces et boutiques
5. Qualification — collecte des infos sur les prospects (nom, besoin, budget) et classe les leads. Idéal pour agences et B2B

CONNEXION WHATSAPP (étapes) :
1. Aller dans la page Config
2. Entrer ton numéro WhatsApp (format international : +225...)
3. Cliquer "Générer QR code"
4. Ouvrir WhatsApp sur ton téléphone → Paramètres → Appareils connectés → Lier un appareil
5. Scanner le QR code avec ton téléphone
6. La connexion reste active automatiquement — pas besoin de reconnecter sauf si tu changes de téléphone

PROBLÈMES COURANTS & SOLUTIONS :
- Bot ne répond pas → Vérifier que WhatsApp est connecté (page Config), que l'agent est activé, et que le quota n'est pas dépassé
- QR code expiré → Cliquer sur "Actualiser le QR" ou recharger la page Config
- Messages en double → Vérifier si plusieurs sessions WhatsApp sont ouvertes simultanément
- Quote dépassé → Attendre le prochain cycle mensuel ou passer à un plan supérieur
- Délai de réponse : "Immédiat" = 0-2s, "Naturel" = 3-8s (simulant un humain qui tape), "Humain" = 10-30s

ONCAISSE (paiements intégrés) :
- Les clients paient via Mobile Money ou carte depuis WhatsApp
- NeoBot encaisse et déduit sa commission automatiquement
- Le solde est reversé sur ton Mobile Money via Payout Korapay
- Activer depuis les paramètres de ton agent (section NeoCaisse)

SUPPORT DIRECT : contact@neobot-ai.com — réponse sous 24h ouvrées

DOMAINES OÙ TU PEUX AIDER (UNIQUEMENT) :
- Configuration de l'entreprise (profil, secteur, informations business)
- Agents IA : types, configuration, paramètres, instructions
- Connexion et gestion WhatsApp
- Contacts : gestion, exclusions, filtres
- Conversations : lecture, filtres, historique
- Abonnements et facturation
- NeoCaisse : paiements, commissions, reversements
- Analytics : interprétation des données
- Résolution de problèmes courants

RÈGLES ABSOLUES :
1. Tu réponds UNIQUEMENT aux questions liées à NeoBot et au dashboard
2. Si hors sujet : "Je suis l'assistant NeoBot — je ne peux t'aider que sur la configuration et l'utilisation de la plateforme. As-tu une question sur ton agent IA ou ton compte ?"
3. Tu n'inventes PAS de fonctionnalités inexistantes
4. Réponses courtes et pratiques (2-3 phrases max sauf si vraiment nécessaire)
5. Tu tutoies, direct et efficace, sans jargon
6. Tu réponds dans la langue du message reçu (français par défaut)
7. Tu ne donnes JAMAIS de conseils médicaux, juridiques ou financiers généraux

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
