"""
Router Agents — CRUD complet pour les templates d'agents IA
Endpoints: /api/tenants/{tenant_id}/agents/*
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.database import get_db
from app.models import AgentTemplate, AgentType, KnowledgeSource, PromptVariable, Tenant
from app.services.agent_service import (
    AgentService,
    build_agent_system_prompt,
    compute_prompt_score,
    AGENT_SYSTEM_PROMPTS,
)
from app.http_client import DeepSeekClient
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tenants", tags=["agents"])


# ======================== SCHEMAS ========================

class AgentCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    agent_type: AgentType
    description: Optional[str] = None
    custom_prompt: Optional[str] = None
    tone: str = "Friendly, Professional"
    language: str = "fr"
    emoji_enabled: bool = True
    max_response_length: int = Field(default=400, ge=50, le=2000)
    availability_start: Optional[str] = None   # "08:00"
    availability_end: Optional[str] = None     # "22:00"
    off_hours_message: Optional[str] = None
    activate: bool = False


class AgentUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    custom_prompt: Optional[str] = None
    tone: Optional[str] = None
    language: Optional[str] = None
    emoji_enabled: Optional[bool] = None
    max_response_length: Optional[int] = Field(default=None, ge=50, le=2000)
    availability_start: Optional[str] = None
    availability_end: Optional[str] = None
    off_hours_message: Optional[str] = None


class PromptVariableRequest(BaseModel):
    key: str = Field(..., pattern=r'^[a-z_][a-z0-9_]*$')
    value: str
    description: Optional[str] = None


class KnowledgeSourceRequest(BaseModel):
    source_type: str  # url, pdf, youtube, faq, text
    name: Optional[str] = None
    source_url: Optional[str] = None
    content_text: Optional[str] = None   # Pour source_type=text ou faq


class GeneratePromptRequest(BaseModel):
    company_name: Optional[str] = None
    business_type: Optional[str] = None
    products_services: Optional[str] = None
    tone: Optional[str] = None
    target_audience: Optional[str] = None


def _agent_to_dict(agent: AgentTemplate) -> dict:
    return {
        "id": agent.id,
        "tenant_id": agent.tenant_id,
        "name": agent.name,
        "agent_type": agent.agent_type,
        "description": agent.description,
        "system_prompt": agent.system_prompt,
        "custom_prompt_override": agent.custom_prompt_override,
        "tone": agent.tone,
        "language": agent.language,
        "emoji_enabled": agent.emoji_enabled,
        "max_response_length": agent.max_response_length,
        "availability_start": agent.availability_start,
        "availability_end": agent.availability_end,
        "off_hours_message": agent.off_hours_message,
        "prompt_score": agent.prompt_score,
        "is_active": agent.is_active,
        "created_at": agent.created_at.isoformat() if agent.created_at else None,
        "updated_at": agent.updated_at.isoformat() if agent.updated_at else None,
    }


# ======================== ENDPOINTS AGENTS ========================

@router.get("/{tenant_id}/agents")
async def list_agents(tenant_id: int, db: Session = Depends(get_db)):
    """Liste tous les agents du tenant."""
    agents = AgentService.list_agents(tenant_id, db)
    return {
        "tenant_id": tenant_id,
        "agents": [_agent_to_dict(a) for a in agents],
        "total": len(agents),
    }


@router.post("/{tenant_id}/agents", status_code=201)
async def create_agent(tenant_id: int, body: AgentCreateRequest, db: Session = Depends(get_db)):
    """Crée un nouvel agent pour le tenant."""
    agent = AgentService.create_agent(
        tenant_id=tenant_id,
        name=body.name,
        agent_type=body.agent_type,
        db=db,
        description=body.description,
        custom_prompt=body.custom_prompt,
        tone=body.tone,
        language=body.language,
        emoji_enabled=body.emoji_enabled,
        max_response_length=body.max_response_length,
        availability_start=body.availability_start,
        availability_end=body.availability_end,
        off_hours_message=body.off_hours_message,
        activate=body.activate,
    )
    return {"status": "created", "agent": _agent_to_dict(agent)}


@router.get("/{tenant_id}/agents/active")
async def get_active_agent(tenant_id: int, db: Session = Depends(get_db)):
    """Retourne l'agent actuellement actif du tenant."""
    agent = AgentService.get_active_agent(tenant_id, db)
    if not agent:
        return {"tenant_id": tenant_id, "agent": None, "message": "Aucun agent actif"}
    return {"tenant_id": tenant_id, "agent": _agent_to_dict(agent)}


