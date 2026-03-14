"""
Intent Classifier - Détecte si un message est pertinent à l'entreprise
Filtre les hors-sujets et redirige intelligemment
"""

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Classification des intentions utilisateur
    Détermine si une question est pertinente au business ou hors-sujet
    """
    
    # Mots-clés PERTINENTS (business-related)
    RELEVANT_KEYWORDS = {
        "neobot", "prix", "coûte", "plan", "tarif", "fcfa",
        "message", "whatsapp", "service", "solution", "automation",
        "assistant", "bot", "fonctionnement", "comment", "setup",
        "intégration", "support", "features", "avantages",
        "essai", "trial", "gratuit", "abonnement", "paiement",
        "facture", "devis", "entreprise", "app", "application",
        "installer", "configurer", "aide", "help", "assistance",
        "contact", "commercial", "démo", "exemple", "cas d'usage",
        # Multi-tenant business keywords
        "produit", "produits", "service", "services", "article", "articles",
        "plat", "plats", "repas", "menu", "restaurant", "food",
        "vêtement", "vêtements", "clothes", "shirt", "jeans", "chaussure", "chaussures", "shoes", "fashion",
        "support", "maintenance", "formation", "conseil", "consulting", "it",
        "proposez", "proposer", "montrez", "montrer", "avoir", "avez", "avoir"
    }
    
    # Questions/patterns HORS-SUJET
    IRRELEVANT_PATTERNS = {
        "président", "gouvernement", "politique", "sports",
        "météo", "recette", "cuisine", "film", "musique",
        "histoire", "géographie", "mathématiques", "physique",
        "chimie", "biologie", "philosophie", "religion",
        "blague", "meme", "jeu", "puzzle", "enigme",
        "amour", "relation", "dating", "mariage",
        "santé", "médical", "docteur", "virus", "maladie"
    }
    
    @staticmethod
    def classify(message: str, business_type: str = "neobot") -> Tuple[bool, str, str]:
        """
        Classifie un message
        
        Args:
            message: Le message de l'utilisateur
            business_type: Type de business ("neobot", "restaurant", "ecommerce")
        
        Returns:
            (is_relevant: bool, intent: str, category: str)
            - is_relevant: True si pertinent, False si hors-sujet
            - intent: Type d'intention détectée
            - category: Catégorie de la question
        """
        message_lower = message.lower().strip()
        
        logger.info(f"🔍 Classifying intent for: '{message_lower[:100]}'")
        
        # 1. Vérifier si c'est clairement hors-sujet
        for irrelevant_pattern in IntentClassifier.IRRELEVANT_PATTERNS:
            if irrelevant_pattern in message_lower:
                logger.warning(f"⚠️ HORS-SUJET détecté: {irrelevant_pattern}")
                return False, "out_of_scope", "completely_irrelevant"
        
        # 2. Vérifier les mots-clés pertinents
        relevant_count = sum(
            1 for keyword in IntentClassifier.RELEVANT_KEYWORDS
            if keyword in message_lower
        )
        
        # 3. Questions courtes sans keywords = probablement hors-sujet
        if len(message_lower.split()) <= 5 and relevant_count == 0:
            # Vérifier quelques patterns génériques
            generic_patterns = ["qui es-tu", "qui tu es", "what are you", "who are you", 
                              "salut", "bonjour", "hello", "hi"]
            if any(pattern in message_lower for pattern in generic_patterns):
                logger.info("💭 Generic greeting detected")
                return True, "greeting", "generic_inquiry"
            
            # Vérifier des patterns basés sur les verbes "avoir", "proposer", "montrer"
            # qui sont typiquement des questions produits/services
            ask_patterns = ["vous proposez", "proposez", "montrez", "montrer", "avez", "avez-", "quel", "quels", "quelle", "quelles"]
            if any(pattern in message_lower for pattern in ask_patterns):
                logger.info("💭 Product/Service inquiry pattern detected")
                return True, "product_inquiry", "business_related"
            
            # Pattern par défaut pour messages courts
            logger.warning(f"⚠️ HORS-SUJET: Message court sans keywords")
            return False, "out_of_scope", "too_generic"
        
        # 4. Si on a au moins des keywords pertinents = RELEVANT
        if relevant_count > 0:
            intent = IntentClassifier._determine_intent(message_lower)
            logger.info(f"✅ PERTINENT - Intent: {intent}")
            return True, intent, "business_related"
        
        # 5. Questions qui contiennent des mots génériques mais basiques
        basic_questions = ["c'est quoi", "comment", "pourquoi", "quand", "où",
                         "vous faites", "vous proposez", "vous vendez"]
        if any(q in message_lower for q in basic_questions):
            # Si c'est une question basique sans keyword pertinent = UNCERTAIN
            # Mais on considère comme pertinent avec tag "uncertain"
            logger.info("❓ UNCERTAIN - Question générique")
            return True, "uncertain", "generic_question"
        
        # Par défaut = HORS-SUJET
        logger.warning(f"⚠️ Par défaut = HORS-SUJET")
        return False, "unknown", "unclassified"
    
    @staticmethod
    def _determine_intent(message_lower: str) -> str:
        """Détermine le type d'intention spécifique"""
        
        if any(word in message_lower for word in ["prix", "coûte", "tarif", "fcfa", "combien"]):
            return "pricing_inquiry"
        
        if any(word in message_lower for word in ["plan", "abonnement", "subscription"]):
            return "plan_inquiry"
        
        if any(word in message_lower for word in ["comment", "fonctionne", "how", "work"]):
            return "how_it_works"
        
        if any(word in message_lower for word in ["essai", "trial", "gratuit", "free", "test"]):
            return "trial_request"
        
        if any(word in message_lower for word in ["avantage", "benefit", "feature"]):
            return "features_inquiry"
        
        if any(word in message_lower for word in ["support", "help", "aide", "problème"]):
            return "support_request"
        
        if any(word in message_lower for word in ["démo", "demo", "exemple", "example"]):
            return "demo_request"
        
        # New: Detect product/service inquiries
        if any(word in message_lower for word in ["proposez", "montrez", "quel", "quels", "quelle", "quelles", "avez"]):
            return "product_inquiry"
        
        return "general_inquiry"
    
    @staticmethod
    def get_redirect_message(intent: str, category: str, business_name: str = "NéoBot") -> str:
        """
        Retourne un message de redirection intelligent pour hors-sujet
        """
        
        if category == "completely_irrelevant":
            return (
                f"Je suis {business_name}, un assistant spécialisé dans les solutions WhatsApp automatisées.\n\n"
                f"Je peux vous aider avec:\n"
                f"✅ Nos tarifs et plans tarifaires\n"
                f"✅ Comment fonctionne {business_name}\n"
                f"✅ Les avantages de notre plateforme\n"
                f"✅ Essai gratuit\n\n"
                f"👉 **Que puis-je faire pour vous?**"
            )
        
        elif category == "too_generic":
            return (
                f"Bonjour! 👋 Je suis {business_name}.\n\n"
                f"Je suis ici pour répondre à vos questions sur:\n"
                f"💰 Nos tarifs (Plan BASIQUE: 20,000 FCFA)\n"
                f"🚀 Comment automatiser votre WhatsApp\n"
                f"✨ Les avantages de notre solution\n\n"
                f"👉 **Par quoi voulez-vous commencer?**"
            )
        
        return (
            f"Merci pour votre message! Je suis {business_name}, spécialisé dans les solutions WhatsApp.\n\n"
            f"Comment puis-je vous aider? Je réponds aux questions sur:\n"
            f"• Tarification\n"
            f"• Fonctionnement\n"
            f"• Essai gratuit\n\n"
            f"👉 **Quel est votre question?**"
        )


def classify_intent(message: str, business_type: str = "neobot") -> Dict:
    """
    Fonction wrapper pour classification
    """
    is_relevant, intent, category = IntentClassifier.classify(message, business_type)
    
    redirect_msg = None
    if not is_relevant:
        redirect_msg = IntentClassifier.get_redirect_message(intent, category)
    
    return {
        "is_relevant": is_relevant,
        "intent": intent,
        "category": category,
        "redirect_message": redirect_msg
    }
