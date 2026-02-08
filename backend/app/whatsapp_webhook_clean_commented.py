"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              WHATSAPP WEBHOOK HANDLER - NéoBot Backend                       ║
║                         Message Receiving & Processing                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Ce fichier définit le "webhook" WhatsApp = un endpoint HTTP que WhatsApp service
appelle CHAQUE FOIS qu'un client envoie un message.

FLUX COMPLET:
  1. Client envoie message via WhatsApp
  2. WhatsApp service (Node.js) reçoit le message
  3. WhatsApp service appelle cet endpoint: POST /api/v1/webhooks/whatsapp
  4. On traite le message (pattern matching + DeepSeek IA)
  5. On envoie une réponse en background
  6. Done! Client reçoit la réponse

ANALOGIE:
  C'est comme une "sonnette" pour le backend
  Chaque message WhatsApp = quelqu'un sonne à la porte
  On ouvre, on lit le message, on répond!
"""

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ IMPORTS                                                                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
# APIRouter = créer des routes dédiées pour ce module
# HTTPException = répondre avec erreur (500, 404, etc.)
# Request = accès aux information brutes de la requête
# BackgroundTasks = faire des choses SANS attendre (asynchrone)

from pydantic import BaseModel
# BaseModel = classe pour valider les données entrantes
# Si les données ne matchent pas, Pydantic rejette automatiquement

from datetime import datetime
# Pour timestamp quand le message est arrivé

from typing import Optional
# Optional[str] = string ou None (optionnel)

import httpx
# Client HTTP async pour appeler d'autres APIs
# Ici: appeler DeepSeek API et WhatsApp service

import os
# Accès aux variables d'environnement
# Ex: DEEPSEEK_API_KEY, WHATSAPP_SERVICE_URL

import logging
# Logs pour déboguer, comprendre ce qui se passe

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ SETUP LOGGING                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

logger = logging.getLogger(__name__)
# Créer un logger pour ce module
# Utilisation: logger.info(), logger.error(), logger.warning()

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ SETUP ROUTING                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

router = APIRouter(
    prefix="/api/v1/webhooks",
    # ↑ Toutes les routes de ce router débutent par /api/v1/webhooks
    tags=["webhooks"]
    # ↑ Tag pour Swagger/documentation (grouper les endpoints)
)

# Dans main.py, ce router est inclus:
#   app.include_router(router)
# Donc la route finale sera: POST /api/v1/webhooks/whatsapp

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ DATA MODELS - Pydantic (Validation)                                         ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class WhatsAppMessage(BaseModel):
    """
    Structure of an incoming WhatsApp message from the WhatsApp service.
    
    UTILISATION:
      Quand le WhatsApp service appelle:
        POST /api/v1/webhooks/whatsapp
        {
          "from_": "+237123456789",
          "to": "+237987654321",
          "text": "Bonjour, quel est votre prix?",
          "senderName": "Alice",
          "messageKey": {"id": "...", "fromMe": false},
          "timestamp": 1707314820,
          "isMedia": false
        }
      
      FastAPI automatiquement:
        ✓ Valide les données
        ✓ Les convertit en WhatsAppMessage
        ✓ Les passe à la fonction webhook
      
      Si données invalides:
        ✗ FastAPI rejette (422 Unprocessable Entity)
        ✗ Renvoie erreur détaillée
    """
    
    from_: str = None
    # Numéro d'où vient le message
    # Format: "+237123456789" (pays code + numéro)
    # Qui l'a envoyé? Le client!
    
    to: str = None
    # Numéro d'où vient le message (le bot)
    # Format: "+237987654321"
    # La destination (le bot)
    # Optional = peut ne pas être fourni
    
    text: str
    # Le texte du message
    # Exemple: "Quel est votre prix?"
    # MANDATORY (pas de default)
    
    senderName: str
    # Nom du client qui a envoyé
    # Exemple: "Alice"
    # MANDATORY
    
    messageKey: dict
    # Métadonnées du message (ID, fromMe, etc.)
    # dict = dictionnaire Python
    # Pas besoin d'utiliser, mais on peut
    
    timestamp: int
    # Quand le message est arrivé (Unix time)
    # Exemple: 1707314820 = 8 février 2026 à 03:47:00
    # MANDATORY
    
    isMedia: bool = False
    # Est-ce que c'est media (image, audio, etc.)?
    # False par défaut (texte seul)

class WhatsAppResponse(BaseModel):
    """
    Structure of a response to send back to WhatsApp.
    
    EXEMPLE:
      {
        "to": "+237123456789",
        "text": "Notre prix est 20,000 FCFA/mois"
      }
    """
    
    to: str
    # Phone du client (où envoyer)
    
    text: str
    # Texte à répondre

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ BRAIN ORCHESTRATOR - L'Intelligence du Bot                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class BrainOrchestrator:
    """
    Cerveau du bot = décide comment répondre à un message.
    
    STRATÉGIE à 2 niveaux:
      Niveau 1: Pattern Matching (rapide, simple)
        "Si client dit 'prix' → répondre avec les tarifs"
      Niveau 2: DeepSeek IA (intelligent, flexible)
        "Si pas de pattern match → appeler IA pour répondre"
    
    ANALOGIE:
      Cerveau humain:
        - Questions usuelles → répondre vite (pattern)
        - Questions complexes → réfléchir (IA)
    
    GAIN:
      ✓ Réponses rapides aux questions courantes
      ✓ Réponses intelligentes aux questions complexes
      ✓ Les 2 mondes = meilleur UX
    """
    
    def __init__(self):
        """Initialiser le cerveau"""
        
        # ═══════════════════════════════════════════════════════════════
        # PATTERNS (Reconnaissance de mots-clés)
        # ═══════════════════════════════════════════════════════════════
        
        self.patterns = {
            # Si le message contient "prix" → appeler _handle_pricing()
            'prix': self._handle_pricing,
            'tarif': self._handle_pricing,
            'coût': self._handle_pricing,
            
            # Si le message contient "aide" → appeler _handle_help()
            'aide': self._handle_help,
            'help': self._handle_help,
            'menu': self._handle_help,
            
            # Si le message contient "demo" → appeler _handle_demo()
            'demo': self._handle_demo,
            
            # Si le message contient "bonjour/hello" → appeler _handle_greeting()
            'hello': self._handle_greeting,
            'bonjour': self._handle_greeting,
            'hi': self._handle_greeting,
            'salut': self._handle_greeting,
        }
        # UTILISATION:
        #   for keyword, handler in self.patterns.items():
        #       if keyword in message:
        #           return handler()  # Appeler la fonction!
        
        # ═══════════════════════════════════════════════════════════════
        # DEEPSEEK API (IA Fallback)
        # ═══════════════════════════════════════════════════════════════
        
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
        # Charger la clé API depuis .env
        # Si pas de clé: None
        # En prod: must avoir une clé!
        
        self.deepseek_url = 'https://api.deepseek.com/v1/chat/completions'
        # Endpoint de l'API DeepSeek
        # C'est où on appelle pour l'IA
    
    # ════════════════════════════════════════════════════════════════════
    # PROCESSUS PRINCIPAL
    # ════════════════════════════════════════════════════════════════════
    
    async def process(self, message: str, sender_name: str) -> str:
        """
        Traiter un message et retourner une réponse.
        
        FLUX:
          1. Normaliser le message (minuscules, espaces)
          2. Chercher les patterns
          3. Si trouvé: utiliser la réponse pre-écrite
          4. Si pas trouvé: appeler DeepSeek pour réponse IA
        
        ASYNC/AWAIT:
          async = cette fonction est "asynchrone"
                  Elle peut faire des appels réseau sans bloquer
          await = attendre qu'une autre fonction async finisse
        
        EXEMPLE:
          response = await brain.process("Quel est votre prix?", "Alice")
          # Retourne: "💰 *Tarifs NéoBot*...\n..."
        """
        
        logger.info(f"Processing message from {sender_name}: {message}")
        # Log pour déboguer = voir le message qui arrive
        
        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 1: Normaliser le message
        # ═══════════════════════════════════════════════════════════════
        
        normalized = message.lower().strip()
        # lower() = convertir en minuscules (pour matching)
        # strip() = enlever espaces au début/fin
        # "  PRIX  " → "prix"
        # "Bonjour" → "bonjour"
        
        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 2: Chercher les patterns
        # ═══════════════════════════════════════════════════════════════
        
        for keyword, handler in self.patterns.items():
            # keyword = "prix", "aide", "bonjour", etc.
            # handler = la fonction _handle_pricing(), _handle_help(), etc.
            
            if keyword in normalized:
                # Si le keyword est dans le message
                # Exemple: "Quel est votre prix?" contient "prix"
                
                response = handler(sender_name)
                # Appeler la fonction correspondante
                # handler() retourne une réponse pré-écrite
                
                logger.info(f"Matched pattern '{keyword}': {response}")
                # Log que on a trouvé un match
                
                return response
                # Retourner la réponse immédiatement
        
        # ═══════════════════════════════════════════════════════════════
        # ÉTAPE 3: Pas de pattern → Appeler DeepSeek IA
        # ═══════════════════════════════════════════════════════════════
        
        logger.info(f"No pattern matched, calling DeepSeek")
        # Log que on va utiliser l'IA
        
        response = await self._call_deepseek(message, sender_name)
        # Appeler DeepSeek pour une réponse intelligente
        # await = attendre la réponse (appel réseau)
        
        return response
    
    # ════════════════════════════════════════════════════════════════════
    # PATTERN HANDLERS (Réponses pré-écrites)
    # ════════════════════════════════════════════════════════════════════
    
    def _handle_pricing(self, sender_name: str) -> str:
        """
        Quand client demande les prix.
        
        UTILE POUR: "Quel est votre prix?", "Tarifs?", "Coûts?"
        """
        return """💰 *Tarifs NéoBot*