@router.get("/{tenant_id}/agents/default-prompts")
async def get_default_prompts(tenant_id: int):
    """Retourne les prompts système pré-définis pour chaque type d'agent."""
    return {"prompts": AgentService.get_default_prompts()}


@router.get("/{tenant_id}/agents/{agent_id}")
async def get_agent(tenant_id: int, agent_id: int, db: Session = Depends(get_db)):
    """Récupère un agent par son ID."""
    agent = db.query(AgentTemplate).filter(
        AgentTemplate.id == agent_id,
        AgentTemplate.tenant_id == tenant_id,
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return {"agent": _agent_to_dict(agent)}


@router.put("/{tenant_id}/agents/{agent_id}")
async def update_agent(
    tenant_id: int, agent_id: int, body: AgentUpdateRequest, db: Session = Depends(get_db)
):
    """Met à jour les champs d'un agent."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if "custom_prompt" in updates:
        updates["custom_prompt_override"] = updates.pop("custom_prompt")

    agent = AgentService.update_agent(agent_id, tenant_id, db, **updates)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return {"status": "updated", "agent": _agent_to_dict(agent)}


@router.post("/{tenant_id}/agents/{agent_id}/activate")
async def activate_agent(tenant_id: int, agent_id: int, db: Session = Depends(get_db)):
    """Active un agent (désactive les autres)."""
    agent = AgentService.activate_agent(agent_id, tenant_id, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return {"status": "activated", "agent": _agent_to_dict(agent)}


@router.delete("/{tenant_id}/agents/{agent_id}")
async def delete_agent(tenant_id: int, agent_id: int, db: Session = Depends(get_db)):
    """Supprime un agent."""
    success = AgentService.delete_agent(agent_id, tenant_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Agent non trouvé")
    return {"status": "deleted", "agent_id": agent_id}


@router.get("/{tenant_id}/agents/{agent_id}/preview-prompt")
async def preview_prompt(tenant_id: int, agent_id: int, db: Session = Depends(get_db)):
    """Prévisualise le prompt système final de l'agent (avec variables résolues)."""
    agent = db.query(AgentTemplate).filter(
        AgentTemplate.id == agent_id,
        AgentTemplate.tenant_id == tenant_id,
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")

    prompt = build_agent_system_prompt(agent, db)
    score = compute_prompt_score(agent, db)
    return {
        "agent_id": agent_id,
        "prompt_preview": prompt,
        "prompt_score": score,
        "score_details": {
            "role_defined": len((agent.custom_prompt_override or agent.system_prompt or "").strip()) >= 50,
            "knowledge_sources": db.query(KnowledgeSource).filter(
                KnowledgeSource.agent_id == agent_id,
                KnowledgeSource.sync_status == "synced"
            ).count(),
            "variables": db.query(PromptVariable).filter(PromptVariable.agent_id == agent_id).count(),
        }
    }


@router.post("/{tenant_id}/agents/{agent_id}/generate-prompt")
async def generate_prompt_with_ai(
    tenant_id: int, agent_id: int, body: GeneratePromptRequest, db: Session = Depends(get_db)
):
    """Génère un prompt personnalisé via DeepSeek en fonction du contexte de l'entreprise."""
    agent = db.query(AgentTemplate).filter(
        AgentTemplate.id == agent_id,
        AgentTemplate.tenant_id == tenant_id,
    ).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent non trouvé")

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()

    company_name = body.company_name or (tenant.name if tenant else "mon entreprise")
    business_type = body.business_type or (tenant.business_type if tenant else "service")
    agent_type_label = {
        "libre": "assistant généraliste",
        "rdv": "assistant de prise de rendez-vous",
        "support": "agent de support client",
        "faq": "assistant FAQ",
        "vente": "conseiller commercial",
        "qualification": "agent de qualification de prospects",
        "notification": "agent de notifications et rappels",
    }.get(str(agent.agent_type).lower(), str(agent.agent_type))

    meta_prompt = f"""Tu es un expert en prompt engineering pour chatbots WhatsApp professionnels.

Génère un prompt système complet et prêt à l'emploi pour un {agent_type_label} WhatsApp avec ces informations :

Entreprise : {company_name}
Secteur : {business_type}
{"Produits/services : " + body.products_services if body.products_services else ""}
{"Ton souhaité : " + body.tone if body.tone else "Ton : professionnel et chaleureux"}
{"Cible : " + body.target_audience if body.target_audience else ""}
Nom du bot : {agent.name}

Le prompt doit :
1. Définir clairement l'identité et le rôle du bot (2-3 phrases d'intro)
2. Lister les missions principales (3-5 points concrets)
3. Donner des règles de comportement spécifiques au secteur {business_type}
4. Utiliser des variables entre doubles accolades : {{{{nom_entreprise}}}}, {{{{nom_agent}}}}, {{{{lien_catalogue}}}}, etc.
5. Indiquer le style de communication adapté
6. Faire 200-350 mots, direct et opérationnel

Réponds UNIQUEMENT avec le prompt, sans introduction ni explication. Commence directement par "Tu es {{{{nom_agent}}}}..."."""

    result = await DeepSeekClient.call(
        messages=[{"role": "user", "content": meta_prompt}],
        model="deepseek-chat",
        temperature=0.8,
        max_tokens=600,
    )

    if "error" in result:
        raise HTTPException(status_code=503, detail=f"Erreur IA : {result['error']}")

    try:
        generated = result["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise HTTPException(status_code=503, detail="Réponse IA invalide")

    return {
        "agent_id": agent_id,
        "generated_prompt": generated,
        "agent_type": str(agent.agent_type),
        "company_name": company_name,
    }


# ======================== ENDPOINTS VARIABLES ========================

@router.get("/{tenant_id}/agents/{agent_id}/variables")
async def list_variables(tenant_id: int, agent_id: int, db: Session = Depends(get_db)):
    """Liste les variables de substitution de l'agent."""
    vars_ = db.query(PromptVariable).filter(PromptVariable.agent_id == agent_id).all()
    return {
        "agent_id": agent_id,
        "variables": [{"id": v.id, "key": v.key, "value": v.value, "description": v.description} for v in vars_],
    }


@router.put("/{tenant_id}/agents/{agent_id}/variables")
async def set_variable(
    tenant_id: int, agent_id: int, body: PromptVariableRequest, db: Session = Depends(get_db)
):
    """Crée ou met à jour une variable {{clé}} pour l'agent."""
    var = AgentService.set_variable(agent_id, tenant_id, body.key, body.value, db, body.description)
    return {"status": "saved", "variable": {"id": var.id, "key": var.key, "value": var.value}}


@router.delete("/{tenant_id}/agents/{agent_id}/variables/{key}")
async def delete_variable(tenant_id: int, agent_id: int, key: str, db: Session = Depends(get_db)):
    """Supprime une variable."""
    var = db.query(PromptVariable).filter(
        PromptVariable.agent_id == agent_id,
        PromptVariable.key == key,
    ).first()
    if not var:
        raise HTTPException(status_code=404, detail="Variable non trouvée")
    db.delete(var)
    db.commit()
    return {"status": "deleted", "key": key}


# ======================== ENDPOINTS KNOWLEDGE ========================

@router.get("/{tenant_id}/agents/{agent_id}/knowledge")
async def list_knowledge(tenant_id: int, agent_id: int, db: Session = Depends(get_db)):
    """Liste les sources de connaissance de l'agent."""
    sources = db.query(KnowledgeSource).filter(KnowledgeSource.agent_id == agent_id).all()
    return {
        "agent_id": agent_id,
        "sources": [
            {
                "id": s.id,
                "name": s.name,
                "source_type": s.source_type,
                "source_url": s.source_url,
                "sync_status": s.sync_status,
                "content_preview": s.content_preview,
                "last_synced_at": s.last_synced_at.isoformat() if s.last_synced_at else None,
            }
            for s in sources
        ],
    }


@router.post("/{tenant_id}/agents/{agent_id}/knowledge", status_code=201)
async def add_knowledge_source(
    tenant_id: int, agent_id: int, body: KnowledgeSourceRequest, db: Session = Depends(get_db)
):
    """Ajoute une source de connaissance à l'agent."""
    source = AgentService.add_knowledge_source(
        agent_id=agent_id,
        tenant_id=tenant_id,
        source_type=body.source_type,
        db=db,
        name=body.name,
        source_url=body.source_url,
        content_text=body.content_text,
    )
    return {
        "status": "created",
        "source": {
            "id": source.id,
            "name": source.name,
            "source_type": source.source_type,
            "sync_status": source.sync_status,
        },
    }


@router.delete("/{tenant_id}/agents/{agent_id}/knowledge/{source_id}")
async def delete_knowledge_source(
    tenant_id: int, agent_id: int, source_id: int, db: Session = Depends(get_db)
):
    """Supprime une source de connaissance."""
    source = db.query(KnowledgeSource).filter(
        KnowledgeSource.id == source_id,
        KnowledgeSource.agent_id == agent_id,
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source non trouvée")
    db.delete(source)
    db.commit()
    return {"status": "deleted", "source_id": source_id}
