"""
Sales Prompt Generator - Crée des prompts persuasifs avec questions
Ajoute les données réelles et des CTAs (Call-To-Action)
"""

import logging
import random
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class SalesPromptGenerator:
    """
    Génère des prompts IA optimisés pour la vente
    Injecte les données réelles + questions pertinentes
    """
    
    # Questions pertinentes par type d'intention
    QUESTIONS_BY_INTENT = {
        "pricing_inquiry": [
            "Quel est votre volume mensuel de messages que vous envisagez d'envoyer?",
            "Avez-vous actuellement une présence WhatsApp Business?",
            "Combien de clients contactez-vous généralement par mois?",
            "Cherchez-vous une solution pour réduire vos coûts de communication?"
        ],
        "plan_inquiry": [
            "Quel est votre volume de messages mensuel estimé?",
            "Avez-vous besoin de support prioritaire?",
            "Combien de canaux WhatsApp envisagez-vous d'avoir?",
            "Quelle est votre priorité: coût ou fonctionnalités?"
        ],
        "how_it_works": [
            "Êtes-vous intéressé pour tester gratuitement pendant 14 jours?",
            "Avez-vous des questions sur l'installation ou la configuration?",
            "Quel est votre cas d'usage principal? (Support client, ventes, notifications?)",
            "Souhaiteriez-vous une démo personn alisée?"
        ],
        "trial_request": [
            "Quel est ce qui vous intéresse le plus à tester en priorité?",
            "Avez-vous une date limite pour votre décision?",
            "Y a-t-il des fonctionnalités spécifiques que vous aimeriez tester?"
        ],
        "features_inquiry": [
            "Lequel de ces avantages est le plus important pour vous?",
            "Avez-vous d'autres besoins spécifiques?",
            "Cela correspond-il à vos attentes?"
        ],
        "support_request": [
            "Avez-vous rencontré un problème avec votre compte?",
            "Comment puis-je mieux vous assister?",
            "Aimeriez-vous une session de support en direct?"
        ],
        "demo_request": [
            "Préférez-vous une démo vidéo ou un appel en direct?",
            "Y a-t-il des cas d'usage spécifiques à démontrer?",
            "Quelle est votre disponibilité cette semaine?"
        ],
        "greeting": [
            "Comment puis-je vous aider aujourd'hui?",
            "Que voulez-vous savoir sur NéoBot?",
            "Êtes-vous intéressé par notre solution pour WhatsApp?"
        ],
        "product_inquiry": [
            "Quel type de produit/service vous intéresse spécifiquement?",
            "Avez-vous des questions sur nos offres?",
            "Devrais-je vous montrer plus de détails sur certains articles?"
        ],
        "general_inquiry": [
            "Y a-t-il un aspect particulier de NéoBot que vous aimeriez explorer?",
            "Quelle est votre principale préoccupation en matière d'automatisation?",
            "Etes-vous actuellement en train d'évaluer des solutions similaires?"
        ]
    }
    
    # CTAs (Call-To-Action) par type
    CTAS_BY_INTENT = {
        "pricing_inquiry": "Démarrer mon essai gratuit 14 jours →",
        "plan_inquiry": "Découvrir le plan Essential →",
        "how_it_works": "Réserver une démo gratuite →",
        "trial_request": "S'inscrire pour l'essai gratuit 14 jours →",
        "features_inquiry": "Découvrir plus de fonctionnalités →",
        "support_request": "Contacter notre support →",
        "demo_request": "Réserver mon créneau démo →",
        "greeting": "En savoir plus sur NéoBot →",
        "product_inquiry": "Voir notre catalogue complet →",
        "general_inquiry": "Commencer dès maintenant →"
    }
    
    @staticmethod
    def generate(
        message: str,
        intent: str,
        category: str,
        business_data: Dict,
        conversation_history: Optional[list] = None,
        extra_context: Optional[str] = None
    ) -> str:
        """
        Génère un prompt optimisé pour DeepSeek
        
        Args:
            message: Le message de l'utilisateur
            intent: Type d'intention détecté
            category: Catégorie de la question
            business_data: Données du profil métier (company, prices, features)
            conversation_history: Historique de conversation
        
        Returns:
            Prompt complet à envoyer à DeepSeek
        """
        
        logger.info(f"📝 Generating sales prompt for intent: {intent}")
        
        # Extraire les données
        company_name = business_data.get("company_name", "NéoBot")
        tone = business_data.get("tone", "Professional, Friendly")
        product_data = business_data.get("products_services", [])
        
        # Formatter les produits
        products_str = _format_products(product_data)
        
        # Sélectionner une question pertinente
        relevant_questions = SalesPromptGenerator.QUESTIONS_BY_INTENT.get(
            intent,
            SalesPromptGenerator.QUESTIONS_BY_INTENT["general_inquiry"]
        )
        question = random.choice(relevant_questions)
        
        # Sélectionner un CTA
        cta = SalesPromptGenerator.CTAS_BY_INTENT.get(
            intent,
            SalesPromptGenerator.CTAS_BY_INTENT["general_inquiry"]
        )
        
        # Construire le prompt complet
        prompt = f"""Tu es {company_name}, un assistant IA pour WhatsApp automatisé.

=== INFORMATIONS ENTREPRISE ===
Nom: {company_name}
Ton: {tone}
Message de l'utilisateur: "{message}"

=== OFFRE ACTUELLE (SEUL PLAN DISPONIBLE) ===
{products_str}

⚠️ RÈGLES ABSOLUES SUR LES PLANS :
- SEUL le plan Essential (20 000 FCFA/mois) est disponible aujourd'hui
- Si l'utilisateur demande d'autres plans, réponds : "D'autres formules arrivent bientôt. Pour l'instant, notre plan Essential couvre tous vos besoins."
- Ne JAMAIS mentionner Business, Enterprise, Standard, Pro, Starter ou tout autre nom de plan
- Ne JAMAIS inventer de prix ou fonctionnalités absents de la base
- Plan Essential : 20 000 FCFA/mois — 2 500 messages/mois — 1 agent IA — essai 14 jours GRATUIT

=== INSTRUCTIONS ===
1. Réponds UNIQUEMENT aux questions liées à {company_name} et nos services
2. Si tu ne sais pas la réponse, dis-le honnêtement
3. Parle UNIQUEMENT du plan Essential (20 000 FCFA/mois, 2 500 msgs, essai 14j gratuit)
4. Si l'utilisateur demande d'autres plans, oriente vers Essential et annonce qu'autres formules arrivent bientôt
5. Sois persuasif mais honnête - pas de mensonges
6. Chaque réponse DOIT finir par cette question EXACTE (sur une nouvelle ligne):

🎯 QUESTION: {question}

7. Ne mentionne PAS le CTA directement dans la réponse
8. Garde la réponse concise (max 3-4 paragraphes)
9. Utilise des emojis pertinents pour améliorer lisibilité
10. Sois enthousiaste mais professionnel

=== RÉPONSE À FOURNIR ===
Réponds à la question de l'utilisateur en intégrant naturellement les informations ci-dessus.
Termine TOUJOURS par: 🎯 QUESTION: [la question sélectionnée]
"""
        
        if extra_context and extra_context.strip():
            prompt += f"\n=== CONTEXTE CLIENT (CRM & Historique) ===\n{extra_context.strip()}\n"
        
        logger.info(f"✅ Prompt générée pour intent={intent}, question='{question[:60]}...'")
        
        return prompt
    
    @staticmethod
    def generate_rejection_response(
        is_relevant: bool,
        category: str,
        redirect_message: Optional[str] = None,
        business_name: str = "NéoBot"
    ) -> str:
        """
        Génère une réponse pour les messages hors-sujet
        """
        
        if is_relevant:
            return ""  # Pas de rejection si c'est pertinent
        
        if redirect_message:
            return redirect_message
        
        # Fallback par catégorie
        fallbacks = {
            "completely_irrelevant": (
                f"Je suis {business_name}, spécialisé dans l'automatisation WhatsApp. "
                f"Je ne peux pas répondre à cette question. "
                f"Avez-vous des questions sur nos services?\n\n"
                f"👉 Que puis-je faire pour vous?"
            ),
            "too_generic": (
                f"Bonjour! 👋 Je suis {business_name}. "
                f"Pour mieux vous aider, pouvez-vous préciser votre question?\n\n"
                f"Exemples: prix, fonctionnement, essai gratuit?\n\n"
                f"👉 Quel est votre besoin?"
            ),
            "unclassified": (
                f"Merci pour votre message! Je n'ai pas bien compris votre question. "
                f"Pouvez-vous reformuler?\n\n"
                f"👉 Comment puis-je vous aider?"
            )
        }
        
        return fallbacks.get(category, "Comment puis-je vous aider?")