📱 Plan Starter: 20,000 FCFA/mois
   • 2000 messages WhatsApp
   • Dashboard basique
   • Support manuel

🚀 Plus tard: plans supérieurs

Voulez-vous activer? Répondez "ACTIVER"
"""
        # Multi-ligne string avec formatage WhatsApp
        # *Gras* = *texte*
        # ~ est pas utilisé dans ce code
        # Émojis rendent la réponse plus agréable
    
    def _handle_help(self, sender_name: str) -> str:
        """Afficher le menu/aide"""
        return """📋 *Menu NéoBot*

Tapez un mot-clé:
   📌 *prix* - Voir nos tarifs
   🆘 *aide* - Ce menu
   🎁 *demo* - Voir une démo
   
Ou posez n'importe quelle question!
"""
    
    def _handle_demo(self, sender_name: str) -> str:
        """Envoyer une démo/présentation"""
        return f"""🎬 *Démo NéoBot*

Bonjour {sender_name}! 👋

Je suis NéoBot, un assistant WhatsApp alimenté par l'IA.
Je peux:
   ✅ Répondre à vos questions
   ✅ Afficher le menu produits
   ✅ Traiter les commandes
   ✅ Vous aider 24/7

Prêt à commencer? 🚀
"""
        # Notez: {sender_name} = interpolation (personnalisation)
        # "Bonjour Alice!" au lieu de "Bonjour !"
    
    def _handle_greeting(self, sender_name: str) -> str:
        """Salutation"""
        return f"""Bonjour {sender_name}! 👋

