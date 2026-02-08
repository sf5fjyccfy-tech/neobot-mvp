#!/usr/bin/env python3
"""
Script de démarrage robuste du serveur NéoBot
"""
import subprocess
import sys
import time
import requests

def check_dependencies():
    print("🔍 Vérification des dépendances...")
    
    # Vérifier PostgreSQL
    result = subprocess.run("pg_isready", shell=True, capture_output=True)
    if result.returncode != 0:
        print("❌ PostgreSQL n'est pas prêt - démarrage...")
        subprocess.run("sudo systemctl start postgresql", shell=True)
        time.sleep(3)
    
    # Vérifier la connexion DB
    try:
        from app.database import test_connection
        if test_connection():
            print("✅ Connexion DB OK")
            return True
        else:
            print("❌ Échec connexion DB - tentative de réparation...")
            # Lancer la réparation automatique
            subprocess.run("python3 scripts/fix_database.py", shell=True)
            time.sleep(2)
            return test_connection()  # Retester après réparation
    except Exception as e:
        print(f"❌ Erreur vérification DB: {e}")
        return False

def start_server():
    print("🚀 DÉMARRAGE DU SERVEUR NÉOBOT AVEC FALLBACK INTELLIGENT")
    print("=" * 60)
    
    if not check_dependencies():
        print("⚠️  Dépendances problématiques, mais démarrage quand même...")
    
    # Démarrer uvicorn avec gestion d'erreurs
    cmd = [
        "uvicorn", "app.main:app", 
        "--reload", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--log-level", "info"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Serveur arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur serveur: {e}")

if __name__ == "__main__":
    start_server()
