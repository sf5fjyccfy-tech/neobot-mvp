#!/usr/bin/env python3
"""
COMPREHENSIVE NEOBOT AUDIT SCRIPT
Tests all critical systems and generates a deployment readiness report
"""

import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# ============= CONFIGURATION =============
BACKEND_PORT = 8000
DATABASE_URL = "postgresql://neobot:neobot_secure_password@localhost:5432/neobot_db"

# ============= COLORS FOR OUTPUT =============
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

# ============= REPORT DATA =============
audit_report = {
    "timestamp": datetime.now().isoformat(),
    "tests": [],
    "issues": [],
    "warnings": [],
    "critical": [],
    "deployment_ready": True
}

def test(name: str, passed: bool, details: str = ""):
    """Record a test result"""
    status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
    print(f"  {status} | {name}")
    if details:
        print(f"       └─ {details}")
    
    audit_report["tests"].append({
        "name": name,
        "passed": passed,
        "details": details
    })
    
    if not passed:
        audit_report["deployment_ready"] = False

def issue(level: str, title: str, description: str):
    """Record an issue"""
    colors = {
        "CRITICAL": RED,
        "WARNING": YELLOW,
        "INFO": BLUE
    }
    icon = "🔴" if level == "CRITICAL" else "⚠️" if level == "WARNING" else "ℹ️"
    print(f"  {icon} [{level}] {title}")
    if description:
        print(f"       └─ {description}")
    
    audit_report["issues"].append({
        "level": level,
        "title": title,
        "description": description
    })
    
    if level == "CRITICAL":
        audit_report["deployment_ready"] = False

# =========================================
# AUDIT TESTS
# =========================================

print(f"\n{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}")
print(f"{BOLD}{BLUE}   NEOBOT PROJECT COMPREHENSIVE AUDIT{RESET}")
print(f"{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}\n")

# ============= 1. ENVIRONMENT & CONFIG =============
print(f"{BOLD}1. ENVIRONMENT & CONFIGURATION{RESET}")

try:
    from dotenv import load_dotenv
    load_dotenv()
    test("Python .env loading", True)
except Exception as e:
    test("Python .env loading", False, str(e))
    issue("CRITICAL", "dotenv not working", "Cannot load .env file")

# Check .env file
env_file = Path(".env")
test(".env file exists", env_file.exists())

# Check required env vars
required_env = [
    "DATABASE_URL", "JWT_SECRET", "DEEPSEEK_API_KEY",
    "BACKEND_PORT", "FRONTEND_URL"
]
for var in required_env:
    val = os.getenv(var)
    test(f"ENV: {var} set", val is not None, f"Value: {val[:20] if val else 'MISSING'}...")

# Check for hardcoded secrets in .env
env_content = env_file.read_text() if env_file.exists() else ""
if "neobot_secure_password" in env_content.lower():
    issue("WARNING", "Weak database password", "Database password appears weak: 'neobot_secure_password'")

if "debug=true" in env_content.lower():
    issue("WARNING", "Debug mode enabled", "BACKEND_DEBUG=true should be false in production")

# ============= 2. PYTHON IMPORTS & MODELS =============
print(f"\n{BOLD}2. PYTHON MODULES & IMPORTS{RESET}")

try:
    from app.models import (
        User, Tenant, Conversation, Message, 
        Subscription, WhatsAppSession, UsageTracking, Overage
    )
    test("Core models import", True, "All 8 models loaded")
except Exception as e:
    test("Core models import", False, str(e)[:50])
    issue("CRITICAL", "Models import failed", str(e)[:100])

try:
    from app.database import get_db, init_db, Base
    test("Database module import", True)
except Exception as e:
    test("Database module import", False, str(e)[:50])
    issue("CRITICAL", "Database module failed", str(e)[:100])

try:
    from app.routers import auth, subscription
    test("Auth/Subscription routers import", True)
except Exception as e:
    test("Auth/Subscription routers import", False, str(e)[:50])
    issue("CRITICAL", "Routers import failed", str(e)[:100])

try:
    from app.services.subscription_service import SubscriptionService
    test("Subscription service import", True)
except Exception as e:
    test("Subscription service import", False, str(e)[:50])
    issue("WARNING", "Subscription service failed", str(e)[:100])

try:
    from app.dependencies import get_current_user, get_tenant_from_request
    test("Dependencies module import", True)
except Exception as e:
    test("Dependencies module import", False, str(e)[:50])
    issue("CRITICAL", "Dependencies module failed", str(e)[:100])

# ============= 3. DATABASE CONNECTIVITY & SCHEMA =============
print(f"\n{BOLD}3. DATABASE CONNECTIVITY & SCHEMA{RESET}")