Bienvenue chez NéoBot!

Tapez:
   *prix* - Voir nos tarifs
   *aide* - Voir le menu
   
Ou posez votre question!
"""
    
    # ════════════════════════════════════════════════════════════════════
    # IA FALLBACK - Réponse Intelligente
    # ════════════════════════════════════════════════════════════════════
    
    async def _call_deepseek(self, user_message: str, sender_name: str) -> str:
        """
        Appeler l'API DeepSeek pour une réponse IA.
        
        C'est le "super pouvoir" du bot:
          L'utilisateur peut poser n'importe quelle question
          DeepSeek va répondre intelligemment
        
        ASYNC/AWAIT:
          Cette fonction appelle un service externe
          On doit attendre sa réponse (réseau)
          "async" permet attendre sans bloquer
        
        EXEMPLE:
          user: "Quel est le meilleur produit pour acné?"
          response = await brain._call_deepseek("...", "Alice")
          # DeepSeek pense: "Acné, produits... parler de soins..."
          # Retourne: "Pour l'acné, je recommande notre gamme Clarify..."
        """
        
        # ═══════════════════════════════════════════════════════════════
        # VÉRIFICATION: API key existe?
        # ═══════════════════════════════════════════════════════════════
        
        if not self.deepseek_api_key:
            # Si pas de clé API configurée
            logger.warning("DeepSeek API key not configured")
            # Log un warning (pas critique, mais important)
            
            return "Je ne peux pas répondre à cette question en ce moment. Essayez: prix, aide, demo"
            # Répondre au client qu'on peut pas
            # Fallback to patterns
        
        try:
            # ═══════════════════════════════════════════════════════════════
            # PRÉPARATION: Construire le payload
            # ═══════════════════════════════════════════════════════════════
            
            payload = {
                "model": "deepseek-chat",
                # Quel modèle IA utiliser: deepseek-chat
                
                "messages": [
                    {
                        "role": "system",
                        # Instructions au modèle (contexte)
                        "content": "Vous êtes NéoBot, un assistant WhatsApp IA. Répondez en français, court (max 160 caractères pour SMS), amical."
                        # C'est comme dire au bot: "Tu es NéoBot, parle en français, sois court, sois gentil"
                    },
                    {
                        "role": "user",
                        # Message de l'utilisateur
                        "content": user_message
                    }
                ],
                # Format de conversation (role-content pairs)
                
                "temperature": 0.7,
                # Créativité (0.0 = robot, 1.0 = très créatif)
                # 0.7 = équilibre entre structure et créativité
                
                "max_tokens": 150
                # Maximum de mots à générer
                # 150 tokens ~= 100-120 mots
                # Court pour SMS
            }
            
            # ═══════════════════════════════════════════════════════════════
            # PRÉPARATION: Construire les headers
            # ═══════════════════════════════════════════════════════════════
            
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                # Authentification (API key)
                # Format: "Bearer <API_KEY>"
                
                "Content-Type": "application/json"
                # Type de données = JSON
            }
            
            # ═══════════════════════════════════════════════════════════════
            # APPEL: Faire la requête HTTP vers DeepSeek
            # ═══════════════════════════════════════════════════════════════
            
            async with httpx.AsyncClient() as client:
                # Créer un client HTTP (async)
                # "async with" = garder la connexion ouverte
                
                response = await client.post(
                    # Appel POST (envoyer données)
                    self.deepseek_url,
                    # URL: https://api.deepseek.com/v1/chat/completions
                    
                    json=payload,
                    # Données à envoyer (dict)
                    # httpx convertit en JSON automatiquement
                    
                    headers=headers,
                    # Headers HTTP (Auth, Content-Type, etc.)
                    
                    timeout=10
                    # Maximum 10 secondes pour la réponse
                    # Sinon: TimeoutError
                )
            
            # ═══════════════════════════════════════════════════════════════
            # VÉRIFICATION: Réponse OK?
            # ═══════════════════════════════════════════════════════════════
            
            if response.status_code != 200:
                # Si pas 200 (OK)
                # Peut être 401 (auth fail), 500 (server error), etc.
                
                logger.error(f"DeepSeek API error: {response.status_code}")
                # Log l'erreur
                
                return "Je dois vérifier ma mémoire. Essayez: prix, aide, demo"
                # Fallback friendly message
            
            # ═══════════════════════════════════════════════════════════════
            # EXTRACTION: Parser la réponse
            # ═══════════════════════════════════════════════════════════════
            
            data = response.json()
            # Convertir la réponse JSON en dict Python
            # Structure: {"choices": [{"message": {"content": "..."}}]}
            
            message = data['choices'][0]['message']['content']
            # Extraire le texte de la réponse
            # data['choices'] = liste de choix (on prend le 1er)
            # ['message'] = le message contenu
            # ['content'] = le texte
            
            logger.info(f"DeepSeek response: {message}")
            # Log la réponse reçue
            
            return message
            # Retourner la réponse IA au client
        
        except Exception as e:
            # SI une erreur occur quelque part dans le try
            # Réseau fail, JSON parsing fail, etc.
            
            logger.error(f"DeepSeek error: {str(e)}")
            # Log l'erreur détaillée
            
            return "Je rencontre une petite difficulté. Réessayez ou tapez: prix, aide, demo"
            # Fallback response

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ BRAIN INSTANCE (Global)                                                     ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

brain = BrainOrchestrator()
# Créer une instance UNIQUE du cerveau
# Partagée par toutes les requêtes webhook
# Gain: pas recréer l'objet à chaque fois (pattern caching)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ WEBHOOK ENDPOINT - La "Sonnette"                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

@router.post("/whatsapp")
# POST /api/v1/webhooks/whatsapp
# Quand WhatsApp service appelle ce endpoint
async def whatsapp_webhook(
    message: WhatsAppMessage,
    # Les données du message (validées par Pydantic)
    
    background_tasks: BackgroundTasks
    # FastAPI injection: tâches à faire en background
):
    """
    Webhook endpoint pour recevoir les messages WhatsApp.
    
    FLUX COMPLET:
      1. WhatsApp service appelle: POST /api/v1/webhooks/whatsapp {"data": ...}
      2. FastAPI valide et parse les données
      3. Cette fonction est appelée
      4. On traite le message
      5. On ajoute une tâche en background pour envoyer la réponse
      6. On retourne immédiatement une réponse au service
      7. Le background task s'exécute en parallèle
    
    ASYNCE/AWAIT:
      async = cette fonction peut faire plusieurs choses en parallèle
      background_tasks.add_task() = ajouter une tâche sans attendre
    
    GAIN: Réponse immédiate au WhatsApp service (~100ms)
          Traitement en parallèle (~2-5 secondes)
          Ne pas bloquer l'utilisateur
    """
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # LOG: Quoi?
        # ═══════════════════════════════════════════════════════════════
        
        logger.info(f"📨 Received message from {message.senderName}: {message.text}")
        # Log le message reçu (débogage)
        
        # ═══════════════════════════════════════════════════════════════
        # EXTRACTION: Phone number
        # ═══════════════════════════════════════════════════════════════
        
        phone = message.from_
        # Phone d'où le message vient: "+237123456789"
        
        if phone.startswith('+'):
            phone = phone[1:]
            # Enlever le "+" au début pour stockage
            # "+237123456789" → "237123456789"
        
        # ═══════════════════════════════════════════════════════════════
        # TODO: Sauvegarder ce la DB
        # ═══════════════════════════════════════════════════════════════
        
        # conversation = await save_message_to_db(
        #     phone=phone,
        #     sender_name=message.senderName,
        #     text=message.text,
        #     direction='incoming'
        # )
        # TODO = à faire plus tard
        # Pour l'instant: rien faire
        
        # ═══════════════════════════════════════════════════════════════
        # TRAITEMENT: Appeler le cerveau
        # ═══════════════════════════════════════════════════════════════
        
        response_text = await brain.process(message.text, message.senderName)
        # Appeler le BrainOrchestrator
        # Retourne la réponse (pattern ou IA)
        # await = attendre que DeepSeek réponde (si applicable)
        
        # ═══════════════════════════════════════════════════════════════
        # ENVOI: Ajouter en background task
        # ═══════════════════════════════════════════════════════════════
        
        background_tasks.add_task(
            # Ajouter une tâche en background
            send_whatsapp_response,
            # Fonction à exécuter
            phone=phone,
            text=response_text
            # Paramètres à passer
        )
        # Cette tâche s'exécutera APRÈS que on retourne la réponse
        # Ne pas bloquer la requête!
        
        # ═══════════════════════════════════════════════════════════════
        # RÉPONSE: Retour immédiat
        # ═══════════════════════════════════════════════════════════════
        
        return {
            "status": "received",
            # Message reçu et traité
            
            "phone": phone,
            # Le téléphone du client
            
            "sender": message.senderName,
            # Nom du client
            
            "timestamp": datetime.now().isoformat()
            # Quand on a reçu (format ISO 8601)
        }
        # Retourner une réponse JSON au service
        # Status 200 = OK
    
    except Exception as e:
        # SI une erreur occur
        
        logger.error(f"Error processing webhook: {str(e)}")
        # Log l'erreur
        
        raise HTTPException(
            status_code=500,
            # Status HTTP: 500 (Server Error)
            detail=str(e)
            # Message d'erreur
        )
        # Retourner erreur au service

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ BACKGROUND TASK - Envoyer la réponse                                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

async def send_whatsapp_response(phone: str, text: str):
    """
    Envoyer une réponse via le service WhatsApp.
    
    EXÉCUTÉ EN BACKGROUND:
      - Ne bloque pas la requête webhook
      - L'utilisateur ne attend pas
      - Fait quelque part "en arrière-plan"
    
    FLUX:
      1. Constructive payload (téléphone + texte)
      2. Appeler le service WhatsApp (port 3001)
      3. Service envoie via Baileys/WhatsApp
      4. Utilisateur reçoit la réponse
    
    ASYNC/AWAIT:
      async with httpx.AsyncClient() = connexion asynchrone
      await client.post() = attendre sans bloquer
    """
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # CONFIG: Où est le service WhatsApp?
        # ═══════════════════════════════════════════════════════════════
        
        whatsapp_service_url = os.getenv(
            'WHATSAPP_SERVICE_URL',
            # Chercher la variable d'environnement
            
            'http://localhost:3001'
            # Fallback: localhost (développement)
        )
        # En prod: WHATSAPP_SERVICE_URL = "http://whatsapp-service:3001"
        # En dev: WHATSAPP_SERVICE_URL = "http://localhost:3001"
        
        # ═══════════════════════════════════════════════════════════════
        # PAYLOAD: Structure de la réponse
        # ═══════════════════════════════════════════════════════════════
        
        payload = {
            "to": phone,
            # Téléphone du client (où envoyer)
            
            "text": text
            # La réponse (de pattern ou IA)
        }
        # Format simple: juste le téléphone et texte
        
        # ═══════════════════════════════════════════════════════════════
        # APPEL: POST vers le service WhatsApp
        # ═══════════════════════════════════════════════════════════════
        
        async with httpx.AsyncClient() as client:
            # Créer un client HTTP async
            
            response = await client.post(
                # POST request
                f"{whatsapp_service_url}/send",
                # Endpoint: /send du service
                # Exemple: http://localhost:3001/send
                
                json=payload,
                # Données en JSON
                
                timeout=10
                # Maximum 10 secondes
            )
        
        # ═══════════════════════════════════════════════════════════════
        # VÉRIFICATION: Envoyé OK?
        # ═══════════════════════════════════════════════════════════════
        
        if response.status_code == 200:
            # Status 200 = success
            logger.info(f"✅ Message sent to {phone}")
            # Log success
        
        else:
            # Erreur
            logger.error(f"Failed to send message: {response.status_code}")
            # Log l'erreur
            
            logger.error(response.text)
            # Log le détail
    
    except Exception as e:
        # SI réseau fail, service down, etc.
        
        logger.error(f"Error sending WhatsApp response: {str(e)}")
        # Log l'erreur
        # Note: pas d'exception levée (background task)
        # Juste log et continue

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ UTILS - Functions à implémenter                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

async def save_message_to_db(phone: str, sender_name: str, text: str, direction: str):
    """
    TODO: Sauvegarder le message dans la base de données.
    
    LOGIQUE:
      1. Trouver le Conversation avec ce phone
      2. Si pas existe: créer une nouvelle
      3. Créer un nouveau Message
      4. Sauvegarder (commit)
    
    PARAMETÉRISATION:
      phone: "+237123456789" (ou "237123456789")
      sender_name: "Alice"
      text: "Bonjour, quel est votre prix?"
      direction: "incoming" (du client vers nous)
    
    RETOUR:
      Retourner l'objet Conversation créé/trouvé
    
    STATUS: ❌ À FAIRE
    """
    pass
    # pass = rien ne se passe (placeholder)

def is_daily_limit_reached(phone: str) -> bool:
    """
    TODO: Vérifier si le client a dépassé sa limite JOURNALIÈRE.
    
    LOGIQUE:
      1. Trouver le Tenant associé à ce phone
      2. Compter messages d'aujourd'hui
      3. Comparer avec sa limite journalière
      4. Retourner True/False
    
    RETOUR: True si limite atteinte, False sinon
    
    STATUS: ❌ À FAIRE
    """
    return False
    # Pour l'instant: toujours False (pas de limite)

def is_monthly_limit_reached(phone: str) -> bool:
    """
    TODO: Vérifier si le client a dépassé sa limite MENSUELLE.
    
    LOGIQUE:
      1. Trouver le Tenant associé à ce phone
      2. Compter messages de ce mois
      3. Comparer avec sa limite mensuelle (plan)
      4. Retourner True/False
    
    RETOUR: True si limite atteinte, False sinon
    
    UTILISATION FUTURE:
      if is_monthly_limit_reached(phone):
          return "Désolé, vous avez atteint votre limite mensuelle."
    
    STATUS: ❌ À FAIRE
    """
    return False
    # Pour l'instant: toujours False (pas de limite)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ RÉSUMÉ: FLUX COMPLET D'UN MESSAGE                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# 1. CLIENT envoie message WhatsApp
#    "Quel est votre prix?"
#    ↓
# 2. WHATSAPP SERVICE reçoit (Baileys)
#    Service Node.js écoute la conversation
#    ↓
# 3. SERVICE appelle notre webhook
#    POST /api/v1/webhooks/whatsapp
#    {"from_": "+237123...", "text": "Quel est votre prix?", ...}
#    ↓
# 4. FASTAPI valide data → WhatsAppMessage
#    ↓
# 5. whatsapp_webhook() s'exécute
#    ↓
# 6. brain.process() appelé
#    - Normaliser message    "quel est votre prix?" 
#    - Chercher pattern      Match "prix"!
#    - Appeler _handle_pricing()
#    - Retourne réponse formatée
#    ↓
# 7. background_tasks.add_task(send_whatsapp_response, ...)
#    ↓
# 8. webhook_endpoint() retourne Status 200 au service
#    (Fast ~100ms)
#    ↓
# 9. send_whatsapp_response() s'exécute en background
#    - POST http://localhost:3001/send
#    - {"to": "+237123...", "text": "💰 *Tarifs NéoBot*..."}
#    ↓
# 10. WHATSAPP SERVICE envoie via Baileys
#     ↓
# 11. CLIENT reçoit: "💰 *Tarifs NéoBot*..."
#     (Peut être à plusieurs secondes)
#
# TOTAL: 
#   - Réponse immédiate au service: ~100ms
#   - Réponse au client: ~2-5 secondes

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ FIN DU FICHIER                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
