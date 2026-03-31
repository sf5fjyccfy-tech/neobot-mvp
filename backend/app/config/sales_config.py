"""
Configuration du Plan Essential — NéoBot
Seul plan disponible actuellement (Business et Enterprise : bientôt)
"""

# ========== PLAN ESSENTIAL (SEUL ACTIF) ==========

BASIC_PLAN = {
    "name": "Essential",
    "slug": "essential",
    "price": 20000,
    "currency": "FCFA",
    "billing_period": "mensuel",
    "messages_limit": 2500,
    "description": "Plan Essential — automatisation WhatsApp pour PME africaines",

    "features": [
        "2 500 messages WhatsApp/mois",
        "1 agent IA actif",
        "Types d'agents : Libre, RDV, Support, FAQ, Vente, Qualification",
        "Sources de connaissance : Texte + PDF (3 max)",
        "Génération de prompt par IA",
        "Délai de réponse configurable",
        "Rappels RDV automatiques",
        "Dashboard Analytics 30 jours",
        "20 crédits de test bot par session",
        "Support par email",
        "Essai gratuit 14 jours",
    ],

    "benefits": [
        "Répond à vos clients 24h/24, 7j/7",
        "Économise 2 à 3 heures par jour",
        "Pas de carte bancaire requise pour l'essai",
        "Déploiement en moins de 10 minutes",
        "Aucun engagement — résiliable à tout moment",
    ],

    "cta": "Commencer l'essai gratuit 14 jours",
    "trial_days": 14,
    "trial_message": "Essayez NéoBot gratuitement pendant 14 jours — Aucune carte bancaire requise !",

    "is_active": True,
    "is_default": True,

    "pricing_message": (
        "Notre plan **Essential** coûte **20 000 FCFA/mois** et comprend :\n"
        "✅ 2 500 messages WhatsApp inclus chaque mois\n"
        "✅ 1 agent IA actif (Vente, RDV, Support, FAQ…)\n"
        "✅ Sources de connaissance : Texte + PDF (3 max)\n"
        "✅ Génération de prompt par IA\n"
        "✅ Dashboard Analytics 30 jours\n"
        "✅ Rappels RDV automatiques\n"
        "✅ Support par email\n\n"
        "🎯 **Essai gratuit 14 jours — Aucune carte bancaire requise !**"
    )
}

# Configuration active
ACTIVE_PLANS = {
    "essential": BASIC_PLAN
}

DEFAULT_PLAN = BASIC_PLAN

PLAN_UNAVAILABLE_MESSAGE = (
    "D'autres formules arrivent bientôt ! 🚀\n\n"
    "Pour l'instant, notre plan **Essential** à 20 000 FCFA/mois couvre tous les besoins :\n\n"
    "✅ 2 500 messages WhatsApp/mois\n"
    "✅ 1 agent IA actif\n"
    "✅ Sources Texte + PDF\n"
    "✅ Dashboard Analytics 30 jours\n"
    "✅ Essai gratuit 14 jours — aucune carte requise !"
)


def get_plan(plan_slug: str = "essential") -> dict:
    """Récupère un plan par slug"""
    return ACTIVE_PLANS.get(plan_slug, DEFAULT_PLAN)


def get_all_active_plans() -> dict:
    """Retourne tous les plans actifs"""
    return ACTIVE_PLANS


def is_plan_active(plan_slug: str) -> bool:
    """Vérifie si un plan est actif"""
    return plan_slug in ACTIVE_PLANS


def get_plan_features_formatted(plan_slug: str = "essential") -> str:
    """Retourne les features formatées du plan"""
    plan = get_plan(plan_slug)
    
    features_str = f"**{plan['name']} - {plan['price']:,} {plan['currency']}/mois**\n\n"
    features_str += "**Inclus:**\n"
    for feature in plan['features']:
        features_str += f"✅ {feature}\n"
    
    return features_str


def get_plan_pricing_message(plan_slug: str = "essential") -> str:
    """Retourne le message de tarification du plan"""
    plan = get_plan(plan_slug)
    return plan.get('pricing_message', '')


def get_trial_message(plan_slug: str = "essential") -> str:
    """Retourne le message d'essai gratuit"""
    plan = get_plan(plan_slug)
    return plan.get('trial_message', '')


# Constantes utiles
BASIC_PLAN_PRICE = 20000
BASIC_PLAN_MESSAGES = 2500
BASIC_PLAN_NAME = "Essential"
BASIC_PLAN_TRIAL_DAYS = 14
