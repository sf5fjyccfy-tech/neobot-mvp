class RocketBrain:
    def __init__(self):
        self.fallback_responses = {
            "greeting": "👋 Bonjour ! Je suis NéoBot, votre assistant WhatsApp. Envoyez '1' pour la présentation ou '2' pour les tarifs.",
            "pricing": "💰 Nos tarifs :\n- Basique : 20k FCFA/mois\n- Standard : 50k FCFA/mois\n- Pro : 90k FCFA/mois\n\nEnvoyez 'demo' pour une démo.",
            "demo": "🎥 Voici comment NéoBot fonctionne :\n1. Vous recevez un message WhatsApp\n2. NéoBot répond automatiquement\n3. Vous gagnez du temps !\n\nPrêt à essayer ? Envoyez 'oui' !",
            "default": "🤖 NéoBot - Automatisation WhatsApp\n\nEnvoyez '1' pour la présentation, '2' pour les tarifs, ou 'demo' pour une démonstration."
        }

    def detect_category(self, message: str) -> str:
        message_lower = message.lower().strip()
        if any(word in message_lower for word in ["bonjour", "salut", "hello", "coucou"]):
            return "greeting"
        elif any(word in message_lower for word in ["prix", "tarif", "combien", "coût", "coûte"]):
            return "pricing"
        elif any(word in message_lower for word in ["demo", "démo", "montre", "exemple"]):
            return "demo"
        else:
            return "default"

    def get_response(self, message: str) -> str:
        category = self.detect_category(message)
        return self.fallback_responses.get(category, self.fallback_responses["default"])
