from datetime import datetime, timedelta
from sqlalchemy.orm import Session

class StockService:
    def __init__(self, db: Session):
        self.db = db
        self.reservations = {}
    
    def reserve_product(self, product_id: int, client_phone: str, minutes: int = 15):
        """Réserve un produit temporairement"""
        expiry = datetime.utcnow() + timedelta(minutes=minutes)
        self.reservations[product_id] = {'client': client_phone, 'expiry': expiry}
        print(f"📦 Produit {product_id} réservé pour {client_phone} jusqu'à {expiry}")
        
    def check_available_stock(self, product_id: int) -> int:
        """Retourne le stock réel (stock_base - réservations_valides)"""
        from app.models import Product
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return 0
            
        # Nettoyer les réservations expirées
        self._clean_expired_reservations()
        
        # Compter réservations actives pour ce produit
        reserved_count = sum(1 for pid, res in self.reservations.items() 
                           if pid == product_id and res['expiry'] > datetime.utcnow())
        
        available = max(0, product.stock - reserved_count)
        print(f"📊 Stock produit {product_id}: {available} disponible(s)")
        return available
    
    def _clean_expired_reservations(self):
        """Nettoie les réservations expirées"""
        now = datetime.utcnow()
        expired = [pid for pid, res in self.reservations.items() if res['expiry'] <= now]
        for pid in expired:
            print(f"🕒 Réservation expirée pour produit {pid}")
            del self.reservations[pid]
    
    def release_reservation(self, product_id: int, client_phone: str):
        """Libère une réservation"""
        if product_id in self.reservations and self.reservations[product_id]['client'] == client_phone:
            del self.reservations[product_id]
            print(f"✅ Réservation libérée pour produit {product_id}")
