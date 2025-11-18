"""
Routes API pour la gestion des produits
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.product_service import ProductService

router = APIRouter()

@router.get("/api/tenants/{tenant_id}/products")
async def search_products(
    tenant_id: int, 
    q: str = "", 
    category: str = "",
    db: Session = Depends(get_db)
):
    """Recherche de produits"""
    product_service = ProductService(db)
    results = product_service.search_products(tenant_id, q)
    
    # Filtrer par catégorie si spécifiée
    if category:
        results = [p for p in results if p.get('category') == category]
    
    return {
        "tenant_id": tenant_id,
        "query": q,
        "category": category,
        "count": len(results),
        "products": results
    }

@router.get("/api/tenants/{tenant_id}/products/{product_id}")
async def get_product_details(
    tenant_id: int,
    product_id: int,
    db: Session = Depends(get_db)
):
    """Détails d'un produit spécifique"""
    product_service = ProductService(db)
    product = product_service.get_product_by_id(product_id)
    
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    # Vérifier que le produit appartient au tenant
    if product.get('tenant_id') != tenant_id:
        raise HTTPException(status_code=403, detail="Accès non autorisé")
    
    return product

@router.get("/api/tenants/{tenant_id}/categories")
async def get_categories(tenant_id: int, db: Session = Depends(get_db)):
    """Liste des catégories de produits"""
    product_service = ProductService(db)
    products = product_service.search_products(tenant_id, "")
    
    categories = list(set(p.get('category') for p in products if p.get('category')))
    
    return {
        "tenant_id": tenant_id,
        "categories": categories
    }
