"""
Agent Service — Gestion des templates d'agents IA
Calcul du score, substitution de variables, construction du prompt final
"""
from __future__ import annotations

import re
import logging
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import AgentTemplate, AgentType, KnowledgeSource, PromptVariable, OutboundTracking, PLAN_LIMITS, PlanType

logger = logging.getLogger(__name__)

# =============================================================================
# PROMPTS SYSTÈME PRÉ-DÉFINIS PAR TYPE D'AGENT
# =============================================================================

AGENT_SYSTEM_PROMPTS: Dict[str, str] = {
    AgentType.LIBRE: """Tu es {{nom_agent}}, l'assistant WhatsApp de {{nom_entreprise}}.
{{instructions_personnalisees}}

Règles fondamentales :
- Réponds toujours en français sauf si le client écrit dans une autre langue
- Sois concis : 2-3 phrases max par réponse, sauf si une explication longue est vraiment nécessaire
- Ne mentionne jamais que tu es une IA sauf si on te le demande directement
- Si tu ne sais pas, dis-le honnêtement : "Je vais vérifier ça pour vous"
- Termine chaque échange par une question ou une invitation à en savoir plus""",

    AgentType.RDV: """Tu es {{nom_agent}}, l'assistant rendez-vous de {{nom_entreprise}}.

📍 Adresse : {{adresse}}
🕐 Horaires : {{jours_ouverture}} de {{heure_ouverture}} à {{heure_fermeture}}
💼 Services disponibles : {{liste_services}}
💰 Tarifs : {{grille_tarifs}}

Ton rôle :
1. Accueillir chaleureusement et identifier le service souhaité
2. Proposer 2-3 créneaux disponibles (si tu ne connais pas les dispo, demande la préférence et confirme qu'un conseiller validera)
3. Confirmer le nom, le contact et le service avant de valider
4. Envoyer un résumé de confirmation : date, heure, adresse, préparation éventuelle
5. Gérer les modifications et annulations avec souplesse

📣 RAPPELS AUTOMATIQUES (RDV confirmé uniquement) :
- 24h avant le RDV → "Rappel : votre RDV [service] est prévu demain à [heure] chez {{nom_entreprise}}. Adresse : {{adresse}}. Confirmer ? OUI / Annuler"
- Maximum 2 messages sortants par contact — jamais de relance non sollicitée
- Si le client répond "STOP" ou "Annuler" → enregistrer la préférence, cesser tout contact proactif

À chaque RDV confirmé, inclure : "Un rappel vous sera envoyé 24h avant. Besoin d'autre chose ?"

Style : chaleureux, organisé, rassurant. Jamais de pression.""",

    AgentType.SUPPORT: """Tu es {{nom_agent}}, l'agent support de {{nom_entreprise}}.

Politique de résolution :
- Remboursements acceptés jusqu'à {{seuil_remboursement}} — délai de retour : {{delai_retour}}
- Email support : {{email_support}}
- Escalade humaine : contacter {{nom_responsable}} si le problème nécessite une intervention manuelle
- Délai de résolution standard : {{delai_resolution}}

Protocole de traitement :
1. ACCUEIL : Nomme le client si possible, valide son émotion ("Je comprends que c'est frustrant…")
2. DIAGNOSTIC : Pose UNE seule question ciblée pour cerner le problème
3. SOLUTION : Propose une solution claire et actionnable en moins de 3 étapes
4. ESCALADE : Si le problème dépasse tes capacités → "Je transmets votre dossier à notre équipe sous {{delai_resolution}}"
5. CLÔTURE : Toujours demander "Votre problème est-il résolu ? Y a-t-il autre chose ?"

📣 EXPIRATION ABONNEMENT (services d'abonnement uniquement) :
- Avant expiration → "Votre abonnement {{nom_entreprise}} expire le [date]. Renouvelez maintenant pour [avantage]. Lien : {{lien_renouvellement}}"
- Maximum 2 messages sortants par contact sur ce sujet
- Jamais envoyé à un contact sans historique d'échange

Principes absolus :
- Ne jamais laisser un client sans réponse ni délai
- Ne jamais inventer une information — préférer "Je vérifie et reviens vers vous"
- Offrir une compensation spontanée si l'erreur vient de {{nom_entreprise}} (selon politique interne)

Style : empathique, professionnel, solution-oriented.""",

    AgentType.FAQ: """Tu es {{nom_agent}}, l'assistant FAQ de {{nom_entreprise}}.

Sujets couverts : {{sujets_faq}}
Contact pour questions hors FAQ : {{contact_info}}

Règles de réponse :
1. Réponds uniquement avec des informations vérifiées de ta base de connaissance
2. Structure tes réponses avec des listes quand il y a 3 éléments ou plus
3. Si l'information n'est pas disponible → "Cette information n'est pas dans ma base. Je vous recommande de contacter : {{contact_info}}"
4. Ne jamais improviser ou extrapoler au-delà de ce que tu sais avec certitude
5. Si la question est ambiguë → demande une précision avant de répondre

Format des réponses :
- Questions simples : réponse directe en 1-2 phrases
- Questions complexes : réponse structurée avec titres courts
- Toujours terminer par "D'autres questions ?" pour maintenir l'engagement

Style : informatif, précis, accessible. Évite le jargon technique sauf si le contexte l'exige.""",

    AgentType.VENTE: """Tu es {{nom_agent}}, le closeur commercial de {{nom_entreprise}}.

Offre principale : {{produit_phare}}
Catalogue complet : {{catalogue_produits}}
Grille tarifaire : {{grille_tarifs}}
Garantie / SAV : {{garantie}}
Offre spéciale en cours : {{offre_speciale}}
Délai de démarrage : {{delai_demarrage}}

Processus de vente (AIDA) :
1. ATTENTION : Commence par une question ouverte sur la situation du prospect ("Qu'est-ce qui vous amène aujourd'hui ?")
2. INTÉRÊT : Reformule son besoin, présente {{produit_phare}} en lien DIRECT avec ce besoin (bénéfices, pas features)
3. DÉSIR : Utilise une preuve sociale, un résultat concret ou {{offre_speciale}} pour créer l'envie
4. ACTION : Propose un passage à l'acte simple et sans friction ("Voulez-vous que je vous envoie le lien de commande ?")

Gestion des objections courantes :
- "C'est trop cher" → "Pour le prix d'un [comparaison], vous obtenez [bénéfice clé]…"
- "Je vais réfléchir" → "Sachez que {{offre_speciale}} est valable jusqu'au [date]"
- "Je ne suis pas sûr" → "Nous offrons {{garantie}}, donc aucun risque pour vous"

📣 MESSAGES SORTANTS (contacts avec historique uniquement) :
- Panier abandonné → "Vous avez laissé {{produit_phare}} dans votre panier. {{offre_speciale}} — finalisez : {{lien_commande}}"
- Promo ciblée → "Offre réservée à nos clients : {{description_promo}}. Valable jusqu'au [date] : {{lien_commande}}"
- Maximum 2 messages sortants par contact — uniquement vers des contacts ayant déjà échangé
- Jamais de cold outreach (numéro sans historique) — interdit et bloqué système

Règles :
- UNE seule question par message pour ne pas submerger
- Jamais de pression agressive — si pas prêt, proposer un suivi dans 48h

Style : confiant, chaleureux, solution-focused. L'objectif est un client satisfait, pas une vente forcée.""",

    AgentType.QUALIFICATION: """Tu es {{nom_agent}}, l'agent de qualification de {{nom_entreprise}}.

Offre qualifiée : {{offre_principale}}
Budget minimum requis : {{budget_minimum}}
Délai de recontact commercial : {{delai_contact}}

Mission : Identifier si le prospect correspond à notre offre AVANT de mobiliser un commercial humain.

Méthode BANT (1 question à la fois, naturellement intégrée dans la conversation) :
- Budget → "Avez-vous déjà une idée du budget alloué à ce type de projet ?"
- Authority → "C'est vous qui prenez la décision finale, ou y a-t-il d'autres personnes impliquées ?"
- Need → "Quel est votre principal défi en ce moment sur ce sujet ?"
- Timeline → "Pour quand idéalement souhaitez-vous avoir une solution en place ?"

Profil qualifié (tous ces critères réunis) :
✅ Budget ≥ {{budget_minimum}}
✅ Décideur ou forte influence sur la décision
✅ Besoin clair et aligné avec {{offre_principale}}
✅ Horizon de décision < 3 mois

Protocole de transmission :
- Prospect qualifié → "Parfait ! Un conseiller de {{nom_entreprise}} va vous recontacter dans {{delai_contact}} pour la suite."
- Prospect non qualifié → Orienter vers une ressource utile sans créer de frustration
- Prospect indécis → Proposer un contenu éducatif et relancer dans 7 jours

Style : curieux, professionnel, non-intrusif. Conversationnel, pas un interrogatoire.""",
}


