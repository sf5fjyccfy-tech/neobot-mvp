"""
Service de gestion des paniers et commandes
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Optional

class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.active_carts = {}  # {conversation_id: cart_data}
    
    def create_or_get_cart(self, conversation_id: int) -> Dict:
        """Crée ou récupère un panier pour une conversation"""
        if conversation_id not in self.active_carts:
            self.active_carts[conversation_id] = {
                'id': conversation_id,
                'items': [],
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            }
        
        return self.active_carts[conversation_id]
    
    def add_to_cart(self, conversation_id: int, product_id: int, quantity: int = 1) -> Dict:
        """Ajoute un produit au panier"""
        from app.services.product_service import ProductService
        
        product_service = ProductService(self.db)
        product = product_service.get_product_by_id(product_id)
        
        if not product:
            return {'success': False, 'error': 'Produit non trouvé'}
        
        # Vérifier le stock
        available_stock = product_service.check_stock(product_id)
        if available_stock < quantity:
            return {'success': False, 'error': f'Stock insuffisant. Plus que {available_stock} disponible(s)'}
        
        cart = self.create_or_get_cart(conversation_id)
        
        # Vérifier si le produit est déjà dans le panier
        for item in cart['items']:
            if item['product_id'] == product_id:
                item['quantity'] += quantity
                break
        else:
            cart['items'].append({
                'product_id': product_id,
                'name': product['name'],
                'price': product['price'],
                'quantity': quantity,
                'image': product['images'][0] if product['images'] else None
            })
        
        cart['updated_at'] = datetime.utcnow()
        
        return {'success': True, 'cart': cart}
    
    def get_cart_summary(self, conversation_id: int) -> Dict:
        """Récupère le résumé du panier"""
        cart = self.active_carts.get(conversation_id, {'items': []})
        
        total = sum(item['price'] * item['quantity'] for item in cart['items'])
        item_count = sum(item['quantity'] for item in cart['items'])
        
        return {
            'item_count': item_count,
            'total_amount': total,
            'items': cart['items']
        }
    
    def remove_from_cart(self, conversation_id: int, product_id: int) -> Dict:
        """Retire un produit du panier"""
        cart = self.active_carts.get(conversation_id)
        if not cart:
            return {'success': False, 'error': 'Panier vide'}
        
        cart['items'] = [item for item in cart['items'] if item['product_id'] != product_id]
        cart['updated_at'] = datetime.utcnow()
        
        return {'success': True, 'cart': cart}
    
    def clear_cart(self, conversation_id: int):
        """Vide le panier"""
        if conversation_id in self.active_carts:
            del self.active_carts[conversation_id]
    
    def create_order_from_cart(self, conversation_id: int, customer_info: Dict) -> Dict:
        """Crée une commande à partir du panier"""
        cart = self.active_carts.get(conversation_id)
        if not cart or not cart['items']:
            return {'success': False, 'error': 'Panier vide'}
        
        # Ici, on simule la création de commande
        # Dans la vraie version, on enregistrerait en base
        order_data = {
            'order_id': f"CMD-{conversation_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'customer_phone': customer_info.get('phone', ''),
            'items': cart['items'],
            'total_amount': sum(item['price'] * item['quantity'] for item in cart['items']),
            'status': 'pending',
            'created_at': datetime.utcnow()
        }
        
        # Réserver les produits (anti-survente)
        from app.services.stock_service import StockService
        stock_service = StockService(self.db)
        
        for item in cart['items']:
            stock_service.reserve_product(item['product_id'], customer_info.get('phone', ''))
        
        # Vider le panier après commande
        self.clear_cart(conversation_id)
        
        return {'success': True, 'order': order_data}
