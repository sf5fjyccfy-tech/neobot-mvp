"""
╔════════════════════════════════════════════════════════════════════════════╗
║                     🚀 NÉOBOT BACKEND - main.py                            ║
║                          Version Éducative v1.0                             ║
║                                                                            ║
║ QUOI C'EST CE FICHIER?                                                    ║
║ ────────────────────────────────────────────────────────────────────────  ║
║ Ceci est le CŒUR du backend NéoBot.                                       ║
║                                                                            ║
║ LE BOT REÇOIT:   Message WhatsApp → le backend reçoit                    ║
║ LE BOT TRAITE:   Sauvegarde + Appelle l'IA                               ║
║ LE BOT RÉPOND:   Envoie réponse intelligente                             ║
║                                                                            ║
║ ANALOGIE: main.py = Réceptionniste d'hôtel                               ║
║ - Reçoit les appels (messages)                                            ║
║ - Traite les demandes (sauvegarde + IA)                                   ║
║ - Répond clairement (API responses)                                        ║
║                                                                            ║
║ COMMENT ÇA MARCHE EN BREF:                                                ║
║ 1. FastAPI crée un serveur HTTP (port 8000)                               ║
║ 2. Quand message arrive → une "route" le reçoit                           ║
║ 3. Route appelle fonction qui traite                                       ║
║ 4. Fonction sauvegarde dans DB + appelle IA                               ║
║ 5. Répond avec une réponse intelligente                                    ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
"""

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: IMPORTS (Amener les outils externes)
# ═══════════════════════════════════════════════════════════════════════════
# 
# QUOI: Qu'est-ce qu'on importe?
#       FastAPI = librairie pour créer des APIs
#       Session = outil pour parler à la base de données
#       logging = outil pour afficher messages et erreurs
#       etc.
#
# POURQUOI: On besoin ces outils pour faire fonctionner le bot
#
# COMMENT LES GENS UTILISENT:
#   - from X import Y = "Prend l'outil Y de la librairie X"

# ┌─ Imports FastAPI (server HTTP) ─────────────────────────────────────┐
from fastapi import FastAPI, HTTPException, Request, Depends  # Tools pour créer API
from fastapi.middleware.cors import CORSMiddleware  # Permet frontend accéder backend
from fastapi.responses import JSONResponse  # Formater réponses JSON

# ┌─ Imports Database (parler à PostgreSQL) ─────────────────────────┐
from sqlalchemy.orm import Session  # Tool pour interagir avec DB

# ┌─ Imports Date/Time (gérer dates) ─────────────────────────────┐
from datetime import datetime  # Pour marquer QUAND un message arrive

# ┌─ Imports Logging (afficher messages) ─────────────────────────┐
import logging  # Pour écrire logs dans console/fichiers
import os  # Pour lire variables d'environnement (.env)

# ┌─ Imports Configuration ─────────────────────────────────────┐
from dotenv import load_dotenv  # Charger fichier .env
import httpx  # Pour faire requêtes HTTP (appeler l'IA)

