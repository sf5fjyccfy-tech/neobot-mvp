"""
Service de Correction Orthographique Africaine
Corrige les fautes courantes du marché camerounais
"""
import re
from typing import Dict, List, Tuple
from difflib import SequenceMatcher

class CorrecteurAfricain:
    def __init__(self):
        # Dictionnaire de fautes courantes spécifiques au Cameroun
        self.corrections_base = {
            # Plats camerounais
            "ndole": "ndolé", "ndolee": "ndolé", "nddolé": "ndolé", "ndolè": "ndolé",
            "poulet dg": "poulet DG", "pouletdg": "poulet DG", "poulet d.g": "poulet DG",
            "eru": "eru", "erou": "eru", "iro": "eru",
            "okok": "okok", "okook": "okok", "okok feuille": "okok",
            "bobolo": "bobolo", "bobolot": "bobolo", "boboloo": "bobolo",
            "kokki": "kokki", "koki": "koki", "koki haricot": "koki",
            
            # Fruits/Légumes
            "plantain": "plantain", "plantin": "plantain", "plantains": "plantain",
            "macabo": "macabo", "makabo": "macabo", "macabos": "macabo",
            "igname": "igname", "yame": "igname", "gnam": "igname",
            
            # Viandes/Poissons
            "poisson braise": "poisson braisé", "poisson braize": "poisson braisé",
            "poulet braise": "poulet braisé", "poulet braize": "poulet braisé",
            "porc braise": "porc braisé", "porc braize": "porc braisé",
            "soya": "soya", "soya poulet": "soya", "soya boeuf": "soya",
            
            # Boissons
            "jus nature": "jus naturel", "jus naturel": "jus naturel",
            "bierre": "bière", "biere": "bière", "beer": "bière",
            "cafe": "café", "caffé": "café", "coffee": "café"
        }
        
        # Fautes de frappe courantes
        self.fautes_frappe = {
            "combien": "combien", "konbien": "combien", "combi1": "combien", "combiem": "combien",
            "prix": "prix", "pri": "prix", "prixx": "prix", "pris": "prix", "pric": "prix",
            "taille": "taille", "tay": "taille", "tayle": "taille", "tail": "taille",
            "couleur": "couleur", "kouleur": "couleur", "coleur": "couleur", "coulor": "couleur",
            "disponible": "disponible", "dispo": "disponible", "disponible": "disponible",
            "livraison": "livraison", "livrezon": "livraison", "livraizon": "livraison",
            "commande": "commande", "kommande": "commande", "comande": "commande",
            
            # Mots courts fréquents
            "stp": "s'il te plaît", "svp": "s'il vous plaît",
            "c": "c'est", "j": "je", "t": "tu", "m": "me", "s": "ce",
            "ds": "dans", "pk": "pourquoi", "pq": "pourquoi",
            "pt": "petit", "g": "grand", "moy": "moyen"
        }
        
        # Termes e-commerce
        self.termes_ecommerce = {
            "tshirt": "t-shirt", "t shirt": "t-shirt", "tshirtt": "t-shirt",
            "chemise": "chemise", "chemiz": "chemise", "chemisse": "chemise",
            "robe": "robe", "rob": "robe", "robes": "robe",
            "chaussure": "chaussure", "chausure": "chaussure", "chaussures": "chaussure",
            "sac": "sac", "sacc": "sac", "sacs": "sac",
            "bijou": "bijou", "bijoux": "bijou", "bijouu": "bijou",
            "electronique": "électronique", "electronik": "électronique"
        }
        
        # Combinaison de tous les dictionnaires
        self.tous_corrections = {**self.corrections_base, **self.fautes_frappe, **self.termes_ecommerce}
        
        # Patterns regex pour détection contextuelle
        self.patterns_contextuels = {
            r"\b(ndol|nddl|ndole)\b": "ndolé",
            r"\b(poulet\s*[dg\.])\b": "poulet DG",
            r"\b(plantin|plantains)\b": "plantain",
            r"\b(tshirt|t\s*shirt)\b": "t-shirt",
            r"\b(chausure|chaussures)\b": "chaussure"
        }

    def similarite(self, mot1: str, mot2: str) -> float:
        """Calcule la similarité entre deux mots (0.0 à 1.0)"""
        return SequenceMatcher(None, mot1.lower(), mot2.lower()).ratio()

    def trouver_correction_approximative(self, mot: str, seuil: float = 0.7) -> str:
        """Trouve la correction la plus proche dans le dictionnaire"""
        mot_lower = mot.lower()
        
        # Recherche exacte d'abord
        if mot_lower in self.tous_corrections:
            return self.tous_corrections[mot_lower]
        
        # Recherche approximative
        meilleur_score = 0.0
        meilleure_correction = mot
        
        for correct, correction in self.tous_corrections.items():
            score = self.similarite(mot_lower, correct)
            if score > meilleur_score and score >= seuil:
                meilleur_score = score
                meilleure_correction = correction
        
        return meilleure_correction if meilleur_score >= seuil else mot

    def corriger_avec_contexte(self, phrase: str) -> str:
        """Correction intelligente avec prise en compte du contexte"""
        # Application des patterns contextuels
        for pattern, correction in self.patterns_contextuels.items():
            phrase = re.sub(pattern, correction, phrase, flags=re.IGNORECASE)
        
        # Correction mot par mot
        mots = phrase.split()
        mots_corriges = []
        
        for mot in mots:
            # Garder la ponctuation
            ponctuation = ""
            if not mot[-1].isalnum():
                ponctuation = mot[-1]
                mot = mot[:-1]
            
            if mot:  # Éviter les mots vides
                mot_corrige = self.trouver_correction_approximative(mot)
                mots_corriges.append(mot_corrige + ponctuation)
            else:
                mots_corriges.append(ponctuation)
        
        return " ".join(mots_corriges)

    def analyser_et_corriger(self, message: str) -> Dict:
        """Analyse complète et correction avec métriques"""
        original = message
        corrige = self.corriger_avec_contexte(message)
        
        # Calcul des métriques
        mots_originaux = original.split()
        mots_corriges = corrige.split()
        corrections_appliquees = sum(1 for o, c in zip(mots_originaux, mots_corriges) if o != c)
        
        return {
            "original": original,
            "corrige": corrige,
            "a_ete_corrige": original != corrige,
            "nombre_corrections": corrections_appliquees,
            "taux_correction": corrections_appliquees / max(len(mots_originaux), 1)
        }

    def detecter_intention_achat(self, message_corrige: str) -> List[str]:
        """Détecte les intentions d'achat après correction"""
        intentions = []
        message_lower = message_corrige.lower()
        
        # Détection basée sur le message corrigé
        if any(mot in message_lower for mot in ["combien", "prix", "coûte", "tarif"]):
            intentions.append("demande_prix")
        
        if any(mot in message_lower for mot in ["taille", "couleur", "modèle", "disponible"]):
            intentions.append("specification_produit")
        
        if any(mot in message_lower for mot in ["commander", "acheter", "prendre", "je veux"]):
            intentions.append("intention_achat")
        
        if any(mot in message_lower for mot in ["livraison", "livrer", "domicile"]):
            intentions.append("demande_livraison")
        
        # Détection produits spécifiques
        produits_detectes = []
        for produit in ["ndolé", "poulet DG", "t-shirt", "robe", "chaussure", "sac"]:
            if produit.lower() in message_lower:
                produits_detectes.append(produit)
        
        if produits_detectes:
            intentions.append(f"produit_specifique:{','.join(produits_detectes)}")
        
        return intentions

# Instance globale pour performance
correcteur_global = CorrecteurAfricain()
