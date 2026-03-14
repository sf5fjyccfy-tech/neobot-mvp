#!/usr/bin/env python3
"""
🔍 DIAGNOSTIC SYSTÈME COMPLET - NéoBot
Vérifie cohérence & synergie de TOUS les composants avant déploiement
Created: 11 Mars 2026
"""

import os
import sys
import json
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemDiagnostic:
    """Complete system diagnostic before deployment"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.utcnow().isoformat(),
            "components": {},
            "integration": {},
            "database": {},
            "issues": [],
            "recommendations": [],
            "overall_status": "UNKNOWN"
        }
        self.base_path = Path("/home/tim/neobot-mvp")
    
    # ========== PART 1: COMPONENT VERIFICATION ==========
    def check_backend(self) -> Dict:
        """Vérifier Backend API"""
        logger.info("\n" + "="*60)
        logger.info("1️⃣  CHECKING BACKEND API")
        logger.info("="*60)
        
        results = {
            "status": "UNKNOWN",
            "checks": {},
            "details": []
        }
        
        backend_dir = self.base_path / "backend"
        
        # Check 1: Dockerfile exists
        dockerfile = backend_dir / "Dockerfile.prod"
        results["checks"]["dockerfile"] = "✅" if dockerfile.exists() else "❌ NOT FOUND"
        logger.info(f"   Dockerfile.prod: {results['checks']['dockerfile']}")
        
        # Check 2: requirements.txt exists
        requirements = backend_dir / "requirements.txt"
        results["checks"]["requirements"] = "✅" if requirements.exists() else "❌ NOT FOUND"
        logger.info(f"   requirements.txt: {results['checks']['requirements']}")
        
        # Check 3: main app structure
        app_dir = backend_dir / "app"
        app_files = {
            "database.py": "Database config",
            "main.py": "FastAPI app",
            "models.py": "SQLAlchemy models"
        }
        
        for filename, desc in app_files.items():
            exists = (app_dir / filename).exists()
            results["checks"][f"app_{filename}"] = "✅" if exists else "❌"
            logger.info(f"   app/{filename} ({desc}): {'✅' if exists else '❌'}")
        
        # Check 4: Routers exist
        routers_dir = app_dir / "routers"
        if routers_dir.exists():
            routers = list(routers_dir.glob("*.py"))
            logger.info(f"   Routers found: {len(routers)} files")
            results["checks"]["routers"] = f"✅ {len(routers)} routers"
        else:
            results["checks"]["routers"] = "❌ Not found"
        
        # Check 5: Services exist
        services_dir = app_dir / "services"
        if services_dir.exists():
            services = list(services_dir.glob("*.py"))
            logger.info(f"   Services found: {len(services)} files")
            results["checks"]["services"] = f"✅ {len(services)} services"
        else:
            results["checks"]["services"] = "❌ Not found"
        
        # Check 6: Environment files
        env_files = ["requirements.txt", ".env.example", ".env.production.example"]
        for env_file in env_files:
            exists = (backend_dir / env_file).exists()
            results["checks"][env_file] = "✅" if exists else "❌"
            logger.info(f"   {env_file}: {'✅' if exists else '❌'}")
        
        # Check 7: Try to import models
        try:
            sys.path.insert(0, str(backend_dir))
            from app.models import Tenant, Contact, Conversation, Message
            results["checks"]["models_import"] = "✅ Can import"
            logger.info(f"   Models import: ✅ Success")
            results["details"].append("Models: Tenant, Contact, Conversation, Message")
        except Exception as e:
            results["checks"]["models_import"] = f"❌ {str(e)[:50]}"
            logger.error(f"   Models import: ❌ {e}")
            self.results["issues"].append(f"Backend models import failed: {e}")
        
        # Overall status
        passed = sum(1 for v in results["checks"].values() if "✅" in str(v))
        total = len(results["checks"])
        results["status"] = "✅ PASS" if passed >= total * 0.8 else "⚠️  WARNING"
        
        logger.info(f"\n   Backend Status: {results['status']} ({passed}/{total} checks)")
        self.results["components"]["backend"] = results
        return results
    
    def check_frontend(self) -> Dict:
        """Vérifier Frontend React"""
        logger.info("\n" + "="*60)
        logger.info("2️⃣  CHECKING FRONTEND")
        logger.info("="*60)
        
        results = {
            "status": "UNKNOWN",
            "checks": {},
            "details": []
        }
        
        frontend_dir = self.base_path / "frontend"
        
        # Check 1: Dockerfile
        dockerfile = frontend_dir / "Dockerfile.prod"
        results["checks"]["dockerfile"] = "✅" if dockerfile.exists() else "❌"
        logger.info(f"   Dockerfile.prod: {'✅' if dockerfile.exists() else '❌'}")
        
        # Check 2: Next.js config
        next_config = frontend_dir / "next.config.js"
        results["checks"]["next_config"] = "✅" if next_config.exists() else "⚠️"
        logger.info(f"   next.config.js: {'✅' if next_config.exists() else '⚠️'}")
        
        # Check 3: package.json
        package_json = frontend_dir / "package.json"
        results["checks"]["package_json"] = "✅" if package_json.exists() else "❌"
        logger.info(f"   package.json: {'✅' if package_json.exists() else '❌'}")
        
        # Check 4: src directory
        src_dir = frontend_dir / "src"
        if src_dir.exists():
            components = list(src_dir.rglob("*.tsx")) + list(src_dir.rglob("*.ts"))
            logger.info(f"   Components/Files: {len(components)} files")
            results["checks"]["src_structure"] = f"✅ {len(components)} files"
        else:
            results["checks"]["src_structure"] = "❌"
        
        # Check 5: TailwindCSS config
        tailwind = frontend_dir / "tailwind.config.js"
        results["checks"]["tailwind"] = "✅" if tailwind.exists() else "⚠️"
        logger.info(f"   tailwind.config.js: {'✅' if tailwind.exists() else '⚠️'}")
        
        # Check 6: Environment files
        env_prod = frontend_dir / ".env.production"
        results["checks"]["env_production"] = "✅" if env_prod.exists() else "⚠️ Missing"
        logger.info(f"   .env.production: {'✅' if env_prod.exists() else '⚠️ Missing'}")
        
        passed = sum(1 for v in results["checks"].values() if "✅" in str(v))
        total = len(results["checks"])
        results["status"] = "✅ PASS" if passed >= total * 0.8 else "⚠️ WARNING"
        
        logger.info(f"\n   Frontend Status: {results['status']} ({passed}/{total} checks)")
        self.results["components"]["frontend"] = results
        return results
    
    def check_whatsapp_service(self) -> Dict:
        """Vérifier Service WhatsApp"""
        logger.info("\n" + "="*60)
        logger.info("3️⃣  CHECKING WHATSAPP SERVICE")
        logger.info("="*60)
        
        results = {
            "status": "UNKNOWN",
            "checks": {},
            "details": []
        }
        
        wa_dir = self.base_path / "whatsapp-service"
        
        # Check 1: Dockerfile
        dockerfile = wa_dir / "Dockerfile.prod"
        results["checks"]["dockerfile"] = "✅" if dockerfile.exists() else "❌"
        logger.info(f"   Dockerfile.prod: {'✅' if dockerfile.exists() else '❌'}")
        
        # Check 2: package.json
        package_json = wa_dir / "package.json"
        results["checks"]["package_json"] = "✅" if package_json.exists() else "❌"
        logger.info(f"   package.json: {'✅' if package_json.exists() else '❌'}")
        
        # Check 3: main service file
        main_files = ["index.js", "index_intelligent.js", "baileys-phase8m.js"]
        main_exists = any((wa_dir / f).exists() for f in main_files)
        results["checks"]["main_service"] = "✅" if main_exists else "❌"
        logger.info(f"   Main service file: {'✅' if main_exists else '❌'}")
        
        # Check 4: Baileys dependency
        if package_json.exists():
            with open(package_json) as f:
                try:
                    pkg = json.load(f)
                    has_baileys = "baileys" in pkg.get("dependencies", {})
                    results["checks"]["baileys_dep"] = "✅" if has_baileys else "❌ Missing"
                    logger.info(f"   Baileys dependency: {'✅' if has_baileys else '❌'}")
                except:
                    results["checks"]["baileys_dep"] = "⚠️ Cannot parse"
        
        # Check 5: Start script
        if package_json.exists():
            with open(package_json) as f:
                try:
                    pkg = json.load(f)
                    has_start = "start" in pkg.get("scripts", {})
                    results["checks"]["start_script"] = "✅" if has_start else "⚠️"
                    logger.info(f"   Start script: {'✅' if has_start else '⚠️'}")
                except:
                    pass
        
        # Check 6: Environment
        env_file = wa_dir / ".env.example"
        results["checks"]["env_example"] = "✅" if env_file.exists() else "⚠️"
        logger.info(f"   .env.example: {'✅' if env_file.exists() else '⚠️'}")
        
        passed = sum(1 for v in results["checks"].values() if "✅" in str(v))
        total = len(results["checks"])
        results["status"] = "✅ PASS" if passed >= total * 0.7 else "⚠️ WARNING"
        
        logger.info(f"\n   WhatsApp Status: {results['status']} ({passed}/{total} checks)")
        self.results["components"]["whatsapp"] = results
        return results
    
    # ========== PART 2: INTEGRATION CHECKS ==========
    def check_integration(self) -> Dict:
        """Vérifier intégration entre services"""
        logger.info("\n" + "="*60)
        logger.info("🔗 INTEGRATION CHECKS")
        logger.info("="*60)
        
        results = {
            "status": "UNKNOWN",
            "checks": {}
        }
        
        # Check 1: Backend-Frontend API contract
        logger.info("\n   1. Backend-Frontend API Contract")
        backend_main = self.base_path / "backend" / "app" / "main.py"
        frontend_api = list(self.base_path.glob("frontend/src/**/*api*"))
        
        api_ok = backend_main.exists() and len(frontend_api) > 0
        results["checks"]["api_contract"] = "✅" if api_ok else "❌"
        logger.info(f"      API endpoints defined: {'✅' if backend_main.exists() else '❌'}")
        logger.info(f"      Frontend API client: {'✅' if len(frontend_api) > 0 else '❌'}")
        
        # Check 2: Backend-WhatsApp integration
        logger.info("\n   2. Backend-WhatsApp Integration")
        whatsapp_service = self.base_path / "whatsapp-service" / "index.js"
        backend_webhooks = list(self.base_path.glob("backend/app/routers/**/*whatsapp*"))
        
        wa_ok = whatsapp_service.exists() and len(backend_webhooks) > 0
        results["checks"]["whatsapp_integration"] = "✅" if wa_ok else "❌"
        logger.info(f"      WhatsApp service exists: {'✅' if whatsapp_service.exists() else '❌'}")
        logger.info(f"      WhatsApp webhook endpoints: {'✅' if len(backend_webhooks) > 0 else '❌'}")
        
        # Check 3: Database models consistency
        logger.info("\n   3. Database Models Consistency")
        try:
            sys.path.insert(0, str(self.base_path / "backend"))
            from app.models import Base
            
            # Get all models
            models = [mapper.class_ for mapper in Base.registry.mappers]
            model_names = [m.__name__ for m in models]
            
            required_models = ["Tenant", "Contact", "Conversation", "Message", "User"]
            missing = [m for m in required_models if m not in model_names]
            
            results["checks"]["models"] = "✅" if not missing else f"⚠️ Missing: {missing}"
            logger.info(f"      Models found: {len(model_names)} ({', '.join(model_names[:5])}...)")
            if missing:
                logger.warning(f"      Missing models: {missing}")
        except Exception as e:
            results["checks"]["models"] = f"❌ Error: {str(e)[:40]}"
            logger.error(f"      Error checking models: {e}")
        
        # Check 4: Environment variable consistency
        logger.info("\n   4. Environment Configuration")
        env_files = [
            self.base_path / "backend" / ".env.example",
            self.base_path / "frontend" / ".env.example",
            self.base_path / "whatsapp-service" / ".env.example"
        ]
        
        env_ok = sum(1 for f in env_files if f.exists())
        results["checks"]["env_files"] = f"✅ {env_ok}/3" if env_ok >= 2 else f"⚠️ {env_ok}/3"
        logger.info(f"      Environment files: {env_ok}/3 services configured")
        
        # Check 5: Docker setup
        logger.info("\n   5. Docker Configuration")
        docker_compose = self.base_path / "docker-compose.yml"
        docker_compose_oracle = self.base_path / "docker-compose.oracle.yml"
        
        docker_ok = docker_compose.exists() or docker_compose_oracle.exists()
        results["checks"]["docker"] = "✅" if docker_ok else "⚠️"
        logger.info(f"      docker-compose.yml: {'✅' if docker_compose.exists() else '❌'}")
        logger.info(f"      docker-compose.oracle.yml: {'✅' if docker_compose_oracle.exists() else '✅ (Oracle)'}")
        
        passed = sum(1 for v in results["checks"].values() if "✅" in str(v))
        total = len(results["checks"])
        results["status"] = "✅ PASS" if passed >= total * 0.8 else "⚠️ WARNING"
        
        logger.info(f"\n   Integration Status: {results['status']} ({passed}/{total} checks)")
        self.results["integration"] = results
        return results
    
    # ========== PART 3: DATABASE CHECKS ==========
    def check_database(self) -> Dict:
        """Vérifier base de données"""
        logger.info("\n" + "="*60)
        logger.info("🗄️  DATABASE CHECKS")
        logger.info("="*60)
        
        results = {
            "status": "UNKNOWN",
            "checks": {}
        }
        
        # Check 1: PostgreSQL running
        logger.info("\n   1. PostgreSQL Connection")
        try:
            result = subprocess.run(
                ["pg_isready", "-h", "localhost"],
                capture_output=True,
                timeout=5
            )
            pg_ok = result.returncode == 0
            results["checks"]["postgresql"] = "✅" if pg_ok else "❌"
            logger.info(f"      PostgreSQL running: {'✅' if pg_ok else '❌'}")
        except Exception as e:
            results["checks"]["postgresql"] = "❌"
            logger.warning(f"      PostgreSQL check failed: {e}")
        
        # Check 2: Database migrations
        logger.info("\n   2. Database Migrations")
        alembic_dir = self.base_path / "backend" / "alembic"
        migrations_exist = alembic_dir.exists()
        results["checks"]["migrations"] = "✅" if migrations_exist else "⚠️"
        logger.info(f"      Alembic configured: {'✅' if migrations_exist else '⚠️'}")
        
        # Check 3: Models & schema
        logger.info("\n   3. Database Schema")
        try:
            sys.path.insert(0, str(self.base_path / "backend"))
            from app.database import engine, Base
            
            # Try to count tables
            inspector_sql = "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public'"
            try:
                conn = engine.connect()
                result = conn.execute(inspector_sql)
                table_count = result.scalar()
                results["checks"]["tables"] = f"✅ {table_count} tables"
                logger.info(f"      Tables in database: {table_count}")
                conn.close()
            except:
                results["checks"]["tables"] = "⚠️ Cannot connect"
        except Exception as e:
            results["checks"]["tables"] = f"⚠️ {str(e)[:30]}"
        
        passed = sum(1 for v in results["checks"].values() if "✅" in str(v))
        total = len(results["checks"])
        results["status"] = "✅ PASS" if passed >= total * 0.7 else "⚠️ WARNING"
        
        logger.info(f"\n   Database Status: {results['status']} ({passed}/{total} checks)")
        self.results["database"] = results
        return results
    
    # ========== PART 4: FEATURES CHECK ==========
    def check_features(self) -> Dict:
        """Vérifier les features (paiement, dashboard, vitrine)"""
        logger.info("\n" + "="*60)
        logger.info("✨ FEATURES CHECK")
        logger.info("="*60)
        
        results = {
            "features": {}
        }
        
        # Check 1: Payment system
        logger.info("\n   1. Payment System")
        payment_files = list(self.base_path.rglob("*payment*")) + list(self.base_path.rglob("*stripe*")) + list(self.base_path.rglob("*paypal*"))
        
        payment_ok = len(payment_files) > 0
        results["features"]["payment"] = {
            "status": "✅ Found" if payment_ok else "⚠️ Not configured",
            "files": len(payment_files)
        }
        logger.info(f"      Payment integration: {'✅ Found' if payment_ok else '⚠️ Not configured'}")
        
        # Check 2: Dashboard
        logger.info("\n   2. Dashboard")
        dashboard_files = list(self.base_path.rglob("*dashboard*"))
        dashboard_ok = len(dashboard_files) > 0
        results["features"]["dashboard"] = {
            "status": "✅ Found" if dashboard_ok else "⚠️ Not found",
            "files": len(dashboard_files)
        }
        logger.info(f"      Dashboard: {'✅ Found' if dashboard_ok else '⚠️ Not found'}")
        
        # Check 3: Landing page / site vitrine
        logger.info("\n   3. Landing Page / Site Vitrine")
        landing_files = list(self.base_path.rglob("*landing*")) + list(self.base_path.rglob("*home*")) + list(self.base_path.rglob("*index*"))
        landing_ok = len(landing_files) > 0
        results["features"]["landing"] = {
            "status": "✅ Found" if landing_ok else "⚠️ Not found",
            "files": len(landing_files)
        }
        logger.info(f"      Landing page: {'✅ Found' if landing_ok else '⚠️ Not found'}")
        
        # Check 4: Admin panel
        logger.info("\n   4. Admin Panel")
        admin_files = list(self.base_path.rglob("*admin*"))
        admin_ok = len(admin_files) > 0
        results["features"]["admin"] = {
            "status": "✅ Found" if admin_ok else "⚠️ Not found",
            "files": len(admin_files)
        }
        logger.info(f"      Admin panel: {'✅ Found' if admin_ok else '⚠️ Not found'}")
        
        self.results["features"] = results
        return results
    
    # ========== GENERATE REPORT ==========
    def generate_report(self) -> None:
        """Generate complete diagnostic report"""
        logger.info("\n" + "="*60)
        logger.info("📋 DIAGNOSTIC SUMMARY")
        logger.info("="*60)
        
        # Count overall status
        issues = len(self.results["issues"])
        components_ok = all("PASS" in str(v.get("status", "")) for v in self.results["components"].values())
        integration_ok = "PASS" in str(self.results["integration"].get("status", ""))
        database_ok = "PASS" in str(self.results["database"].get("status", ""))
        
        overall = "✅ READY FOR DEPLOYMENT" if (components_ok and integration_ok and database_ok and issues == 0) else "⚠️ REVIEW REQUIRED"
        
        self.results["overall_status"] = overall
        
        logger.info(f"\nBackend:       {self.results['components'].get('backend', {}).get('status', 'UNKNOWN')}")
        logger.info(f"Frontend:      {self.results['components'].get('frontend', {}).get('status', 'UNKNOWN')}")
        logger.info(f"WhatsApp:      {self.results['components'].get('whatsapp', {}).get('status', 'UNKNOWN')}")
        logger.info(f"Integration:   {self.results['integration'].get('status', 'UNKNOWN')}")
        logger.info(f"Database:      {self.results['database'].get('status', 'UNKNOWN')}")
        
        logger.info(f"\n🎯 OVERALL STATUS: {overall}")
        
        if self.results["issues"]:
            logger.warning(f"\n⚠️  ISSUES FOUND ({len(self.results['issues'])}):")
            for issue in self.results["issues"]:
                logger.warning(f"   - {issue}")
        
        if self.results["recommendations"]:
            logger.info(f"\n💡 RECOMMENDATIONS ({len(self.results['recommendations'])}):")
            for rec in self.results["recommendations"]:
                logger.info(f"   - {rec}")
        
        # Save report
        report_file = self.base_path / f"diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n📄 Full report saved: {report_file}")
    
    # ========== MAIN EXECUTE ==========
    def execute(self) -> bool:
        """Run complete diagnostic"""
        logger.info("\n" + "="*60)
        logger.info("🔍 NEOBOT COMPLETE SYSTEM DIAGNOSTIC")
        logger.info(f"Start time: {datetime.now().strftime('%H:%M:%S')}")
        logger.info("="*60)
        
        try:
            # Run all checks
            self.check_backend()
            self.check_frontend()
            self.check_whatsapp_service()
            self.check_integration()
            self.check_database()
            self.check_features()
            
            # Generate report
            self.generate_report()
            
            return "✅ READY" in self.results["overall_status"]
            
        except Exception as e:
            logger.error(f"\n❌ Diagnostic error: {e}", exc_info=True)
            self.results["overall_status"] = "❌ ERROR"
            return False

# ========== MAIN ==========
if __name__ == "__main__":
    diagnostic = SystemDiagnostic()
    success = diagnostic.execute()
    
    sys.exit(0 if success else 1)
