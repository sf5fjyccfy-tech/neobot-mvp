"""
Service de vente intelligent pour e-commerce
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

class SalesService:
    def __init__(self, db: Session):
        self.db = db
        self.abandoned_carts = {}  # {cart_id: last_activity}
    
    def detect_purchase_intent(self, message: str) -> bool:
        """Détecte si le client exprime une intention d'achat"""
        purchase_keywords = [
            'acheter', 'commander', 'prendre', 'je veux', 'voudrais',
            'prix', 'combien', 'coûte', 'disponible', 'stock',
            'taille', 'couleur', 'modèle', 'marque'
        ]
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in purchase_keywords)
    
    def generate_product_suggestion(self, products: list, customer_query: str) -> str:
        """Génère une suggestion de produits pertinents"""
        if not products:
            return "❌ Désolé, je n'ai pas trouvé de produits correspondant à votre recherche."
        
        suggestion = "🎯 **PRODUITS CORRESPONDANTS**\n\n"
        
        for i, product in enumerate(products[:3]):  # Max 3 produits
            stock_status = "✅ Disponible" if product['stock'] > 0 else "❌ Rupture"
            suggestion += f"{i+1}. **{product['name']}**\n"
            suggestion += f"   💰 {product['price']:,} FCFA\n"
            suggestion += f"   📦 {stock_status}\n"
            if product['description']:
                suggestion += f"   📝 {product['description'][:100]}...\n"
            suggestion += "\n"
        
        suggestion += "💬 **Répondez avec le numéro du produit qui vous intéresse !**"
        return suggestion
    
    def create_urgency_message(self, product: dict) -> str:
        """Crée un message d'urgence basé sur le stock réel"""
        stock = product.get('stock', 0)
        
        if stock == 1:
            return f"🚨 **DERNIER ARTICLE !** Plus qu'un seul {product['name']} disponible !"
        elif stock <= 3:
            return f"🔥 **STOCK LIMITÉ !** Plus que {stock} {product['name']} disponible(s) !"
        else:
            return f"⭐ **PRODUIT POPULAIRE** - {product['name']} est très demandé en ce moment !"
    
    def handle_abandoned_cart(self, conversation_id: int, products: list) -> str:
        """Relance pour panier abandonné"""
        if not products:
            return "🛒 Votre sélection vous attend ! Revenez finaliser votre commande 🎁"
        
        product_names = ", ".join([p['name'] for p in products[:2]])
        return f"""🛒 **VOTRE PANIER VOUS ATTEND !**

Produits sélectionnés : {product_names}

💎 **Offre spéciale** : Commandez dans les 2h et bénéficiez d'un suivi prioritaire !

💬 Répondez « COMMANDER » pour finaliser votre achat."""
    
    def qualify_vague_request(self, message: str) -> str:
        """Qualifie les demandes vagues pour mieux conseiller"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['chose', 'truc', 'qqch', 'quelque']):
            return """🎯 **POUR MIEUX VOUS CONSEILLER**

Quel type de produit cherchez-vous ?
• 👗 Vêtements (robes, chemises, etc.)
• 👟 Chaussures (baskets, sandales, etc.)  
• 👜 Sacs & Accessoires
• 💎 Bijoux & Montres

Quel est votre budget approximatif ?"""
        
        elif any(word in message_lower for word in ['cadeau', 'offrir']):
            return """🎁 **EXCELLENT IDÉE CADEAU !**

Pour qui achetez-vous ?
• 👧 Enfant
• 👩 Femme  
• 👨 Homme
• 👵 Personne âgée

Quel budget prévoyez-vous ?"""
        
        return None
