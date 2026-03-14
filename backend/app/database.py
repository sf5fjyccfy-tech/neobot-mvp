"""
Configuration PostgreSQL pour NéoBot - Version robuste et flexible
"""
from sqlalchemy import create_engine, pool, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine
import os
from dotenv import load_dotenv
import logging

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

# ========== CONFIGURATION DATABASE ==========
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://neobot:neobot_secure_password@localhost:5432/neobot_db"
)

# Pool configuration
POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", 20))
MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", 30))
POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", 30))

# ========== ENGINE CREATION ==========
engine = create_engine(
    DATABASE_URL,
    poolclass=pool.QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_pre_ping=False,  # Désactiver les pings pour la performance
    pool_recycle=3600,   # Recycler les connexions chaque heure
    echo=False,  # TOUJOURS désactiver en production (SQLAlchemy logging = lent!)
)

# ========== SESSION FACTORY ==========
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# ========== BASE MODELS ==========
Base = declarative_base()

# ========== DEPENDENCY INJECTION ==========
def get_db():
    """Dépendance pour obtenir une session DB"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()

# ========== DATABASE INIT ==========
def init_db():
    """Créer toutes les tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Base de données initialisée")
    except Exception as e:
        logger.error(f"❌ Erreur init DB: {e}")
        raise

# ========== CONNECTION POOL EVENTS ==========
@event.listens_for(Engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Event listener pour les connexions"""
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except Exception as e:
        logger.warning(f"Connection verification failed: {e}")
