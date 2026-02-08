"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DATABASE CONFIGURATION - NéoBot                           ║
║                    PostgreSQL with SQLAlchemy ORM                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

Ce fichier configuré PostgreSQL pour l'application NeobotMVP.
Il établit la connexion, crée le pool, et fournit les sessions.

ANALOGIE:
  PostgreSQL (base de données) = Un grand coffre-fort avec des milliers de tiroirs
  SQLAlchemy (ORM)             = Une façon de parler avec le coffre
  database.py (ce fichier)     = La clé et les instructions pour accéder au coffre
  psycopg2 (driver)            = Le traducteur entre Python et PostgreSQL

SI psycopg2 est absent = la clé ne fonctionne pas = erreur silencieuse!
"""

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ IMPORTS ESSENTIELS                                                           ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

from sqlalchemy import create_engine, pool, event
# EXPLICATION:
#   create_engine() = Crée la connexion vers PostgreSQL
#   pool            = Gère un "pool" (groupe) de connexions
#   event           = Système pour écouter les événements de connexion

from sqlalchemy.ext.declarative import declarative_base
# EXPLICATION:
#   declarative_base() = Crée une classe de base pour tous les modèles ORM
#   Ex: class Tenant(Base): ... = Tenant hérité de Base

from sqlalchemy.orm import sessionmaker
# EXPLICATION:
#   sessionmaker() = Factory pour créer des "sessions"
#   Une session = une conversation avec la base de données

from sqlalchemy.engine import Engine
# EXPLICATION:
#   Engine = le moteur qui gère la communication avec PostgreSQL

import os
# EXPLICATION:
#   os = accès aux variables d'environnement
#   Utile pour: DATABASE_URL, POOL_SIZE, etc.

from dotenv import load_dotenv
# EXPLICATION:
#   load_dotenv() = charge le fichier .env
#   .env contient: DATABASE_URL, DEBUG_MODE, etc.

import logging
# EXPLICATION:
#   logging = système pour afficher des logs
#   Utile pour: debug, erreurs, informations

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ SETUP LOGGING                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Charger les variables d'environnement du fichier .env
load_dotenv()

# Créer un logger nommé après ce fichier (__name__ = "app.database")
logger = logging.getLogger(__name__)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ CONFIGURATION 1: DATABASE URL                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

DATABASE_URL = os.getenv(
    "DATABASE_URL",  # Cherche la variable d'environnement DATABASE_URL
    # SI elle existe → l'utilise
    # SI elle n'existe pas → utilise cette valeur par défaut
    "postgresql://neobot:neobot_secure_password@localhost:5432/neobot_db"
)

# FORMAT de l'URL:
#   postgresql://  ← Protocol (PostgreSQL)
#   neobot         ← Username (user)
#   :              ← Séparateur
#   neobot_secure_password  ← Password
#   @              ← Séparateur
#   localhost      ← Host (adresse du serveur)
#   :5432          ← Port (5432 = port PostgreSQL par défaut)
#   /neobot_db     ← Nom de la base de données

# ANALOGIE de l'URL:
#   postgresql://neobot:password@localhost:5432/neobot_db
#   = "Va à localhost:5432, connecte-toi avec neobot/password, utilise neobot_db"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ CONFIGURATION 2: CONNECTION POOL                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Qu'est-ce qu'un "pool"?
# ANALOGIE: Pool = parking avec places limitées
#   - Ces places = des connexions PostgreSQL
#   - Plutôt que créer une nouvelle connexion à chaque requête
#   - On crée un pool et réutilise les connexions existantes
#   - GAIN: Plus rapide, moins de ressources!

POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", 10))
# EXPLICATION:
#   Nombre de connexions à garder "toujours prêtes"
#   Par défaut: 10
#   Ce qu'il signifie: "Garde 10 places de parking réservées"

MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", 20))
# EXPLICATION:
#   Nombre de connexions "en plus" si toutes les 10 sont occupées
#   Par défaut: 20 connexions supplémentaires
#   Ce qu'il signifie: "Si les 10 sont occupées, peux en faire 20 de plus"
#   Total max = POOL_SIZE + MAX_OVERFLOW = 30 connexions

POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", 30))
# EXPLICATION:
#   Temps à attendre (en secondes) pour une connexion disponible
#   Par défaut: 30 secondes
#   Ce qu'il signifie: "Si 30 connexions sont occupées, attends 30 sec pour une libre"
#   Après 30 sec: erreur "timeout"

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ CONFIGURATION 3: LES PARAMÈTRES du Pool                                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# pool_pre_ping=True
# EXPLICATION:
#   Avant d'utiliser une connexion du pool, vérifier qu'elle marche
#   Si elle ne marche pas → la supprimer et en créer une nouvelle
#   GAIN: Évite les "stale connections" (connexions mortes)

# pool_recycle=3600
# EXPLICATION:
#   Recycler (supprimer) les connexions après 3600 secondes (1 heure)
#   Raison: PostgreSQL tue les connexions inactives après 8-12 heures
#   Si on recycle après 1h: on est toujours safe!
#   ANALOGIE: Changer l'huile de la voiture tous les 1000km (prévention)

# echo=...
# EXPLICATION:
#   Si DEBUG_MODE=true: afficher TOUTES les queries SQL générées
#   Utile pour déboguer, voir ce que SQLAlchemy fait
#   Exemple:
#     SELECT * FROM tenants WHERE id = 1;
#     INSERT INTO messages (conversation_id, content) VALUES (1, 'Hello');

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ CRÉATION DU MOTEUR (ENGINE)                                                  ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

engine = create_engine(
    DATABASE_URL,  # URL de connexion (où aller et comment se connecter)
    poolclass=pool.QueuePool,  # Type de pool = "QueuePool" (file d'attente)
    pool_size=POOL_SIZE,  # 10 connexions toujours prêtes
    max_overflow=MAX_OVERFLOW,  # +20 connexions si besoin
    pool_timeout=POOL_TIMEOUT,  # Attendre 30 sec max
    pool_pre_ping=True,  # Vérifier la connexion avant utilisation
    pool_recycle=3600,  # Recycler après 1 heure
    echo=os.getenv("DEBUG_MODE", "false").lower() == "true",  # Debug mode
)

# QU'EST-CE QUE LE "ENGINE"?
# ANALOGIE: Engine = le contrôle de tour d'une usine
#   - Il dit: "Y a-t-il une place au pool?"
#   - Il crée des connexions si besoin
#   - Il gère la file d'attente
#   - Il recycle les vieilles connexions
#   - TOUT passe par le engine!

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ SESSION FACTORY (Sessionmaker)                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

SessionLocal = sessionmaker(
    autocommit=False,  # Ne pas auto-commit (attendre un .commit() explicite)
    autoflush=False,   # Ne pas auto-flush (attendre un .flush() explicite)
    bind=engine,       # Utiliser notre engine pour les connexions
    expire_on_commit=False  # Après .commit(), garder les objets (pas les recharger)
)

# QU'EST-CE QU'UNE "SESSION"?
# ANALOGIE: Session = une "conversation" avec la base de données
#   - Cette conversation dure jusqu'à .close()
#   - On peut faire plusieurs requêtes dans UNE session
#   - À la fin: .commit() pour sauvegarder, .rollback() pour annuler
#
# EXEMPLE:
#   session = SessionLocal()  # Ouvrir une conversation
#   user = session.query(User).filter(User.id == 1).first()  # Question
#   user.name = "Alice"  # Modification en mémoire
#   session.commit()  # Sauvegarder dans la base
#   session.close()  # Terminer la conversation

# autocommit=False SIGNIFIE:
#   Tu dois faire .commit() toi-même pour sauvegarder
#   Si tu oublies .commit() → les changements sont perdus!
#   ANALOGIE: Écrire dans un cahier, mais passer par un correcteur avant de sauver

# autoflush=False SIGNIFIE:
#   Tu dois faire .flush() toi-même pour envoyer les changements à la DB
#   Si tu oublies → les changements restent en mémoire
#   ANALOGIE: Réciter ce que tu as écrit, mais pas encore le sauver

# expire_on_commit=False SIGNIFIE:
#   Après .commit(), les objets gardent leurs valeurs (pas rechargées)
#   Si tu veux les valeurs à jour: fais .refresh()
#   GAIN: Plus rapide, moins de requêtes!

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ BASE POUR LES MODÈLES ORM                                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

Base = declarative_base()

# QU'EST-CE QUE "Base"?
# ANALOGIE: Base = "mother class" de tous les modèles
#   Chaque modèle (Tenant, Conversation, Message) pour HÉRITER de Base
#   Base dit: "Tu es un modèle ORM, voici tes pouvoirs!"
#
# EXEMPLE D'UTILISATION dans models.py:
#   from database import Base
#
#   class Tenant(Base):  # ← Hérite de Base
#       __tablename__ = "tenants"
#       id = Column(Integer, primary_key=True)
#       name = Column(String)
#
# SUPER POUVOIRS donnés par Base:
#   ✓ Mapping automatique Python ↔ PostgreSQL
#   ✓ .query() pour chercher
#   ✓ .add() pour ajouter
#   ✓ .delete() pour supprimer
#   ✓ Et plus!

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ DEPENDENCY INJECTION - get_db()                                              ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def get_db():
    """
    Dépendance pour FastAPI: fournir une session DB à chaque requête.
    
    ANALOGIE: get_db = "guichet" automatique
      - ChaqueFOIS qu'une route a besoin d'une session
      - FastAPI appelle get_db()
      - Ouvre une session, la donne à la route
      - La route l'utilise
      - get_db() la ferme automatiquement
    
    UTILISATION dans main.py:
      from fastapi import Depends
      
      @app.get("/api/tenants")
      def list_tenants(db: Session = Depends(get_db)):
          # ← FastAPI appelle get_db(), obtient une session
          # ← Passe 'db' à la fonction
          tenants = db.query(Tenant).all()
          return tenants
          # ← La fonction se termine
          # ← get_db() ferme la session (finally: db.close())
    """
    
    # Créer une nouvelle session
    db = SessionLocal()
    
    try:
        # Donner la session à la route
        yield db
        # ↑ "yield" = "voilà ta session, utilise-la, puis on continue"
        
    except Exception as e:
        # SI une erreur se produit
        # → Annuler tous les changements (rollback)
        db.rollback()
        logger.error(f"Database error: {e}")
        # → Re-lancer l'erreur
        raise
        
    finally:
        # TOUJOURS exécuté, même si erreur
        # → Fermer la session, libérer la ressource
        db.close()
        # ↑ Important! Sinon le pool se remplit de sessions mortes!

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ INITIALISATION DE LA BASE - init_db()                                        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def init_db():
    """
    Créer TOUTES les tables dans PostgreSQL.
    
    ANALOGIE: init_db = "première utilisation" du coffre-fort
      - D'abord: le coffre est vide (pas de tables)
      - init_db() crée: tenants, conversations, messages
      - Après: le coffre est prêt!
    
    UTILISATION:
      - Appelé UNE FOIS au démarrage du serveur
      - Si tables existent déjà: rien ne se passe (idempotent)
      - Si tables n'existent pas: créées maintenant
    
    WHAT IT DOES:
      Base.metadata.create_all(bind=engine)
      ↑ Regarde TOUS les modèles qui héritent de Base
      ↑ Crée les tables correspondantes dans PostgreSQL
    """
    try:
        # Créer les tables basées sur les modèles
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Architecture database initialisée")
        
    except Exception as e:
        # SI le création échoue
        logger.error(f"❌ Erreur initialization base: {e}")
        raise  # Relancer l'erreur (critique!)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ EVENT LISTENER - Vérification de Connexion                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

@event.listens_for(Engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """
    Événement déclenché CHAQUE FOIS qu'une nouvelle connexion est créée.
    
    PURPOSE: Vérifier que la connexion marche VRAIMENT
    
    POURQUOI?
      - SQLAlchemy peut créer une connexion invalide
      - PostgreSQL peut ne pas répondre
      - Avec cette vérification: on sait immédiatement
      - GAIN: Erreurs claires, pas de confusion!
    
    COMMENT?
      - Exécuter "SELECT 1" (la requête la plus simple du monde)
      - Si elle marche: OK, la connexion est valide
      - Si elle échoue: on log un warning
    """
    try:
        # Créer un curseur (pointeur pour exécuter des requêtes)
        cursor = dbapi_conn.cursor()
        
        # Exécuter la requête la plus simple: "SELECT 1"
        # Résultat: 1 (toujours)
        # Utilité: juste vérifier que PostrgreSQL répond
        cursor.execute("SELECT 1")
        
        # Fermer le curseur (libérer la ressource)
        cursor.close()
        # ↑ Important! Sinon c'est une fuite mémoire
        
    except Exception as e:
        # SI la vérification échoue
        logger.warning(f"🚨 Connection verification échoué: {e}")
        # Note: on log un WARNING, pas une ERROR
        # Raison: ce n'est pas fatal, la connexion peut être recréée

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ RÉSUMÉ: FLUX COMPLET DE DÉMARRAGE                                            ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# 1. Au démarrage du serveur:
#    init_db()
#    → Crée les tables (tenants, conversations, messages)

# 2. Première requête arrive (ex: GET /api/tenants):
#    FastAPI appelle get_db()
#    → SessionLocal() crée une session
#    → Demande une connexion au pool
#    → Pool vérifie avec pool_pre_ping=True
#    → event.listens_for execute SELECT 1
#    → OK! La session est donnée à la route

# 3. La route utilise la session:
#    db.query(Tenant).all()
#    → SQLAlchemy génère: SELECT * FROM tenants
#    → engine envoie via PostgreSQL
#    → PostgreSQL répond
#    → Résultat retourné

# 4. La route termine:
#    finally: db.close()
#    → Connexion retournée au pool
#    → Pool la garde pour la prochaine requête
#    → GAIN: Pas d'ouverture/fermeture à chaque fois!

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ DÉPANNAGE: ERREURS COURANTES                                                 ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# ERREUR 1: "ModuleNotFoundError: No module named 'psycopg2'"
# CAUSE: psycopg2-binary pas installé
# FIX: pip install psycopg2-binary==2.9.9
# LEÇON: driver DOIT être listé dans requirements.txt

# ERREUR 2: "could not connect to server: Connection refused"
# CAUSE: PostgreSQL n'est pas lancé
# FIX: docker-compose up -d
# LEÇON: Vérifier DATABASE_URL pointe vers le bon serveur

# ERREUR 3: "QueuePool limit exceeded with overflow"
# CAUSE: Trop de connexions simultanées
# FIX: Augmenter POOL_SIZE ou MAX_OVERFLOW
# LEÇON: Vérifier que .close() est toujours appelé

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║ FIN DU FICHIER                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝
