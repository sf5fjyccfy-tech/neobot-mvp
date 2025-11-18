def build_chat_messages(tenant, customer_message: str, conversation_history: list = None):
    """Construit les messages pour l'API IA"""
    
    system_prompt = f"""Tu es l'assistant virtuel de {tenant.name}, {tenant.business_type} au Cameroun.

CONTEXTE:
- Nom: {tenant.name}
- Type: {tenant.business_type}
- Ton: Courtois, chaleureux, professionnel
- Langue: Français (Cameroun)

RÈGLES:
- Réponses courtes (max 3 phrases)
- Prix en FCFA
- Horaires: 11h-22h (si restaurant)
- Propose toujours d'aider davantage

MENU TYPIQUE (si restaurant):
- Ndolé: 2500 FCFA
- Poulet DG: 3500 FCFA
- Eru: 2800 FCFA
- Poisson braisé: 3000 FCFA
"""
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Ajouter historique
    if conversation_history:
        for msg in conversation_history[-5:]:
            role = "assistant" if msg.is_ai else "user"
            messages.append({"role": role, "content": msg.content})
    
    # Ajouter message actuel
    messages.append({"role": "user", "content": customer_message})
    
    return messages
