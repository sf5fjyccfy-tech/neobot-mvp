"""
Moteur Ultimate NéoBot - Simple et Fiable
"""
import re
import random
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session

class NeobotIntelligent:
    def __init__(self, db: Session = None):
        self.db = db
        
        # NUMÉRO NÉOBOT OFFICIEL
        self.NEOBOT_PHONE = "237640748907"
        
        # Base de connaissances COMPLÈTE
        self.neobot_responses = {
            "presentation": [
                "🚀 **NÉOBOT** par DIMANI BALLA TIM PATRICK\n\nSolution d'automatisation conversationnelle par IA pour les businesses africains.\n\n✨ **Fonctionnalités :** IA conversationnelle, Multi-canaux, Analytics temps réel\n🎯 **Secteurs :** Restaurants, E-commerce, Boutiques, Services\n\n💬 Envie d'en savoir plus ?"
            ],
            "prix": [
                "💰 **FORMULES NÉOBOT**\n\n• BASIQUE : 20,000 FCFA/mois (2,000 messages, 1 canal)\n• STANDARD : 50,000 FCFA/mois (5,000 messages, 3 canaux, IA avancée)\n• PREMIUM : 90,000 FCFA/mois (Messages illimités, Tous canaux, Support prioritaire)\n\n💡 Promotions possibles selon votre business !"
            ],
            "fondateur": [
                "👨‍💼 **FONDATEUR : DIMANI BALLA TIM PATRICK**\n\nCréateur de NéoBot - Solution d'IA optimisée marché africain.\n🎯 Mission : Rendre l'automatisation accessible aux businesses locaux.\n\n🚀 Une question sur NéoBot ?"
            ],
            "fonctionnalites": [
                "🤖 **FONCTIONNALITÉS NÉOBOT**\n\n• IA conversationnelle intelligente\n• Multi-canaux (WhatsApp, Site, Messenger)\n• Analytics temps réel\n• Support multilingue (FR, EN, Pidgin)\n• Templates e-commerce\n• Paiements Mobile Money (bientôt)\n• Installation rapide (3-7 jours)\n\n💡 Quelle fonctionnalité vous intéresse ?"
            ],
            "achat": [
                "🎉 **EXCELLENT CHOIX !**\n\nProcessus simple :\n1. Discussion besoins\n2. Choix formule  \n3. Configuration\n4. Mise en ligne\n\n📱 **Contact achat :**\n👉 +237 6 94 25 62 67 (Tim Patrick)\n\n💬 Je peux vous aider à choisir ?"
            ],
            "secteurs": [
                "🏪 **SECTEURS SUPPORTÉS**\n\n• Restaurants & Food\n• E-commerce & Dropshipping\n• Boutiques & Fashion\n• Salons & Services\n• Tous secteurs configurables\n\n🔧 Installation : 3-7 jours\n💼 Votre secteur est dans la liste ?"
            ],
            "demo": [
                "🎬 **DÉMO NÉOBOT**\n\nJe peux vous montrer :\n• Réponses IA intelligentes\n• Prise de commande auto\n• Analytics dashboard\n• Multi-canaux\n\n💡 Exemple : Dites 'Je veux commander' pour voir l'IA en action !"
            ],
            "default": [
                "💬 **NÉOBOT** - Comment vous aider ?\n\nJe peux vous parler de :\n• Présentation NéoBot\n• Formules et prix\n• Fonctionnalités\n• Secteurs supportés\n• Notre fondateur\n• Démonstration\n\n🎯 Dites-moi ce qui vous intéresse !"
            ]
        }

    def is_neobot_destination(self, destination_phone: str) -> bool:
        """Vérifie si la destination est le numéro NéoBot"""
        normalized_dest = re.sub(r'[^\d]', '', destination_phone)
        normalized_neobot = re.sub(r'[^\d]', '', self.NEOBOT_PHONE)
        
        is_neobot = normalized_dest == normalized_neobot
        print(f"🔍 DESTINATION: {normalized_dest} → NÉOBOT: {is_neobot}")
        return is_neobot

    def detect_neobot_intent(self, message: str) -> str:
        """Détection ULTRA-SIMPLE des intentions NéoBot"""
        message_lower = message.lower().strip()
        
        # Détection directe par mots-clés
        if any(word in message_lower for word in ["quoi", "qu'est", "explique", "présente", "c'est quoi"]):
            if any(word in message_lower for word in ["néobot", "neo bot", "neo-bot"]):
                return "presentation"
                
        if any(word in message_lower for word in ["prix", "tarif", "combien", "coûte", "abonnement", "formule"]):
            return "prix"
            
        if any(word in message_lower for word in ["fondateur", "créateur", "tim", "patrick", "dimani", "balla"]):
            return "fondateur"
            
        if any(word in message_lower for word in ["fonctionnalité", "fonctionne", "capacité", "possibilité"]):
            return "fonctionnalites"
            
        if any(word in message_lower for word in ["acheter", "commander", "s'abonner", "je veux acheter"]):
            return "achat"
            
        if any(word in message_lower for word in ["secteur", "domaine", "restaurant", "e-commerce", "boutique"]):
            return "secteurs"
            
        if any(word in message_lower for word in ["démo", "démonstration", "montre", "essayer", "tester"]):
            return "demo"
            
        return "default"

    def get_neobot_response(self, message: str) -> str:
        """Retourne une réponse NéoBot PRÉ-ÉCRITE"""
        intent = self.detect_neobot_intent(message)
        print(f"🎯 INTENTION: {intent} pour: {message}")
        
        responses = self.neobot_responses.get(intent, self.neobot_responses["default"])
        return random.choice(responses)

    def get_client_response(self, message: str) -> str:
        """Réponse pour les clients (utilisera l'IA)"""
        return "IA_NEEDED"  # L'IA s'occupera des clients

    def generate_response(self, message: str, destination_phone: str) -> str:
        """Génère la réponse selon la DESTINATION"""
        if self.is_neobot_destination(destination_phone):
            # MODE NÉOBOT - Réponses pré-écrites
            return self.get_neobot_response(message)
        else:
            # MODE CLIENT - Utiliser l'IA
            return self.get_client_response(message)

    def learn_from_ai_response(self, message: str, ai_response: str):
        """Apprentissage (pour plus tard)"""
        print(f"🎓 APPRENTISSAGE: {message} → {ai_response}")