# =============================================================================
# CRITÈRES DU SCORE DE PROMPT (sur 100)
# =============================================================================
# Clarté du rôle         : 25 pts (system_prompt ou custom_prompt défini)
# Complétude offre       : 25 pts (au moins 1 source de connaissance synced)
# Style de communication : 25 pts (ton + langue + longueur configurés)
# Base de connaissance   : 25 pts (au moins 1 source active)

def compute_prompt_score(agent: AgentTemplate, db: Session) -> int:
    score = 0

    # 1. Clarté du rôle
    active_prompt = agent.custom_prompt_override or agent.system_prompt or ""
    if len(active_prompt.strip()) >= 50:
        score += 25
    elif len(active_prompt.strip()) > 0:
        score += 10

    # 2. Complétude — sources de connaissance synced
    synced_sources = db.query(KnowledgeSource).filter(
        KnowledgeSource.agent_id == agent.id,
        KnowledgeSource.sync_status == "synced"
    ).count()
    if synced_sources >= 2:
        score += 25
    elif synced_sources == 1:
        score += 15

    # 3. Style configuré
    if agent.tone and agent.language:
        score += 15
    if agent.max_response_length and agent.max_response_length != 400:
        score += 10

    # 4. Disponibilité horaire configurée
    if agent.availability_start and agent.availability_end:
        score += 10

    # 5. Variables définies
    var_count = db.query(PromptVariable).filter(PromptVariable.agent_id == agent.id).count()
    if var_count >= 2:
        score += 15
    elif var_count == 1:
        score += 5

    return min(score, 100)


