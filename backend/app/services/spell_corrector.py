"""
Service de correction orthographique étendu
"""
class SpellCorrector:
    def __init__(self):
        self.corrections = {
            # Sacs
            'sak': 'sac', 'sack': 'sac', 'sacq': 'sac', 'sacs': 'sac',
            'sacmain': 'sac main', 'sacados': 'sac à dos',
            
            # Couleurs
            'rooge': 'rouge', 'rouje': 'rouge', 'roug': 'rouge', 'rouges': 'rouge',
            'blancs': 'blanc', 'blance': 'blanc', 'blans': 'blanc',
            'noirs': 'noir', 'noire': 'noir', 'noirs': 'noir',
            'verts': 'vert', 'vertes': 'vert', 'ver': 'vert',
            'bleus': 'bleu', 'bleue': 'bleu', 'bleus': 'bleu',
            'jaunes': 'jaune', 'jaune': 'jaune',
            'roses': 'rose', 'rose': 'rose',
            'violets': 'violet', 'violette': 'violet',
            
            # Tailles
            'tail': 'taille', 'taiye': 'taille', 'taye': 'taille', 'tailles': 'taille',
            'petit': 'S', 'petite': 'S', 'petits': 'S',
            'moyen': 'M', 'moyenne': 'M', 'moyens': 'M', 
            'grand': 'L', 'grande': 'L', 'grands': 'L',
            'tresgrand': 'XL', 'trèsgrand': 'XL',
            
            # Vêtements
            'chemize': 'chemise', 'chemizes': 'chemise', 'chemises': 'chemise',
            'chaussuree': 'chaussures', 'chaussure': 'chaussures', 'chausure': 'chaussures',
            'robes': 'robe', 'rob': 'robe',
            'jup': 'jupe', 'jupes': 'jupe', 'jupe': 'jupe',
            'pantalon': 'pantalon', 'pantalons': 'pantalon', 'pantalong': 'pantalon',
            'pullover': 'pull', 'pulls': 'pull', 'polos': 'polo',
            'tshirt': 't-shirt', 'tee': 't-shirt', 't-shirts': 't-shirt',
            'veste': 'veste', 'vestes': 'veste',
            
            # Accessoires
            'bijoux': 'bijou', 'bijou': 'bijou',
            'montre': 'montre', 'montres': 'montre',
            'lunetes': 'lunettes', 'lunete': 'lunettes',
            'ceinture': 'ceinture', 'ceintures': 'ceinture',
            
            # Marques courantes
            'nike': 'nike', 'adidas': 'adidas', 'puma': 'puma',
            'zara': 'zara', 'h&m': 'h&m', 'hm': 'h&m',
            
            # Termes génériques
            'habits': 'vêtements', 'vetements': 'vêtements', 'fringues': 'vêtements',
            'baskets': 'baskets', 'basket': 'baskets',
            'escarpins': 'escarpins', 'escarpin': 'escarpins',
            'sandales': 'sandales', 'sandale': 'sandales',
            
            # Actions
            'acheter': 'acheter', 'achete': 'acheter', 'acheté': 'acheter',
            'commander': 'commander', 'commande': 'commander',
            'payer': 'payer', 'paie': 'payer', 'payé': 'payer',
            'livrer': 'livraison', 'livré': 'livraison',
            
            # Questions
            'disponible': 'disponible', 'disponibles': 'disponible', 'dispo': 'disponible',
            'prix': 'prix', 'combien': 'prix', 'coute': 'coûte', 'coutent': 'coûtent',
            'stock': 'stock', 'stocks': 'stock'
        }
    
    def correct_message(self, message: str) -> str:
        """Corrige les fautes courantes dans les messages"""
        words = message.lower().split()
        corrected = [self.corrections.get(word, word) for word in words]
        return ' '.join(corrected)
