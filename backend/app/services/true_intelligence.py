"""
VRAI SERVICE INTELLIGENT NÉOBOT
Pas de conneries, juste du business
"""
import re
from typing import Dict, Optional

class TrueIntelligence:
    def __init__(self):
        # RÈGLES DE PRIORITÉ ÉLEVÉE (d'abord ces tests)
        self.priority_patterns = {
            "presentation": [
                r"^(qui\s+(es\s+)?tu|qui\s+êtes\s+vous|présente(\s+toi)?|explique\s+toi|parle\s+moi\s+de\s+toi)",
                r"c('|’)est\s+quoi\s+néobot|qu('|’)est(\s+ce\s+que)?\s+néobot",
                r"^néobot\s*\?*$",
                r"raconte\s+ton\s+histoire|ton\s+rôle|à\s+quoi\s+tu\s+sers"
            ],
            "pricing": [
                r"combien\s+ça\s+coute|prix|tarif|abonnement|coût",
                r"^(\s*)?\d+\s*heures?\s*(\d+)?|forfait",
                r"mensuel|annuel|facturation|payer",
                r"(\d+)\s*000?\s*fcfa|\d+\s*fcfa"
            ],
            "features": [
                r"fonctionnalités|features|que\s+peux\s+tu\s+faire",
                r"ça\s+fait\s+quoi|à\s+quoi\s+ça\s+sert",
                r"avantages|bénéfices|gains"
            ]
        }
        
        # RÈGLES STANDARD (après)
        self.standard_patterns = {
            "salutation": [
                r"^(salut|bonjour|bonsoir|hello|coucou|yo)\b",
                r"^(bjr|slt|cc)\b"
            ],
            "merci": [
                r"^merci|thanks|thank you|merci\s+beaucoup"
            ],
            "demande": [
                r".*\?$",  # Toute question qui finit par ?
                r"comment\s+.*|pourquoi\s+.*|quand\s+.*"
            ]
        }
        
        # RÉPONSES PROFESSIONNELLES
        self.responses = {
            "presentation": """🚀 **NÉOBOT** - Automatisation WhatsApp intelligente

Je suis l'assistant commercial de NéoBot, une plateforme qui automatise les conversations WhatsApp pour les entreprises africaines.

Je peux vous montrer comment :
• Gagner 2-3h par jour sur la gestion des messages
• Convertir +30% de prospects via WhatsApp
• Automatiser réponses, commandes et rappels

Vous gérez une entreprise ? Je peux vous faire une démo personnalisée.""",
            
            "pricing": """💰 **PLANS NÉOBOT** - ROI immédiat

• BASIQUE : 20k FCFA/mois → 2000 msg WhatsApp + IA
• STANDARD : 50k FCFA/mois → IA avancée + multi-canaux  
• PRO : 90k FCFA/mois → API + Dashboard complet + Support

💡 Le Standard est le plus populaire : il paie souvent sa 1ère vente en 48h.

Quel type d'entreprise gérez-vous ?""",
            
            "salutation": """👋 **Bonjour !**

Je suis NéoBot, spécialisé dans l'automatisation WhatsApp pour les entreprises africaines.

Vous cherchez à :
1. Gagner du temps sur la gestion des messages clients ?
2. Augmenter vos ventes via WhatsApp ?
3. Automatiser vos processus commerciaux ?

Dites-moi ce qui vous intéresse !""",
            
            "default": """💼 **Je peux vous aider sur :**

1. Présentation de NéoBot et ses fonctionnalités
2. Tarifs et plans d'abonnement  
3. Démonstration personnalisée
4. Cas clients et résultats

Que souhaitez-vous savoir en priorité ?"""
        }

    def detect_intent(self, message: str) -> str:
        """Détection INTELLIGENTE avec priorité"""
        msg_lower = message.lower().strip()
        
        # 1. PRIORITÉ HAUTE : Présentation, Prix, Fonctionnalités
        for intent, patterns in self.priority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, msg_lower, re.IGNORECASE):
                    return intent
        
        # 2. RÈGLES STANDARD
        for intent, patterns in self.standard_patterns.items():
            for pattern in patterns:
                if re.match(pattern, msg_lower, re.IGNORECASE):
                    return intent
        
        return "default"

    def get_response(self, message: str) -> str:
        """Donne la VRAIE réponse business"""
        intent = self.detect_intent(message)
        
        # Cas spécial pour "Qui es-tu ?" mal orthographié
        msg_lower = message.lower().strip()
        if re.search(r"qui\s+(es|est|s)", msg_lower) and len(msg_lower) < 20:
            return self.responses["presentation"]
        
        return self.responses.get(intent, self.responses["default"])

    def should_use_ia(self, message: str) -> bool:
        """Quand utiliser l'IA externe vs notre intelligence"""
        msg_lower = message.lower().strip()
        
        # JAMAIS d'IA pour les messages simples
        simple = [
            "salut", "bonjour", "bonsoir", "hello",
            "merci", "thanks", 
            "qui es tu", "qui es-tu", "présente toi",
            "combien", "prix", "tarif",
            "c'est quoi", "néobot"
        ]
        
        if any(pattern in msg_lower for pattern in simple):
            return False  # Utiliser notre intelligence
        
        # IA seulement pour les questions complexes
        if len(msg_lower.split()) > 8:
            return True
        
        return False
