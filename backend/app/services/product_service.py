"""
Service de gestion des produits pour e-commerce
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Optional

class ProductService:
    def __init__(self, db: Session):
        self.db = db
    
    def search_products(self, tenant_id: int, query: str) -> List[Dict]:
        """Recherche des produits par nom, description ou catégorie"""
        from app.models import Product
        
        # Nettoyer la requête
        clean_query = query.lower().strip()
        
        products = self.db.query(Product).filter(
            Product.tenant_id == tenant_id
        ).all()
        
        # Filtrage simple
        matched_products = []
        for product in products:
            # Gérer les champs potentiellement manquants
            category = getattr(product, 'category', 'vêtements')
            is_active = getattr(product, 'is_active', True)
            images = getattr(product, 'images', [])
            
            if not is_active:
                continue
                
            search_text = f"{product.name} {product.description} {category}".lower()
            if clean_query in search_text:
                matched_products.append({
                    'id': product.id,
                    'name': product.name,
                    'description': product.description or '',
                    'price': product.price,
                    'stock': product.stock,
                    'category': category,
                    'images': images or []
                })
        
        return matched_products
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict]:
        """Récupère un produit par son ID"""
        from app.models import Product
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            # Gérer les champs potentiellement manquants
            category = getattr(product, 'category', 'vêtements')
            images = getattr(product, 'images', [])
            
            return {
                'id': product.id,
                'name': product.name,
                'description': product.description or '',
                'price': product.price,
                'stock': product.stock,
                'category': category,
                'images': images
            }
        return None
    
    def get_products_by_category(self, tenant_id: int, category: str) -> List[Dict]:
        """Récupère les produits par catégorie"""
        from app.models import Product
        
        products = self.db.query(Product).filter(
            Product.tenant_id == tenant_id
        ).all()
        
        result = []
        for product in products:
            product_category = getattr(product, 'category', 'vêtements')
            is_active = getattr(product, 'is_active', True)
            
            if product_category.lower() == category.lower() and is_active:
                images = getattr(product, 'images', [])
                result.append({
                    'id': product.id,
                    'name': product.name,
                    'description': product.description or '',
                    'price': product.price,
                    'stock': product.stock,
                    'category': product_category,
                    'images': images
                })
        
        return result
    
    def check_stock(self, product_id: int) -> int:
        """Vérifie le stock d'un produit"""
        from app.models import Product
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            return product.stock
        return 0
    
    def update_stock(self, product_id: int, new_stock: int):
        """Met à jour le stock d'un produit"""
        from app.models import Product
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            product.stock = new_stock
            self.db.commit()
            print(f"📦 Stock mis à jour: {product.name} -> {new_stock}")
