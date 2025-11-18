"""
Script pour ajouter les champs manquants à la table products
"""
from app.database import SessionLocal, engine
from sqlalchemy import text

def add_missing_columns():
    print("🔄 Ajout des champs manquants...")
    
    with engine.connect() as conn:
        try:
            # Vérifier et ajouter 'category'
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='category'
            """))
            
            if not result.fetchone():
                print("➕ Ajout de 'category'...")
                conn.execute(text("ALTER TABLE products ADD COLUMN category VARCHAR(100) DEFAULT 'vêtements'"))
            
            # Vérifier et ajouter 'images'
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='images'
            """))
            
            if not result.fetchone():
                print("➕ Ajout de 'images'...")
                conn.execute(text("ALTER TABLE products ADD COLUMN images JSON"))
                
            # Vérifier et ajouter 'is_active'
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='is_active'
            """))
            
            if not result.fetchone():
                print("➕ Ajout de 'is_active'...")
                conn.execute(text("ALTER TABLE products ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
            
            conn.commit()
            print("✅ Champs ajoutés avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            conn.rollback()

if __name__ == "__main__":
    add_missing_columns()
