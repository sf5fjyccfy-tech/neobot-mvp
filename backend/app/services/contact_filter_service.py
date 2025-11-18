from sqlalchemy.orm import Session
from typing import Tuple
import os
from openai import OpenAI

class ContactFilterService:
    
    # Mots-clés personnels
    PERSONAL_INDICATORS = [
        "salut", "coucou", "yo", "wesh", "slt", "cc", "ça va",
        "comment vas-tu", "quoi de neuf", "on se voit",
        "bro", "pote", "frérot", "cousin", "ma sœur",
        "hier", "la dernière fois", "tu te souviens"
    ]
    
    # Mots-clés business
    BUSINESS_INDICATORS = [
        "prix", "tarif", "coute", "combien", "commander", "acheter",
        "disponible", "livraison", "paiement", "catalogue", "menu",
        "bonjour", "bonsoir", "je voudrais", "j'aimerais",
        "produit", "service", "offre", "promo", "réservation"
    ]
    
    def __init__(self, db: Session):
        self.db = db
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
    
    def is_business_contact(
        self, 
        phone: str, 
        message: str, 
        tenant_id: int,
        channel: str = "whatsapp"
    ) -> Tuple[bool, str]:
        """
        Détermine si c'est un contact business ou personnel
        
        Returns:
            (is_business: bool, reason: str)
        """
        
        # 1. Vérifier liste blanche (amis/famille)
        if self._is_in_whitelist(phone, tenant_id):
            return False, "Contact en liste blanche (personnel)"
        
        # 2. Vérifier si déjà client connu
        if self._is_known_customer(phone, tenant_id):
            return True, "Client déjà connu"
        
        # 3. Analyse heuristique rapide (économise l'IA)
        personal_score = self._count_keywords(message, self.PERSONAL_INDICATORS)
        business_score = self._count_keywords(message, self.BUSINESS_INDICATORS)
        
        # Clairement personnel
        if personal_score >= 2 and personal_score > business_score:
            return False, f"Message personnel détecté (score: {personal_score})"
        
        # Clairement business
        if business_score >= 2 and business_score > personal_score:
            return True, f"Message business détecté (score: {business_score})"
        
        # 4. Cas ambigu → demander à l'IA
        return self._ai_classify(message)
    
    def _is_in_whitelist(self, phone: str, tenant_id: int) -> bool:
        """Vérifie si le contact est en liste blanche"""
        from app.models import ContactWhitelist
        
        contact = self.db.query(ContactWhitelist).filter(
            ContactWhitelist.tenant_id == tenant_id,
            ContactWhitelist.phone == phone,
            ContactWhitelist.is_active == True
        ).first()
        
        return contact is not None
    
    def _is_known_customer(self, phone: str, tenant_id: int) -> bool:
        """Vérifie si c'est un client déjà enregistré"""
        from app.models import Conversation
        
        # A au moins 2 conversations précédentes = client régulier
        conv_count = self.db.query(Conversation).filter(
            Conversation.tenant_id == tenant_id,
            Conversation.customer_phone == phone
        ).count()
        
        return conv_count >= 2
    
    def _count_keywords(self, text: str, keywords: list) -> int:
        """Compte les mots-clés présents"""
        text_lower = text.lower()
        return sum(1 for word in keywords if word in text_lower)
    
    def _ai_classify(self, message: str) -> Tuple[bool, str]:
        """Classification IA pour cas ambigus"""
        
        prompt = f"""Tu es un filtre de messages pour une entreprise.
Analyse ce message et détermine s'il vient d'un CLIENT (business) ou d'un AMI/FAMILLE (personnel).

Message : "{message}"

Réponds UNIQUEMENT par un JSON :
{{"type": "business" ou "personal", "confidence": 0-100, "reason": "explication courte"}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=100
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            is_business = result["type"] == "business"
            reason = f"IA: {result['reason']} (confiance: {result['confidence']}%)"
            
            return is_business, reason
            
        except Exception as e:
            # En cas d'erreur IA, on suppose que c'est business (safe)
            return True, f"Erreur IA, traité comme business: {str(e)}"
    
    def add_to_whitelist(
        self, 
        phone: str, 
        tenant_id: int, 
        name: str = None
    ):
        """Ajouter un contact à la liste blanche"""
        from app.models import ContactWhitelist
        
        whitelist_entry = ContactWhitelist(
            tenant_id=tenant_id,
            phone=phone,
            name=name,
            is_active=True
        )
        
        self.db.add(whitelist_entry)
        self.db.commit()
    
    def learn_from_user_action(
        self,
        phone: str,
        tenant_id: int,
        is_business: bool
    ):
        """Apprentissage : mémoriser le choix de l'utilisateur"""
        from app.models import ContactLearning
        
        learning = ContactLearning(
            tenant_id=tenant_id,
            phone=phone,
            classified_as_business=is_business,
            learned_from_user=True
        )
        
        self.db.add(learning)
        self.db.commit()
