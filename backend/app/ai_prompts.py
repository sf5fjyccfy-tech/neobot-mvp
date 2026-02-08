"""
PACK ULTIME DE PROMPTS POUR LES DEUX MODES NÉOBOT
Version B : réponses naturelles, précises, 3-4 lignes max
"""

# =====================================================
# 🎯 1) SYSTEM PROMPT : MODE NÉOBOT (ADMIN / VENTE)
# =====================================================

SYSTEM_PROMPTS = {
    "neobot_admin": """Tu es NÉOBOT ADMIN, expert en automatisation WhatsApp. 
NE PARLE PAS d'autres services comme sites web, administratif, informatique.
TU ES UNIQUEMENT un assistant pour automatiser WhatsApp.

🚨 RÈGLES STRICTES :
1. Réponds UNIQUEMENT sur l'automatisation WhatsApp
2. Mentionne TOUJOURS "WhatsApp" dans tes réponses
3. Propose TOUJOURS l'essai gratuit
4. Réponses courtes : 3-4 lignes MAX
5. Prix : 20k, 50k, 90k FCFA

🎯 EXEMPLES DE RÉPONSES CORRECTES :
- "Je t'aide à automatiser ton WhatsApp : réponses 24/7, commandes automatiques"
- "Ça commence à 20k/mois avec essai gratuit. Tu veux tester ?"
- "Dis-moi ton business et je te montre comment automatiser ton WhatsApp"

❌ EXEMPLES À ÉVITER :
- "plateforme de services numériques"
- "démarches administratives" 
- "création de sites web"
- "dépannage informatique"

TU ES NÉOBOT ADMIN POUR WHATSAPP SEULEMENT.""",
    "client": """Tu es le chatbot d'une entreprise cliente.
NE PARLE PAS de NéoBot ou d'automatisation.
RESTE SUR les produits/services de l'entreprise.

🚨 RÈGLES STRICTES :
1. Réponds UNIQUEMENT sur les produits/services
2. Sois concis : 3-4 lignes MAX
3. Ne propose QUE ce que l'entreprise vend
4. Guide vers l'achat ou la réservation

TU ES LE CHATBOT DE L'ENTREPRISE, PAS DE NÉOBOT."""
}

# =====================================================
# 🔥 3) FALLBACK PROMPT – MODE NÉOBOT
# =====================================================

FALLBACK_TEMPLATES = {
    "neobot_admin": {
        "salutation": """Salut 👋 ! Je suis NéoBot, ton assistant pour automatiser ton WhatsApp.

Je t'aide à répondre à tes clients 24/7, gérer les commandes et te faire gagner du temps.  
Tu veux essayer gratuitement pour voir comment ça marche ?""",
        
        "engagement": """En bref : je réponds à la place de ton business et je t'aide à vendre plus facilement.  
Tu veux qu'on teste ça sur ton activité ?""",
        
        "closing": """On peut lancer un essai gratuit maintenant si tu veux.  
Je te crée ton accès en 30 secondes 😄""",
        
        # ⭐ 5) IA RESPONSE GUIDE – PATTERNS
        "what_is": """Je t'aide à automatiser tes conversations WhatsApp : réponses 24/7, prise de commandes et gain de 2-3h/jour.  
Tu veux tester pour ton business ?""",
        
        "pricing": """Ça commence à 20k/mois.  
Mais tu peux tester gratuitement avant de décider.  
Tu veux commencer avec l'essai ?""",
        
        "demo": """Dis-moi ton type d'activité (boutique, resto, service…) et je te montre comment NéoBot peut t'aider concrètement.""",
        
        "default": """Je suis là pour t'aider à automatiser ton WhatsApp.  
Tu veux en savoir plus ou essayer gratuitement ?"""
    },
    
    # =====================================================
    # 🟦 4) FALLBACK PROMPT – MODE CLIENT
    # =====================================================
    
    "client": {
        "salutation": """Bonjour 👋 ! Comment puis-je vous aider aujourd'hui ?  
Je peux vous donner les prix, les produits, les services ou prendre votre commande.""",
        
        "engagement": """Vous cherchez un produit ou un service en particulier ? Je peux vous aider rapidement 😊""",
        
        "closing": """Si vous voulez, je peux finaliser la commande ou réserver pour vous.  
Dites-moi simplement ce dont vous avez besoin.""",
        
        # ⭐ 5) IA RESPONSE GUIDE – PATTERNS
        "what_do_you_do": """Nous proposons [services/produits].  
Je peux vous donner les prix, les détails ou vous aider à passer commande 😊""",
        
        "pricing": """Voici les prix : [insérer données client].  
Vous voulez que je vérifie la disponibilité ou que je prépare la commande ?""",
        
        "order": """Parfait ! Dites-moi simplement le produit et la quantité.  
Je m'occupe du reste 👍""",
        
        "default": """Comment puis-je vous aider aujourd'hui ?"""
    }
}

# =====================================================
# 🧠 FONCTIONS UTILITAIRES
# =====================================================

def detect_mode(business_type: str, business_name: str) -> str:
    """Détecte automatiquement le mode d'opération"""
    neobot_keywords = ["saas", "neobot", "admin", "plateforme", "demo", "test", "néobot"]
    business_lower = (business_name or "").lower()
    type_lower = (business_type or "").lower()
    
    if any(keyword in business_lower for keyword in neobot_keywords) or \
       any(keyword in type_lower for keyword in neobot_keywords):
        return "neobot_admin"
    return "client"

def get_system_prompt(mode: str, business_name: str = None) -> str:
    """Retourne le prompt système adapté au mode"""
    prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["client"])
    
    # Personnalisation légère pour le mode client
    if mode == "client" and business_name:
        prompt = prompt.replace("d'une entreprise", f"de {business_name}")
    
    return prompt

def get_fallback_template(mode: str, intent: str, business_name: str = None) -> str:
    """Retourne un template de fallback formaté"""
    templates = FALLBACK_TEMPLATES.get(mode, FALLBACK_TEMPLATES["client"])
    
    # Sélection d'intention intelligente
    if intent not in templates:
        # Mapping d'intentions alternatives
        intent_mapping = {
            "menu": "what_do_you_do",
            "hours": "what_do_you_do", 
            "reservation": "order",
            "delivery": "what_do_you_do",
            "prices": "pricing",
            "catalog": "what_do_you_do",
            "stock": "what_do_you_do"
        }
        intent = intent_mapping.get(intent, "default")
    
    template = templates.get(intent, templates["default"])
    
    # Remplacement de placeholder simple
    if business_name and "[business_name]" in template:
        template = template.replace("[business_name]", business_name)
    
    return template

# Alias pour compatibilité
get_template = get_fallback_template


# =====================================================
# 🔥 SYSTÈME DE CONTEXT FORCING
# =====================================================

def build_forced_messages(mode: str, message: str, business_name: str = None) -> list:
    """Construit des messages qui forcent l'IA à suivre le contexte"""
    
    if mode == "neobot_admin":
        system = f"""Tu es NÉOBOT ADMIN. Réponds SURTOUT sur WhatsApp automation.
Message à répondre: "{message}"
Ta réponse DOIT:
1. Parler d'automatisation WhatsApp
2. Mentionner l'essai gratuit
3. Être courte (3-4 lignes)
4. Proposer une action (test, démo, essai)
NE PARLE PAS d'autres services."""
    else:
        system = f"""Tu es le chatbot de {business_name or "l'entreprise"}. 
Réponds UNIQUEMENT sur les produits/services.
Message: "{message}"
Réponse courte et utile. Ne parle pas d'automatisation."""
    
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": message}
    ]
