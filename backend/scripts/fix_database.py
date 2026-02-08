#!/usr/bin/env python3
"""
Script de réparation automatique de la base de données NéoBot
"""
import subprocess
import sys
import time
import os

def run_command(cmd, description):
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - SUCCÈS")
            return True
        else:
            print(f"⚠️  {description} - Attention: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} - Erreur: {e}")
        return False

def main():
    print("🚀 DÉMARRAGE DE LA RÉPARATION AUTOMATIQUE NÉOBOT")
    print("=" * 60)
    
    # 1. Arrêter les services
    run_command("pkill -f uvicorn", "Arrêt des services en cours")
    time.sleep(2)
    
    # 2. Redémarrer PostgreSQL
    run_command("sudo systemctl restart postgresql", "Redémarrage PostgreSQL")
    time.sleep(3)
    
    # 3. Vérifier PostgreSQL
    run_command("sudo systemctl status postgresql", "Statut PostgreSQL")
    run_command("pg_isready", "Test connexion PostgreSQL")
    
    # 4. RÉPARATION CRITIQUE - Réinitialiser le mot de passe et permissions
    repair_commands = [
        "sudo -u postgres psql -c \"ALTER USER neobot WITH PASSWORD 'neobot123';\"",
        "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE neobot TO neobot;\"",
        "sudo -u postgres psql -c \"ALTER DATABASE neobot OWNER TO neobot;\"",
        "sudo -u postgres psql -c \"\\l\" | grep neobot"
    ]
    
    for cmd in repair_commands:
        run_command(cmd, "Réparation DB")
    
    # 5. Tester la connexion depuis Python
    print("🧪 Test de connexion depuis l'application...")
    try:
        # Test direct de connexion
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="neobot", 
            user="neobot",
            password="neobot123"
        )
        conn.close()
        print("✅ Connexion PostgreSQL directe réussie!")
        
        # Test via SQLAlchemy
        from app.database import test_connection
        if test_connection():
            print("✅ Connexion SQLAlchemy réussie!")
        else:
            print("❌ Échec connexion SQLAlchemy")
            
    except Exception as e:
        print(f"❌ Erreur de test: {e}")
    
    print("🎯 RÉPARATION TERMINÉE!")

if __name__ == "__main__":
    main()
