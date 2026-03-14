"""
Service IA avec Retrieval Augmented Generation (RAG)
Récupère les vraies données métier et les injecte dans les prompts
"""

import os
import logging
from typing import Union, Optional
from sqlalchemy.orm import Session
from .http_client import DeepSeekClient
from .knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# ========== PROMPTS DE BASE INTELLIGENTS ==========

def get_system_prompt_with_rag(
    mode: str,
    business_name: str,
    rag_context: str = "",
    tone: str = "Professional",
    selling_focus: str = "Quality"
) -> str:
    """
    Créer le prompt système en utilisant:
    1. Le mode de réponse (neobot_admin vs client)
    2. Les vraies données du business (RAG context)
    3. Le ton et le focus de vente
    """
    
    if mode == "neobot_admin":
        base_prompt = f"""Tu es NéoBot, l'assistant commercial de la plateforme NéoBot pour l'automatisation WhatsApp.

{rag_context if rag_context else ''}

INSTRUCTIONS ESSENTIELLES:
1. Réponds UNIQUEMENT sur NéoBot et ses services
2. Utilise les vrais tarifs et plans ci-dessus
3. Mentionne TOUJOURS WhatsApp dans tes réponses
4. Sois {tone} mais aussi engageant et persuasif
5. Réponse concise: max 3-4 lignes
6. Propose un essai gratuit ou un plan adapté
7. Ne parle PAS de: web design, marketing digital, administratif

PRIORITÉ: Les informations réelles du profil NéoBot ci-dessus sont LA SOURCE DE VÉRITÉ. Utilise-les!
"""
    else:
        base_prompt = f"""Tu es l'assistant commercial de {business_name}.

{rag_context if rag_context else ''}

INSTRUCTIONS ESSENTIELLES:
1. Réponds UNIQUEMENT sur les produits/services de {business_name}
2. Ne mentionne PAS NéoBot (sauf si le client le demande)
3. Ton: {tone}
4. Focus de vente: {selling_focus}
5. Réponse concise: max 3-4 lignes
6. Guide vers l'achat ou la réservation
7. Si le client demande quelque chose que tu ne sais pas, propose aide ou contact
"""
    
    return base_prompt


def build_conversation_messages(
    user_message: str,
    system_prompt: str,
    conversation_history: list = None
) -> list:
    """Construire la liste des messages pour l'API"""
    
    messages = [
        {"role": "system", "content": system_prompt},
    ]
    
    # Ajouter l'historique
    if conversation_history:
        messages.extend(conversation_history)
    
    # Ajouter le message actuel
    messages.append({"role": "user", "content": user_message})
    
    return messages


# ========== FONCTION PRINCIPALE AVEC RAG ==========

async def generate_ai_response_with_db(
    message: str,
    tenant_id: int,
    db: Session,
    conversation_history: list = None
) -> str:
    """
    Générer une réponse IA intelligente en utilisant:
    - Les vraies données du business (via RAG)
    - Le profil du tenant (tone, focus, produits)
    - L'historique de conversation
    """
    
    try:
        # 1️⃣ RÉCUPÉRER LE PROFIL DU TENANT (+ créer s'il n'existe pas)
        profile = KnowledgeBaseService.get_tenant_profile(db, tenant_id)
        if not profile:
            # Si pas de profil, créer le profil par défaut
            profile = KnowledgeBaseService.create_default_neobot_profile(db, tenant_id)
        
        # 2️⃣ DÉTERMINER LE MODE ET FORMATER LE RAG CONTEXT
        is_neobot = profile.get('business_type') == 'neobot' or 'neobot' in profile.get('name', '').lower()
        mode = "neobot_admin" if is_neobot else "client"
        
        # Récupérer le contexte RAG (infos métier formatées)
        rag_context = KnowledgeBaseService.format_profile_for_prompt(profile)
        
        # 3️⃣ CONSTRUIRE LE PROMPT SYSTÈME AVEC LES VRAIES DONNÉES
        system_prompt = get_system_prompt_with_rag(
            mode=mode,
            business_name=profile.get('company_name', 'Sans nom'),
            rag_context=rag_context,
            tone=profile.get('tone', 'Professional'),
            selling_focus=profile.get('selling_focus', 'Quality')
        )
        
        # 4️⃣ GÉRER LES MESSAGES SIMPLES
        message_lower = message.lower().strip()
        simple_triggers = {
            "salutation": ["bonjour", "salut", "hello", "hi", "coucou"],
            "merci": ["merci", "thanks", "thanks you", "merci beaucoup"],
        }
        
        for intent, triggers in simple_triggers.items():
            if any(t in message_lower for t in triggers) and len(message_lower.split()) <= 3:
                if intent == "salutation":
                    # Réponse simple de salutation
                    if is_neobot:
                        return "👋 Bonjour! Je suis NéoBot, votre assistant d'automatisation WhatsApp. Comment je peux vous aider?"
                    else:
                        return f"👋 Bonjour et bienvenue chez {profile.get('company_name')}! Comment puis-je vous aider?"
                elif intent == "merci":
                    return "Merci! C'est un plaisir! 😊 Besoin d'autre chose?"
        
        # 5️⃣ APPEL API DEEPSEEK AVEC RAG CONTEXT
        messages = build_conversation_messages(
            user_message=message,
            system_prompt=system_prompt,
            conversation_history=conversation_history
        )
        
        response_data = await DeepSeekClient.call(
            messages=messages,
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=150
        )
        
        # 6️⃣ TRAITER LA RÉPONSE
        if "error" in response_data:
            logger.warning(f"API error: {response_data.get('error')}")
            # Fallback: réponse simple générée localement
            return _get_smart_fallback(message, profile, is_neobot)
        
        if "choices" not in response_data:
            return _get_smart_fallback(message, profile, is_neobot)
        
        ai_response = response_data["choices"][0]["message"]["content"].strip()
        
        # 7️⃣ POST-PROCESSING
        # Limiter la longueur
        lines = ai_response.split('\n')
        if len(lines) > 5:
            ai_response = '\n'.join(lines[:5])
        
        if len(ai_response) > 400:
            ai_response = ai_response[:397] + "..."
        
        return ai_response
        
    except Exception as e:
        logger.error(f"Error in generate_ai_response_with_db: {e}")
        # Fallback en cas d'erreur
        profile = KnowledgeBaseService.get_tenant_profile(db, tenant_id)
        is_neobot = profile.get('business_type') == 'neobot' if profile else False
        return _get_smart_fallback(message, profile, is_neobot)


