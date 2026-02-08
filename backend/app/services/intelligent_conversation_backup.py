"""
Service de conversation intelligente avec gestion d'état SPIN
Version corrigée avec imports optimisés
"""
import json
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from app.models import Conversation, ConversationState, Tenant

class ConversationManager:
    """Gestionnaire de conversation avec état"""
    
    def __init__(self, db: Session, tenant_id: int, phone: str):
        self.db = db
        self.tenant_id = tenant_id
        self.phone = phone
        self.conversation = None
        self.state = None
        self.load_conversation()
    
    def load_conversation(self):
        """Charge ou crée une conversation avec son état"""
        # Chercher la conversation avec state préchargé
        stmt = (
            select(Conversation)
            .where(
                Conversation.tenant_id == self.tenant_id,
                Conversation.customer_phone == self.phone
            )
            .options(selectinload(Conversation.state))
        )
        
        self.conversation = self.db.execute(stmt).scalar_one_or_none()
        
        if not self.conversation:
            # Créer nouvelle conversation
            self.conversation = Conversation(
                tenant_id=self.tenant_id,
                customer_phone=self.phone,
                customer_name=f"Client {self.phone[-4:]}",
                channel="whatsapp"
            )
            self.db.add(self.conversation)
            self.db.commit()
            self.db.refresh(self.conversation)
        
        # Créer l'état si nécessaire
        if not self.conversation.state:
            self.state = ConversationState(
                conversation_id=self.conversation.id,
                current_stage="initial",
                spin_data=json.dumps({})
            )
            self.db.add(self.state)
            self.db.commit()
        else:
            self.state = self.conversation.state

