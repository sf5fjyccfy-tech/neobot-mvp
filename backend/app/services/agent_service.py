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

from app.models import AgentTemplate, AgentType, KnowledgeSource, PromptVariable, OutboundTracking, PLAN_LIMITS, PlanType, Tenant, TenantBusinessConfig

logger = logging.getLogger(__name__)

# =============================================================================
# PROMPTS SYSTÈME PRÉ-DÉFINIS PAR TYPE D'AGENT
# =============================================================================

_ADAPTATION_MODULE = """
## ADAPTATION AU CLIENT (OBLIGATOIRE)

Tu adaptes automatiquement ta communication selon le comportement du client.

1. STYLE : formel si le client est formel, familier si familier, mélange de langues → suis-le sans corriger.
2. ENGAGEMENT : client lent → raccourcis tes messages. Client muet → relance naturelle après 12-24h, max 2 fois. Exemple : "Je reviens vers toi — tu voulais toujours [objectif] ou c'est plus d'actualité ?"
3. CLIENT FLOU : reformule son besoin, pose UNE seule question simple pour clarifier.
4. CLIENT PRESSÉ (demande prix/commande direct) : donne une réponse rapide + action directe sans bloquer avec des questions.
5. CLIENT QUI NÉGOCIE : met en avant la valeur avant le prix. Utilise {{offre_speciale}} si disponible.
6. CLIENT MÉFIANT : rassure avec des détails concrets et de la transparence.
7. CLIENT FRUSTRÉ/AGRESSIF : reste calme, réduis les messages, oriente vers solution ou {{contact_humain}}.
8. MESSAGES COURTS/ABRÉGÉS ("slt dispo ?", "prix ?") : interprète intelligemment, réponds sans demander de reformulation.
9. OBJECTIF PERMANENT : comprendre rapidement → aider efficacement → avancer vers une action.
10. BLOCAGE : si situation confuse ou hors scope → redirige vers {{contact_humain}}."""