# ========== FONCTION FALLBACK INTELLIGENTE ==========

def _get_smart_fallback(message: str, profile: dict, is_neobot: bool) -> str:
    """
    Fallback intelligent - utilise le profil pour générer une réponse pertinente
    Utilisé quand l'API est lente ou en erreur
    """
    
    message_lower = message.lower()
    company_name = profile.get('company_name', 'NéoBot') if profile else 'NéoBot'
    
    if is_neobot:
        # NéoBot a des templates spécifiques
        if any(w in message_lower for w in ["quoi", "comment", "c'est", "fonctionne"]):
            return f"🤖 NéoBot automatise les réponses WhatsApp de votre entreprise. Vous pouvez répondre à vos clients 24/7!"
        
        elif any(w in message_lower for w in ["prix", "coûte", "tarif", "combien"]):
            return "💰 Nos plans:\n- Basique: 20,000 FCFA/mois\n- Standard: 50,000 FCFA/mois\n- Pro: 90,000 FCFA/mois\nEssai gratuit 7 jours!"
        
        elif any(w in message_lower for w in ["essai", "trial", "demo", "test"]):
            return "🎯 Lancez un essai gratuit de 7 jours - pas de carte bancaire requise! Comment souhaitez-vous commencer?"
        
        else:
            return "🤖 Besoin d'aide avec NéoBot? Posez votre question!"
    else:
        # Client générique
        if any(w in message_lower for w in ["prix", "coûte", "tarif"]):
            return f"💰 Veuillez nous contacter pour les tarifs. Chez {company_name}, nous avons des vous proposer!"
        
        elif any(w in message_lower for w in ["commander", "acheter", "réserver"]):
            return f"✅ Super! Chez {company_name}, nous sommes prêts à vous servir. Qu'aimeriez-vous?"
        
        else:
            return f"👋 Bienvenue chez {company_name}! Comment puis-je vous aider?"


# ========== FONCTION SIMPLE (BACKWARD COMPATIBILITY) ==========

async def generate_ai_response(
    message: str,
    business_info: Union[str, dict],
    business_name: str = None,
    conversation_history: list = None,
    db: Session = None,
    tenant_id: int = None
) -> str:
    """
    Version simple - appelle la version RAG si les paramètres DB sont fournis
    Sinon utilise la logique générique
    """
    
    # Si on a la DB et tenant_id, utiliser la version RAG
    if db and tenant_id:
        return await generate_ai_response_with_db(
            message=message,
            tenant_id=tenant_id,
            db=db,
            conversation_history=conversation_history
        )
    
    # Sinon, logique simple de fallback
    business_type = ""
    if isinstance(business_info, dict):
        business_type = business_info.get("business_type", "")
        if not business_name:
            business_name = business_info.get("name", "")
    elif hasattr(business_info, 'business_type'):
        business_type = business_info.business_type
    
    is_neobot = "neobot" in str(business_type).lower()
    return _get_smart_fallback(message, {}, is_neobot)