def _format_products(products: list) -> str:
    """Formate les produits pour le prompt"""
    
    if not products:
        return "❌ Aucun produit configuré"
    
    formatted = "📦 **NOS SERVICES:**\n\n"
    
    for product in products:
        if isinstance(product, dict):
            name = product.get("name", "Produit")
            price = product.get("price", "N/A")
            description = product.get("description", "")
            
            formatted += f"**{name}**: {price:,} FCFA/mois\n"
            if description:
                # Prendre seulement les premiers 60 caractères
                short_desc = description[:80]
                formatted += f"  └─ {short_desc}\n"
            formatted += "\n"
    
    return formatted


def generate_sales_response(
    user_message: str,
    is_relevant: bool,
    intent: str,
    category: str,
    redirect_message: Optional[str],
    business_data: Dict,
    conversation_history: Optional[list] = None
) -> str:
    """
    Wrapper function - retourne le prompt complet ou la rejection
    """
    
    if not is_relevant:
        # Message hors-sujet = rejeter avec redirection
        return SalesPromptGenerator.generate_rejection_response(
            is_relevant=False,
            category=category,
            redirect_message=redirect_message,
            business_name=business_data.get("company_name", "NéoBot")
        )
    
    # Message pertinent = générer prompt de vente
    return SalesPromptGenerator.generate(
        message=user_message,
        intent=intent,
        category=category,
        business_data=business_data,
        conversation_history=conversation_history
    )