def substitute_variables(text: str, variables: List[PromptVariable]) -> str:
    """Remplace {{clé}} par la valeur correspondante dans le texte."""
    for var in variables:
        placeholder = "{{" + var.key + "}}"
        text = text.replace(placeholder, var.value or "")
    return text


def build_agent_system_prompt(agent: AgentTemplate, db: Session) -> str:
    """
    Construit le prompt système final de l'agent :
    1. Prend le custom_prompt_override si défini, sinon le system_prompt
    2. Substitue les variables {{clé}}
    3. Injecte les sources de connaissance synced
    """
    # Couche 2 : rôle
    base_prompt = agent.custom_prompt_override or agent.system_prompt or AGENT_SYSTEM_PROMPTS.get(
        agent.agent_type, AGENT_SYSTEM_PROMPTS[AgentType.LIBRE]
    )

    # Variables
    variables = db.query(PromptVariable).filter(PromptVariable.agent_id == agent.id).all()
    base_prompt = substitute_variables(base_prompt, variables)

    # Couche 3 : base de connaissance
    sources = db.query(KnowledgeSource).filter(
        KnowledgeSource.agent_id == agent.id,
        KnowledgeSource.sync_status == "synced",
        KnowledgeSource.content_extracted != None,
    ).all()

    if sources:
        knowledge_block = "\n\n=== BASE DE CONNAISSANCE ===\n"
        for source in sources:
            knowledge_block += f"\n--- {source.name or source.source_type} ---\n"
            # 2000 chars par source — réduit de 8000 pour économiser ~1500 tokens/source
            content = (source.content_extracted or "")[:2000]
            knowledge_block += content + "\n"
        base_prompt += knowledge_block

    # Instructions de style
    style_instructions = f"\n\nStyle : {agent.tone}. Langue : {agent.language}. "
    style_instructions += f"Réponses de maximum {agent.max_response_length} tokens."
    if not agent.emoji_enabled:
        style_instructions += " N'utilise pas d'emojis."

    base_prompt += style_instructions

    # ==========================================================================
    # COUCHE GUARDRAILS — injectée en dernier, prioritaire sur tout le reste.
    # Ces règles s'appliquent à tous les agents sans exception, même si
    # l'utilisateur a défini un custom_prompt_override.
    # ==========================================================================
    guardrails = "\n\nRÈGLES: 1.Cite uniquement tes données réelles. 2.Aucun lien inventé. 3.Hors-sujet→refuse poliment. 4.Ne pas nier être une IA. 5.Reste cohérent avec l'historique."

    base_prompt += guardrails

    return base_prompt


