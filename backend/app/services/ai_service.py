import os
import hashlib
import time
import httpx
import logging
from typing import Union
from ..http_client import DeepSeekClient

logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    logger.error("❌ DEEPSEEK_API_KEY non défini — les réponses IA seront non-fonctionnelles")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# ── Cache TTL en mémoire pour les réponses DeepSeek ───────────────────────────
# Clé = SHA-256(system_prompt + message) — ne cache PAS l'historique à dessein.
# Utile surtout pour les FAQ répétitives (bonjour, tarifs, horaires...).
_AI_CACHE: dict[str, tuple[str, float]] = {}
_CACHE_TTL = 3600       # 1 heure en secondes
_CACHE_MAX_SIZE = 1000  # éjection aléatoire au-delà pour éviter la croissance infinie


def _cache_key(system_prompt: str, message: str) -> str:
    return hashlib.sha256(f"{system_prompt}|||{message}".encode()).hexdigest()


def _cache_get(key: str) -> str | None:
    entry = _AI_CACHE.get(key)
    if entry:
        value, expires_at = entry
        if time.monotonic() < expires_at:
            return value
        del _AI_CACHE[key]  # Expiré
    return None


def _cache_set(key: str, value: str) -> None:
    if len(_AI_CACHE) >= _CACHE_MAX_SIZE:
        # Éjection simpliste : supprimer la première entrée (insertion-order dict Python 3.7+)
        _AI_CACHE.pop(next(iter(_AI_CACHE)))
    _AI_CACHE[key] = (value, time.monotonic() + _CACHE_TTL)

# === Fonctions qui étaient dans ai_prompts ===
def detect_mode(business_type: str, business_name: str = None) -> str:
    """Détecter le mode de réponse"""
    if business_type == "NéoBot" or (business_name and "NéoBot" in business_name):
        return "neobot_admin"
    elif business_type in ["restaurant", "boutique", "service"]:
        return business_type
    else:
        return "service"

def get_system_prompt(mode: str, business_name: str = None) -> str:
    """Obtenir le prompt système selon le mode"""
    prompts = {
        "neobot_admin": "Tu es NéoBot, un assistant commercial pour l'automatisation WhatsApp. Tu présentes NéoBot, un service qui automatise les réponses WhatsApp pour les entreprises. Tu ne parles que de ça. Tu proposes des essais gratuits et donnes les tarifs (20k, 50k, 90k FCFA). Tu es concis et direct.",
        "restaurant": f"Tu es l'assistant du restaurant {business_name}. Tu réponds aux questions sur le menu, les horaires, les réservations. Tu es poli et concis.",
        "boutique": f"Tu es l'assistant de la boutique {business_name}. Tu aides les clients avec les produits, les prix, la livraison. Tu es serviable et professionnel.",
        "service": f"Tu es l'assistant de {business_name}. Tu réponds aux questions sur les services, les tarifs, les rendez-vous. Tu es clair et efficace.",
    }
    return prompts.get(mode, prompts["service"])

def get_fallback_template(mode: str, intent: str, business_name: str = None) -> str:
    """Obtenir un template de fallback"""
    templates = {
        "neobot_admin": {
            "salutation": "👋 Bonjour ! Je suis NéoBot, l'assistant qui automatise WhatsApp pour les entreprises. Envoyez '1' pour la présentation ou '2' pour les tarifs.",
            "what_is": "🤖 NéoBot automatise vos réponses WhatsApp. Gain de temps garanti ! Envoyez '1' pour la présentation, '2' pour les tarifs.",
            "pricing": "💰 Tarifs NéoBot :\n- Basique : 20k FCFA/mois\n- Standard : 50k FCFA/mois\n- Pro : 90k FCFA/mois\n\nEssai gratuit 14 jours !",
            "demo": "🎥 NéoBot répond automatiquement à vos clients WhatsApp. Essayez-le gratuitement ! Envoyez '1' pour commencer.",
            "default": "🤖 NéoBot - Automatisation WhatsApp\n\nEnvoyez '1' pour la présentation, '2' pour les tarifs, ou 'demo' pour une démonstration."
        },
        "restaurant": {
            "salutation": f"👋 Bonjour et bienvenue au {business_name} ! Que puis-je faire pour vous ?",
            "pricing": "💰 Nos plats vont de 2000 à 5000 FCFA. Le menu complet est disponible sur demande.",
            "order": "🍽️ Pour commander, veuillez nous indiquer le plat et l'heure de livraison souhaitée.",
            "default": f"🍴 Bienvenue au {business_name}. Comment puis-je vous aider ?"
        },
        "boutique": {
            "salutation": f"👋 Bonjour et bienvenue chez {business_name} ! Comment puis-je vous aider ?",
            "pricing": "💰 Nos prix varient selon les articles. Dites-moi ce qui vous intéresse.",
            "order": "🛍️ Pour commander, veuillez me dire le produit, la taille et la couleur.",
            "default": f"🛒 Bienvenue chez {business_name}. Que cherchez-vous ?"
        },
        "service": {
            "salutation": f"👋 Bonjour ! Bienvenue chez {business_name}. Comment puis-je vous aider ?",
            "pricing": "💰 Nos tarifs dépendent du service. Je peux vous faire un devis personnalisé.",
            "order": "📅 Pour prendre rendez-vous, veuillez me dire la date et l'heure qui vous conviennent.",
            "default": f"💼 Bienvenue chez {business_name}. Que souhaitez-vous savoir ?"
        }
    }
    mode_templates = templates.get(mode, templates["service"])
    return mode_templates.get(intent, mode_templates["default"])

