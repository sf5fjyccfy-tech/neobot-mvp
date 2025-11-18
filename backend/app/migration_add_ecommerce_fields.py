"""
Migration pour ajouter les champs e-commerce à la table products existante
"""
from app.database import engine
from sqlalchemy import text

def migrate_products_table():
    print("🔄 Migration de la table products...")
    
    # Ajouter la colonne category si elle n'existe pas
    with engine.connect() as conn:
        try:
            # Vérifier si category existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='category'
            """))
            
            if not result.fetchone():
                print("➕ Ajout de la colonne 'category'...")
                conn.execute(text("ALTER TABLE products ADD COLUMN category VARCHAR(100) DEFAULT 'vêtements'"))
                conn.commit()
            
            # Vérifier si images existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='images'
            """))
            
            if not result.fetchone():
                print("➕ Ajout de la colonne 'images'...")
                conn.execute(text("ALTER TABLE products ADD COLUMN images JSON"))
                conn.commit()
                
            # Vérifier si is_active existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='is_active'
            """))
            
            if not result.fetchone():
                print("➕ Ajout de la colonne 'is_active'...")
                conn.execute(text("ALTER TABLE products ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
                conn.commit()
                
            print("✅ Migration terminée avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur migration: {e}")

if __name__ == "__main__":
    migrate_products_table()