# =============================================================================
# TENANT NéoBot — VERROUILLÉ
# Le tenant 1 est réservé exclusivement à NéoBot (démo / vente du SaaS).
# Son agent ne peut pas être remplacé ni désactivé via l'API.
# =============================================================================
NEOBOT_TENANT_ID = 1
NEOBOT_AGENT_ID  = 1  # Agent "NéoBot Commercial" (type=vente)


# =============================================================================
# CRUD AGENTS
# =============================================================================

class AgentService:

    @staticmethod
    def get_active_agent(tenant_id: int, db: Session) -> Optional[AgentTemplate]:
        """Retourne l'agent actif du tenant.
        Pour le tenant NéoBot (id=1), retourne toujours l'agent NéoBot Commercial
        quel que soit son flag is_active (protection contre les désactivations accidentelles).
        """
        if tenant_id == NEOBOT_TENANT_ID:
            # Chercher d'abord par id=1 (historique), sinon n'importe quel agent actif du tenant
            agent = db.query(AgentTemplate).filter(
                AgentTemplate.id == NEOBOT_AGENT_ID,
                AgentTemplate.tenant_id == NEOBOT_TENANT_ID,
            ).first()
            if not agent:
                # id=1 absent (DB réinitialisée) — trouver l'agent actif ou le premier disponible
                agent = db.query(AgentTemplate).filter(
                    AgentTemplate.tenant_id == NEOBOT_TENANT_ID,
                    AgentTemplate.is_active == True,
                ).first() or db.query(AgentTemplate).filter(
                    AgentTemplate.tenant_id == NEOBOT_TENANT_ID,
                ).first()
            if agent:
                if not agent.is_active:
                    agent.is_active = True
                    db.commit()
                return agent
        return db.query(AgentTemplate).filter(
            AgentTemplate.tenant_id == tenant_id,
            AgentTemplate.is_active == True
        ).first()

    @staticmethod
    def list_agents(tenant_id: int, db: Session) -> List[AgentTemplate]:
        return db.query(AgentTemplate).filter(
            AgentTemplate.tenant_id == tenant_id
        ).order_by(AgentTemplate.created_at.desc()).all()

    @staticmethod
    def create_agent(
        tenant_id: int,
        name: str,
        agent_type: AgentType,
        db: Session,
        description: str = None,
        custom_prompt: str = None,
        tone: str = "Friendly, Professional",
        language: str = "fr",
        emoji_enabled: bool = True,
        max_response_length: int = 400,
        availability_start: str = None,
        availability_end: str = None,
        off_hours_message: str = None,
        activate: bool = False,
    ) -> AgentTemplate:
        """Crée un nouvel agent pour le tenant."""
        # Si on active ce nouvel agent, désactiver les autres
        if activate:
            db.query(AgentTemplate).filter(
                AgentTemplate.tenant_id == tenant_id,
                AgentTemplate.is_active == True,
            ).update({"is_active": False})

        agent = AgentTemplate(
            tenant_id=tenant_id,
            name=name,
            agent_type=agent_type,
            description=description,
            system_prompt=AGENT_SYSTEM_PROMPTS.get(agent_type),
            custom_prompt_override=custom_prompt,
            tone=tone,
            language=language,
            emoji_enabled=emoji_enabled,
            max_response_length=max_response_length,
            availability_start=availability_start,
            availability_end=availability_end,
            off_hours_message=off_hours_message,
            is_active=activate,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)

        # Calculer le score initial
        agent.prompt_score = compute_prompt_score(agent, db)
        db.commit()

        logger.info(f"✅ Agent créé: {agent.name} (type={agent_type}, tenant={tenant_id})")
        return agent

    @staticmethod
    def update_agent(agent_id: int, tenant_id: int, db: Session, **kwargs) -> Optional[AgentTemplate]:
        """Met à jour les champs d'un agent."""
        agent = db.query(AgentTemplate).filter(
            AgentTemplate.id == agent_id,
            AgentTemplate.tenant_id == tenant_id,
        ).first()

        if not agent:
            return None

        allowed = {
            "name", "description", "custom_prompt_override", "tone", "language",
            "emoji_enabled", "max_response_length", "availability_start",
            "availability_end", "off_hours_message", "response_delay", "typing_indicator",
        }
        for key, value in kwargs.items():
            if key in allowed:
                setattr(agent, key, value)

        agent.updated_at = datetime.utcnow()
        agent.prompt_score = compute_prompt_score(agent, db)
        db.commit()
        db.refresh(agent)
        return agent

    @staticmethod
    def activate_agent(agent_id: int, tenant_id: int, db: Session) -> Optional[AgentTemplate]:
        """Active un agent et désactive tous les autres du tenant."""
        db.query(AgentTemplate).filter(
            AgentTemplate.tenant_id == tenant_id
        ).update({"is_active": False})

        agent = db.query(AgentTemplate).filter(
            AgentTemplate.id == agent_id,
            AgentTemplate.tenant_id == tenant_id,
        ).first()

        if not agent:
            db.commit()
            return None

        agent.is_active = True
        agent.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(agent)
        logger.info(f"✅ Agent activé: {agent.name} (tenant={tenant_id})")
        return agent

    @staticmethod
    def delete_agent(agent_id: int, tenant_id: int, db: Session) -> bool:
        agent = db.query(AgentTemplate).filter(
            AgentTemplate.id == agent_id,
            AgentTemplate.tenant_id == tenant_id,
        ).first()
        if not agent:
            return False
        db.delete(agent)
        db.commit()
        return True

    @staticmethod
    def set_variable(agent_id: int, tenant_id: int, key: str, value: str, db: Session, description: str = None) -> PromptVariable:
        """Crée ou met à jour une variable de substitution."""
        var = db.query(PromptVariable).filter(
            PromptVariable.agent_id == agent_id,
            PromptVariable.key == key,
        ).first()

        if var:
            var.value = value
            if description:
                var.description = description
            var.updated_at = datetime.utcnow()
        else:
            var = PromptVariable(
                agent_id=agent_id,
                tenant_id=tenant_id,
                key=key,
                value=value,
                description=description,
            )
            db.add(var)

        db.commit()
        db.refresh(var)

        # Recalculer le score de l'agent
        agent = db.query(AgentTemplate).filter(AgentTemplate.id == agent_id).first()
        if agent:
            agent.prompt_score = compute_prompt_score(agent, db)
            db.commit()

        return var

    @staticmethod
    def add_knowledge_source(
        agent_id: int,
        tenant_id: int,
        source_type: str,
        db: Session,
        name: str = None,
        source_url: str = None,
        content_text: str = None,
    ) -> KnowledgeSource:
        """Ajoute une source de connaissance à un agent."""
        from app.models import KnowledgeSourceType

        source = KnowledgeSource(
            agent_id=agent_id,
            tenant_id=tenant_id,
            source_type=source_type,
            name=name,
            source_url=source_url,
            sync_status="pending" if source_url else "synced",
        )

        if content_text:
            source.content_extracted = content_text
            source.content_preview = content_text[:500]
            source.sync_status = "synced"
            source.last_synced_at = datetime.utcnow()

        db.add(source)
        db.commit()
        db.refresh(source)

        # Recalculer le score
        agent = db.query(AgentTemplate).filter(AgentTemplate.id == agent_id).first()
        if agent:
            agent.prompt_score = compute_prompt_score(agent, db)
            db.commit()

        return source

    @staticmethod
    def get_default_prompts() -> Dict:
        """Retourne les prompts système pré-définis pour chaque type d'agent."""
        return {
            agent_type.value: {
                "type": agent_type.value,
                "prompt": prompt,
                "label": {
                    "libre": "Mode Libre",
                    "rdv": "Agent RDV",
                    "support": "Agent Support",
                    "faq": "Agent FAQ",
                    "vente": "Agent Vente",
                    "qualification": "Agent Qualification",
                }.get(agent_type.value, agent_type.value),
            }
            for agent_type, prompt in AGENT_SYSTEM_PROMPTS.items()
        }


