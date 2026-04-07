"""
🚨 Escalation Service
Détecte quand escalader vers un humain
"""
from sqlalchemy.orm import Session
from datetime import datetime
from enum import Enum
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class EscalationReason(str, Enum):
    CUSTOMER_FRUSTRATED = "customer_frustrated"
    COMPLEX_QUESTION = "complex_question"
    PAYMENT_ISSUE = "payment_issue"
    TECHNICAL_ISSUE = "technical_issue"
    REQUEST_HUMAN = "request_human"
    MAX_ATTEMPTS = "max_attempts"


class EscalationService:
    """
    Détecte quand escalader vers un humain
    """
    MAX_ATTEMPTS_THRESHOLD = int(os.getenv("ESCALATION_MAX_ATTEMPTS", "200"))
    
    @staticmethod
    def detect_escalation_trigger(message: str, conversation_id: Optional[int], db: Session) -> Optional[EscalationReason]:
        """
        Analyse le message pour détecter si escalade nécessaire
        
        Args:
            message: Message du client
            conversation_id: ID de la conversation (optional)
            db: Session database
            
        Returns:
            EscalationReason si escalade détectée, None sinon
        """
        from app.models import Message
        
        try:
            text = message.lower().strip()
            
            # Pattern 1: Client explicitement frustré (expressions fortes uniquement)
            frustration_phrases = [
                "très mécontent", "pas content du tout", "c'est nul", "mauvais service",
                "je suis frustré", "je suis énervé", "veux me désabonner",
                "arrêter mon abonnement", "annuler mon compte", "rembourse",
                "je veux parler à un humain", "je veux parler à quelqu'un",
            ]
            if any(phrase in text for phrase in frustration_phrases):
                logger.info(f"🚨 Escalade détectée: CLIENT_FRUSTRATED")
                return EscalationReason.CUSTOMER_FRUSTRATED
            
            # Pattern 2: Question complexe (plusieurs points d'interrogation ou très long)
            if text.count("?") >= 4 or len(text) > 500:
                logger.info(f"🚨 Escalade détectée: COMPLEX_QUESTION")
                return EscalationReason.COMPLEX_QUESTION
            
            # Pattern 3: Problème de paiement
            payment_words = ["remboursement", "litige paiement", "erreur de facturation", "débit non autorisé"]
            if any(word in text for word in payment_words):
                logger.info(f"🚨 Escalade détectée: PAYMENT_ISSUE")
                return EscalationReason.PAYMENT_ISSUE
            
            # Pattern 4: Problème technique bloquant
            tech_phrases = ["ne fonctionne plus du tout", "complètement bloqué", "impossible de se connecter", "ça plante", "ça crash"]
            if any(phrase in text for phrase in tech_phrases):
                logger.info(f"🚨 Escalade détectée: TECHNICAL_ISSUE")
                return EscalationReason.TECHNICAL_ISSUE
            
            # Pattern 5: Demande explicite d'agent humain
            if any(phrase in text for phrase in ["parler à un conseiller", "agent humain", "un humain s'il vous plaît", "je veux parler à quelqu'un"]):
                logger.info(f"🚨 Escalade détectée: REQUEST_HUMAN")
                return EscalationReason.REQUEST_HUMAN
            
            # Pattern 6: Trop de tentatives sans satisfaction
            if conversation_id:
                try:
                    from app.models import Conversation
                    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
                    if conversation:
                        message_count = db.query(Message).filter(
                            Message.conversation_id == conversation_id
                        ).count()
                        
                        if message_count > EscalationService.MAX_ATTEMPTS_THRESHOLD:
                            logger.info(f"🚨 Escalade détectée: MAX_ATTEMPTS ({message_count} msgs)")
                            return EscalationReason.MAX_ATTEMPTS
                except Exception as e:
                    logger.warning(f"detect_escalation_trigger: erreur count messages conv {conversation_id}: {e}")
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur detect_escalation_trigger: {str(e)}")
            return None
    
    @staticmethod
    def create_escalation_ticket(conversation_id: int, reason: EscalationReason, db: Session):
        """
        Crée un ticket d'escalade
        
        Args:
            conversation_id: ID de la conversation
            reason: Raison de l'escalade
            db: Session database
            
        Returns:
            Escalation ticket créé
        """
        from app.models import Conversation
        
        try:
            # Marquer la conversation comme escaladée
            conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conversation:
                conversation.status = "escalated"
                conversation.updated_at = datetime.utcnow()
                db.commit()
            
            logger.info(f"✅ Ticket escalade créé: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur create_escalation_ticket: {str(e)}")
            return False
    
    @staticmethod
    def generate_escalation_response(reason: EscalationReason) -> str:
        """
        Génère la réponse quand escalade vers humain
        
        Args:
            reason: Raison de l'escalade
            
        Returns:
            Message de réponse
        """
        responses = {
            EscalationReason.CUSTOMER_FRUSTRATED: 
                "Je comprends votre frustration. 😟 Un agent humain va vous contacter dans les 5 minutes pour mieux vous aider. Merci de votre patience!",
            
            EscalationReason.COMPLEX_QUESTION:
                "Votre question est très intéressante et complexe! 🤔 Un expert spécialisé va vous répondre très bientôt pour une meilleure assistance.",
            
            EscalationReason.PAYMENT_ISSUE:
                "Les questions de paiement sont importantes. 💳 Notre équipe spécialisée va vous contacter immédiatement pour résoudre cela.",
            
            EscalationReason.TECHNICAL_ISSUE:
                "Un problème technique détecté. 🔧 Notre équipe technique va vous contacter rapidement pour une solution optimale.",
            
            EscalationReason.REQUEST_HUMAN:
                "Bien sûr! C'est un plaisir de vous aider. 👤 Un agent va prendre en charge votre demande dans très peu de temps.",
            
            EscalationReason.MAX_ATTEMPTS:
                "Je vois que votre question nécessite plus d'expertise. 🎯 Un spécialiste va vous appeler très bientôt pour vous assister."
        }
        
        default_response = "Un agent va vous contacter bientôt pour une meilleure assistance. Merci!"
        return responses.get(reason, default_response)