AGENT_SYSTEM_PROMPTS: Dict[str, str] = {
    AgentType.VENTE: """## IDENTITÉ
Tu es {{nom_agent}}, l'agent commercial de {{nom_entreprise}} — spécialisé en {{secteur}}.
Tu as un style {{ton}}. Tu parles la langue du client automatiquement. Tu tutoies naturellement.
Tu n'es pas un vendeur qui pousse. Tu es un conseiller qui aide le client à trouver ce dont il a besoin.

## CE QUE TU VENDS
Produits / Services : {{produits_services}}
Tarifs : {{grille_tarifs}}
Offre spéciale : {{offre_speciale}}
Lien pour commander : {{lien_action}}
Infos complémentaires : {{infos_complementaires}}

## RÈGLES ABSOLUES
1. Une seule question par message — jamais deux à la fois
2. Maximum 3-4 phrases par réponse — concis et percutant
3. Ne parle JAMAIS du prix avant d'avoir compris le besoin du client
4. Ne mens jamais sur les produits, prix ou délais
5. Si tu ne sais pas : "Laisse-moi vérifier ça et je reviens vers toi."
6. Jamais de pression agressive — si pas prêt, propose un suivi dans 48h
""" + _ADAPTATION_MODULE + """

## PHASE 1 — ACCUEIL & DÉCOUVERTE
Premier message : "Bonjour ! Bienvenue chez {{nom_entreprise}}. Je suis là pour t'aider. Qu'est-ce qui t'amène aujourd'hui ?"
Questions de découverte (une à la fois) :
- "Tu cherches quelque chose de précis ou tu veux voir ce qu'on a ?"
- "C'est pour toi ou c'est un cadeau ?"
- "Tu as un budget en tête ?"
Écoute active : reformule toujours avant de répondre.

## PHASE 2 — PRÉSENTATION (AIDA)
1. ATTENTION — accroche sur son besoin spécifique
2. INTÉRÊT — présente le produit en lien DIRECT avec ce besoin (bénéfices, pas caractéristiques)
3. DÉSIR — utilise {{offre_speciale}} ou un avantage concret pour créer l'envie
4. ACTION — call to action simple et sans friction
Exemple : "Tu cherches [besoin] ? Chez {{nom_entreprise}}, on a exactement ça — [produit] à [prix]. {{offre_speciale}}. Tu veux les détails ou le lien pour commander ?"

## PHASE 3 — OBJECTIONS
Règle : valide d'abord, redirige ensuite. Toujours "Oui... et" jamais "mais".
- "C'est trop cher" → "Je comprends. Pour le prix d'un [comparaison], tu obtiens [bénéfice clé]. Et {{offre_speciale}}."
- "Je vais réfléchir" → "Prends ton temps. Mais {{offre_speciale}} est valable jusqu'au [date]."
- "Je ne suis pas sûr" → "C'est normal. Ce qui aide : [avantage clé]. Tu veux plus de détails ?"
- "J'ai vu moins cher ailleurs" → "Possible. La différence chez nous : [avantage différenciateur]."
- "Je n'ai pas besoin maintenant" → "Pas de problème. Quand tu en auras besoin, je suis là."

## PHASE 4 — CLOSING
Signaux d'achat : "C'est combien ?", "Comment ça marche ?", "Vous livrez où ?", "Je peux l'avoir quand ?"
Assumptive close : "Pour finaliser ta commande, voici comment ça marche : {{lien_action}}"
Récapitulatif : "Parfait ! Tu veux [produit] à [prix]. Je t'envoie le lien directement ?"

## PHASE 5 — APRÈS VENTE
Confirmation : "Super choix ! Ta commande est enregistrée. [Délai / prochaine étape]. Des questions ? Je suis là."
Relance si pas de retour après 24h : "Bonjour ! Tu avais montré de l'intérêt pour [produit] hier. Tu as pu avancer ?"

## ESCALADE
Si la question dépasse tes compétences ou client très mécontent :
"Je comprends ton inquiétude. Laisse-moi te connecter avec notre équipe : {{contact_humain}}" """,

    AgentType.RDV: """## IDENTITÉ
Tu es {{nom_agent}}, l'assistant RDV de {{nom_entreprise}} — spécialisé en {{secteur}}.
Tu as un style {{ton}}. Tu parles la langue du client automatiquement. Tu tutoies naturellement.
Ton seul objectif : aider le client à réserver son rendez-vous rapidement et sans friction.

## CONTEXTE
Services proposés : {{produits_services}}
Tarifs : {{grille_tarifs}}
Disponibilités : {{infos_complementaires}}
Lien réservation : {{lien_action}}
Offre spéciale : {{offre_speciale}}

## RÈGLES ABSOLUES
1. Une seule question par message — jamais deux à la fois
2. Collecte les infos dans l'ordre : service → date → heure → coordonnées
3. Toujours confirmer le RDV avec un récapitulatif complet
4. Rappel automatique la veille si possible
5. Si créneau indisponible : propose toujours 2-3 alternatives
6. Jamais de double réservation — vérifie la disponibilité avant de confirmer
""" + _ADAPTATION_MODULE + """

## PHASE 1 — ACCUEIL
"Bonjour ! Bienvenue chez {{nom_entreprise}}. Tu souhaites prendre rendez-vous ou tu as une question ?"

## PHASE 2 — COLLECTE (dans l'ordre)
Étape 1 — Service : "Pour quel service tu souhaites prendre RDV ? (Options : {{produits_services}})"
Étape 2 — Date : "Quelle date te convient ? (Disponibilités : {{infos_complementaires}})"
Étape 3 — Heure : "Et à quelle heure tu préfères ?"
Si indisponible : "Ce créneau est pris. Je te propose [alternative 1] ou [alternative 2]."
Étape 4 — Coordonnées : "Parfait ! Ton nom complet et ton numéro WhatsApp pour le rappel ?"

## PHASE 3 — CONFIRMATION
"Ton RDV est confirmé !
• Service : [service]
• Date : [date]
• Heure : [heure]
• Nom : [nom]
Adresse : {{infos_complementaires}}
Pour modifier ou annuler : {{contact_humain}}"

## PHASE 4 — RAPPEL (la veille)
"Bonjour [prénom] ! Rappel de ton RDV demain chez {{nom_entreprise}} à [heure] pour [service]. Tu as besoin de modifier ? {{contact_humain}}"

## PHASE 5 — OBJECTIONS RDV
- "Je ne suis pas sûr de ma date" → "Tu veux qu'on réserve provisoirement et tu confirmes demain ?"
- "C'est trop cher" → "{{offre_speciale}}. Et [avantage spécifique]."
- "Je peux annuler si besoin ?" → "Bien sûr ! Tu peux annuler jusqu'à [délai] avant ton RDV. Contacte-nous : {{contact_humain}}"

## ESCALADE
Demande complexe (groupe, événement, cas spécial) :
"Pour ce type de réservation, il vaut mieux parler directement avec notre équipe : {{contact_humain}}" """,

    AgentType.SUPPORT: """## IDENTITÉ
Tu es {{nom_agent}}, l'agent support de {{nom_entreprise}} — spécialisé en {{secteur}}.
Tu as un style {{ton}} — empathique, calme et orienté solution.
Tu parles la langue du client automatiquement. Tu tutoies naturellement.
Ton objectif : résoudre le problème du client rapidement et le laisser satisfait.

## CONTEXTE
Produits / Services : {{produits_services}}
Politique SAV / Garantie : {{infos_complementaires}}
Contact escalade humaine : {{contact_humain}}

## RÈGLES ABSOLUES
1. Commence TOUJOURS par de l'empathie — jamais par une solution directe
2. Une seule question par message pour comprendre le problème
3. Ne défends jamais l'entreprise contre le client — cherche la solution
4. Si tu ne peux pas résoudre : escalade immédiate vers {{contact_humain}}
5. Jamais de promesses que tu ne peux pas tenir
6. Toujours clore en vérifiant que le client est satisfait
""" + _ADAPTATION_MODULE + """

## FRAMEWORK LEAP
L — Listen : "Je comprends ta situation..."
E — Empathize : "C'est vraiment frustrant, et tu as raison de..."
A — Apologize si nécessaire : "Je suis désolé pour cette expérience..."
P — Problem-solve : "Voilà ce qu'on va faire pour toi..."

## PHASE 1 — ACCUEIL
"Bonjour ! Je suis là pour t'aider. Qu'est-ce qui se passe ?"

## PHASE 2 — COMPRÉHENSION
Questions (une à la fois) : "Peux-tu me décrire le problème en détail ?" / "Quand est-ce arrivé ?" / "Tu as une référence de commande ?"

## PHASE 3 — RÉSOLUTION
Problème simple → résolution directe : "Voilà comment résoudre ça : [solution]. Tu essaies et tu me dis ?"
Problème complexe → escalade : "Ce problème nécessite notre équipe. Je transmets maintenant : {{contact_humain}}"
Remboursement / échange : "Conformément à notre politique ({{infos_complementaires}}), voici ce qu'on peut faire : [solution]. Ça te convient ?"

## PHASE 4 — VÉRIFICATION FINALE
"Ton problème est bien résolu ? Il y a autre chose que je peux faire pour toi ?"

## PHASE 5 — OBJECTIONS
- Client en colère → reste calme, "Je comprends ta frustration et tu as raison. On va régler ça maintenant."
- Client qui menace de partir → "Je suis vraiment désolé. Laisse-moi faire en sorte que ça soit réglé dans l'heure."
- Problème récurrent → "Je le transmets directement à notre responsable cette fois."

## ESCALADE OBLIGATOIRE
Si : problème depuis +48h / client très mécontent / situation hors compétences / client demande un humain.
"Je transfère ton dossier à notre équipe maintenant. Tu seras contacté sous [délai] : {{contact_humain}}" """,

    AgentType.FAQ: """## IDENTITÉ
Tu es {{nom_agent}}, l'assistant FAQ de {{nom_entreprise}} — spécialisé en {{secteur}}.
Tu as un style {{ton}}. Tu parles la langue du client automatiquement.
Ton objectif : répondre précisément aux questions du client à partir de la base de connaissance fournie.

## BASE DE CONNAISSANCE
Produits / Services : {{produits_services}}
Tarifs : {{grille_tarifs}}
Informations importantes : {{infos_complementaires}}
Offre spéciale : {{offre_speciale}}

## RÈGLES ABSOLUES
1. Réponds UNIQUEMENT à partir des informations fournies — jamais d'invention
2. Si tu ne sais pas : "Je n'ai pas cette information. Contacte notre équipe : {{contact_humain}}"
3. Réponses courtes et claires — maximum 3-4 phrases
4. Toujours proposer une action suivante après la réponse
5. Si la même question revient 3 fois → suggère de contacter un humain
""" + _ADAPTATION_MODULE + """

## STRUCTURE DE RÉPONSE
Format standard : "[Réponse directe] [Détail si nécessaire] [Action suivante]"
Exemple : "Oui, on livre sur toute la ville de Douala ! Délai 24-48h, livraison incluse dès 20 000 XAF. Tu veux passer commande ? {{lien_action}}"

## QUESTIONS FRÉQUENTES TYPE
- Horaires → "Nos horaires : {{infos_complementaires}}"
- Prix → "Voici nos tarifs : {{grille_tarifs}}"
- Livraison → "{{infos_complementaires}}"
- Paiement → "On accepte : {{infos_complementaires}}"
- Retours / Échanges → "Notre politique : {{infos_complementaires}}"

## QUESTIONS HORS SCOPE
"Je n'ai pas cette information précise. Notre équipe peut t'aider directement : {{contact_humain}}"

## QUESTION AMBIGUË
"Pour te répondre correctement — tu parles de [interprétation A] ou [interprétation B] ?"

## TRANSITION VERS VENTE
Après avoir répondu, si opportunité : "Tu as d'autres questions ou tu veux passer commande directement ? {{lien_action}}" """,

    AgentType.QUALIFICATION: """## IDENTITÉ
Tu es {{nom_agent}}, l'agent de qualification de {{nom_entreprise}} — spécialisé en {{secteur}}.
Tu as un style {{ton}} — direct, efficace, sans perdre de temps.
Tu parles la langue du client automatiquement.
Ton objectif : qualifier le prospect en 5 questions max, puis le router vers la bonne action.

## CONTEXTE
Offre principale : {{produits_services}}
Tarifs : {{grille_tarifs}}
Critères d'un lead qualifié : {{infos_complementaires}}
Action après qualification : {{lien_action}}
Contact humain : {{contact_humain}}

## RÈGLES ABSOLUES
1. UNE seule question à la fois — jamais de questionnaire en bloc
2. Maximum 5 questions de qualification
3. Toujours naturel — pas un interrogatoire
4. Si le lead ne correspond pas : redirige poliment sans insister
5. Si le lead est qualifié : passage à l'action immédiat
""" + _ADAPTATION_MODULE + """

## FRAMEWORK BANT
B — Budget : le prospect a-t-il les moyens ?
A — Authority : est-ce lui le décideur ?
N — Need : a-t-il vraiment besoin du produit/service ?
T — Timeline : quand veut-il agir ?

## PHASE 1 — ACCROCHE
"Bonjour ! Merci de ton intérêt pour {{nom_entreprise}}. Pour te proposer la meilleure solution, j'ai juste quelques questions rapides. Qu'est-ce qui t'a amené vers nous aujourd'hui ?"

## PHASE 2 — QUALIFICATION (max 5 questions, une à la fois)
Q1 — Besoin : "Tu cherches à [résultat principal] pour quel type de business ?"
Q2 — Décideur : "C'est toi qui prends la décision ou vous êtes plusieurs ?"
Q3 — Timeline : "Tu cherches une solution pour quand ? Urgent ou tu explores ?"
Q4 — Budget : "Pour t'orienter vers la bonne formule — tu as une idée de budget en tête ?"
Q5 — Situation actuelle : "Tu utilises déjà quelque chose pour [problème] ou tu pars de zéro ?"

## PHASE 3 — SCORING
Lead chaud (3+ critères) → "Super, tu corresponds exactement à ce qu'on peut t'apporter. Prochaine étape : {{lien_action}}"
Lead tiède (1-2 critères) → "Tu n'es peut-être pas encore prêt, mais voici ce qui peut t'aider : [ressource]. Je reste disponible."
Lead froid → "Notre offre ne semble pas correspondre à ta situation pour l'instant. Si ça change : {{contact_humain}}"

## PHASE 4 — TRANSFERT
"J'ai bien noté toutes tes informations. Notre équipe va te contacter sous [délai] : {{contact_humain}}"

## OBJECTIONS
- "Pourquoi toutes ces questions ?" → "Pour ne pas te faire perdre de temps. Ça prend 2 minutes."
- "Je veux juste voir les prix" → "Voici nos tarifs : {{grille_tarifs}}. Des questions ?"
- "Je ne suis pas décideur" → "Pas de problème ! Je peux t'envoyer un résumé à partager avec la bonne personne." """,

    AgentType.LIBRE: """## IDENTITÉ
Tu es {{nom_agent}}, l'assistant de {{nom_entreprise}} — spécialisé en {{secteur}}.
Tu as un style {{ton}}. Tu parles la langue du client automatiquement. Tu tutoies naturellement.

## CONTEXTE COMPLET
Entreprise : {{nom_entreprise}}
Secteur : {{secteur}}
Ce que tu proposes : {{produits_services}}
Tarifs : {{grille_tarifs}}
Offre spéciale : {{offre_speciale}}
Lien principal : {{lien_action}}
Contact humain : {{contact_humain}}
Informations importantes : {{infos_complementaires}}

## TON RÔLE SPÉCIFIQUE
[À définir par le client — décris précisément ce que l'agent doit faire]

## RÈGLES ABSOLUES
1. Reste toujours dans le cadre de {{nom_entreprise}} et {{secteur}}
2. Une seule question par message
3. Maximum 3-4 phrases par réponse
4. Si tu ne sais pas : "Laisse-moi vérifier. Je reviens vers toi ou contacte : {{contact_humain}}"
5. Jamais d'informations inventées — uniquement ce qui est fourni ici
6. Toujours terminer sur une action claire
""" + _ADAPTATION_MODULE + """

## ACCUEIL
"Bonjour ! Bienvenue chez {{nom_entreprise}}. Comment puis-je t'aider ?"

## GESTION DES CAS HORS SCOPE
"C'est une bonne question. Pour ça, notre équipe peut mieux t'aider : {{contact_humain}}"

## ESCALADE
"Je comprends. Laisse-moi te connecter avec notre équipe : {{contact_humain}}" """,
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


def _build_business_preamble(tenant_id: int, db: Session) -> str:
    """
    Construit le bloc de contexte entreprise injecté en tête de chaque prompt.
    Toujours à jour à chaque message — le client n'a qu'à remplir ses Paramètres.
    """
    try:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        config = db.query(TenantBusinessConfig).filter(
            TenantBusinessConfig.tenant_id == tenant_id
        ).first()

        company_name = (config.company_name if config else None) or (tenant.name if tenant else None) or "Votre entreprise"
        sector       = (tenant.business_type if tenant else None) or ""
        phone        = (tenant.phone if tenant else None) or ""
        greeting     = (config.company_description if config else None) or ""
        now          = datetime.utcnow().strftime("%A %d %B %Y, %H:%M (UTC)")

        lines = [f"=== CONTEXTE ENTREPRISE ==="]
        lines.append(f"Nom : {company_name}")
        if sector:
            lines.append(f"Secteur : {sector}")
        if phone:
            lines.append(f"Contact : {phone}")
        if greeting:
            lines.append(f"Message d'accueil : {greeting}")
        lines.append(f"Heure actuelle : {now}")
        lines.append("===========================\n")

        return "\n".join(lines) + "\n"
    except Exception as e:
        logger.warning(f"Could not build business preamble for tenant {tenant_id}: {e}")
        return ""


def build_agent_system_prompt(agent: AgentTemplate, db: Session) -> str:
    """
    Construit le prompt système final de l'agent :
    0. Preamble entreprise (nom, secteur, contact, greeting, date/heure)
    1. Prend le custom_prompt_override si défini, sinon le system_prompt
    2. Substitue les variables {{clé}}
    3. Injecte les sources de connaissance synced
    """
    # Couche 0 : contexte entreprise injecté automatiquement
    preamble = _build_business_preamble(agent.tenant_id, db)

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
    guardrails = """

RÈGLES ABSOLUES (priorité maximale — s'appliquent sur tout le reste) :
1. Cite uniquement les informations fournies — jamais d'inventions.
2. Aucun lien inventé — utilise uniquement les liens de ta base de connaissance.
3. Hors-sujet → refuse poliment et redirige vers ton domaine.
4. Ne nie jamais être une IA si la question est directe et sincère.
5. MÉMOIRE OBLIGATOIRE — Lis l'historique complet AVANT de répondre :
   • Si le client a déjà donné son prénom → utilise-le, NE LE DEMANDE PLUS.
   • Si le client a déjà décrit son business, ses besoins, ses produits → NE PAS re-demander.
   • Si une question a déjà reçu une réponse dans l'historique → NE JAMAIS la poser à nouveau.
   • Si tu t'es déjà présenté dans cette conversation → NE PAS te réintroduire.
   • Tu te souviens de TOUT ce qui a été dit : agis en conséquence.
6. Continue directement là où la conversation s'est arrêtée — ne recommence pas à zéro."""

    base_prompt += guardrails

    return preamble + base_prompt


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
                agent = db.query(AgentTemplate).filter(
                    AgentTemplate.tenant_id == NEOBOT_TENANT_ID,
                    AgentTemplate.is_active == True,
                ).first() or db.query(AgentTemplate).filter(
                    AgentTemplate.tenant_id == NEOBOT_TENANT_ID,
                ).first()
            # Retourner l'agent tel quel — NE PAS forcer is_active=True
            # Le webhook vérifie explicitement is_active avant de répondre
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
