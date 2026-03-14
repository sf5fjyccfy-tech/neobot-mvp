"""
Configuration Oracle Cloud (OCI) pour NéoBot
Migration from PostgreSQL to Oracle Database with Redis caching
"""
from sqlalchemy import create_engine, pool, event, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine
import redis
import os
from dotenv import load_dotenv
import logging
import json

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

# ========== ORACLE DATABASE CONFIGURATION ==========
# Format for Oracle OCI: oracle+oracledb://user:password@host:port/database
ORACLE_HOST = os.getenv("ORACLE_HOST", "neobot-db.c9akciq32u84.us-phoenix-1.rds.ocicloudservices.com")
ORACLE_PORT = os.getenv("ORACLE_PORT", "1521")
ORACLE_USER = os.getenv("ORACLE_USER", "admin")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "")
ORACLE_SERVICE = os.getenv("ORACLE_SERVICE", "neobot_pdb")

# Build Oracle connection string
DATABASE_URL = f"oracle+oracledb://{ORACLE_USER}:{ORACLE_PASSWORD}@{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE}"

logger.info(f"🔗 Oracle Connection: {ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE}")

# Pool configuration - optimized for Oracle
POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "25"))
MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "40"))
POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))

# ========== REDIS CONFIGURATION ==========
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", "3600"))  # 1 hour default

# Redis connection
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True,
        health_check_interval=30
    )
    redis_client.ping()
    logger.info(f"✅ Redis Connected: {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.warning(f"⚠️ Redis Connection Failed: {e} - Caching disabled")
    redis_client = None

# ========== ORACLE ENGINE CREATION ==========
# Oracle-specific parameters for optimal performance
engine = create_engine(
    DATABASE_URL,
    poolclass=pool.QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_pre_ping=True,  # Check connections before use
    pool_recycle=POOL_RECYCLE,
    echo=False,  # Never enable in production
    # Oracle specific parameters
    isolation_level="READ_COMMITTED",
    use_returning_clause=True,  # For INSERT...RETURNING
    max_cached_statement_lifetime=3600,
    max_overflow_statement_cache_size=500,
)

# ========== SESSION FACTORY ==========
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
    future=True,  # SQLAlchemy 2.0 style
)

# ========== BASE MODELS ==========
Base = declarative_base()

# ========== CACHE UTILITIES ==========
class RedisCache:
    """Wrapper for Redis caching operations"""
    
    @staticmethod
    def get(key: str):
        """Get value from Redis"""
        if redis_client is None:
            return None
        try:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
        return None
    
    @staticmethod
    def set(key: str, value, ttl: int = REDIS_CACHE_TTL):
        """Set value in Redis"""
        if redis_client is None:
            return False
        try:
            redis_client.setex(key, ttl, json.dumps(value))
            return True
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
        return False
    
    @staticmethod
    def delete(key: str):
        """Delete key from Redis"""
        if redis_client is None:
            return False
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis delete error: {e}")
        return False
    
    @staticmethod
    def flush_pattern(pattern: str):
        """Delete all keys matching pattern"""
        if redis_client is None:
            return 0
        try:
            keys = redis_client.keys(pattern)
            if keys:
                return redis_client.delete(*keys)
        except Exception as e:
            logger.warning(f"Redis flush error: {e}")
        return 0

# ========== DEPENDENCY INJECTION ==========
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        db.close()

# ========== DATABASE INITIALIZATION ==========
def init_db():
    """Initialize all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Oracle Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        raise

# ========== CONNECTION POOL EVENTS ==========
@event.listens_for(Engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Verify Oracle connection"""
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        cursor.close()
    except Exception as e:
        logger.warning(f"Connection verification failed: {e}")

@event.listens_for(Engine, "pool_pre_ping")
def receive_pool_pre_ping(dbapi_conn, connection_record, connection_proxy):
    """Health check before connection reuse"""
    try:
        cursor = dbapi_conn.cursor()
        cursor.execute("SELECT 1 FROM DUAL")
        cursor.close()
    except Exception as e:
        logger.warning(f"Pool health check failed: {e}")
        return False
    return True

# ========== ORACLE UTILITIES ==========
def create_sequence(seq_name: str, start_value: int = 1):
    """Create Oracle sequence for auto-increment"""
    with engine.connect() as conn:
        try:
            conn.execute(text(f"""
                CREATE SEQUENCE {seq_name}_seq 
                START WITH {start_value} 
                INCREMENT BY 1 
                NOCACHE
            """))
            conn.commit()
            logger.info(f"✅ Sequence created: {seq_name}_seq")
        except Exception as e:
            logger.warning(f"Sequence creation: {e}")

def get_next_sequence_value(seq_name: str) -> int:
    """Get next sequence value from Oracle"""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT {seq_name}_seq.NEXTVAL FROM DUAL"))
        return result.scalar()

# ========== HEALTH CHECK ==========
def health_check():
    """Check database and cache health"""
    results = {
        "database": False,
        "redis": False,
        "timestamp": None
    }
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM DUAL"))
            results["database"] = True
            logger.info("✅ Database health check passed")
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
    
    if redis_client:
        try:
            redis_client.ping()
            results["redis"] = True
            logger.info("✅ Redis health check passed")
        except Exception as e:
            logger.error(f"❌ Redis health check failed: {e}")
    
    from datetime import datetime
    results["timestamp"] = datetime.utcnow().isoformat()
    return results
