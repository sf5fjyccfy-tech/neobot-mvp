"""
Amélioration des patterns de détection du Fallback
"""
import re

# Lire le fichier fallback_service.py
with open('app/services/fallback_service.py', 'r') as f:
    content = f.read()

# Améliorer les patterns pour mieux détecter les intentions
improved_patterns = {
    "restaurant": {
        "menu": [
            r".*(menu|plat|manger|nourriture|repas|cuisine|manger|boire).*",
            r".*(qu[']est.ce.que.vous.avez|qu[']est.ce.qu[’]il.y.a|vous.servez.quoi).*",
            r".*(proposer|servir|offrir|disponible).*",
            r".*(ndolé|poulet.dg|eru|poisson|riz|alloc|pâte).*"
        ],
        "horaires": [
            r".*(heure|horaire|ouvrir|fermer|ouvert|fermé|ouverture|fermeture).*",
            r".*(à.quelle.heure|quand.est.ce.que|vous.êtes.ouvert).*",
            r".*(jour|semaine|week.end|lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche).*",
            r".*(matin|midi|soir|nuit).*"
        ],
        "prix": [
            r".*(prix|tarif|combien.coûte|coute|coût|argent).*",
            r".*(cher|pas.cher|abordable|économique).*",
            r".*(frais|fcfà|franc).*",
            r".*(c.est.combien|quel.est.le.prix).*"
        ],
        "réservation": [
            r".*(réserver|réservation|table|place|commander).*",
            r".*(disponible|libre|occuper).*",
            r".*(ce.soir|demain|week.end|ce.après.midi).*",
            r".*(personne|invité|client).*"
        ],
        "adresse": [
            r".*(adresse|localisation|localisé|situé|où|endroit).*",
            r".*(quartier|ville|rue|avenue|boulevard|carrefour).*",
            r".*(trouver|venir|map|gps|localiser).*",
            r".*(bonapriso|akwa|deïdo|centre.ville).*"
        ],
        "livraison": [
            r".*(livraison|livrer|domicile|maison|apporter|porter).*",
            r".*(délai|temps.livraison|moment).*",
            r".*(zone|quartier.livraison|ville).*",
            r".*(frais.livraison|coût.livraison|gratuit|payant).*"
        ]
    },
    "boutique": {
        "catalogue": [
            r".*(produit|article|item|choix|sélection|modèle).*",
            r".*(catalogue|collection|gamme|assortiment).*",
            r".*(qu.est.ce.que.vous.avez|qu.est.ce.qu.il.y.a|vous.vendez.quoi).*",
            r".*(robe|chaussure|sac|vêtement|habit|accessoire).*"
        ],
        "prix": [
            r".*(prix|tarif|combien.coûte|coute|coût|argent).*",
            r".*(cher|pas.cher|abordable|économique).*",
            r".*(frais|fcfà|franc).*",
            r".*(c.est.combien|quel.est.le.prix).*"
        ],
        "stock": [
            r".*(disponible|stock|en.stock|disponibilité).*",
            r".*(avoir|dispo|présent).*",
            r".*(taille|couleur|modèle|pointure).*",
            r".*(petit|medium|grand|xl|xxl|s|m|l).*"
        ],
        "livraison": [
            r".*(livraison|livrer|expédition|envoyer).*",
            r".*(délai|temps.livraison|moment).*",
            r".*(frais.livraison|coût.livraison|gratuit|payant).*",
            r".*(domicile|maison|bureau).*"
        ],
        "paiement": [
            r".*(paiement|payer|règlement|régler).*",
            r".*(orange.money|mtn.money|mobile.money|mom).*",
            r".*(carte|espèces|cash|chèque).*",
            r".*(moyen.paiement|comment.payer).*"
        ]
    }
}

# Remplacer les anciens patterns par les nouveaux améliorés
old_patterns_start = 'self.intent_patterns = {'
old_patterns_end = '}'

# Extraire la partie à remplacer
pattern_section = re.search(r'self\.intent_patterns = \{.*?\n\}', content, re.DOTALL)
if pattern_section:
    # Convertir le nouveau dictionnaire en string
    new_patterns_str = 'self.intent_patterns = ' + str(improved_patterns)
    
    # Remplacer
    content = content.replace(pattern_section.group(0), new_patterns_str)
    print("✅ Patterns de détection améliorés !")
else:
    print("❌ Impossible de trouver les patterns à remplacer")

# Écrire le fichier amélioré
with open('app/services/fallback_service.py', 'w') as f:
    f.write(content)

print("✅ Fallback Service amélioré avec meilleure détection")
