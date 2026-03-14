"""
Configuration du Plan BASIQUE
Seul le plan BASIQUE est actif actuellement
Les autres plans seront ajoutés plus tard
"""

# ========== PLAN BASIQUE (SEUL ACTIF) ==========

BASIC_PLAN = {
    "name": "Basique",
    "slug": "basique",
    "price": 20000,
    "currency": "FCFA",
    "billing_period": "mensuel",
    "messages_limit": 2000,
    "description": "Plan BASIQUE pour les petites entreprises",
    
    "features": [
        "2,000 messages/mois",
        "Support par email",
        "Analytics basiques",
        "Intégration WhatsApp Business",
        "Profil entreprise personnalisé",
        "Essai gratuit 7 jours",
        "Tableau de bord simple"
    ],
    
    "benefits": [
        "Parfait pour débuter",
        "Accès complet aux tous les outils",
        "Support réactif",
        "Pas de contrat long terme",
        "Facile à upgrade vers plan supérieur"
    ],
    
    "cta": "Commencer l'essai gratuit",
    "trial_days": 7,
    "trial_message": "Essayez NéoBot gratuitement pendant 7 jours - Aucune carte de crédit requise!",
    
    "is_active": True,  # ACTIF
    "is_default": True,  # Plan par défaut
    
    "pricing_message": (
        "Notre plan BASIQUE coûte **20,000 FCFA par mois** et vous permet:\n"
        "✅ 2,000 messages inclus chaque mois\n"
        "✅ Support par email\n"
        "✅ Analytics et statistiques basiques\n"
        "✅ Intégration WhatsApp Business\n"
        "✅ Profil entreprise avec vos données\n\n"
        "🎯 **Essai gratuit 7 jours - Aucune carte requise!**"
    )
}

# Configuration active (SEULEMENT BASIQUE)
ACTIVE_PLANS = {
    "basique": BASIC_PLAN
}

# Plan par défaut
DEFAULT_PLAN = BASIC_PLAN

# Message si on essaie d'accéder à un plan inexistant
PLAN_UNAVAILABLE_MESSAGE = (
    "Les autres plans seront disponibles très bientôt! 🚀\n\n"
    f"Pour le moment, nous proposons uniquement le plan **BASIQUE**:\n\n"
    f"✅ **20,000 FCFA/mois**\n"
    f"✅ 2,000 messages inclus\n"
    f"✅ Support par email\n"
    f"✅ Analytics basiques\n"
    f"✅ Intégration WhatsApp Business\n\n"
    f"👉 Essai gratuit 7 jours - Aucune carte requise!"
)


def get_plan(plan_slug: str = "basique") -> dict:
    """Récupère un plan par slug"""
    if plan_slug in ACTIVE_PLANS:
        return ACTIVE_PLANS[plan_slug]
    else:
        return DEFAULT_PLAN


def get_all_active_plans() -> dict:
    """Retourne tous les plans actifs"""
    return ACTIVE_PLANS


def is_plan_active(plan_slug: str) -> bool:
    """Vérifie si un plan est actif"""
    return plan_slug in ACTIVE_PLANS


def get_plan_features_formatted(plan_slug: str = "basique") -> str:
    """Retourne les features formatées du plan"""
    plan = get_plan(plan_slug)
    
    features_str = f"**{plan['name']} - {plan['price']:,} {plan['currency']}/mois**\n\n"
    features_str += "**Inclus:**\n"
    for feature in plan['features']:
        features_str += f"✅ {feature}\n"
    
    return features_str


def get_plan_pricing_message(plan_slug: str = "basique") -> str:
    """Retourne le message de tarification du plan"""
    plan = get_plan(plan_slug)
    return plan.get('pricing_message', '')


def get_trial_message(plan_slug: str = "basique") -> str:
    """Retourne le message d'essai gratuit"""
    plan = get_plan(plan_slug)
    return plan.get('trial_message', '')


# Constantes utiles
BASIC_PLAN_PRICE = 20000
BASIC_PLAN_MESSAGES = 2000
BASIC_PLAN_NAME = "Basique"
BASIC_PLAN_TRIAL_DAYS = 7
