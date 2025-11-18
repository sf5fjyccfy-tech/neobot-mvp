from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Utiliser la variable d'environnement ou une valeur par défaut
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://neobot:password@localhost:5432/neobot"
)

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialiser la base de données"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Base de données initialisée")
    except Exception as e:
        print(f"❌ Erreur initialisation DB: {e}")
