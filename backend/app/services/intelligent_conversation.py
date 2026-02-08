"""
SPIN SELLING GARANTI - Retourne TOUJOURS une réponse valide
"""
from datetime import datetime

def get_conversation_response(message: str, db=None, tenant_id=None, phone=None) -> str:
    """
    IMPÉRATIF : Retourne TOUJOURS une string non-vide
    """
    # Sauvegarde originale pour debugging
    original_message = message
    
    try:
        message_lower = message.lower().strip()
        
        # ========== RÉPONSES GARANTIES ==========
        responses = {
            # ÉTAPE 0: SALUTATION
            "salutation": "👋 **Salut !** Je suis NéoBot, l'assistant IA qui automatise WhatsApp.\n\n"
                         "🚀 Je fais gagner **2-3h/jour** aux entreprises en répondant 24/7 aux clients.\n\n"
                         "Tu veux voir **comment ça marche** ?",
            
            # ÉTAPE 1: INTÉRÊT
            "interet": "✅ **Parfait !** 🎉\n\n"
                      "Pour personnaliser NéoBot pour toi :\n\n"
                      "1. **Quel est ton secteur d'activité ?**\n"
                      "   (restaurant, boutique, service, autre)\n\n"
                      "2. **Combien de messages WhatsApp reçois-tu par jour ?**\n\n"
                      "Avec ça, je te montre **exactement** ce que NéoBot peut faire pour toi !",
            
            # ÉTAPE 2: SECTEUR
            "secteur_boutique": "🎯 **EXCELLENT !** Secteur **Boutique** détecté.\n\n"
                               "Pour ta boutique, NéoBot peut :\n"
                               "• Gérer ton catalogue produits\n"
                               "• Répondre aux questions sur les stocks\n"
                               "• Prendre des commandes via WhatsApp\n"
                               "• Gérer les livraisons\n\n"
                               "**Prochaines questions :**\n"
                               "1. Actuellement, **combien de temps passes-tu** à répondre à tes clients ?\n"
                               "2. **Combien de ventes** tu rates par manque de réponse rapide ?",
            
            # ÉTAPE 3: ANALYSE BESOINS
            "analyse_besoins": "⚠️  **JE COMPRENDS !** Tu perds du temps et des ventes...\n\n"
                              "🎯 **VOICI COMMENT NÉOBOT RÉSOUT ÇA :**\n\n"
                              "1. **Réponses instantanées** 24h/24 → Plus de ventes perdues\n"
                              "2. **Gain de 2-3h/jour** → Tu te concentres sur ta boutique\n"
                              "3. **+30% de conversions** → Messages optimisés pour vendre\n\n"
                              "**Ça te dit d'essayer gratuitement pendant 14 jours ?**",
            
            # ÉTAPE 4: TARIFS
            "tarifs": "💰 **INVESTISSEMENT NÉOBOT** (pour Boutique) :\n\n"
                     "🏷️  **BASIQUE** - 20k FCFA/mois\n"
                     "   → 2000 messages WhatsApp\n"
                     "   → Réponses automatiques\n"
                     "   → Dashboard de base\n\n"
                     "🏷️  **STANDARD** - 50k FCFA/mois\n"
                     "   → Messages illimités\n"
                     "   → IA avancée\n"
                     "   → Analytics complets\n\n"
                     "🏷️  **PRO** - 90k FCFA/mois\n"
                     "   → API + intégrations\n"
                     "   → Support prioritaire\n\n"
                     "🎁 **ESSAI GRATUIT 14 JOURS** (aucune carte requise)\n\n"
                     "**Tu veux activer l'essai maintenant ?**",
            
            # RÉPONSE PAR DÉFAUT GARANTIE
            "default": "🚀 **NÉOBOT** - Automatisation WhatsApp intelligente\n\n"
                      "Je peux automatiser tes conversations, répondre 24h/24 à tes clients,\n"
                      "gérer les commandes et analyser tes performances.\n\n"
                      "**Essai gratuit 14 jours !**\n"
                      "Tu veux que je t'explique comment ça marche ?"
        }
        
        # ========== DÉTECTION INFAILLIBLE ==========
        
        # Salutations
        if any(word in message_lower for word in ["salut", "bonjour", "hello", "bonsoir", "coucou"]):
            return responses["salutation"]
        
        # Intérêt
        elif any(word in message_lower for word in ["oui", "d'accord", "ok", "vas-y", "intéressé", "montre"]):
            return responses["interet"]
        
        # Secteur boutique
        elif any(word in message_lower for word in ["boutique", "magasin", "shop", "vêtements", "produits"]):
            return responses["secteur_boutique"]
        
        # Analyse besoins (temps + pertes)
        elif any(word in message_lower for word in ["heure", "temps", "3h", "4h", "5h", "perd", "rate", "manque"]):
            return responses["analyse_besoins"]
        
        # Tarifs
        elif any(word in message_lower for word in ["prix", "tarif", "combien", "coûte", "abonnement", "payer"]):
            return responses["tarifs"]
        
        # Question "qui es-tu"
        elif any(word in message_lower for word in ["qui es", "présente", "explique", "c'est quoi"]):
            return responses["salutation"]  # Recycle la salutation
        
        # Sinon, réponse par défaut GARANTIE
        else:
            return responses["default"]
            
    except Exception as e:
        # FALLBACK ABSOLU - MÊME SI TOUT PLANTE
        print(f"⚠️  SPIN CRITICAL ERROR: {e}")
        return "🚀 **NÉOBOT** - Je suis ton assistant pour automatiser WhatsApp. Essai gratuit 14 jours !"
