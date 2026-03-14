"""
Human Detection Service - Détecte quand humain intervient
Phase 8M: Feature 2 - Détection intervention humain
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from ..models import ConversationHumanState, Message
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class HumanDetectionService:
    """Détecte si un humain a intervenu dans une conversation"""
    
    @staticmethod
    def should_ai_respond(conversation_id: int, db: Session) -> bool:
        """
        Vérifie si IA doit répondre ou si humain est en train de gérer
        Logique:
        - Si humain_active ET dernière intervention < 5 min → IA ne répond pas
        - Sinon → IA répond normalement
        """
        state = db.query(ConversationHumanState).filter(
            ConversationHumanState.conversation_id == conversation_id
        ).first()
        
        if not state:
            return True  # Par défaut, IA répond
        
        if not state.human_active:
            return True  # Pas d'humain actif = IA répond
        
        # Humain est actif, vérifier timeout
        if state.last_human_message_at:
            time_since_human = datetime.utcnow() - state.last_human_message_at
            
            # Si silence > 5 minutes depuis humain = réactive IA
            if time_since_human > timedelta(minutes=5):
                state.human_active = False
                db.commit()
                logger.info(f"🤖 Réactive IA pour conversation {conversation_id} (timeout 5 min)")
                return True
        
        logger.info(f"🚫 IA pausée (humain actif) pour conversation {conversation_id}")
        return False
    
    @staticmethod
    def detect_human_response(messages: list) -> bool:
        """
        Analyse les messages récents pour détecter signature d'un humain
        Critères:
        1. Présence de typos (IA corrige toujours)
        2. Ton très informel (IA reste pro)
        3. Erreurs grammaticales multiples
        4. Références personnelles ("Je suis", "C'est moi")
        5. Marques de frustration/émotion brutes
        """
        if not messages or len(messages) == 0:
            return False
        
        last_msg = messages[-1].lower() if isinstance(messages[-1], str) else str(messages[-1]).lower()
        
        # Score detection
        human_score = 0
        
        # 1. Erreurs grammaticales simples
        errors_patterns = [
            "tu meme",  # au lieu de "toi-même"
            "j ais",    # au lieu de "j'ai"
            "sava",     # au lieu de "ça va"
            "kc",       # abréviations excessives
            "cmnt",
            "slut",
            "fo",
            "vrmt"
        ]
        if any(err in last_msg for err in errors_patterns):
            human_score += 1
        
        # 2. Ton très informel/slang
        informal_words = ["yo", "lol", "haha", "chelou", "ouais", "genre", "t'sais"]
        if sum(1 for w in informal_words if w in last_msg) >= 2:
            human_score += 1
        
        # 3. Références personnelles directes
        personal_refs = ["je suis", "c'est moi", "moi c'est", "m'appelle"]
        if any(ref in last_msg for ref in personal_refs):
            human_score += 1
        
        # 4. Excès de ponctuation (vraiment humain)
        if "???" in last_msg or "!!!" in last_msg or "?!?!" in last_msg:
            human_score += 1
        
        # 5. Absence complète de ponctuation (très informel)
        if len(last_msg) > 20 and last_msg.count('.') + last_msg.count('?') + last_msg.count('!') == 0:
            # Mais pas de faux positif sur messages très courts
            if len(last_msg) > 50:
                human_score += 1
        
        # Détection si 2+ critères matchent
        is_human = human_score >= 2
        
        if is_human:
            logger.info(f"👤 Humain détecté (score: {human_score}/5)")
        
        return is_human
    
    @staticmethod
    def mark_human_active(conversation_id: int, db: Session, confidence: int = 80) -> dict:
        """
        Marque que un humain est actif dans cette conversation
        """
        state = db.query(ConversationHumanState).filter(
            ConversationHumanState.conversation_id == conversation_id
        ).first()
        
        if not state:
            state = ConversationHumanState(
                conversation_id=conversation_id,
                human_active=True,
                last_human_message_at=datetime.utcnow(),
                detection_confidence=confidence
            )
            db.add(state)
        else:
            state.human_active = True
            state.last_human_message_at = datetime.utcnow()
            state.ai_paused_at = datetime.utcnow()
            state.detection_confidence = confidence
        
        db.commit()
        
        logger.info(f"👤 Humain marqué actif pour conversation {conversation_id}")
        
        return {
            "conversation_id": conversation_id,
            "human_active": True,
            "ai_paused": True,
            "message": "IA mise en pause (humain en conversation)"
        }
    
    @staticmethod
    def mark_human_inactive(conversation_id: int, db: Session) -> dict:
        """
        Marque que humain a terminé avec cette conversation
        """
        state = db.query(ConversationHumanState).filter(
            ConversationHumanState.conversation_id == conversation_id
        ).first()
        
        if not state:
            return {
                "error": "State not found",
                "conversation_id": conversation_id
            }
        
        state.human_active = False
        state.last_human_message_at = None
        db.commit()
        
        logger.info(f"🤖 IA réactivée pour conversation {conversation_id}")
        
        return {
            "conversation_id": conversation_id,
            "human_active": False,
            "ai_paused": False,
            "message": "IA réactivée"
        }
    
    @staticmethod
    def get_conversation_state(conversation_id: int, db: Session) -> dict:
        """
        Récupère l'état d'une conversation
        """
        state = db.query(ConversationHumanState).filter(
            ConversationHumanState.conversation_id == conversation_id
        ).first()
        
        if not state:
            return {
                "conversation_id": conversation_id,
                "human_active": False,
                "ai_paused": False,
                "message": "État normal: IA active"
            }
        
        return {
            "conversation_id": conversation_id,
            "human_active": state.human_active,
            "ai_paused": state.human_active,
            "last_human_message_at": state.last_human_message_at.isoformat() if state.last_human_message_at else None,
            "ai_paused_since": state.ai_paused_at.isoformat() if state.ai_paused_at else None,
            "detection_confidence": state.detection_confidence,
            "message": "Humain en conversation" if state.human_active else "IA active"
        }
    
    @staticmethod
    def auto_detect_and_update(conversation_id: int, db: Session) -> dict:
        """
        Récupère derniers messages et auto-détecte si humain intervenu
        """
        # Récupère derniers 3 messages
        messages = db.query(Message.content).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.id.desc()
        ).limit(3).all()
        
        message_contents = [m[0] for m in messages]
        
        # Détecte sur dernier message
        is_human = HumanDetectionService.detect_human_response(message_contents)
        
        if is_human:
            return HumanDetectionService.mark_human_active(
                conversation_id, 
                db,
                confidence=75
            )
        
        return {
            "conversation_id": conversation_id,
            "detected_human": False,
            "message": "Pas de détection d'humain"
        }
