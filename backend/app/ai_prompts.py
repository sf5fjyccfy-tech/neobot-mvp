def get_system_prompt(business_name: str, business_type: str, custom_context: str = "") -> str:
    base = f"Tu es l'assistant WhatsApp de {business_name}. Réponds en français camerounais, max 3 phrases."
    
    prompts = {
        "restaurant": f"{base}\nTu connais le menu, les prix, tu prends des commandes. Menu: Ndolé 2500F, Poulet DG 3500F, Eru 2800F.",
        "boutique": f"{base}\nTu vérifies le stock, donnes les prix, prends les commandes.",
        "service": f"{base}\nTu proposes des rendez-vous, expliques les prestations.",
        "autre": f"{base}\nTu fournis des infos générales."
    }
    return prompts.get(business_type.lower(), prompts["autre"])

def get_examples_by_sector(business_type: str) -> list:
    return []

def build_chat_messages(tenant, customer_message: str, conversation_history: list = None) -> list:
    messages = [{"role": "system", "content": get_system_prompt(tenant.name, tenant.business_type or "autre")}]
    
    if conversation_history:
        for msg in conversation_history[-5:]:
            role = "user" if msg.direction == "incoming" else "assistant"
            messages.append({"role": role, "content": msg.content})
    
    messages.append({"role": "user", "content": customer_message})
    return messages
