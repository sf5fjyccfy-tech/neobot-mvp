"""
🧠 Conversation Memory Service
Gère la mémoire long-terme des conversations pour contexte enrichi
"""
from sqlalchemy.orm import Session
from app.models import Conversation, Message
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class ConversationMemoryService:
    """
    Gère la mémoire des conversations pour contexte long-terme
    """
    
    @staticmethod
    def get_conversation_history(phone_number: str, tenant_id: int, db: Session, limit: int = 10):
        """
        Récupère l'historique des derniers messages
        Utilité: Contexte pour que l'IA comprenne la conversation
        
        Args:
            phone_number: Numéro WhatsApp du client
            tenant_id: ID du tenant
            db: Session database
            limit: Nombre de messages à récupérer
            
        Returns:
            Liste des derniers messages
        """
        try:
            conversation = db.query(Conversation).filter(
                Conversation.customer_phone == phone_number,
                Conversation.tenant_id == tenant_id
            ).order_by(Conversation.id.desc()).first()
            
            if not conversation:
                return []
            
            messages = db.query(Message).filter(
                Message.conversation_id == conversation.id
            ).order_by(Message.id.desc()).limit(limit).all()
            
            return list(reversed(messages))
        except Exception as e:
            logger.error(f"❌ Erreur récupération historique: {str(e)}")
            return []
    
    @staticmethod
    def format_history_for_prompt(messages: list) -> str:
        """
        Formate l'historique pour injection dans le prompt DeepSeek
        
        Args:
            messages: Liste des messages Message
            
        Returns:
            Texte formaté pour le prompt
        """
        if not messages:
            return "Aucun historique précédent."
        
        history = "HISTORIQUE DE LA CONVERSATION:\n"
        for msg in messages:
            if not msg.is_ai:
                history += f"👤 Client: {msg.content}\n"
            else:
                history += f"🤖 Bot: {msg.content}\n"
        
        return history
    
    @staticmethod
    def extract_customer_info(messages: list) -> dict:
        """
        Extrait les infos client des messages précédents
        Exemple: nom, secteur, besoins, budget
        
        Args:
            messages: Liste des messages Message
            
        Returns:
            Dict avec infos client extraites
        """
        customer_info = {
            "name": None,
            "business_type": None,
            "needs": [],
            "budget": None,
            "mentioned_pain_points": []
        }
        
        try:
            # Analyse simple du texte pour extraire infos
            for msg in messages:
                if msg.is_ai:
                    continue
                    
                text = msg.content.lower()
                
                # Détection du nom (après "je m'appelle", "mon nom est", "c'est")
                if "m'appelle" in text or "nom est" in text or "c'est" in text:
                    parts = text.split()
                    for i, word in enumerate(parts):
                        if any(kw in word for kw in ["appelle", "nom", "suis"]):
                            if i + 1 < len(parts):
                                potential_name = parts[i + 1].capitalize()
                                if len(potential_name) > 2 and potential_name != "Je":
                                    customer_info["name"] = potential_name
                                    break
                
                # Détection des besoins
                needs_keywords = ["besoin", "veux", "require", "envie", "cherche", "intéressé", "cherche"]
                if any(kw in text for kw in needs_keywords):
                    customer_info["needs"].append(msg.content)
                
                # Détection budget
                if "budget" in text or "prix" in text or "coûte" in text or "combien" in text:
                    customer_info["mentioned_pain_points"].append("budget_conscious")
                
                # Détection secteur
                if "restaurant" in text or "café" in text:
                    customer_info["business_type"] = "restaurant"
                elif "ecommerce" in text or "vente" in text or "produit" in text:
                    customer_info["business_type"] = "ecommerce"
                elif "voyage" in text or "tour" in text:
                    customer_info["business_type"] = "travel"
        
        except Exception as e:
            logger.error(f"❌ Erreur extraction infos client: {str(e)}")
        
        return customer_info
    
    @staticmethod
    def get_conversation_summary(conversation_id: int, db: Session) -> str:
        """
        Crée un résumé court de la conversation pour le contexte
        
        Args:
            conversation_id: ID de la conversation
            db: Session database
            
        Returns:
            Résumé texte
        """
        try:
            messages = db.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.id).all()
            
            if not messages:
                return "Conversation vide"
            
            # Prendre les 3 premiers et 3 derniers messages
            summary_msgs = messages[:3] + (messages[-3:] if len(messages) > 6 else [])
            
            summary = f"Conversation avec {len(messages)} messages\n"
            summary += "Points clés:\n"
            
            for msg in summary_msgs:
                if not msg.is_ai:
                    summary += f"- Client demande: {msg.content[:100]}\n"
            
            return summary
        except Exception as e:
            logger.error(f"❌ Erreur résumé conversation: {str(e)}")
            return "Conversation (erreur lors du résumé)"
