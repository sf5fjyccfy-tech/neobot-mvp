"""
RÉPONDRE ROCKET - Zéro dépendance DB
"""
import random
from datetime import datetime

class RocketResponder:
    """Répond TOUJOURS, même si tout est cassé"""
    
    RESPONSES = {
        "salutation": [
            "👋 **Salut !** Je suis NéoBot, l'IA qui automatise ton WhatsApp.\n\n🚀 Gain garanti: 2-3h/jour. Essai gratuit 14 jours !",
            "🤖 **Bonjour !** NéoBot ici. Je réponds à tes clients 24h/24.\n\n💰 À partir de 20k FCFA/mois. Démo ?",
            "✨ **Hey !** Assistant NéoBot. Je transforme WhatsApp en machine à ventes.\n\n🎁 Essai gratuit. Tu veux voir ?"
        ],
        "interet": [
            "✅ **Parfait !** 🎉\n\nPour te montrer NéoBot:\n\n1. **Ton secteur?** (restaurant/boutique/service)\n2. **Messages/jour?**\n\nJe m'adapte à 100% !",
            "🎯 **Super !** On personnalise:\n\n1. Quel business?\n2. Volume messages?\n\nJe te montre une démo sur-mesure.",
            "🚀 **Excellent !** Personnalisons:\n\n1. Secteur d'activité?\n2. Clients sur WhatsApp?\n\nDémo immédiate !"
        ],
        "secteur_boutique": [
            "🛍️ **BOUTIQUE DÉTECTÉE !** Parfait pour NéoBot:\n\n• Catalogue auto\n• Stocks en temps réel\n• Commandes WhatsApp\n• Livraison gérée\n\n**Prochaine étape:**\n1. Temps passé à répondre?\n2. Ventes perdues par jour?",
            "📦 **Boutique repérée !** NéoBot excelle ici:\n\n• Réponses produits 24/7\n• Prix automatiques\n• Gestion commandes\n• Fidélisation clients\n\n**Questions clés:**\n1. Heures/jour sur WhatsApp?\n2. Clients perdus par lenteur?",
            "👗 **Secteur boutique !** NéoBot optimise:\n\n• Vente assistée IA\n• Notification stocks\n• Paiements intégrés\n• Analytics ventes\n\n**Analyse besoins:**\n1. Temps de réponse actuel?\n2. Taux de conversion?"
        ],
        "analyse_besoins": [
            "⚠️  **JE COMPRENDS !** Perte de temps = perte d'argent.\n\n🎯 **SOLUTION NÉOBOT:**\n1. Réponses instantanées → +30% ventes\n2. Gain 2-3h/jour → focus business\n3. Service 24/7 → clients fidèles\n\n💰 **ESSAI GRATUIT 14 JOURS**\nTu veux activer ?",
            "💸 **PROBLÈME IDENTIFIÉ !** Temps = Argent perdu.\n\n🚀 **RÉSOLUTION:**\n• Réponses auto → +35% conversions\n• 2-3h économisées → productivité\n• 24/7 → zéro client perdu\n\n🎁 **ESSAI 14 JOURS GRATUIT**\nOn commence ?",
            "📉 **DIAGNOSTIC:** Inefficacité coûteuse.\n\n⚡ **REMÈDE NÉOBOT:**\n→ Réponses IA: +40% ventes\n→ Temps gagné: 15h/semaine\n→ Service permanent\n\n✅ **ESSAI GRATUIT IMMÉDIAT**\nTu es partant ?"
        ],
        "tarifs": [
            "💰 **PLAN ESSENTIAL — NéoBot :**\n\n🏷️ Essential : 20 000 FCFA/mois\n  ✅ 2 500 messages WhatsApp/mois\n  ✅ 1 agent IA actif\n  ✅ Sources Texte + PDF\n  ✅ Dashboard Analytics 30 jours\n  ✅ Rappels RDV automatiques\n\n🎁 **ESSAI 14 JOURS GRATUIT** — Aucune carte requise\nD'autres formules arrivent bientôt.\n\nActivation maintenant ?",
            "📊 **TARIF NÉOBOT :**\n\n🏷️ **Essential** (20 000 FCFA/mois)\n  → 2 500 messages WhatsApp\n  → 1 agent IA (Vente, RDV, Support, FAQ…)\n  → Sources Texte + PDF\n  → Dashboard 30 jours\n\n⭐ **AVANTAGE:** 14 jours d'essai gratuit\nD'autres formules bientôt disponibles.\n\n🔓 **DÉMARRER L'ESSAI ?**",
            "💳 **INVESTISSEMENT ESSENTIEL :**\n\n🏷️ Essential (20 000 FCFA/mois)\n  • 2 500 messages/mois\n  • 1 agent IA\n  • Texte + PDF\n  • Analytics\n\n✨ **GARANTIE:** Essai 14 jours gratuit\n⏱️ **DÉCISION:** 2 min pour activer\nD'autres plans arrivent bientôt.\n\n🚪 **ON DÉMARRE ?"
        ],
        "default": [
            "🚀 **NÉOBOT** - Automatisation WhatsApp\n\nJe réponds 24/7, je vends pour toi, j'analyse tout.\n\n🎁 Essai gratuit 14 jours\n💬 Envie de voir une démo ?",
            "🤖 **ASSISTANT NÉOBOT**\n\n• Réponses IA instantanées\n• Gestion commandes auto\n• Analytics performances\n• À partir de 20k/mois\n\n✅ Essai gratuit. On teste ?",
            "⚡ **SOLUTION WHATSAPP**\n\nAutomatise, convertis, fidélise.\nGain garanti: 2-3h/jour + 30% ventes.\n\n🎯 Essai 14 jours. Départ ?"
        ]
    }
    
    @staticmethod
    def respond(message: str) -> str:
        """Réponse garantie - Zéro DB, zéro exception"""
        if not message:
            message = ""
        
        msg_lower = message.lower().strip()
        
        # Détection infaillible
        if any(w in msg_lower for w in ["salut", "bonjour", "hello", "bonsoir"]):
            category = "salutation"
        elif any(w in msg_lower for w in ["oui", "ok", "d'accord", "vas-y", "intéressé"]):
            category = "interet"
        elif any(w in msg_lower for w in ["boutique", "magasin", "shop", "vêtement"]):
            category = "secteur_boutique"
        elif any(w in msg_lower for w in ["heure", "temps", "3h", "4h", "5h", "perd", "rate"]):
            category = "analyse_besoins"
        elif any(w in msg_lower for w in ["prix", "tarif", "combien", "coûte", "abonnement"]):
            category = "tarifs"
        else:
            category = "default"
        
        # Réponse aléatoire dans la catégorie
        responses = RocketResponder.RESPONSES.get(category, RocketResponder.RESPONSES["default"])
        return random.choice(responses)

# Instance globale
rocket = RocketResponder()