class NeoBotSalesAgent(ConversationManager):
    """Agent de vente NéoBot (Tenant 1) - SPIN Selling avancé"""
    
    SPIN_STAGES = {
        "initial": "👋 Accueil et qualification",
        "situation": "📊 Analyse du contexte",
        "problem": "❌ Identification des problèmes",
        "implication": "💰 Quantification des pertes",
        "need": "🎯 Présentation de la solution",
        "closing": "🚀 Proposition d'essai"
    }
    
    def process_message(self, message: str) -> str:
        """Traite un message selon le stade SPIN actuel"""
        message_lower = message.lower().strip()
        intent = self.detect_intent(message_lower)
        
        # Mettre à jour le timestamp
        self.state.last_interaction = datetime.utcnow()
        
        # Router vers le bon handler
        handler = getattr(self, f"handle_{self.state.current_stage}_stage", self.handle_fallback)
        response = handler(message_lower, intent)
        
        self.db.commit()
        return response
    
    def detect_intent(self, message: str) -> str:
        """Détecte l'intention du message avec précision"""
        intent_patterns = {
            "greeting": [r"^(salut|bonjour|bonsoir|hello|coucou)[\s!?]*$"],
            "identity": [r".*(qui es|tu es qui|ton nom|t'appelle).*"],
            "philosophical": [r".*(dieu|philosoph|existen|sens de la vie).*"],
            "difference": [r".*(différenc|spécific|unique|particulier).*"],
            "price": [r".*(prix|tarif|combien coûte|coût).*"],
            "agreement": [r"^(oui|d'accord|ok|ouais|pui|yes)[\s!?]*$"],
            "refusal": [r"^(non|pas intéressé|plus tard|not now)[\s!?]*$"],
            "product": [r".*(produit|vends|commerce|business|activité).*"],
            "help": [r".*(aide|assist|soutien).*"]
        }
        
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.match(pattern, message, re.IGNORECASE):
                    return intent
        
        # Détection par mots-clés pour les cas non capturés
        if any(word in message for word in ["quoi", "comment", "pourquoi"]):
            return "question"
        
        return "unknown"
    
    def handle_initial_stage(self, message: str, intent: str) -> str:
        """Stade 1: Accueil et qualification"""
        if intent == "greeting":
            self.state.current_stage = "situation"
            return "👋 Salut ! Je suis NéoBot, l'assistant IA qui **convertit tes prospects WhatsApp 24/7** en clients payants. Pour mieux t'aider : quel est le **produit phare** que tu vends actuellement ?"
        
        elif intent in ["identity", "philosophical", "difference"]:
            return "🤖 Je suis un programme IA conçu pour une seule mission : **maximiser ton chiffre d'affaires via l'automatisation WhatsApp**. Parlons concret : quel est ton **plus gros défi pour atteindre 50 commandes par jour** ?"
        
        else:
            self.state.current_stage = "situation"
            return "🎯 Intéressant ! Pour personnaliser mon aide, dis-moi : quel est ton **secteur d'activité principal** ? (e-commerce, service, restauration, etc.)"
    
    def handle_situation_stage(self, message: str, intent: str) -> str:
        """Stade 2: Analyse du contexte"""
        # Sauvegarder l'information sectorielle
        spin_data = json.loads(self.state.spin_data or "{}")
        spin_data["sector_or_product"] = message
        self.state.spin_data = json.dumps(spin_data)
        self.state.current_stage = "problem"
        
        return f"📊 Excellent ! Maintenant, pour quantifier l'impact : combien de **messages WhatsApp** reçois-tu en moyenne par jour pour :\n• Questions sur les prix\n• Vérification du stock\n• Suivi de commande\n• Autres demandes ?"
    
    def handle_problem_stage(self, message: str, intent: str) -> str:
        """Stade 3: Identification des problèmes"""
        # Extraire les chiffres du message
        numbers = re.findall(r'\d+', message)
        volume = int(numbers[0]) if numbers else 0
        
        spin_data = json.loads(self.state.spin_data or "{}")
        spin_data["daily_volume"] = volume
        spin_data["raw_response"] = message
        self.state.spin_data = json.dumps(spin_data)
        self.state.current_stage = "implication"
        
        return "❌ Je vois. Et à ton avis, quelle est la **principale conséquence** de répondre manuellement à tous ces messages ?\n(Perte de temps ⏳, ventes manquées 💸, clients frustrés 😠, surcharge mentale 🧠)"
    
    def handle_implication_stage(self, message: str, intent: str) -> str:
        """Stade 4: Quantification des pertes"""
        spin_data = json.loads(self.state.spin_data or "{}")
        spin_data["pain_point"] = message
        self.state.spin_data = json.dumps(spin_data)
        self.state.current_stage = "need"
        
        return "💰 Faisons un calcul rapide :\nSi tu perds ne serait-ce que **2 ventes par jour** à 50€ chacune, ça fait **3 000€/mois de CA manqué**.\n\nEst-ce que cette estimation est proche de ta réalité ?"
    
    def handle_need_stage(self, message: str, intent: str) -> str:
        """Stade 5: Présentation de la solution"""
        if intent in ["agreement", "product"]:
            self.state.current_stage = "closing"
            return "🎯 PARFAIT ! Voici ce que NéoBot peut faire pour toi :\n\n✅ Réponse automatique en **3 secondes** 24/7\n✅ Gestion des commandes & réservations\n✅ Qualification des leads avec **score d'intention**\n✅ Relances automatisées des paniers abandonnés\n✅ Analytics en temps réel\n\n🚀 **Veux-tu tester gratuitement pendant 7 jours ?**"
        else:
            return "Je comprends. Mais imagine : un assistant qui travaille pendant que tu dors, qui ne prend jamais de congés, et qui convertit tes prospects 24/7. \n\nÇa vaut le coup d'essayer, non ? 😉"
    
    def handle_closing_stage(self, message: str, intent: str) -> str:
        """Stade 6: Closing"""
        if intent in ["agreement", "product"]:
            # Réinitialiser pour un nouveau cycle ou passage à l'email
            spin_data = json.loads(self.state.spin_data or "{}")
            spin_data["interested"] = True
            spin_data["closing_time"] = datetime.utcnow().isoformat()
            self.state.spin_data = json.dumps(spin_data)
            
            return "🔥 EXCELLENT ! Voici la marche à suivre :\n\n1. Je t'envoie un lien d'activation\n2. Tu connectes ton WhatsApp business\n3. Tu configures tes réponses automatiques\n4. Tu testes pendant 7 jours GRATUITEMENT\n\nTon adresse email pour recevoir le lien ?"
        
        elif intent == "refusal":
            return "Pas de problème ! L'important c'est de progresser à ton rythme. \n\nUne dernière question : à part le prix, quelle est la **principale raison** qui te retient ?\n(Je pose la question pour améliorer notre offre 💡)"
        
        else:
            return "D'accord, pas de pression ! \n\nMais avant de partir : si je pouvais te garantir une **augmentation de 15% de ton CA en 30 jours** grâce à l'automatisation, ça changerait quelque chose pour toi ? 🤔"
    
    def handle_fallback(self, message: str, intent: str) -> str:
        """Fallback intelligent pour stade inconnu"""
        fallback_responses = {
            "identity": "🤖 Je suis NéoBot, ton futur assistant commercial IA. Ma mission : transformer tes prospects WhatsApp en clients payants 24/7. Maintenant, parlons business : quel est ton secteur ?",
            "philosophical": "😅 Je suis spécialisé dans l'automatisation commerciale, pas dans la théologie ! Mais si tu veux philosopher : quel est le sens d'un business qui perd des ventes à cause de réponses tardives ? 🤔",
            "difference": "🥇 3 différences clés :\n1. **Spécialisation WhatsApp** (pas juste un chatbot généraliste)\n2. **Intégration native** avec Shopify/WooCommerce\n3. **Support local** francophone\n\nÇa répond à ta question ?",
            "price": "💰 Parlons chiffres après avoir vu la valeur. D'abord : combien de prospects WhatsApp perds-tu par mois à cause d'une réponse tardive ?",
            "question": "Bonne question ! Mais laisse-moi te demander : **quelle est ta plus grande frustration avec ton système actuel de gestion client ?**",
            "help": "Bien sûr ! Je peux t'aider avec :\n• Automatisation WhatsApp\n• Qualification de leads\n• Augmentation du taux de conversion\n• Analytics en temps réel\n\nPar quoi veux-tu commencer ?",
            "unknown": "Je ne suis pas sûr de comprendre. Pour recentrer sur ce qui compte : **quel est ton objectif commercial principal ce mois-ci ?**"
        }
        
        for intent_key, response in fallback_responses.items():
            if intent == intent_key:
                return response
        
        return fallback_responses["unknown"]

class ClientAssistant(ConversationManager):
    """Assistant pour les clients NéoBot (restaurants, boutiques, etc.)"""
    
    def process_message(self, message: str) -> str:
        # Pour l'instant, simple fallback sectoriel
        # À étendre avec logique sectorielle spécifique
        return "Mode client - fonctionnalité en développement. Bientôt disponible !"

def get_conversation_response(db: Session, tenant_id: int, phone: str, message: str) -> str:
    """Route principale pour obtenir une réponse intelligente"""
    
    if tenant_id == 1:
        # Mode NéoBot Sales avec SPIN
        try:
            agent = NeoBotSalesAgent(db, tenant_id, phone)
            return agent.process_message(message)
        except Exception as e:
            print(f"Erreur NeoBotSalesAgent: {e}")
            return "Désolé, une erreur technique est survenue. Notre équipe est notifiée !"
    else:
        # Mode Client Assistant (simple pour l'instant)
        try:
            assistant = ClientAssistant(db, tenant_id, phone)
            return assistant.process_message(message)
        except Exception as e:
            print(f"Erreur ClientAssistant: {e}")
            return "Service temporairement indisponible. Réessayez plus tard."
