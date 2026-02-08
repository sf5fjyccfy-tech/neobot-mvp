"""
Service Fallback Intelligent amélioré
"""
import re
from typing import Tuple
from sqlalchemy.orm import Session

class FallbackService:
    def __init__(self, db: Session):
        self.db = db
        
        # Réponses par secteur - OPTIMISÉES pour le marché camerounais
        self.fallback_responses = {
            "restaurant": {
                "salutation": "🍽️ Bonjour et bienvenue chez {business_name} ! Je suis votre assistant virtuel. Souhaitez-vous voir le menu, connaître nos horaires ou réserver une table ?",
                "menu": "📋 Notre menu propose des plats camerounais délicieux : Ndolé avec crevettes (3000F), Poulet DG (3500F), Eru avec fufu (2500F), Poisson braisé (4000F). Que desirez-vous ?",
                "horaires": "🕒 Nous sommes ouverts du lundi au dimanche, de 10h à 23h. Service continu !",
                "prix": "💰 Nos plats vont de 2000 à 5000 FCFA. Le Ndolé est à 3000 FCFA, Poulet DG à 3500 FCFA, Poisson braisé à 4000 FCFA.",
                "réservation": "📅 Pour réserver, envoyez-nous votre nom, le nombre de personnes et l'heure souhaitée. Nous vous confirmerons rapidement !",
                "adresse": "📍 Nous sommes situé au centre-ville, Rue du Commerce, face au marché central. Facile d'accès !",
                "livraison": "🚚 Nous livrons dans tout Douala. Délai : 30-45 min. Frais de livraison : 500 FCFA pour les commandes < 5000F, gratuit au-delà.",
                "default": "🍴 Je peux vous aider avec le menu, les horaires, les prix ou une réservation. Que souhaitez-vous savoir ?"
            },
            "boutique": {
                "salutation": "🛍️ Bonjour ! Bienvenue chez {business_name}. Je peux vous aider avec nos produits, promotions ou la livraison. Que cherchez-vous ?",
                "catalogue": "📦 Nous avons : 👗 Vêtements (chemises, robes, pantalons), 👟 Chaussures, 👜 Sacs et accessoires, 📱 Électronique. Quel type de produit vous intéresse ?",
                "prix": "💰 Dites-moi le produit qui vous intéresse pour le prix exact. Exemple : chemise homme 5000-15000F, robe 8000-25000F.",
                "stock": "🔍 Dites-moi le produit, taille et couleur, je vérifie immédiatement la disponibilité.",
                "livraison": "🚚 Livraison gratuite à partir de 10000 FCFA d'achat. Délai : 24-48h en ville. Nous livrons partout au Cameroun.",
                "paiement": "💳 Nous acceptons Orange Money, MTN Money, cash à la livraison, et cartes bancaires.",
                "promotions": "🎁 Promotions du moment : -20% sur les sacs, -15% sur les chaussures jusqu'à dimanche !",
                "default": "👋 Je peux vous aider avec nos produits, stocks, prix ou livraison. Dites-moi ce que vous cherchez !"
            },
            "service": {
                "salutation": "👋 Bonjour ! Bienvenue chez {business_name}. Comment puis-je vous aider aujourd'hui ?",
                "tarifs": "💰 Nos tarifs dépendent du service. Pour un devis personnalisé, dites-moi ce dont vous avez besoin précisément.",
                "disponibilité": "📅 Nous sommes disponibles du lundi au vendredi, 8h-18h, et le samedi 9h-13h. Quel créneau vous convient ?",
                "réservation": "🗓️ Pour prendre rendez-vous, envoyez votre nom, prénom et le service souhaité. Je vous propose un créneau.",
                "contact": "📞 Vous pouvez nous joindre au 237 6XX XX XX XX ou par email : contact@{business_name.lower()}.cm",
                "default": "💼 Je peux vous aider avec nos tarifs, disponibilités, prise de rendez-vous ou informations de contact."
            },
            "autre": {
                "salutation": "👋 Bonjour ! Bienvenue chez {business_name}. Comment puis-je vous aider ?",
                "default": "🤝 Je suis là pour vous aider. Souhaitez-vous des informations sur nos services, tarifs ou disponibilités ?"
            }
        }

    def detect_intent(self, message: str, business_type: str) -> str:
        """Détecte l'intention du message"""
        message_lower = message.lower().strip()
        
        # Salutations
        salutations = ["bonjour", "salut", "hello", "bonsoir", "coucou", "bjr", "slt"]
        if any(salut in message_lower for salut in salutations):
            return "salutation"
        
        # Questions fréquentes RESTAURANT
        if business_type == "restaurant":
            if any(word in message_lower for word in ["menu", "plat", "manger", "nourriture", "repas", "carte", "commander"]):
                return "menu"
            elif any(word in message_lower for word in ["heure", "horaire", "ouvrir", "fermer", "ouvert", "fermé", "ferme"]):
                return "horaires"
            elif any(word in message_lower for word in ["prix", "tarif", "combien", "coûte", "coût", "cher"]):
                return "prix"
            elif any(word in message_lower for word in ["réserver", "réservation", "table", "place"]):
                return "réservation"
            elif any(word in message_lower for word in ["adresse", "localisation", "où", "situé", "trouver"]):
                return "adresse"
            elif any(word in message_lower for word in ["livraison", "livrer", "domicile", "maison"]):
                return "livraison"
        
        # Questions fréquentes BOUTIQUE
        elif business_type == "boutique":
            if any(word in message_lower for word in ["produit", "article", "catalogue", "collection", "modèle", "avoir"]):
                return "catalogue"
            elif any(word in message_lower for word in ["prix", "tarif", "combien", "coûte"]):
                return "prix"
            elif any(word in message_lower for word in ["stock", "disponible", "dispo", "disponibilité", "taille", "couleur"]):
                return "stock"
            elif any(word in message_lower for word in ["livraison", "livrer", "expédition", "envoyer"]):
                return "livraison"
            elif any(word in message_lower for word in ["paiement", "payer", "orange", "mtn", "mobile money", "argent"]):
                return "paiement"
            elif any(word in message_lower for word in ["promotion", "réduction", "solde", "offre"]):
                return "promotions"
        
        # Questions fréquentes SERVICE
        elif business_type == "service":
            if any(word in message_lower for word in ["prix", "tarif", "combien", "devis", "estimation"]):
                return "tarifs"
            elif any(word in message_lower for word in ["disponible", "libre", "rendez-vous", "rdv", "horaire"]):
                return "disponibilité"
            elif any(word in message_lower for word in ["réserver", "prendre rendez-vous", "rendez-vous"]):
                return "réservation"
            elif any(word in message_lower for word in ["contact", "joindre", "téléphone", "appeler", "email"]):
                return "contact"
        
        return "default"

    def get_fallback_response(self, message: str, business_type: str, business_name: str) -> str:
        """Génère une réponse de fallback adaptée"""
        intent = self.detect_intent(message, business_type)
        
        # Choisir le secteur
        sector = business_type if business_type in self.fallback_responses else "autre"
        responses = self.fallback_responses[sector]
        
        # Récupérer la réponse
        response = responses.get(intent, responses["default"])
        
        # Formater avec le nom de l'entreprise
        return response.format(business_name=business_name)

    def should_use_fallback(self, message: str) -> bool:
        """Détermine si on doit utiliser le fallback"""
        message_lower = message.lower().strip()
        
        # Toujours utiliser fallback pour messages courts/simples
        if len(message_lower.split()) <= 4:
            return True
            
        # Messages complexes (> 10 mots) peuvent utiliser l'IA
        if len(message_lower.split()) > 10:
            return False
            
        # Par défaut, utiliser fallback
        return True