# === Fin des fonctions ai_prompts ===

async def generate_ai_response(
    message: str, 
    business_info: Union[str, dict],
    business_name: str = None,
    conversation_history: list = None
) -> str:
    # 1. Extraire business_type et business_name
    business_type = ""
    if isinstance(business_info, dict):
        business_type = business_info.get("business_type", "")
        if not business_name:
            business_name = business_info.get("name", "")
    elif hasattr(business_info, 'business_type'):
        business_type = business_info.business_type
        if not business_name and hasattr(business_info, 'name'):
            business_name = business_info.name
    else:
        business_type = str(business_info)
    
    # 2. Détection du mode
    mode = detect_mode(business_type, business_name)
    
    # 3. Pour messages simples → fallback direct
    message_lower = message.lower().strip()
    simple_words = ["bonjour", "salut", "hello", "merci", "ok", "d'accord"]
    
    if any(word in message_lower for word in simple_words) and len(message_lower.split()) <= 3:
        if "bonjour" in message_lower or "salut" in message_lower or "hello" in message_lower:
            return get_fallback_template(mode, "salutation", business_name)
        return get_fallback_template(mode, "default", business_name)
    
    # 4. Récupérer le prompt système FORT
    system_prompt = get_system_prompt(mode, business_name)
    
    # 5. AJOUTER DES INSTRUCTIONS FORTES AU PROMPT
    if mode == "neobot_admin":
        system_prompt += "\n\n🚨 INSTRUCTIONS FORTES :\n- Réponds UNIQUEMENT sur l'automatisation WhatsApp\n- Mentionne 'WhatsApp' dans ta réponse\n- Propose l'essai gratuit\n- Réponse courte (3-4 lignes max)\n- Prix : 20k, 50k, 90k FCFA\n- NE PARLE PAS de sites web, administratif, numérique général"
    else:
        system_prompt += "\n\n🚨 INSTRUCTIONS FORTES :\n- Réponds UNIQUEMENT sur les produits/services\n- Ne parle PAS de NéoBot\n- Sois concis (3-4 lignes)\n- Guide vers l'achat ou réservation"
    
    # 6. Construire messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]
    
    if conversation_history:
        messages = conversation_history + messages[-2:]
    
    # 7. Appel API avec client global (pooling) — vérification cache d'abord
    cache_k = _cache_key(system_prompt, message)
    cached = _cache_get(cache_k)
    if cached is not None:
        return cached

    try:
        response_data = await DeepSeekClient.call(
            messages=messages,
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=120
        )
        
        if "error" not in response_data and "choices" in response_data:
            ai_response = response_data["choices"][0]["message"]["content"]
            
            # Post-processing SIMPLE
            ai_response = ai_response.strip()
            
            # Vérifier si la réponse est hors-sujet
            if mode == "neobot_admin" and "whatsapp" not in ai_response.lower():
                # Forcer une réponse de fallback
                return get_fallback_template(mode, "what_is", business_name)
            
            # Limiter la longueur
            lines = ai_response.split('\n')
            if len(lines) > 4:
                ai_response = '\n'.join(lines[:4])
            
            if len(ai_response) > 300:
                ai_response = ai_response[:297] + "..."
            
            _cache_set(cache_k, ai_response)
            return ai_response
        else:
            return get_fallback_response(mode, message_lower, business_name)
                
    except Exception as e:
        print(f"⚠️  Erreur IA: {e}")
        return get_fallback_response(mode, message_lower, business_name)

def get_fallback_response(mode: str, message: str, business_name: str = None) -> str:
    """Fallback intelligent"""
    message_lower = message.lower()
    
    if mode == "neobot_admin":
        if any(word in message_lower for word in ["quoi", "comment", "fonctionne", "c'est quoi"]):
            intent = "what_is"
        elif any(word in message_lower for word in ["prix", "combien", "coûte", "tarif"]):
            intent = "pricing"
        elif any(word in message_lower for word in ["exemple", "montre", "démo"]):
            intent = "demo"
        elif any(word in message_lower for word in ["bonjour", "salut", "hello"]):
            intent = "salutation"
        else:
            intent = "default"
    else:
        if any(word in message_lower for word in ["bonjour", "salut", "hello"]):
            intent = "salutation"
        elif any(word in message_lower for word in ["prix", "combien", "coûte"]):
            intent = "pricing"
        elif any(word in message_lower for word in ["commander", "acheter", "prendre"]):
            intent = "order"
        else:
            intent = "default"
    
    return get_fallback_template(mode, intent, business_name)