try:
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    test("PostgreSQL connection", True, "Connected to neobot_db")
    
    cur = conn.cursor()
    
    # Check tables exist
    required_tables = [
        "users", "tenants", "conversations", "messages",
        "subscriptions", "whatsapp_sessions", "usage_tracking",
        "overages", "business_types", "tenant_business_config"
    ]
    
    cur.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public'
    """)
    existing_tables = [row[0] for row in cur.fetchall()]
    
    for table in required_tables:
        exists = table in existing_tables
        test(f"Table: {table}", exists)
        if not exists:
            issue("CRITICAL", f"Missing table: {table}", "Run migrations to create")
    
    # Check subscriptions table columns
    cur.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='subscriptions' 
        ORDER BY ordinal_position
    """)
    sub_cols = [row[0] for row in cur.fetchall()]
    
    required_sub_cols = [
        "id", "tenant_id", "plan", "is_trial", 
        "trial_start_date", "trial_end_date", "status"
    ]
    
    for col in required_sub_cols:
        test(f"Subscription column: {col}", col in sub_cols)
    
    # Check for enum types
    cur.execute("SELECT typname FROM pg_type WHERE typnamespace = 11")
    enum_types = [row[0] for row in cur.fetchall()]
    test("Custom PostgreSQL enums exist", len(enum_types) > 0, f"Found {len(enum_types)} enums")
    
    conn.close()
    
except psycopg2.OperationalError as e:
    test("PostgreSQL connection", False, str(e)[:50])
    issue("CRITICAL", "Database connection failed", "PostgreSQL is not running or credentials are wrong")
except Exception as e:
    test("PostgreSQL operations", False, str(e)[:50])
    issue("WARNING", "Database test error", str(e)[:100])

# ============= 4. BACKEND API TESTS =============
print(f"\n{BOLD}4. BACKEND API ENDPOINTS{RESET}")

try:
    import requests
    
    # Check health endpoint
    response = requests.get(f"http://localhost:{BACKEND_PORT}/health", timeout=5)
    test("Health endpoint", response.status_code == 200, f"Status: {response.status_code}")
    
    # Check OpenAPI schema
    response = requests.get(f"http://localhost:{BACKEND_PORT}/openapi.json", timeout=5)
    test("OpenAPI schema available", response.status_code == 200)
    
    if response.status_code == 200:
        openapi = response.json()
        paths = openapi.get("paths", {})
        test("API endpoints registered", len(paths) > 0, f"Found {len(paths)} endpoints")
        
        # Check critical endpoints
        critical_endpoints = [
            "/api/auth/login",
            "/api/auth/register",
            "/api/tenants/{tenant_id}/subscription/trial/start",
            "/api/tenants/{tenant_id}/subscription/status"
        ]
        
        for endpoint in critical_endpoints:
            exists = endpoint in paths or endpoint.replace("{tenant_id}", "1") in paths
            test(f"Endpoint exists: {endpoint[:40]}", exists)
    
except requests.exceptions.ConnectionError:
    test("Backend connectivity", False, "Cannot connect to backend")
    issue("CRITICAL", "Backend not running", f"Uvicorn not responding on port {BACKEND_PORT}")
except Exception as e:
    test("Backend API test", False, str(e)[:50])
    issue("WARNING", "Backend test error", str(e)[:100])

# ============= 5. FRONTEND FILES & CONFIG =============
print(f"\n{BOLD}5. FRONTEND FILES & BUILD{RESET}")

required_frontend_files = {
    "frontend/src/app/page.tsx": "Landing page",
    "frontend/src/app/pricing/page.tsx": "Pricing page",
    "frontend/src/app/login/page.tsx": "Login page",
    "frontend/src/app/signup/page.tsx": "Signup page",
    "frontend/src/app/dashboard/page.tsx": "Dashboard",
    "frontend/src/middleware.ts": "Auth middleware",
    "frontend/package.json": "NPM config"
}

for file_path, desc in required_frontend_files.items():
    exists = Path(file_path).exists()
    test(f"{desc}: {file_path}", exists)

# Check next.config.js
next_config = Path("frontend/next.config.js")
if next_config.exists():
    test("Next.js config exists", True)
else:
    issue("WARNING", "next.config.js missing", "Next.js may not build properly without config")

# ============= 6. KEY FILES & STRUCTURE =============
print(f"\n{BOLD}6. PROJECT STRUCTURE VALIDATION{RESET}")

