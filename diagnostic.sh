
# [#!/usr/bin/env python3
"""
Script de diagnostic et nettoyage NéoBot V2
Usage: python diagnostic_neobot.py
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

class NeoBotDiagnostic:
    def __init__(self):
        self.root = Path.cwd()
        self.issues = []
        self.successes = []
        self.warnings = []
        
    def header(self, text):
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def check(self, name, condition, success_msg, error_msg):
        """Vérifier une condition et logger"""
        if condition:
            self.successes.append(f"✅ {name}: {success_msg}")
            print(f"✅ {name}: {success_msg}")
            return True
        else:
            self.issues.append(f"❌ {name}: {error_msg}")
            print(f"❌ {name}: {error_msg}")
            return False
    
    def warn(self, name, message):
        """Avertissement"""
        self.warnings.append(f"⚠️  {name}: {message}")
        print(f"⚠️  {name}: {message}")
    
    # ===== VÉRIFICATIONS STRUCTURE =====
    
    def check_structure(self):
        self.header("1. VÉRIFICATION STRUCTURE PROJET")
        
        # Fichiers backend essentiels
        backend_files = {
            "backend/app/main.py": "API principale",
            "backend/app/models.py": "Modèles base de données",
            "backend/app/database.py": "Configuration DB",
            "backend/requirements.txt": "Dépendances Python",
            "docker-compose.yml": "Services Docker"
        }
        
        for file_path, description in backend_files.items():
            exists = (self.root / file_path).exists()
            self.check(
                description,
                exists,
                f"Présent ({file_path})",
                f"MANQUANT: {file_path}"
            )
        
        # Fichiers inutiles à supprimer
        junk_patterns = [
            "script*.sh",
            "fix_*.sh",
            "test_*.sh",
            "*.save",
            "*.save.*",
            ".env.backup.*"
        ]
        
        print("\n🗑️  FICHIERS INUTILES DÉTECTÉS:")
        junk_found = False
        for pattern in junk_patterns:
            files = list(self.root.glob(pattern))
            if files:
                junk_found = True
                for f in files:
                    print(f"   - {f.name}")
        
        if not junk_found:
            print("   Aucun fichier inutile détecté")
        
        return junk_found
    
    # ===== VÉRIFICATIONS CODE =====
    
    def check_models_completeness(self):
        self.header("2. VÉRIFICATION MODELS.PY")
        
        models_file = self.root / "backend/app/models.py"
        if not models_file.exists():
            self.check("models.py", False, "", "Fichier introuvable")
            return False
        
        content = models_file.read_text()
        
        # Vérifier imports critiques
        required_imports = {
            "from cryptography.fernet import Fernet": "Chiffrement tokens",
            "import os": "Variables d'environnement"
        }
        
        for imp, desc in required_imports.items():
            present = imp in content
            self.check(
                f"Import {desc}",
                present,
                "Présent",
                f"MANQUANT: {imp}"
            )
        
        # Vérifier méthodes Tenant
        required_methods = [
            "set_whatsapp_tokens",
            "get_whatsapp_tokens",
            "clear_whatsapp_tokens",
            "has_valid_whatsapp_config"
        ]
        
        for method in required_methods:
            present = f"def {method}" in content
            self.check(
                f"Méthode Tenant.{method}",
                present,
                "Implémentée",
                f"MANQUANTE - API crashera"
            )
        
        return all(f"def {m}" in content for m in required_methods)
    
    # ===== VÉRIFICATIONS DÉPENDANCES =====
    
    def check_dependencies(self):
        self.header("3. VÉRIFICATION DÉPENDANCES")
        
        req_file = self.root / "backend/requirements.txt"
        if not req_file.exists():
            self.check("requirements.txt", False, "", "Fichier introuvable")
            return False
        
        content = req_file.read_text()
        
        # Dépendances critiques
        required_deps = {
            "fastapi": "Framework API principal",
            "uvicorn": "Serveur ASGI",
            "cryptography": "Chiffrement tokens WhatsApp",
            "redis": "Cache et sessions",
            "sqlalchemy": "ORM base de données",
            "psycopg2-binary": "Driver PostgreSQL",
            "python-dotenv": "Variables d'environnement",
            "pydantic": "Validation données"
        }
        
        installed = {}
        for dep, desc in required_deps.items():
            present = dep in content.lower()
            installed[dep] = present
            self.check(
                desc,
                present,
                f"{dep} installé",
                f"MANQUANT: pip install {dep}"
            )
        
        # Vérifier conflits
        if "flask" in content.lower():
            self.warn(
                "Conflit Flask/FastAPI",
                "Flask détecté avec FastAPI - Supprimer Flask"
            )
        
        return all(installed.values())
    
    # ===== VÉRIFICATIONS DOCKER =====
    
    def check_docker(self):
        self.header("4. VÉRIFICATION DOCKER")
        
        # Vérifier docker-compose.yml
        compose_file = self.root / "docker-compose.yml"
        self.check(
            "docker-compose.yml",
            compose_file.exists(),
            "Fichier présent",
            "Fichier introuvable"
        )
        
        # Vérifier si Docker est installé
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            docker_installed = result.returncode == 0
            self.check(
                "Docker installé",
                docker_installed,
                result.stdout.strip(),
                "Docker non installé"
            )
        except Exception as e:
            self.check("Docker installé", False, "", f"Erreur: {e}")
            return False
        
        # Vérifier si les containers tournent
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            containers = result.stdout.strip().split("\n")
            
            postgres_running = "neobot_postgres" in containers
            redis_running = "neobot_redis" in containers
            
            self.check(
                "PostgreSQL container",
                postgres_running,
                "En cours d'exécution",
                "Container arrêté - Lancer: docker-compose up -d"
            )
            
            self.check(
                "Redis container",
                redis_running,
                "En cours d'exécution",
                "Container arrêté - Lancer: docker-compose up -d"
            )
            
            return postgres_running and redis_running
            
        except Exception as e:
            self.warn("Docker containers", f"Impossible de vérifier: {e}")
            return False
    
    # ===== VÉRIFICATIONS BASE DE DONNÉES =====
    
    def check_database(self):
        self.header("5. VÉRIFICATION BASE DE DONNÉES")
        
        try:
            # Tenter de se connecter
            import psycopg2
            conn = psycopg2.connect(
                dbname="neobot",
                user="neobot",
                password="password123",
                host="localhost",
                port="5432"
            )
            cursor = conn.cursor()
            
            self.check(
                "Connexion PostgreSQL",
                True,
                "Connexion réussie",
                ""
            )
            
            # Vérifier tables
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ["tenants", "conversations", "messages", "whatsapp_sessions"]
            for table in required_tables:
                exists = table in tables
                self.check(
                    f"Table {table}",
                    exists,
                    "Existe",
                    "MANQUANTE - Lancer migrations"
                )
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            self.check(
                "Connexion PostgreSQL",
                False,
                "",
                f"ERREUR: {e}"
            )
            return False
    
    # ===== VÉRIFICATIONS API =====
    
    def check_api(self):
        self.header("6. VÉRIFICATION API")
        
        # Vérifier si l'API tourne
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=2)
            api_running = response.status_code == 200
            
            if api_running:
                data = response.json()
                self.check(
                    "API FastAPI",
                    True,
                    f"En ligne - Status: {data.get('status', 'unknown')}",
                    ""
                )
            else:
                self.check(
                    "API FastAPI",
                    False,
                    "",
                    f"Réponse HTTP {response.status_code}"
                )
        except Exception as e:
            self.check(
                "API FastAPI",
                False,
                "",
                f"API non accessible - Lancer: cd backend && uvicorn app.main:app --reload"
            )
            return False
        
        # Tester endpoints critiques
        endpoints = {
            "/": "Root endpoint",
            "/health": "Health check",
            "/api/plans": "Liste des plans"
        }
        
        for path, desc in endpoints.items():
            try:
                response = requests.get(f"http://localhost:8000{path}", timeout=2)
                self.check(
                    f"Endpoint {path}",
                    response.status_code == 200,
                    f"{desc} OK",
                    f"Erreur HTTP {response.status_code}"
                )
            except Exception as e:
                self.check(
                    f"Endpoint {path}",
                    False,
                    "",
                    f"Erreur: {e}"
                )
        
        return True
    
    # ===== GÉNÉRATION RAPPORT =====
    
    def generate_report(self):
        self.header("📊 RAPPORT FINAL")
        
        total_checks = len(self.successes) + len(self.issues)
        success_rate = (len(self.successes) / total_checks * 100) if total_checks > 0 else 0
        
        print(f"\n📈 STATISTIQUES:")
        print(f"   ✅ Succès: {len(self.successes)}")
        print(f"   ❌ Erreurs: {len(self.issues)}")
        print(f"   ⚠️  Avertissements: {len(self.warnings)}")
        print(f"   📊 Taux de réussite: {success_rate:.1f}%")
        
        if self.issues:
            print(f"\n❌ PROBLÈMES CRITIQUES À CORRIGER:")
            for issue in self.issues:
                print(f"   {issue}")
        
        if self.warnings:
            print(f"\n⚠️  AVERTISSEMENTS:")
            for warning in self.warnings:
                print(f"   {warning}")
        
        # Sauvegarder rapport JSON
        report = {
            "timestamp": datetime.now().isoformat(),
            "success_rate": success_rate,
            "successes": self.successes,
            "issues": self.issues,
            "warnings": self.warnings
        }
        
        report_file = self.root / "diagnostic_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Rapport sauvegardé: {report_file}")
        
        return success_rate > 75
    
    # ===== EXÉCUTION COMPLÈTE =====
    
    def run_full_diagnostic(self):
        print("\n🔍 DIAGNOSTIC NEOBOT V2")
        print(f"📁 Dossier: {self.root}")
        print(f"🕐 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Exécuter toutes les vérifications
        self.check_structure()
        self.check_models_completeness()
        self.check_dependencies()
        self.check_docker()
        self.check_database()
        self.check_api()
        
        # Générer rapport final
        success = self.generate_report()
        
        if success:
            print("\n✅ DIAGNOSTIC GLOBAL: SYSTÈME OPÉRATIONNEL")
        else:
            print("\n❌ DIAGNOSTIC GLOBAL: CORRECTIONS NÉCESSAIRES")
        
        return success

# ===== SCRIPT DE NETTOYAGE =====

def cleanup_project():
    """Nettoyer les fichiers inutiles"""
    print("\n🧹 NETTOYAGE PROJET")
    
    root = Path.cwd()
    
    # Patterns à supprimer
    patterns_to_remove = [
        "script1_*.sh",
        "script2_*.sh",
        "script3_*.sh",
        "script4_*.sh",
        "script5_*.sh",
        "fix_*.sh",
        "test_*.sh",
        "update_*.sh",
        "verify_*.sh",
        "*.save",
        "*.save.*",
        ".env.backup.*"
    ]
    
    files_removed = []
    for pattern in patterns_to_remove:
        for file in root.glob(pattern):
            if file.is_file():
                print(f"🗑️  Suppression: {file.name}")
                file.unlink()
                files_removed.append(file.name)
    
    # Supprimer dossiers inutiles
    dirs_to_remove = [
        "backup_*",
        "backups"
    ]
    
    for pattern in dirs_to_remove:
        for dir_path in root.glob(pattern):
            if dir_path.is_dir():
                print(f"🗑️  Suppression dossier: {dir_path.name}")
                import shutil
                shutil.rmtree(dir_path)
                files_removed.append(f"{dir_path.name}/")
    
    if files_removed:
        print(f"\n✅ {len(files_removed)} éléments supprimés")
    else:
        print("\n✅ Aucun fichier inutile trouvé")
    
    return len(files_removed)

# ===== MAIN =====

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Diagnostic NéoBot V2")
    parser.add_argument("--cleanup", action="store_true", help="Nettoyer les fichiers inutiles")
    parser.add_argument("--full", action="store_true", help="Diagnostic complet")
    
    args = parser.parse_args()
    
    if args.cleanup:
        cleanup_project()
    elif args.full or len(sys.argv) == 1:
        diagnostic = NeoBotDiagnostic()
        diagnostic.run_full_diagnostic()
    else:
        parser.print_help()]

