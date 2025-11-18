"""
Service de Fallback Intelligent pour NéoBot
Gère les réponses automatiques quand l'IA n'est pas disponible
"""
import re
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session

class FallbackService:
    def __init__(self, db: Session):
        self.db = db
        
        # Patterns d'intentions par secteur
        self.intent_patterns = {
            "restaurant": {
                "menu": [
                    r".*(menu|plat|manger|nourriture|repas|cuisine).*",
                    r".*(qu[']est.ce.que.vous.avez|qu[']est.ce.qu[’]il.y.a).*",
                    r".*(proposer|servir|offrir).*"
                ],
                "horaires": [
                    r".*(heure|horaire|ouvrir|fermer|ouvert|fermé).*",
                    r".*(à.quelle.heure|quand.est.ce.que).*",
                    r".*(jour|semaine|week.end).*"
                ],
                "prix": [
                    r".*(prix|tarif|combien.coûte|coute|coût).*",
                    r".*(cher|pas.cher|abordable).*",
                    r".*(frais|fcfà|argent).*"
                ],
                "réservation": [
                    r".*(réserver|réservation|table|place).*",
                    r".*(disponible|libre).*",
                    r".*(ce.soir|demain|week.end).*"
                ],
                "adresse": [
                    r".*(adresse|localisation|localisé|situé|où).*",
                    r".*(quartier|ville|rue|avenue).*",
                    r".*(trouver|venir|map).*"
                ],
                "livraison": [
                    r".*(livraison|livrer|domicile|maison).*",
                    r".*(délai|temps.livraison).*",
                    r".*(zone|quartier.livraison).*"
                ]
            },
            "boutique": {
                "catalogue": [
                    r".*(produit|article|item|choix|sélection).*",
                    r".*(catalogue|collection|gamme).*",
                    r".*(qu.est.ce.que.vous.avez|qu.est.ce.qu.il.y.a).*"
                ],
                "prix": [
                    r".*(prix|tarif|combien.coûte|coute).*",
                    r".*(coût|frais|argent).*"
                ],
                "stock": [
                    r".*(disponible|stock|en.stock).*",
                    r".*(avoir|dispo).*",
                    r".*(taille|couleur|modèle).*"
                ],
                "livraison": [
                    r".*(livraison|livrer|expédition).*",
                    r".*(délai|temps.livraison).*",
                    r".*(frais.livraison|coût.livraison).*"
                ],
                "paiement": [
                    r".*(paiement|payer|règlement).*",
                    r".*(orange.money|mtn.money|mobile.money).*",
                    r".*(carte|espèces|cash).*"
                ]
            },
            "service": {
                "tarifs": [
                    r".*(prix|tarif|combien.coûte|coute).*",
                    r".*(devis|estimation).*"
                ],
                "disponibilité": [
                    r".*(disponible|libre|rendez.vous).*",
                    r".*(quand|horaire).*"
                ],
                "réservation": [
                    r".*(réserver|prendre.rendez.vous).*",
                    r".*(rendez.vous|rdv).*"
                ]
            }
        }
        
        # Réponses par défaut par secteur et intention
        self.fallback_responses = {
            "restaurant": {
                "menu": "🍽️ Notre menu propose des plats camerounais délicieux : Ndolé, Poulet DG, Eru, Poisson braisé. Plats entre 2000-5000 FCFA.",
                "horaires": "🕒 Nous sommes ouverts du lundi au dimanche, de 11h à 22h.",
                "prix": "💰 Nos plats vont de 2000 à 5000 FCFA. Le Ndolé est à 2500 FCFA, Poulet DG à 3500 FCFA.",
                "réservation": "📅 Pour réserver, envoyez-nous votre nom, le nombre de personnes et l'heure souhaitée.",
                "adresse": "📍 Nous sommes situé au centre-ville, Rue du Commerce. Facile d'accès !",
                "livraison": "🚚 Nous livrons dans un rayon de 5km. Délai : 30-45 min. Frais : 500 FCFA.",
                "default": "🍴 Bienvenue ! Pour le menu tapez 'menu', pour les horaires 'horaires', ou dites-moi ce que vous cherchez."
            },
            "boutique": {
                "catalogue": "🛍️ Nous avons vêtements, chaussures, accessoires et électronique. Dites-moi ce qui vous intéresse !",
                "prix": "💰 Les prix varient selon les articles. Dites-moi quel produit vous intéresse pour le prix exact.",
                "stock": "📦 Dites-moi le produit et la taille/couleur, je vérifie la disponibilité.",
                "livraison": "🚚 Livraison offerte à partir de 10000 FCFA. Délai : 24-48h en ville.",
                "paiement": "💳 Nous acceptons Orange Money, MTN Money, cash et cartes.",
                "default": "👋 Bienvenue ! Tapez 'catalogue' pour voir nos produits, ou dites-moi ce que vous cherchez."
            },
            "service": {
                "tarifs": "💰 Nos tarifs dépendent du service. Dites-moi ce dont vous avez besoin pour un devis précis.",
                "disponibilité": "📅 Nous sommes disponibles du lundi au vendredi, 8h-18h. Quel créneau vous convient ?",
                "réservation": "🗓️ Pour prendre rendez-vous, envoyez votre nom et le service souhaité.",
                "default": "👋 Bienvenue ! Dites-moi comment je peux vous aider aujourd'hui."
            }
        }

    def detect_intent(self, message: str, business_type: str) -> Tuple[str, float]:
        """Détecte l'intention du message avec un score de confiance"""
        message_lower = message.lower().strip()
        
        if business_type not in self.intent_patterns:
            return "default", 0.8
            
        best_intent = "default"
        best_score = 0.0
        
        for intent, patterns in self.intent_patterns[business_type].items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    score = 0.7  # Score de base
                    # Bonus pour les patterns plus spécifiques
                    if any(keyword in message_lower for keyword in ["combien", "prix", "coûte"]):
                        score += 0.2
                    if len(message_lower.split()) <= 3:  # Message court
                        score += 0.1
                    
                    if score > best_score:
                        best_score = score
                        best_intent = intent
        
        # Fallback pour les salutations simples
        if best_intent == "default":
            if any(salutation in message_lower for salutation in ["salut", "bonjour", "hello", "bonsoir"]):
                return "salutation", 0.9
            if any(merci in message_lower for merci in ["merci", "thanks"]):
                return "remerciement", 0.9
        
        return best_intent, best_score

    def get_fallback_response(self, message: str, business_type: str, business_name: str) -> str:
        """Génère une réponse de fallback adaptée"""
        intent, confidence = self.detect_intent(message, business_type)
        
        # Réponses spéciales pour salutations
        if intent == "salutation":
            return f"👋 Bonjour ! Bienvenue chez {business_name}. Comment puis-je vous aider ?"
        elif intent == "remerciement":
            return "🙏 Avec plaisir ! N'hésitez pas si vous avez d'autres questions."
        
        # Réponse selon l'intention détectée
        sector_responses = self.fallback_responses.get(business_type, self.fallback_responses["service"])
        response = sector_responses.get(intent, sector_responses["default"])
        
        return response

    def should_use_fallback(self, message: str, ai_available: bool = True) -> bool:
        """Détermine si on doit utiliser le fallback"""
        message_lower = message.lower().strip()
        
        # Toujours utiliser fallback si IA indisponible
        if not ai_available:
            return True
            
        # Utiliser fallback pour les messages simples
        simple_patterns = [
            r"^(salut|bonjour|bonsoir|hello)[\s!?]*$",
            r"^(merci|thanks)[\s!?]*$", 
            r"^(ok|d'accord|ça va)[\s!?]*$",
            r"^[^a-z]*$"  # Message sans lettres
        ]
        
        for pattern in simple_patterns:
            if re.match(pattern, message_lower, re.IGNORECASE):
                return True
                
        # Fallback pour messages très courts
        if len(message_lower.split()) <= 2:
            return True
            
        return False
