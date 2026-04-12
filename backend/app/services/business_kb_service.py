"""
Business Knowledge Base Service
Gère la constellation de prompts intelligents basée sur le type de business
"""
from sqlalchemy.orm import Session
from app.models import TenantBusinessConfig, ConversationContext, BusinessTypeModel, Message
from app.database import engine
import json
import logging

logger = logging.getLogger(__name__)

class BusinessKBService:
    """Service pour gérer la Knowledge Base par type de business"""
    
    @staticmethod
    def get_business_persona(tenant_id: int, db: Session) -> dict:
        """
        Récupère la configuration complète du business d'un tenant
        
        Retour:
        {
            "business_type": "restaurant",
            "company_name": "La Saveur",
            "persona": "Tu es l'assistant de...",
            "instructions": {...},
            "products": [...],
            "tone": "friendly"
        }
        """
        
        # 1. Récupérer config business du tenant
        config = db.query(TenantBusinessConfig).filter(
            TenantBusinessConfig.tenant_id == tenant_id
        ).first()
        
        # Si pas de config, retourner la persona NéoBot par défaut
        if not config:
            return BusinessKBService._get_default_neobot_persona()
        
        # 2. Récupérer le type de business
        try:
            business_type = config.business_type.slug
        except Exception as e:
            logger.warning(f"business_type.slug inaccessible pour tenant config {config.id}: {e}")
            business_type = "custom"

        # 3. Parser les produits/services
        try:
            products = json.loads(config.products_services) if isinstance(config.products_services, str) else config.products_services or []
        except Exception as e:
            logger.warning(f"Parsing products_services échoué pour tenant config {config.id}: {e}")
            products = []
        
        # 4. Construire la persona complète
        return {
            "business_type": business_type,
            "company_name": config.company_name or "Our Company",
            "company_description": config.company_description or "",
            "tone": config.tone or "professional",
            "selling_focus": config.selling_focus or "Quality",
            "products": products,
            "instructions": BusinessKBService._get_business_instructions(business_type),
            "persona": BusinessKBService._generate_persona(config),
        }
    
    @staticmethod
    def _generate_persona(config: TenantBusinessConfig) -> str:
        """Génère une persona personnalisée"""
        
        base_persona = f"""Tu es l'assistant IA de {config.company_name or 'our company'}.

"""
        
        if config.company_description:
            base_persona += f"Description: {config.company_description}\n\n"
        
        base_persona += f"""Tes objectifs:
1. Accueillir le client chaleureusement
2. Comprendre ses besoins
3. Proposer uniquement les produits/services de notre catalogue
4. Conclure la vente intelligemment

Ton: {config.tone or 'Professional'}
Focus: {config.selling_focus or 'Quality'}

🚨 RÈGLES ABSOLUES — NE JAMAIS ENFREINDRE:
1. CATALOGUE UNIQUEMENT: Cite UNIQUEMENT les produits, modèles, prix et liens présents dans la liste "PRODUITS/SERVICES" fournie. JAMAIS inventer un produit, un modèle, une couleur, un prix ou une URL qui n'y est pas.
2. Si un client demande un produit non listé: "Je n'ai pas ce modèle dans mon catalogue actuel. Voici ce que j'ai disponible: [liste] — souhaitez-vous que je vous aide à choisir parmi ces options ?"
3. Si le catalogue est vide: "Notre catalogue n'est pas encore configuré. Contactez-nous directement pour vos demandes."
4. HORS-SUJET: Si la question n'a aucun rapport avec {config.company_name or 'notre activité'} ou nos produits/services, réponds: "Je suis l'assistant de {config.company_name or 'cette boutique'} et je suis spécialisé sur nos produits. Comment puis-je vous aider sur ce sujet ?" — ne réponds JAMAIS à des questions sur d'autres business, d'autres sujets, ou des conseils généraux.
5. LIENS: Ne donne JAMAIS un lien inventé. Utilise uniquement les liens fournis dans le catalogue.
6. COHÉRENCE: Reste cohérent avec l'historique de conversation.
7. Personnalise selon les intérêts du client."""
        
        return base_persona
    
    @staticmethod
    def _get_default_neobot_persona() -> dict:
        """Persona par défaut: NéoBot se vend lui-même"""
        return {
            "business_type": "neobot",
            "company_name": "NéoBot",
            "company_description": "NéoBot - Plateforme d'automatisation WhatsApp avec IA",
            "tone": "professional_friendly",
            "selling_focus": ["Automatisation", "24/7", "IA"],
            "products": [
                {
                    "name": "Essential",
                    "price": 20000,
                    "messages": 2500,
                    "description": "2 500 messages/mois — 1 agent IA — Essai 14j gratuit"
                },
            ],
            "instructions": BusinessKBService._get_business_instructions("neobot"),
            "persona": """Tu es NéoBot, l'assistant commercial qui présente et vend NéoBot.

NéoBot = Plateforme SaaS africaine d'automatisation WhatsApp par IA

Avantages clés :
✅ Réponses 24h/24, 7j/7 à tes clients
✅ Gain de 2 à 3 heures par jour
✅ +30% de conversions via WhatsApp
✅ Dashboard Analytics 30 jours

Plan disponible : Essential
- 20 000 FCFA/mois
- 2 500 messages WhatsApp/mois
- 1 agent IA actif (Vente, RDV, Support, FAQ, Qualification)
- Sources Texte + PDF (3 max)
- Essai gratuit 14 jours — aucune carte bancaire requise

D'autres formules arrivent bientôt.

Ton objectif : CONVAINCRE que l'automatisation WhatsApp est INDISPENSABLE.
Sois professionnel, enthousiaste, honnête."""
        }
    
    @staticmethod
    def _get_business_instructions(business_type: str) -> dict:
        """Retourne instructions de vente spécifiques par business"""
        
        instructions_map = {
            "restaurant": {
                "opening_move": "Bienvenue! Que puis-je vous proposer du jour?",
                "suggest_strategy": "Proposes toujours les plats du jour en premier",
                "key_questions": [
                    "Etes-vous régulier chez nous?",
                    "Avez-vous des préférences (viande, poisson, végé)?",
                    "Voulez-vous une boisson?",
                    "Connaissez-vous notre spécialité maison?"
                ],
                "closing_move": "Je peux vous proposer un dessert ou un café?",
                "sales_tips": "Montrer enthousiasme pour les plats, mention allergies"
            },
            
            "ecommerce": {
                "opening_move": "Bienvenue dans notre boutique! Cherchez-vous quelque chose?",
                "suggest_strategy": "Montrer produits tendance et best-sellers en premier",
                "key_questions": [
                    "Savez-vous déjà quel modèle vous voulez?",
                    "Quelle est votre taille habituelle?",
                    "Quel est votre budget?",
                    "C'est pour vous ou un cadeau?"
                ],
                "closing_move": "Je peux vous aider avec le paiement ou vous avez des questions?",
                "sales_tips": "Montrer des images, suggestions alternatives, promotions actives"
            },
            
            "travel": {
                "opening_move": "Aventure Voyages! Où rêvez-vous d'aller?",
                "suggest_strategy": "Proposer destinations exotiques et packages all-inclusive",
                "key_questions": [
                    "Quand souhaitez-vous voyager?",
                    "Vous préférez plage, montagne, ou culture?",
                    "Combien de jours pour le voyage?",
                    "Voyagez-vous seul, en couple ou en famille?"
                ],
                "closing_move": "Je vous envoie les détails du package et assurances?",
                "sales_tips": "Mettez en avant sécurité, confort, expériences uniques"
            },
            
            "salon": {
                "opening_move": "Bienvenue au salon! Quel service désirez-vous?",
                "suggest_strategy": "Proposer services signature et promotions actuelles",
                "key_questions": [
                    "Première visite avec nous?",
                    "Avez-vous rendez-vous ou c'est walk-in?",
                    "Quelle est votre préférence (coupe, couleur)?",
                    "Avez-vous des services compliments à ajouter?"
                ],
                "closing_move": "Je vous réserve un créneau pratique? Prochain RDV?",
                "sales_tips": "Souligner expertise, résultats avant/après, soins premium"
            },
            
            "fitness": {
                "opening_move": "Bienvenue au fitness! Cherchez-vous un abonnement?",
                "suggest_strategy": "Montrer offres de démarrage et packages populaires",
                "key_questions": [
                    "Quel est votre objectif (musculation, cardio, flexibilité)?",
                    "Vous avez déjà une expérience?",
                    "Combien de fois par semaine pouvez-vous venir?",
                    "Préférez-vous coaching personnel?"
                ],
                "closing_move": "Je vous fais une visite des installations et on démarre?",
                "sales_tips": "Mentionner succès clients, équipement modern, communauté"
            },
            
            "neobot": {
                "opening_move": "Bienvenue! Vous voulez découvrir NéoBot?",
                "suggest_strategy": "Identifier les pain points client (messages, support, temps)",
                "key_questions": [
                    "Quel est votre business?",
                    "Combien de messages recevez-vous par mois?",
                    "Quel est votre défi major en customer service?",
                    "Avez-vous actuellement un bot WhatsApp?"
                ],
                "closing_move": "Je vous fais une démo perso sur votre business?",
                "sales_tips": "Focus sur ROI, temps gagné, clients satisfaits"
            },
            
            "custom": {
                "opening_move": "Bonjour! Comment puis-je vous aider?",
                "suggest_strategy": "Adapter selon les produits/services configurés",
                "key_questions": ["Que pouvez-vous me dire de vos besoins?"],
                "closing_move": "Comment puis-je finir de vous convaincre?",
                "sales_tips": "Soyez flexible et à l'écoute du client"
            }
        }
        
        return instructions_map.get(business_type, instructions_map["custom"])
    
    @staticmethod
    def enrich_prompt_with_context(
        tenant_id: int,
        conversation_id: int,
        user_message: str,
        conversation_history: list,
        db: Session
    ) -> str:
        """
        Crée un prompt RICHE avec contexte complet
        
        Inclut:
        - Persona personnalisée
        - Historique complet (10 derniers messages)
        - Contexte client
        - Produits/services
        - Instructions de vente
        - Message clientactuel
        """
        
        # 1. Récupérer persona complète
        persona_config = BusinessKBService.get_business_persona(tenant_id, db)
        
        # 2. Récupérer contexte conversation
        context = db.query(ConversationContext).filter(
            ConversationContext.conversation_id == conversation_id
        ).first()
        
        # 3. Construire historique (max 10 derniers messages)
        history_lines = []
        for msg in conversation_history[-10:]:
            direction = "👤 Client" if msg.get('direction') == 'incoming' else "🤖 Toi"
            content = msg.get('content', '')[:200]  # Limiter à 200 chars par message
            history_lines.append(f"{direction}: {content}")
        
        history_text = "\n".join(history_lines) if history_lines else "Première interaction"
        
        # 4. Construire infos client
        client_info = ""
        if context and context.client_name:
            client_info = f"\n👤 CLIENT: {context.client_name}"
            if context.client_previous_interest:
                interests = context.client_previous_interest.get('interested_in', [])
                if interests:
                    client_info += f"\nIntérêts: {', '.join(interests[:3])}"
        else:
            client_info = "\n(Première interaction avec ce client)"
        
        # 5. Construire infos produits
        products_text = ""
        if persona_config.get('products'):
            products_text = "\n\n📦 CATALOGUE OFFICIEL — SEULS CES PRODUITS EXISTENT:\n"
            for p in persona_config['products'][:10]:  # Max 10 produits dans le prompt
                name = p.get('name', 'Unknown')
                price = p.get('price', 'N/A')
                desc = p.get('description', '')
                url = p.get('url', '')
                products_text += f"  • {name}: {price} F"
                if desc:
                    products_text += f" — {desc[:80]}"
                if url:
                    products_text += f" — Lien: {url}"
                products_text += "\n"
            products_text += "⚠️ Ne jamais citer un produit, modèle, prix ou lien qui n'est pas dans cette liste.\n"
        else:
            products_text = "\n\n⚠️ CATALOGUE VIDE: Aucun produit n'est configuré. Si le client demande des produits spécifiques, dis-lui honnêtement que le catalogue n'est pas encore disponible et invite-le à recontacter directement.\n"
        
        # 6. Construire instructions
        instructions = persona_config.get('instructions', {})
        instructions_text = f"""
💡 INSTRUCTIONS POUR CETTE CONVERSATION:
- Ouverture: {instructions.get('opening_move', 'Bienvenue')}
- Stratégie: {instructions.get('suggest_strategy', 'Soyez utile')}
- Questions clés: {', '.join(instructions.get('key_questions', ['Comment puis-je aider?'])[:2])}
- Fermeture: {instructions.get('closing_move', 'Autre chose?')}
"""
        
        # 7. CONSTRUIRE LE PROMPT FINAL
        final_prompt = f"""{persona_config.get('persona', '')}

═══════════════════════════════════════════════════════════════

📋 HISTORIQUE CONVERSATION:
{history_text}{client_info}

{products_text}{instructions_text}

═══════════════════════════════════════════════════════════════

🎯 MESSAGE CLIENT ACTUEL:
"{user_message}"

📌 RAPPELS IMPORTANTS:
1. Réponds en français
2. Sois COHÉRENT avec ce qui a été dit avant
3. CATALOGUE UNIQUEMENT — ne jamais inventer un produit, modèle, couleur, prix ou lien absent de la liste ci-dessus
4. HORS-SUJET — si la question n'a rien à voir avec nos produits/services, redirige poliment vers le catalogue
5. Personnalise selon le client
6. Sois naturel et amical
7. Guide vers l'action/vente

Réponds maintenant:
"""
        
        return final_prompt
    
    @staticmethod
    def initialize_business_types(db: Session):
        """Initialise les types de business par défaut"""
        try:
            # Vérifier si déjà initialisés
            count = db.query(BusinessTypeModel).count()
            if count > 0:
                logger.info(f"✅ Business types already initialized ({count} types)")
                return
            
            # Types par défaut
            business_types_data = [
                ("neobot", "NéoBot Service", "Vendre NéoBot lui-même", "🤖"),
                ("restaurant", "Restaurant", "Café, restaurant, fast-food", "🍽️"),
                ("ecommerce", "E-commerce", "Boutique en ligne", "🛍️"),
                ("travel", "Agence de Voyage", "Tours et vacances", "✈️"),
                ("salon", "Salon de Beauté", "Coiffure et esthétique", "💇"),
                ("fitness", "Fitness", "Gym et entraînement", "💪"),
                ("consulting", "Consulting", "Services professionnels", "📊"),
                ("custom", "Custom", "Configuration personnalisée", "⚙️"),
            ]
            
            for slug, name, description, icon in business_types_data:
                bt = BusinessTypeModel(
                    slug=slug,
                    name=name,
                    description=description,
                    icon=icon
                )
                db.add(bt)
            
            db.commit()
            logger.info(f"✅ Initialized {len(business_types_data)} business types")
            
        except Exception as e:
            logger.error(f"❌ Error initializing business types: {e}")
            db.rollback()
