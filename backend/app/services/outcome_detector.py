"""
OutcomeDetector — Détecte le résultat d'une conversation à partir de la réponse IA.

Stratégie : analyse la réponse IA + type d'agent. Conservative : un seul outcome
par conversation, jamais écrasé. Seuil de confiance = au moins 2 signaux concordants
pour les agents ambigus (LIBRE, FAQ), 1 suffit pour les agents métier (RDV, VENTE).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Conversation, AgentType

logger = logging.getLogger(__name__)

# ── Signaux par type d'agent ───────────────────────────────────────────────────
# Chaque tuple : (pattern_dans_la_réponse_ia, poids)
# On cumule les poids — si total >= THRESHOLD, l'outcome est confirmé.

_THRESHOLD = 2  # seuil minimal de poids pour enregistrer

_SIGNALS: dict[str, list[tuple[str, int]]] = {
    "rdv_pris": [
        ("rendez-vous confirmé", 3),
        ("rdv confirmé", 3),
        ("votre rendez-vous est prévu", 3),
        ("on se retrouve le", 3),
        ("je vous attends le", 3),
        ("c'est noté pour le", 2),
        ("votre séance est", 2),
        ("votre consultation est", 2),
        ("à lundi", 1), ("à mardi", 1), ("à mercredi", 1),
        ("à jeudi", 1), ("à vendredi", 1), ("à samedi", 1), ("à dimanche", 1),
        ("l'heure est confirmée", 2),
        ("rappel vous sera envoyé", 2),
    ],
    "vente": [
        ("commande confirmée", 3),
        ("votre commande est", 3),
        ("paiement reçu", 3),
        ("votre achat", 2),
        ("je vous prépare", 2),
        ("sera livré", 2),
        ("livraison prévue", 2),
        ("numéro de commande", 3),
        ("facture", 2),
        ("reçu de paiement", 3),
        ("transaction validée", 3),
    ],
    "lead_qualifié": [
        ("notre équipe va vous recontacter", 3),
        ("un conseiller va vous appeler", 3),
        ("je transmets votre demande", 3),
        ("vous êtes éligible", 3),
        ("vous correspondez", 2),
        ("nous allons vous proposer", 2),
        ("votre dossier a été", 2),
        ("qualification complétée", 3),
    ],
    "support_résolu": [
        ("problème résolu", 3),
        ("votre problème a été résolu", 3),
        ("ticket fermé", 3),
        ("demande traitée", 2),
        ("n'hésitez pas à revenir", 2),
        ("bonne continuation", 2),
        ("tout est en ordre", 2),
        ("votre réclamation a été", 2),
        ("solution a été appliquée", 3),
    ],
    "désintérêt": [
        ("ne suis pas intéressé", 2),
        ("pas intéressé", 2),
        ("recontactez-moi plus tard", 2),
        ("pas le bon moment", 2),
        ("annulé votre", 2),
    ],
}

# Mapping agent_type → outcomes possibles (par ordre de priorité)
_AGENT_OUTCOMES: dict[str, list[str]] = {
    AgentType.RDV:           ["rdv_pris", "désintérêt"],
    AgentType.VENTE:         ["vente", "lead_qualifié", "désintérêt"],
    AgentType.SUPPORT:       ["support_résolu", "désintérêt"],
    AgentType.QUALIFICATION: ["lead_qualifié", "désintérêt"],
    AgentType.LIBRE:         ["rdv_pris", "vente", "lead_qualifié", "support_résolu", "désintérêt"],
    AgentType.FAQ:           ["support_résolu", "désintérêt"],
}


def _score_response(response_lower: str, outcome_key: str) -> int:
    """Cumule les poids des signaux détectés dans la réponse pour un outcome donné."""
    score = 0
    for pattern, weight in _SIGNALS.get(outcome_key, []):
        if pattern in response_lower:
            score += weight
    return score


def detect_outcome(
    agent_type: str,
    ai_response: str,
) -> Optional[str]:
    """
    Analyse la réponse IA et retourne l'outcome détecté ou None.
    Conservative : retourne le premier outcome dont le score >= THRESHOLD.
    """
    response_lower = ai_response.lower()
    candidates = _AGENT_OUTCOMES.get(agent_type, list(_SIGNALS.keys()))

    best_outcome = None
    best_score = 0

    for outcome_key in candidates:
        score = _score_response(response_lower, outcome_key)
        if score >= _THRESHOLD and score > best_score:
            best_outcome = outcome_key
            best_score = score

    return best_outcome


def update_conversation_outcome(
    conversation_id: int,
    agent_type: str,
    ai_response: str,
    db: Session,
) -> Optional[str]:
    """
    Détecte et enregistre l'outcome sur la conversation si pas déjà défini.
    Retourne l'outcome enregistré ou None.
    """
    try:
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conv:
            return None

        # Ne jamais écraser un outcome déjà enregistré
        if conv.outcome_type is not None:
            return conv.outcome_type

        outcome = detect_outcome(agent_type, ai_response)
        if outcome:
            conv.outcome_type = outcome
            conv.outcome_detected_at = datetime.now(timezone.utc)
            db.commit()
            logger.info(
                f"📊 Outcome '{outcome}' enregistré sur conversation {conversation_id} "
                f"(agent_type={agent_type})"
            )

        return outcome

    except Exception as e:
        logger.error(f"OutcomeDetector error on conv {conversation_id}: {e}")
        db.rollback()
        return None
