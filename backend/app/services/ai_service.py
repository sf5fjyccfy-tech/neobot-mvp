import os
import httpx

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-3e69ef3cc448412ca65629406152abd0")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

async def generate_ai_response(message: str, business_type: str, business_name: str, conversation_history: list = None) -> str:
    system_prompts = {
        "restaurant": f"Tu es l'assistant de {business_name}, un restaurant. Réponds en français, courtois, concis (2-3 phrases). Tu connais les plats camerounais (ndolé, poulet DG, eru). Prix: 2000-5000 FCFA. Horaires: 11h-22h.",
        "boutique": f"Tu es l'assistant de {business_name}, une boutique. Réponds en français, pro, concis (2-3 phrases). Tu informes sur produits, prix, horaires.",
        "service": f"Tu es l'assistant de {business_name}. Réponds en français, pro, concis (2-3 phrases). Tu expliques services, tarifs, rendez-vous."
    }
    
    system_prompt = system_prompts.get(business_type, system_prompts["service"])
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": message}]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                DEEPSEEK_URL,
                headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": messages, "temperature": 0.7, "max_tokens": 150}
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return "Merci pour votre message. Notre équipe vous répondra bientôt."
    except Exception as e:
        print(f"Erreur IA: {e}")
        return "Merci, comment puis-je vous aider?"