class OutboundService:
    """Gestion des messages sortants proactifs avec enforcement max 2/contact."""

    MAX_OUTBOUND_PER_CONTACT = 2

    @staticmethod
    def check_can_send(
        tenant_id: str,
        phone_number: str,
        trigger_type: str,
        db,
        plan_type: str = None,
    ) -> tuple[bool, str]:
        """
        Vérifie si un message sortant peut être envoyé.
        Retourne (can_send: bool, reason: str).
        """
        from app.models import Conversation, Message

        # 1. Vérifier que le contact a un historique (anti cold outreach)
        has_history = (
            db.query(Message)
            .join(Conversation)
            .filter(
                Conversation.tenant_id == tenant_id,
                Conversation.phone_number == phone_number,
            )
            .first()
        )
        if not has_history:
            return False, "Aucun historique — cold outreach interdit"

        # 2. Vérifier les limites plan
        if plan_type:
            limits = PLAN_LIMITS.get(plan_type, {})
            allowed_triggers = limits.get("outbound_triggers", [])
            if allowed_triggers != ["all"] and trigger_type not in allowed_triggers:
                return False, f"Trigger '{trigger_type}' non autorisé sur ce plan"

        # 3. Vérifier le compteur OutboundTracking
        record = (
            db.query(OutboundTracking)
            .filter(
                OutboundTracking.tenant_id == tenant_id,
                OutboundTracking.phone_number == phone_number,
            )
            .first()
        )

        if record:
            if record.opted_out:
                return False, "Contact a demandé STOP"
            if record.total_outbound_count >= OutboundService.MAX_OUTBOUND_PER_CONTACT:
                return False, f"Limite {OutboundService.MAX_OUTBOUND_PER_CONTACT} messages sortants atteinte"

        return True, "OK"

    @staticmethod
    def record_outbound(
        tenant_id: str,
        phone_number: str,
        trigger_type: str,
        db,
    ) -> None:
        """Incrémente les compteurs après envoi d'un message sortant."""
        from datetime import datetime

        record = (
            db.query(OutboundTracking)
            .filter(
                OutboundTracking.tenant_id == tenant_id,
                OutboundTracking.phone_number == phone_number,
            )
            .first()
        )

        if not record:
            record = OutboundTracking(
                tenant_id=tenant_id,
                phone_number=phone_number,
                total_outbound_count=0,
                rdv_outbound_count=0,
                order_outbound_count=0,
                subscription_outbound_count=0,
                promo_outbound_count=0,
            )
            db.add(record)

        record.total_outbound_count += 1
        record.last_outbound_at = datetime.utcnow()
        record.last_trigger_type = trigger_type

        if trigger_type == "rdv_reminder":
            record.rdv_outbound_count = (record.rdv_outbound_count or 0) + 1
        elif trigger_type == "order_followup":
            record.order_outbound_count = (record.order_outbound_count or 0) + 1
        elif trigger_type == "subscription_expiry":
            record.subscription_outbound_count = (record.subscription_outbound_count or 0) + 1
        elif trigger_type == "promo":
            record.promo_outbound_count = (record.promo_outbound_count or 0) + 1

        db.commit()

    @staticmethod
    def handle_stop(tenant_id: str, phone_number: str, db) -> None:
        """Enregistre le opt-out d'un contact (réponse STOP)."""
        from datetime import datetime

        record = (
            db.query(OutboundTracking)
            .filter(
                OutboundTracking.tenant_id == tenant_id,
                OutboundTracking.phone_number == phone_number,
            )
            .first()
        )

        if not record:
            record = OutboundTracking(
                tenant_id=tenant_id,
                phone_number=phone_number,
                total_outbound_count=0,
            )
            db.add(record)

        record.opted_out = True
        record.opted_out_at = datetime.utcnow()
        db.commit()
