#! /bin/bash
# ========================================
# NEOBOT PRODUCTION DEPLOYMENT CHECKLIST
# ========================================
# This script validates all security requirements before deployment

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔒 NEOBOT PRODUCTION DEPLOYMENT SECURITY CHECKLIST"
echo "=================================================="
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0

check() {
    local description="$1"
    local command="$2"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $description"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} $description"
        ((CHECKS_FAILED++))
    fi
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# ========== 1. ENVIRONMENT VALIDATION ==========
echo ""
echo "1. ENVIRONMENT CONFIGURATION:"

check "Database password is strong (not 'neobot_secure_password')" \
    "! grep -q 'neobot_secure_password' .env.production"

check "JWT_SECRET is 64+ characters" \
    "[ \$(grep JWT_SECRET .env.production | cut -d= -f2 | wc -c) -gt 64 ]"

check "DEBUG mode is disabled" \
    "grep -q 'BACKEND_DEBUG=false' .env.production"

check "Production environment set" \
    "grep -q 'BACKEND_ENV=production' .env.production"

check ".env.production exists" \
    "[ -f .env.production ]"

check ".env.production is not in git" \
    "grep -q '.env.production' .gitignore"

# ========== 2. CODE QUALITY ==========
echo ""
echo "2. CODE QUALITY:"

check "No datetime.utcnow() in auth.py" \
    "! grep -q 'datetime.utcnow()' backend/app/routers/auth.py"

check "No hardcoded secrets in code" \
    "! grep -r 'neobot_secure_password' backend/app/ --include='*.py'"

check "CORS is configured" \
    "grep -q 'CORSMiddleware' backend/app/main.py"

check "Rate limiting configured" \
    "grep -q 'RATE_LIMIT' backend/app/main.py || grep -q 'limiter' backend/app/main.py"

# ========== 3. DATABASE ==========
echo ""
echo "3. DATABASE SETUP:"

check "PostgreSQL is running" \
    "pg_isready -h localhost -U neobot -d neobot_db"

check "Subscriptions table exists" \
    "psql -U neobot -d neobot_db -h localhost -c 'SELECT 1 FROM subscriptions' > /dev/null 2>&1"

check "All migrations applied" \
    "psql -U neobot -d neobot_db -h localhost -c 'SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=\"public\" AND table_name IN (\"users\", \"tenants\", \"subscriptions\")' | grep -q 3"

# ========== 4. BACKEND HEALTH ==========
echo ""
echo "4. BACKEND SERVICES:"

check "Backend responds to health check" \
    "curl -s http://localhost:8000/health | grep -q 'healthy'"

check "OpenAPI schema is valid" \
    "curl -s http://localhost:8000/openapi.json | python3 -m json.tool > /dev/null 2>&1"

# ========== 5. FRONTEND ==========
echo ""
echo "5. FRONTEND CONFIGURATION:"

check "Landing page exists" \
    "[ -f frontend/src/app/page.tsx ]"

check "Pricing page exists" \
    "[ -f frontend/src/app/pricing/page.tsx ]"

check "Next.js .env is configured" \
    "[ -f frontend/.env.local ] || [ -f frontend/.env ]"

check "Next.js config exists" \
    "[ -f frontend/next.config.js ]"

# ========== 6. DEPLOYMENT FILES ==========
echo ""
echo "6. DEPLOYMENT READINESS:"

check "Docker Compose configured" \
    "[ -f docker-compose.yml ]"

check "Deployment script present" \
    "[ -f deploy-staging.sh ]"

check "Audit report generated" \
    "[ -f DEPLOYMENT_AUDIT.md ]"

# ========== 7. SECURITY BEST PRACTICES ==========
echo ""
echo "7. SECURITY BEST PRACTICES:"

warn ".gitignore must include: .env, .env.*, *.key, *.pem, /logs/"
[ -f .gitignore ] && grep -q '\.env' .gitignore && echo -e "${GREEN}✓${NC} .env in .gitignore" || echo -e "${RED}✗${NC} .env NOT in .gitignore"

warn "Ensure SSL/TLS certificates are in place"
warn "Ensure database backups are automated"
warn "Ensure monitoring/alerting is configured"
warn "Ensure SMTP is configured for email notifications"

# ========== 7. BACKUP VALIDATION ==========
echo ""
echo "8. BACKUP CONFIGURATION:"

check "Backup script exists" \
    "[ -f scripts/backup_database.sh ] || [ -f backup.sh ]"

warn "Test database backup restoration monthly"
warn "Ensure backups are encrypted and stored offsite"

# ========== SUMMARY ==========
echo ""
echo "=================================================="
echo -e "${GREEN}✓ PASSED: $CHECKS_PASSED${NC}"
echo -e "${RED}✗ FAILED: $CHECKS_FAILED${NC}"
echo "=================================================="
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL CHECKS PASSED - READY FOR DEPLOYMENT${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review .env.production for all secrets"
    echo "2. Verify HTTPS/TLS certificates"
    echo "3. Run fire-and-forget tests"
    echo "4. Deploy to staging environment"
    echo "5. Run smoke tests in staging"
    echo ""
    exit 0
else
    echo -e "${RED}❌ SOME CHECKS FAILED - DO NOT DEPLOY${NC}"
    echo ""
    echo "Please fix the issues above before deploying."
    exit 1
fi
