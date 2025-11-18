"""
Closeur Pro Final - Version 100% stable et éthique
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import re
import random

class CloseurProService:
    def __init__(self, db: Session):
        self.db = db
        
        # Messages 100% éthiques - Pas de promos inventées
        self.ethical_messages = {
            "restaurant": {
                "high": [
                    "👨‍🍳 **Préparation immédiate** - Votre plat peut être préparé maintenant. On commence ?",
                    "🚚 **Service rapide** - Prêt en 20-30 minutes. Parfait pour manger bientôt !",
                    "😊 **Clients satisfaits** - Ce plat reçoit d'excellents retours. Bon choix !"
                ],
                "medium": [
                    "💫 **Fait maison** - Préparé sur place avec des ingrédients frais.",
                    "👥 **Plat populaire** - Très apprécié par nos clients réguliers.",
                    "⏱️ **Pratique** - Plus besoin de cuisiner, on s'occupe de tout."
                ]
            },
            "boutique": {
                "high": [
                    "🛍️ **Disponible maintenant** - Je peux vous le réserver si vous voulez.",
                    "🚀 **Livraison rapide** - Reçu rapidement après commande.",
                    "✅ **Qualité vérifiée** - Nos clients sont satisfaits de ce produit."
                ],
                "medium": [
                    "💎 **Bon rapport qualité** - Apprécié pour son excellent rapport qualité-prix.",
                    "👗 **Tendance** - Choix populaire en ce moment.",
                    "🎁 **Bien présenté** - Emballage soigné pour une belle réception."
                ]
            },
            "service": {
                "high": [
                    "⏰ **Disponible rapidement** - Je peux vous trouver un créneau soon.",
                    "🎯 **Solution efficace** - Notre méthode donne de bons résultats.",
                    "💼 **Expérience** - Basé sur notre expérience avec de nombreux clients."
                ],
                "medium": [
                    "⭐ **Retours positifs** - Nos clients sont satisfaits du service.",
                    "🔧 **Approche éprouvée** - Méthode qui a fait ses preuves.",
                    "📊 **Résultats concrets** - Des retours clients très encourageants."
                ]
            }
        }

    def analyze_conversation(self, conversation):
        """Analyse simple et fiable"""
        if not conversation.messages:
            return {"level": "low", "score": 0}
        
        last_msg = conversation.messages[-1]
        inactive_mins = (datetime.utcnow() - last_msg.created_at).total_seconds() / 60
        
        score = 0
        triggers = []
        
        # Compter les questions du client
        customer_questions = [m for m in conversation.messages if m.direction == "incoming"]
        question_count = len(customer_questions)
        
        if question_count >= 2:
            score += 20
            triggers.append("multiple_questions")
        
        # Vérifier l'intérêt pour les prix/produits
        for msg in customer_questions[-2:]:
            content = msg.content.lower()
            if re.search(r"(prix|combien|coûte|tarif)", content):
                if "price_interest" not in triggers:
                    score += 15
                    triggers.append("price_interest")
            if re.search(r"(menu|plat|produit|article|modèle)", content):
                if "product_interest" not in triggers:
                    score += 15  
                    triggers.append("product_interest")
            if re.search(r"(réfléchir|hésite|comparer|plus tard)", content):
                if "hesitation" not in triggers:
                    score += 10
                    triggers.append("hesitation")
        
        # Inactivité
        if inactive_mins > 7:
            score += 15
            triggers.append("inactive")
        
        # Niveau de risque
        if score >= 40:
            level = "high"
        elif score >= 25:
            level = "medium"
        else:
            level = "low"
        
        return {
            "level": level,
            "score": score,
            "triggers": triggers,
            "inactive_mins": inactive_mins,
            "question_count": question_count
        }

    def get_persuasion_message(self, conversation, analysis):
        """Message de persuasion éthique"""
        sector = conversation.tenant.business_type
        messages = self.ethical_messages.get(sector, self.ethical_messages["service"])
        
        level_messages = messages.get(analysis["level"], messages["medium"])
        return random.choice(level_messages)

    def should_send_persuasion(self, conversation):
        """Décision simple et claire"""
        analysis = self.analyze_conversation(conversation)
        
        # Conditions pour envoyer un message
        has_interest = any(t in analysis["triggers"] for t in ["price_interest", "product_interest"])
        has_questions = analysis["question_count"] >= 2
        is_inactive = analysis["inactive_mins"] > 5
        
        return (has_interest or has_questions) and is_inactive and analysis["level"] in ["medium", "high"]

    def process_conversation_persuasion(self, conversation):
        """Processus complet de persuasion"""
        if not self.should_send_persuasion(conversation):
            return None
        
        analysis = self.analyze_conversation(conversation)
        message = self.get_persuasion_message(conversation, analysis)
        
        # Sauvegarder le message
        from app.models import Message
        msg = Message(
            conversation_id=conversation.id,
            content=message,
            direction="outgoing",
            is_ai=True,
            created_at=datetime.utcnow()
        )
        self.db.add(msg)
        self.db.commit()
        
        print(f"💬 PERSUASION ÉTHIQUE:")
        print(f"   → Client: {conversation.customer_phone}")
        print(f"   → Niveau: {analysis['level']} ({analysis['score']} pts)")
        print(f"   → Message: {message}")
        
        return message