required_backend_files = {
    "backend/app/main.py": "FastAPI app",
    "backend/app/models.py": "Database models",
    "backend/app/database.py": "Database config",
    "backend/app/dependencies.py": "JWT dependencies",
    "backend/app/routers/auth.py": "Auth router",
    "backend/app/routers/subscription.py": "Subscription router",
    "backend/app/services/subscription_service.py": "Subscription service",
    "backend/requirements.txt": "Python dependencies",
    "docker-compose.yml": "Docker config",
    "deploy-staging.sh": "Deployment script"
}

for file_path, desc in required_backend_files.items():
    exists = Path(file_path).exists()
    test(f"{desc}: {file_path}", exists)

# ============= 7. SECURITY & CONFIG ISSUES =============
print(f"\n{BOLD}7. SECURITY ASSESSMENT{RESET}")

# Check JWT secret strength
jwt_secret = os.getenv("JWT_SECRET", "")
test("JWT secret configured", len(jwt_secret) > 20, f"Length: {len(jwt_secret)}")
if len(jwt_secret) < 32:
    issue("WARNING", "JWT secret too short", "Should be at least 32 characters")

# Check for .env in git
gitignore = Path(".gitignore")
if gitignore.exists():
    gitignore_content = gitignore.read_text()
    test(".env in .gitignore", ".env" in gitignore_content)
else:
    issue("WARNING", ".gitignore missing", "Cannot verify .env is ignored from git")

# ============= 8. CRITICAL FILE INSPECTION =============
print(f"\n{BOLD}8. CODE QUALITY CHECKS{RESET}")

main_py = Path("backend/app/main.py")
if main_py.exists():
    content = main_py.read_text()
    has_cors = "CORSMiddleware" in content
    has_routers = "include_router" in content
    has_subscription = "subscription_router" in content
    
    test("CORS middleware configured", has_cors)
    test("Routers included", has_routers)
    test("Subscription router included", has_subscription)

auth_py = Path("backend/app/routers/auth.py")
if auth_py.exists():
    content = auth_py.read_text()
    has_trial_start = "start_trial" in content or "trial_start_date" in content
    has_subscription_create = "Subscription" in content
    
    test("Auth creates trial on signup", has_trial_start or has_subscription_create)

# ============= 9. DEPLOYMENT FILES =============
print(f"\n{BOLD}9. DEPLOYMENT & DEVOPS{RESET}")

# Check docker-compose.yml
docker_compose = Path("docker-compose.yml")
if docker_compose.exists():
    content = docker_compose.read_text()
    has_postgres = "postgres" in content.lower()
    has_backend = "backend" in content.lower() or "uvicorn" in content.lower()
    
    test("Docker Compose has PostgreSQL", has_postgres)
    test("Docker Compose has backend service", has_backend)

# Check deployment script
deploy_script = Path("deploy-staging.sh")
test("Deployment script exists", deploy_script.exists())

# ============= GENERATE REPORT =============
print(f"\n{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}")
print(f"{BOLD}AUDIT SUMMARY{RESET}\n")

total_tests = len(audit_report["tests"])
passed_tests = len([t for t in audit_report["tests"] if t["passed"]])
failed_tests = total_tests - passed_tests

print(f"  {GREEN}Passed: {passed_tests}/{total_tests}{RESET}")
print(f"  {RED}Failed: {failed_tests}/{total_tests}{RESET}")

print(f"\n{BOLD}ISSUES FOUND:{RESET}\n")

critical_issues = [i for i in audit_report["issues"] if i["level"] == "CRITICAL"]
warning_issues = [i for i in audit_report["issues"] if i["level"] == "WARNING"]

if critical_issues:
    print(f"  {RED}CRITICAL ({len(critical_issues)}):{RESET}")
    for issue in critical_issues:
        print(f"    🔴 {issue['title']}")
        print(f"       → {issue['description']}\n")

if warning_issues:
    print(f"  {YELLOW}WARNINGS ({len(warning_issues)}):{RESET}")
    for issue in warning_issues:
        print(f"    ⚠️  {issue['title']}")
        print(f"       → {issue['description']}\n")

print(f"{BOLD}DEPLOYMENT READY:{RESET} {GREEN if audit_report['deployment_ready'] else RED}{'YES' if audit_report['deployment_ready'] else 'NO'}{RESET}\n")

if not audit_report["deployment_ready"]:
    print(f"  {RED}⚠️  Fix critical issues before deployment!{RESET}\n")
else:
    print(f"  {GREEN}✅ All systems ready for deployment!{RESET}\n")

# Save report to JSON
report_file = Path("AUDIT_REPORT.json")
report_file.write_text(json.dumps(audit_report, indent=2))
print(f"  Report saved to: {report_file}\n")

print(f"{BOLD}{BLUE}═══════════════════════════════════════════════════════════{RESET}\n")

sys.exit(0 if audit_report["deployment_ready"] else 1)