# ┌─ Imports Locaux (notre code) ──────────────────────────────┐
from .database import get_db, init_db, Base, engine  # Base de données
from .models import Tenant, Conversation, Message  # Modèles DB
from .whatsapp_webhook import router as whatsapp_router  # Routes WhatsApp

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: LOGGER SET UP (L'outil pour afficher messages)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: Logger = quelque chose qui écrit des messages
#
# POURQUOI: Pendant que le bot travaille, on veut voir:
#   "✅ Message reçu de +237123456789"
#   "❌ Erreur: client non trouvé"
#   "🤖 IA a répondu"
#
# COMMENT:
#   logger.info("✅ Quelque chose d'IMPORTANT")
#   logger.error("❌ ERREUR grave")
#   logger.warning("⚠️ Attention")

logging.basicConfig(level=logging.INFO)  # Affiche tous les messages INFO et plus
logger = logging.getLogger(__name__)  # Crée notre logger personnel

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: CHARGER LES VARIABLES D'ENVIRONNEMENT (.env)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: Fichier .env = fichier secret avec infos sensibles
#
# EXEMPLE de .env:
#   DEEPSEEK_API_KEY=sk_123456789_secret_key
#   DATABASE_URL=postgresql://user:password@localhost:5432/neobot
#   BACKEND_PORT=8000
#
# POURQUOI: On stocke secrets pas dans le code GitHub (dangereux)
#           Au lieu, on les lit d'un fichier .env local
#
# COMMENT:
#   load_dotenv() = "Lis le fichier .env et charge les variables"
#   os.getenv("DEEPSEEK_API_KEY") = "Récupère la valeur de DEEPSEEK_API_KEY"

load_dotenv()

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: CRÉATION DE L'APP FastAPI (le serveur principal)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: FastAPI() = crée le serveur principal
#
# ANALOGIE: Comme ouvrir un restaurant
#   - App = le restaurant
#   - title = "Restaurant NéoBot"
#   - version = "Édition 1.0"
#   - description = "Cuisine IA française"
#
# COMMENT ÇA MARCHE:
#   1. FastAPI() crée un serveur
#   2. Le serveur écoute sur le port 8000
#   3. Quand quelqu'un accède /health → on répond "je suis vivant"
#   4. Quand quelqu'un POST message → on le traite

app = FastAPI(
    title="NÉOBOT",
    version="1.0.0",
    description="WhatsApp Bot Assistant avec IA pour PME Africaines"
)

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: ACTIVER LES ROUTES DU WEBHOOK WHATSAPP
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: "Routes" = chemins URL où on reçoit des messages
#
# EXEMPLE DE ROUTES:
#   GET /health → "Tu fonctionnes?"
#   POST /api/v1/webhooks/whatsapp → "Message WhatsApp entrant"
#   GET /api/tenants → "Donne-moi tous les clients"
#
# POURQUOI .include_router():
#   - Le webhook WhatsApp a beaucoup de routes
#   - Au lieu de les mettre ICI (fichier trop long)
#   - On les met dans whatsapp_webhook.py (fichier séparé)
#   - Puis on les "ajoute" au main avec .include_router()
#
# ANALOGIE: Comme un grand building
#   - main.py = le réceptionniste principal
#   - whatsapp_webhook.py = département WhatsApp
#   - .include_router() = "Ajoute le département WhatsApp au building"

app.include_router(whatsapp_router)

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: MIDDLEWARE CORS (Autorise le Frontend à appeler Backend)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: CORS = "Cross-Origin Resource Sharing"
#
# PROBLÈME SANS CORS:
#   Frontend (port 3000) essaie appeler Backend (port 8000)
#   Le backend dit: "Non! Tu viens d'un autre port, c'est pas sûr!"
#   Frontend reçoit erreur.
#
# SOLUTION AVEC CORS:
#   On dit au backend: "Oui, accepte les appels du frontend"
#
# QUOI C'EST allow_origins=["*"] ?
#   - "*" = "Accepte les appels de PARTOUT" (facile pour dev)
#   - ⚠️ En production, changer à: allow_origins=["https://mysite.com"]
#
# EXEMPLE CORS EN ACTION:
#   Frontend: "Hello Backend, comment ça va?"
#   Backend sans CORS: "Non, t'es interdit!"
#   Backend avec CORS: "Oui bien sûr, viens!"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Accepte appels de TOUS les domaines
    allow_credentials=True,  # Autorise cookies/auth
    allow_methods=["*"],  # Accepte GET, POST, DELETE, etc.
    allow_headers=["*"],  # Accepte n'importe quel header HTTP
)

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: ÉVÉNEMENTS STARTUP/SHUTDOWN (Quand app démarre/s'arrête)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: @app.on_event() = "Quand cet événement arrive, exécute cette fonction"
#
# ANALOGIE RESTAURANT:
#   - STARTUP = Ouverture du restaurant le matin
#     → Allumer les lumières
#     → Préparer les tables
#     → Dire "Bonjour, on est prêt!"
#   - SHUTDOWN = Fermeture le soir
#     → Éteindre les lumières
#     → Nettoyer
#     → Dire "Au revoir!"
#
# POURQUOI on besoin?
#   Startup: Initialiser la base de données au démarrage
#   Shutdown: Fermer connexions proprement en arrêtant

@app.on_event("startup")
async def startup():
    """
    QUOI FAIT: S'exécute QUAND L'APP DÉMARRE (une seule fois)
    
    ÉTAPES:
      1. Appelle init_db() pour initialiser la base de données
      2. Si pas d'erreur → affiche "✅ Application démarrée"
      3. Si erreur → affiche le message d'erreur
    
    EXEMPLE:
      Utilisateur: python -m uvicorn app.main:app --reload
      → L'app démarre
      → startup() s'exécute
      → Base de données initialisée
      → "✅ Application démarrée" s'affiche
    """
    try:
        init_db()  # Initialiser la base de données (créer tables si besoin)
        logger.info("✅ Application démarrée avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur au démarrage: {e}")

@app.on_event("shutdown")
async def shutdown():
    """
    QUOI FAIT: S'exécute QUAND L'APP S'ARRÊTE (une seule fois)
    
    ÉTAPES:
      1. Affiche "🛑 Application arrêtée"
      2. Les connexions DB se ferment automatiquement
    
    EXEMPLE:
      Utilisateur: CTRL+C (arrête l'app)
      → shutdown() s'exécute
      → "🛑 Application arrêtée" s'affiche
    """
    logger.info("🛑 Application arrêtée")

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: ROUTES HEALTH (Est-ce que le bot est vivant?)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: Health checks = vérifie que le serveur fonctionne
#
# POURQUOI: Avant d'envoyer un message, on veut être SÛR que:
#   - Le backend est vivant
#   - La base de données répond
#   - Tout est en bonne santé
#
# ANALOGIE: Comme un docteur qui prend le pouls
#   - @app.get("/health") = prendre le pouls simple
#   - @app.get("/api/health") = prendre le pouls + vérifier cœur + poumons
#
# COMMENT LES GENS UTILISENT:
#   Frontend: curl http://localhost:8000/health
#   Backend répond: {"status": "healthy", ...}
#   Frontend: "Ah bon, le backend marche!"

@app.get("/health")
async def health():
    """
    QUOI FAIT: Répondre "Je suis vivant!" (health check basique)
    
    POURQUOI: Vérifier rapidement que le serveur répond
    
    COMMENT:
      1. Retourne un dictionnaire JSON
      2. status = "healthy" (tout va bien)
      3. timestamp = l'heure actuelle
      4. version = version du app
    
    EXEMPLE DE RÉPONSE:
      {
        "status": "healthy",
        "timestamp": "2026-02-08T10:30:45.123456",
        "version": "1.0.0"
      }
    
    USAGE:
      curl http://localhost:8000/health
      → Affiche la réponse JSON
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/health")
async def api_health(db: Session = Depends(get_db)):
    """
    QUOI FAIT: Health check COMPLET (vérifie aussi la database)
    
    POURQUOI: Plus de détails que le health() simple
             On veut être SÛR que la database répond aussi
    
    COMMENT:
      1. db.execute("SELECT 1") = demande simple à la DB
      2. Si la DB répond → "database": "connected"
      3. Si la DB ne répond pas → "database": "disconnected"
    
    EXEMPLE RÉPONSE OK:
      {
        "status": "healthy",
        "database": "connected",
        "timestamp": "2026-02-08T10:30:45.123456"
      }
    
    EXEMPLE RÉPONSE ERREUR:
      HTTP 503 (Service Unavailable)
      {
        "status": "unhealthy",
        "database": "disconnected",
        "error": "Connection refused"
      }
    
    USAGE:
      curl http://localhost:8000/api/health
      → Affiche la réponse JSON (ou erreur avec HTTP 503)
    
    ARGUMENT db:
      - Depends(get_db) = "Récupère une session DB"
      - C'est automatique, pas besoin de le faire manuellement
    """
    try:
        # Teste la connexion DB avec une requête simple
        db.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"DB Health check échoué: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }, 503  # HTTP 503 = Service Unavailable

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 9: ROUTE ROOT (Accueil du serveur)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: POST / = accueil du serveur
#
# ANALOGIE: Comme entrer dans un shop
#   - Vous: "Bonjour!"
#   - Shop: "Bonjour! Bienvenue! Voici nos services:"

@app.get("/")
async def root():
    """
    QUOI FAIT: Affiche welcome message + liens utiles
    
    EXEMPLE RÉPONSE:
      {
        "message": "🚀 NÉOBOT API v1.0.0",
        "docs": "/docs",
        "status": "running"
      }
    
    USAGE:
      curl http://localhost:8000/
      → Affiche le message
    
      Ou ouvrir dans browser: http://localhost:8000/
      → Affiche le message en JSON
    """
    return {
        "message": "🚀 NÉOBOT API v1.0.0",
        "docs": "/docs",  # Lien vers documentation Swagger
        "status": "running"
    }

@app.get("/docs")
async def docs():
    """
    QUOI FAIT: Documentation liste des endpoints
    
    NOTE: FastAPI génère automatiquement /docs (Swagger UI)
          Cette route est juste pour info supplémentaire
    
    EXEMPLE RÉPONSE:
      {
        "endpoints": {
          "health": "GET /health",
          "tenants": "GET /api/tenants",
          "whatsapp": "POST /api/whatsapp/message",
          "conversations": "GET /api/conversations/{tenant_id}"
        }
      }
    
    USAGE:
      curl http://localhost:8000/docs
      → Affiche tous les endpoints disponibles
    """
    return {
        "endpoints": {
            "health": "GET /health - Est-ce que je suis vivant?",
            "api_health": "GET /api/health - Suis-je en bonne santé (+ DB)?",
            "tenants": "GET /api/tenants - Liste tous les clients",
            "tenant_detail": "GET /api/tenants/{id} - Un client spécifique",
            "conversations": "GET /api/conversations/{tenant_id} - Conversations d'un client",
            "messages": "GET /api/messages/{conversation_id} - Messages d'une conversation",
            "whatsapp": "POST /api/whatsapp/message - Reçois message WhatsApp"
        }
    }

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 10: ROUTES TENANTS (Gérer les clients)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: Routes pour créer/lister/modifier les clients (Tenants)
#
# RAPPEL: Tenant = un CLIENT qui utilise NéoBot
#         Exemple: Restaurant Ali, Boutique Yvetle, Salon de coiffure, etc.
#
# OPÉRATIONS CRUD:
#   CREATE: POST /api/tenants → créer nouveau client
#   READ: GET /api/tenants → lister tous clients
#   READ: GET /api/tenants/1 → un client spécifique
#   UPDATE: PATCH /api/tenants/1 → modifier client (pas implémenté ici)
#   DELETE: DELETE /api/tenants/1 → supprimer client (pas implémenté ici)

@app.get("/api/tenants")
async def list_tenants(db: Session = Depends(get_db)):
    """
    QUOI FAIT: Lister TOUS les clients
    
    COMMENT:
      1. db.query(Tenant).all() = "Récupère TOUS les tenants de la DB"
      2. Pour chaque tenant, retourne infos de base
      3. Retourne liste complète
    
    EXEMPLE RÉPONSE:
      {
        "count": 2,
        "tenants": [
          {
            "id": 1,
            "name": "Restaurant Ali",
            "email": "ali@restaurant.cm",
            "plan": "basique",
            "whatsapp_connected": true
          },
          {
            "id": 2,
            "name": "Boutique Yvetle",
            "email": "yvetle@boutique.cm",
            "plan": "standard",
            "whatsapp_connected": false
          }
        ]
      }
    
    USAGE:
      curl http://localhost:8000/api/tenants
      → Affiche tous les clients
    """
    # Requête DB: "Récupère TOUS les tenants"
    tenants = db.query(Tenant).all()
    
    # Construire la réponse (extraire infos importantes)
    return {
        "count": len(tenants),  # Nombre de clients
        "tenants": [
            {
                "id": t.id,
                "name": t.name,
                "email": t.email,
                "plan": t.plan,
                "whatsapp_connected": t.whatsapp_connected
            }
            for t in tenants  # Pour CHAQUE tenant t, extraire ces infos
        ]
    }

@app.get("/api/tenants/{tenant_id}")
async def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    """
    QUOI FAIT: Récupérer les détails d'UN client spécifique
    
    ARGUMENT:
      tenant_id: l'ID du client (ex: 1, 2, 3, etc.)
    
    COMMENT:
      1. db.query(Tenant).filter(Tenant.id == tenant_id).first()
         = "Cherche le tenant avec cet ID"
      2. Si pas trouvé → HTTPException (erreur 404)
      3. Si trouvé → retourne tous ses détails
    
    EXEMPLE REQUÊTE:
      curl http://localhost:8000/api/tenants/1
      → Affiche détails du client #1
    
    EXEMPLE RÉPONSE:
      {
        "id": 1,
        "name": "Restaurant Ali",
        "email": "ali@restaurant.cm",
        "plan": "basique",
        "whatsapp_connected": true,
        "messages_used": 45,
        "messages_limit": 2000
      }
    
    ERREUR SI TENANT PAS TROUVÉ:
      HTTP 404
      {"detail": "Tenant not found"}
    """
    # Cherche le tenant avec cet ID
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    # Si pas trouvé, retourne erreur 404
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Si trouvé, retourne ses infos détaillées
    return {
        "id": tenant.id,
        "name": tenant.name,
        "email": tenant.email,
        "plan": tenant.plan.value,  # .value = convertir enum en texte
        "whatsapp_connected": tenant.whatsapp_connected,
        "messages_used": tenant.messages_used,
        "messages_limit": tenant.messages_limit
    }

@app.post("/api/tenants")
async def create_tenant(data: dict, db: Session = Depends(get_db)):
    """
    QUOI FAIT: Créer UN NOUVEAU client
    
    ARGUMENT:
      data: dictionnaire JSON avec infos du client
            exemple: {"name": "Restaurant Ali", "email": "ali@...", "phone": "+237...", ...}
    
    ÉTAPES:
      1. Extraire infos du data JSON
      2. Créer nouvel objet Tenant
      3. Ajouter à la DB avec db.add()
      4. Sauvegarder avec db.commit()
      5. Retourner confirmation
    
    EXEMPLE REQUÊTE (depuis Postman ou curl):
      POST /api/tenants
      Content-Type: application/json
      
      {
        "name": "Restaurant Ali",
        "email": "ali@restaurant.cm",
        "phone": "+237123456789",
        "business_type": "restaurant"
      }
    
    EXEMPLE RÉPONSE:
      {
        "success": true,
        "tenant_id": 1,
        "message": "Tenant créé"
      }
    
    ERREUR SI PROBLÈME:
      HTTP 400
      {"detail": "Email déjà utilisé"}
    """
    try:
        # Créer nouvel objet Tenant avec infos du JSON
        tenant = Tenant(
            name=data.get("name"),                           # Nom du business
            email=data.get("email"),                         # Email
            phone=data.get("phone"),                         # Téléphone
            business_type=data.get("business_type", "autre")  # Type (restaurant, boutique, etc.)
        )
        
        # Ajouter à la DB
        db.add(tenant)
        
        # Sauvegarder (commit = enregistrer définitivement)
        db.commit()
        
        # Récupérer l'ID généré automatique
        db.refresh(tenant)
        
        # Log de succès
        logger.info(f"✅ Tenant créé: {tenant.name} (ID: {tenant.id})")
        
        # Retourner confirmation
        return {
            "success": True,
            "tenant_id": tenant.id,
            "message": "Tenant créé avec succès"
        }
        
    except Exception as e:
        # Si erreur, annuler les changements (rollback)
        db.rollback()
        
        # Log l'erreur
        logger.error(f"❌ Erreur création tenant: {e}")
        
        # Retourner erreur
        raise HTTPException(status_code=400, detail=str(e))

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 11: ROUTES CONVERSATIONS (Gérer les chats)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: Routes pour lister les conversations
#
# RAPPEL: Conversation = un chat entre
#         - Un client spécifique (ex: "+237123456789")
#         - Et un tenant/business (ex: Restaurant Ali)
#
# EXEMPLE:
#   Conversation #1: Client "+237111111111" ↔ Restaurant Ali
#   Conversation #2: Client "+237222222222" ↔ Restaurant Ali
#   Conversation #3: Client "+237333333333" ↔ Boutique Yvetle

@app.get("/api/conversations/{tenant_id}")
async def get_conversations(tenant_id: int, db: Session = Depends(get_db)):
    """
    QUOI FAIT: Lister toutes les conversations d'UN client
    
    ARGUMENT:
      tenant_id: l'ID du client (ex: 1)
    
    COMMENT:
      1. db.query(Conversation).filter(...) = "Récupère conversations du tenant 1"
      2. Pour chaque conversation, affiche infos
      3. Retourne liste
    
    EXEMPLE REQUÊTE:
      curl http://localhost:8000/api/conversations/1
      → Affiche conversations du client #1
    
    EXEMPLE RÉPONSE:
      {
        "tenant_id": 1,
        "count": 3,
        "conversations": [
          {
            "id": 1,
            "customer_phone": "+237111111111",
            "customer_name": "Client 1111",
            "status": "active",
            "messages": 12,
            "last_message": "2026-02-08T10:30:45.123456"
          },
          {
            "id": 2,
            "customer_phone": "+237222222222",
            "customer_name": "Client 2222",
            "status": "closed",
            "messages": 5,
            "last_message": "2026-02-07T15:20:10.654321"
          }
        ]
      }
    """
    # Récupère toutes les conversations du tenant
    conversations = db.query(Conversation).filter(
        Conversation.tenant_id == tenant_id
    ).all()
    
    # Construire la réponse
    return {
        "tenant_id": tenant_id,
        "count": len(conversations),
        "conversations": [
            {
                "id": c.id,
                "customer_phone": c.customer_phone,
                "customer_name": c.customer_name,
                "status": c.status,
                "messages": len(c.messages),
                "last_message": c.last_message_at.isoformat() if c.last_message_at else None
            }
            for c in conversations
        ]
    }

@app.get("/api/messages/{conversation_id}")
async def get_messages(conversation_id: int, db: Session = Depends(get_db)):
    """
    QUOI FAIT: Récupérer TOUS les messages d'UNE conversation
    
    ARGUMENT:
      conversation_id: l'ID de la conversation (ex: 1)
    
    COMMENT:
      1. db.query(Message).filter(...) = "Récupère messages"
      2. .order_by(Message.created_at) = "Trier par date"
      3. Pour chaque message, affiche contenu
      4. Retourne liste
    
    EXEMPLE REQUÊTE:
      curl http://localhost:8000/api/messages/1
      → Affiche tous messages de la conversation #1
    
    EXEMPLE RÉPONSE:
      {
        "conversation_id": 1,
        "count": 3,
        "messages": [
          {
            "id": 1,
            "content": "Bonjour, vous êtes ouvert?",
            "direction": "incoming",
            "is_ai": false,
            "created_at": "2026-02-08T10:00:00.000000"
          },
          {
            "id": 2,
            "content": "Bonjour! Oui on est ouvert jusqu'à 22h.",
            "direction": "outgoing",
            "is_ai": true,
            "created_at": "2026-02-08T10:00:05.000000"
          },
          {
            "id": 3,
            "content": "Super! Merci beaucoup!",
            "direction": "incoming",
            "is_ai": false,
            "created_at": "2026-02-08T10:00:15.000000"
          }
        ]
      }
    """
    # Récupère tous les messages de la conversation, triés par date
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()  # .all() = tous, .order_by() = trier
    
    # Construire la réponse
    return {
        "conversation_id": conversation_id,
        "count": len(messages),
        "messages": [
            {
                "id": m.id,
                "content": m.content,
                "direction": m.direction,  # "incoming" ou "outgoing"
                "is_ai": m.is_ai,  # true = réponse IA, false = message client
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 12: IA INTEGRATION (Appeler l'IA DeepSeek)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: Fonctions pour appeler l'IA
#
# POURQUOI: Quand on reçoit un message du client, on besoin de l'IA
#           pour générer une RÉPONSE INTELLIGENTE
#
# COMMENT ÇA MARCHE:
#   Message Client: "Bonjour, vous êtes ouverts?"
#         ↓
#   Appelle DeepSeek API
#         ↓
#   IA répond: "Bonjour! Oui, nous sommes ouverts de 9h à 22h!"
#         ↓
#   Envoie réponse au client

async def get_ai_response(message: str, business_name: str = "NéoBot") -> str:
    """
    QUOI FAIT: Appelle l'IA DeepSeek pour générer une réponse
    
    ARGUMENTS:
      message: le texte du client (ex: "Bonjour, vous êtes ouverts?")
      business_name: le nom du business (ex: "Restaurant Ali")
    
    RETOURNE:
      string: la réponse IA (ex: "Bonjour! Oui, nous sommes ouverts...")
    
    ÉTAPES:
      1. Récupère la clé API de DeepSeek depuis .env
      2. Si pas de clé → utilise fallback (réponses prédéfinies)
      3. Si clé existe → appelle l'API DeepSeek
      4. Si succès → retourne réponse IA
      5. Si erreur → retourne fallback
    
    EXEMPLE:
      response = await get_ai_response("Quel est votre horaire?", "Restaurant Ali")
      # Retourne: "Notre horaire est de 9h à 22h, 7 jours par semaine."
    
    COÛT: ~0.10 FCFA par message avec DeepSeek
    """
    # Récupère la clé API depuis .env
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    # Si pas de clé API configurée, utilise fallback
    if not api_key:
        logger.warning("⚠️ DEEPSEEK_API_KEY non configurée, utilise fallback")
        return get_fallback_response(message, business_name)
    
    try:
        # Appelle l'API DeepSeek (via httpx, un client HTTP)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",  # Le modèle IA à utiliser
                    "messages": [
                        {
                            "role": "system",
                            "content": f"Tu es l'assistant de {business_name}. Réponds en français, sois courtois et concis (max 2 phrases)."
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ],
                    "temperature": 0.7,  # 0.7 = réponses pas trop aléatoires
                    "max_tokens": 150  # Limite la longueur de réponse
                }
            )
            
            # Si répon OK (code 200)
            if response.status_code == 200:
                data = response.json()
                ai_response = data['choices'][0]['message']['content']
                logger.info(f"🤖 IA a généré réponse")
                return ai_response
            else:
                # Erreur API, utilise fallback
                logger.warning(f"⚠️ DeepSeek API erreur: {response.status_code}")
                return get_fallback_response(message, business_name)
                
    except Exception as e:
        # Exception (timeout, connexion, etc.), utilise fallback
        logger.error(f"❌ Erreur appel IA: {e}")
        return get_fallback_response(message, business_name)

def get_fallback_response(message: str, business_name: str = "NéoBot") -> str:
    """
    QUOI FAIT: Retourne une réponse pré-définie (pas l'IA)
    
    POURQUOI: Si l'IA échoue ou pas disponible, on besoin de répondre
             quelque chose d'intéressant automatiquement
    
    COMMENT:
      1. Regarde le message client
      2. Cherche des mots clés (prix, salut, merci, etc.)
      3. Retourne une réponse appropriée
    
    EXEMPLE MOTS CLÉS:
      - "bonjour", "salut", "hello" → Réponse d'accueil
      - "prix", "tarif", "combien" → Réponse prix
      - "merci", "thank" → Réponse remerciement
      - Autre → Réponse neutre
    
    AVANTAGE: Rapide et pas cher (pas d'appel API)
    """
    msg_lower = message.lower()  # Convertir en minuscules pour comparer
    
    # Cherche BONJOUR/SALUT
    if any(word in msg_lower for word in ["bonjour", "salut", "hello", "hi"]):
        return f"👋 Bonjour ! Bienvenue chez {business_name}. Comment puis-je vous aider ?"
    
    # Cherche PRIX/TARIF
    elif any(word in msg_lower for word in ["prix", "tarif", "coût", "combien"]):
        return f"💰 Pour plus d'informations sur nos tarifs, veuillez nous contacter au numéro du business."
    
    # Cherche HORAIRE/OUVERTURE
    elif any(word in msg_lower for word in ["horaire", "ouvert", "ferme", "heure"]):
        return f"🕐 Pour connaître nos horaires précis, veuillez nous contacter directement."
    
    # Cherche MERCI/GRATITUDE
    elif any(word in msg_lower for word in ["merci", "thank", "gracias"]):
        return f"😊 De rien ! Avez-vous autre chose ?"
    
    # Défaut: réponse neutre
    else:
        return f"✅ Merci pour votre message ! Notre équipe vous répondra rapidement."

# NOTE IMPORTANTE POUR DÉBUTANT:
# Le fallback est TRÈS important car:
# 1. Économise argent (pas d'appels API pour questions communes)
# 2. Plus rapide (pas besoin d'attendre l'IA)
# 3. Plus fiable (pas risque d'erreur API)
# Dans NéoBot, on utilise fallback D'ABORD, puis IA si besoin

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 13: ERROR HANDLERS (Gérer les erreurs)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: Handlers = fonctions spéciales qui gèrent les erreurs
#
# POURQUOI: Quand quelque chose va mal, on veut:
#   1. Montrer un message d'erreur clair
#   2. Log l'erreur pour debugging
#   3. Retourner status code HTTP correct
#
# EXEMPLE: Si client demande /api/tenants/999999
#          Tenant 999999 n'existe pas
#          Au lieu de crash → HTTP 404 + message clair

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    QUOI FAIT: Gère les erreurs HTTP (404, 400, 500, etc.)
    
    EXEMPLE: Client demande /api/tenants/999999
             La route retourne: HTTPException(status_code=404)
             Ce handler formate la réponse en JSON clair
    
    RETOURNE:
      {
        "error": "Tenant not found",
        "status": "error",
        "timestamp": "2026-02-08T10:30:45.123456"
      }
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    QUOI FAIT: Gère les erreurs INATTENDUES (crash, bug, etc.)
    
    EXEMPLE: Un bug dans le code fait une erreur qui n'est pas HTTP
             Ce handler le capture et retourne HTTP 500 (Internal Error)
    
    RETOURNE:
      HTTP 500
      {
        "error": "Internal server error",
        "status": "error",
        "timestamp": "2026-02-08T10:30:45.123456"
      }
    """
    logger.error(f"❌ Erreur non gérée: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# ═══════════════════════════════════════════════════════════════════════════
# SECTION 14: LANCER L'APP (main() - entry point)
# ═══════════════════════════════════════════════════════════════════════════
#
# QUOI: if __name__ == "__main__": = ce code s'exécute DIRECTEMENT
#
# POURQUOI: Permet de lancer l'app deux façons:
#   1. Directement: python main.py (utilise __main__)
#   2. Via uvicorn: uvicorn app.main:app --reload (pas utilise __main__)
#
# COMMENT: Utilise uvicorn.run() pour lancer le serveur

if __name__ == "__main__":
    import uvicorn
    
    # Récupère infos de configuration depuis .env (ou utilise défauts)
    HOST = os.getenv("BACKEND_HOST", "0.0.0.0")  # Écoute sur TOUS les IPs
    PORT = int(os.getenv("BACKEND_PORT", 8000))  # Port 8000
    RELOAD = os.getenv("BACKEND_RELOAD", "true").lower() == "true"  # Reload en développement
    
    # Lance le serveur
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=RELOAD  # True = recharger code quand on change quelque chose
    )

# ═══════════════════════════════════════════════════════════════════════════
# FIN DU FICHIER main.py
# ═══════════════════════════════════════════════════════════════════════════
#
# RÉSUMÉ:
#   Ce fichier = le CŒUR de l'API NéoBot
#   Il fait:
#     1. Accueille les messages WhatsApp
#     2. Les sauvegarde dans la DB
#     3. Appelle l'IA pour générer réponse
#     4. Retourne la réponse
#   
# FLOT COMPLET D'UN MESSAGE:
#   1. Message arrive via WhatsApp → porter 3001
#   2. Service WhatsApp l'envoie au Backend via HTTP → port 8000
#   3. Route /api/whatsapp/message le reçoit
#   4. Sauvegarde message dans Conversation
#   5. Appelle get_ai_response()
#   6. IA ou fallback génère réponse
#   7. Sauvegarde réponse dans Conversation
#   8. Retourne réponse au WhatsApp Service
#   9. WhatsApp Service envoie réponse à l'utilisateur
#   10. Utilisateur reçoit réponse! ✅
#
# LES PLUS IMPORTANTS À COMPRENDRE:
#   ✅ Routes = les endpoints que le frontend appelle
#   ✅ Async = répondre à plusieurs requêtes simultanément
#   ✅ Database = sauvegarder messages/conversations
#   ✅ IA = générer réponses intelligentes
#   ✅ Fallback = réponses rapides quand l'IA pas disponible
#   ✅ Error Handling = gérer les erreurs proprement
#
# PROCHAINE ÉTAPE:
#   Lire et comprendre les other fichiers:
#   - database.py → comment on parle à PostgreSQL?
#   - models.py → tables: Tenant, Conversation, Message
#   - whatsapp_webhook.py → routes du webhook WhatsApp
#   - services/ → IA, Fallback, etc.
#
"""

