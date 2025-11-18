from typing import Dict, List
"""
Service d'analytics pour le vendeur
"""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from sqlalchemy import func

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_daily_sales(self, tenant_id: int) -> Dict:
        """Statistiques des ventes du jour"""
        # Simulation - à connecter avec les vraies commandes
        return {
            'date': datetime.utcnow().strftime('%Y-%m-%d'),
            'orders_count': 12,  # À remplacer par vraie donnée
            'total_revenue': 185000,  # À remplacer par vraie donnée
            'average_order_value': 15416
        }
    
    def get_popular_products(self, tenant_id: int, limit: int = 5) -> List[Dict]:
        """Produits les plus populaires"""
        from app.models import Product
        
        # Simulation - à connecter avec les vraies données de vente
        products = self.db.query(Product).filter(
            Product.tenant_id == tenant_id
        ).limit(limit).all()
        
        return [{
            'id': p.id,
            'name': p.name,
            'sales_count': 25,  # À remplacer par vraie donnée
            'revenue': p.price * 25  # À remplacer par vraie donnée
        } for p in products]
    
    def get_conversion_rate(self, tenant_id: int) -> float:
        """Taux de conversion conversations → commandes"""
        from app.models import Conversation
        
        total_conversations = self.db.query(Conversation).filter(
            Conversation.tenant_id == tenant_id
        ).count()
        
        # Simulation - à connecter avec vraies commandes
        successful_orders = 8  # À remplacer par vraie donnée
        
        if total_conversations == 0:
            return 0.0
        
        return round((successful_orders / total_conversations) * 100, 1)
    
    def get_abandoned_carts(self, tenant_id: int) -> List[Dict]:
        """Paniers abandonnés récents"""
        # Simulation - à connecter avec vrai système panier
        return [
            {
                'customer_phone': '+237612345678',
                'items_count': 2,
                'total_amount': 45000,
                'abandoned_since': '2 heures'
            },
            {
                'customer_phone': '+237698765432', 
                'items_count': 1,
                'total_amount': 25000,
                'abandoned_since': '1 heure'
            }
        ]
    
    def get_dashboard_overview(self, tenant_id: int) -> Dict:
        """Vue d'ensemble du dashboard vendeur"""
        return {
            'today': self.get_daily_sales(tenant_id),
            'popular_products': self.get_popular_products(tenant_id),
            'conversion_rate': self.get_conversion_rate(tenant_id),
            'abandoned_carts': self.get_abandoned_carts(tenant_id),
            'performance_metrics': {
                'response_time': '2.3s',  # Moyenne temps de réponse
                'customer_satisfaction': '4.8/5',  # Satisfaction clients
                'messages_today': 47  # Nombre de messages aujourd'hui
            }
        }
