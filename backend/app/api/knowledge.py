"""
Endpoints pour la gestion de la base de connaissances
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.knowledge_service import KnowledgeService
from app.models import GlobalKnowledge, TenantKnowledge, KnowledgeCategory

router = APIRouter()

# ===== ENDPOINTS ADMIN (NéoBot) =====

@router.get("/admin/knowledge/global")
def list_global_knowledge(
    category: str = None,
    sector: str = "all", 
    db: Session = Depends(get_db)
):
    """Lister les connaissances globales NéoBot"""
    knowledge_service = KnowledgeService(db)
    
    query = db.query(GlobalKnowledge).filter(GlobalKnowledge.is_active == True)
    
    if category:
        query = query.filter(GlobalKnowledge.category == category)
    if sector != "all":
        query = query.filter(GlobalKnowledge.sector == sector)
    
    knowledge = query.order_by(GlobalKnowledge.priority.desc()).all()
    
    return {
        "total": len(knowledge),
        "knowledge": [
            {
                "id": k.id,
                "category": k.category.value,
                "title": k.title,
                "sector": k.sector,
                "priority": k.priority,
                "usage_count": k.usage_count,
                "success_rate": k.success_rate
            }
            for k in knowledge
        ]
    }

@router.post("/admin/knowledge/global")
def create_global_knowledge(
    category: str,
    title: str,
    content: dict,
    sector: str = "all",
    priority: int = 1,
    db: Session = Depends(get_db)
):
    """Ajouter une connaissance globale"""
    knowledge = GlobalKnowledge(
        category=category,
        title=title,
        content=content,
        sector=sector,
        priority=priority
    )
    
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)
    
    return {"id": knowledge.id, "status": "created"}

# ===== ENDPOINTS TENANT (Clients) =====

@router.get("/tenants/{tenant_id}/knowledge")
def get_tenant_knowledge(tenant_id: int, db: Session = Depends(get_db)):
    """Récupérer toutes les connaissances d'un tenant"""
    knowledge_service = KnowledgeService(db)
    
    return {
        "business_info": knowledge_service.get_tenant_business_info(tenant_id),
        "products_services": knowledge_service.get_tenant_products(tenant_id),
        "testimonials": knowledge_service.get_tenant_testimonials(tenant_id)
    }

@router.post("/tenants/{tenant_id}/knowledge/{knowledge_type}")
def update_tenant_knowledge(
    tenant_id: int,
    knowledge_type: str,
    content: dict,
    db: Session = Depends(get_db)
):
    """Mettre à jour les connaissances d'un tenant"""
    knowledge_service = KnowledgeService(db)
    knowledge_service.update_tenant_knowledge(tenant_id, knowledge_type, content)
    
    return {"status": "updated", "knowledge_type": knowledge_type}

@router.get("/tenants/{tenant_id}/conversation-templates")
def get_conversation_templates(
    tenant_id: int,
    template_type: str = "greeting",
    db: Session = Depends(get_db)
):
    """Récupérer des templates de conversation pour un tenant"""
    knowledge_service = KnowledgeService(db)
    
    # Récupérer le secteur du tenant
    from app.models import Tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    sector = tenant.business_sector.value if tenant else "all"
    
    template = knowledge_service.get_business_templates(sector, template_type)
    
    return {
        "tenant_id": tenant_id,
        "sector": sector,
        "template_type": template_type,
        "template": template
    }
