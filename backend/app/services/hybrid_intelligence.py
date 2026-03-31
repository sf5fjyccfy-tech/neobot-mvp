"""
INTELLIGENCE HYBRIDE NÉOBOT
- TrueIntelligence pour les questions simples/fixes
- IA externe (DeepSeek) pour les questions complexes
- Fallback garanti
"""
import re
import os
import httpx
from typing import Dict, Optional

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

class HybridIntelligence:
    def __init__(self):
        # RÈGLES PRIORITAIRES pour TrueIntelligence
        self.priority_patterns = {
            "presentation": [
                r"^(qui\s+(es\s+)?tu|qui\s+êtes\s+vous|présente(\s+toi)?|explique\s+toi)",
                r"c('|’)est\s+quoi\s+néobot|qu('|’)est(\s+ce\s+que)?\s+néobot",
                r"^néobot\s*\?*$",
                r"raconte\s+ton\s+histoire|ton\s+rôle"
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
            ],
            "salutation": [
                r"^(salut|bonjour|bonsoir|hello|coucou|yo)\b",
                r"^(bjr|slt|cc)\b"
            ]
        }
        
        # RÉPONSES PROFESSIONNELLES
        self.true_responses = {
            "presentation": """🚀 **NÉOBOT** - Automatisation WhatsApp intelligente

Je suis l'assistant commercial de NéoBot, une plateforme qui automatise les conversations WhatsApp pour les entreprises africaines.

Je peux vous montrer comment :
• Gagner 2-3h par jour sur la gestion des messages
• Convertir +30% de prospects via WhatsApp
• Automatiser réponses, commandes et rappels

Vous gérez une entreprise ? Je peux vous faire une démo personnalisée.""",
            
            "pricing": """💰 **PLAN ESSENTIAL — NéoBot** — ROI immédiat

🏷️ **Essential** : 20 000 FCFA/mois
   ✅ 2 500 messages WhatsApp/mois
   ✅ 1 agent IA actif (Vente, RDV, Support, FAQ, Qualification…)
   ✅ Sources Texte + PDF (3 max)
   ✅ Dashboard Analytics 30 jours
   ✅ Essai gratuit 14 jours — aucune carte requise

D'autres formules arrivent bientôt.

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
        
        # 1. PRIORITÉ HAUTE
        for intent, patterns in self.priority_patterns.items():
            for pattern in patterns:
                if re.search(pattern, msg_lower, re.IGNORECASE):
                    return intent
        
        return "default"

    def get_true_response(self, message: str) -> str:
        """Donne la VRAIE réponse business (TrueIntelligence)"""
        intent = self.detect_intent(message)
        
        # Cas spécial pour "Qui es-tu ?" mal orthographié
        msg_lower = message.lower().strip()
        if re.search(r"qui\s+(es|est|s)", msg_lower) and len(msg_lower) < 25:
            return self.true_responses["presentation"]
        
        return self.true_responses.get(intent, self.true_responses["default"])

    async def get_ai_response(self, message: str) -> Optional[str]:
        """Appelle l'IA externe pour questions complexes"""
        if not DEEPSEEK_API_KEY:
            return None
        
        try:
            # Prompt professionnel pour l'IA
            system_prompt = """Tu es NéoBot, assistant commercial spécialisé dans l'automatisation WhatsApp pour entreprises africaines.
Réponds de manière professionnelle, concise et orientée business.
Ne fais pas de forcing commercial agressif.
Informe sur l'automatisation, ROI, gains de temps, augmentation des ventes.
Sois précis et donne des exemples concrets."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    DEEPSEEK_URL,
                    headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                    json={"model": "deepseek-chat", "messages": messages, "temperature": 0.7, "max_tokens": 200}
                )
                
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]
                else:
                    return None
                    
        except Exception:
            return None

    def should_use_external_ai(self, message: str) -> bool:
        """Décide si on utilise l'IA externe"""
        msg_lower = message.lower().strip()
        
        # Questions qui méritent l'IA externe
        complex_patterns = [
            r"comment.*faire.*|comment.*fonctionne.*",
            r"pourquoi.*choisir.*|pourquoi.*néobot.*",
            r"différence.*entre.*|comparaison.*",
            r"quelle.*solution.*pour.*",
            r"intégration.*|api.*|connecter.*",
            r"exemple.*|cas.*client.*",
            r".*[?.!]{2,}.*",  # Questions complexes
        ]
        
        for pattern in complex_patterns:
            if re.search(pattern, msg_lower):
                return True
        
        # Longues questions
        if len(msg_lower.split()) > 10:
            return True
        
        return False

    async def get_hybrid_response(self, message: str) -> dict:
        """Stratégie hybride : TrueIntelligence d'abord, IA externe si complexe"""
        # 1. Toujours vérifier TrueIntelligence d'abord
        true_response = self.get_true_response(message)
        intent = self.detect_intent(message)
        
        # 2. Si c'est une question simple, retourner TrueIntelligence
        if intent != "default":
            return {
                "response": true_response,
                "source": "true_intelligence",
                "intent": intent
            }
        
        # 3. Si question complexe, essayer l'IA externe
        if self.should_use_external_ai(message):
            ai_response = await self.get_ai_response(message)
            if ai_response:
                return {
                    "response": ai_response,
                    "source": "deepseek_ai",
                    "intent": "ai_complex"
                }
        
        # 4. Fallback sur TrueIntelligence
        return {
            "response": true_response,
            "source": "true_intelligence",
            "intent": "default"
        }
