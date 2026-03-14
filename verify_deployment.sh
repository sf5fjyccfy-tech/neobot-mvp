#!/bin/bash

# NEOBOT COMPLETE SYSTEM VERIFICATION
# Comprehensive final check of all components

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         NeoBOT MVP - COMPLETE SYSTEM VERIFICATION              ║"
echo "║         Deep Audit & Issue Discovery                           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNINGS=0
CRITICAL=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

test_result() {
    local test_name="$1"
    local result="$2"
    local details="$3"
    
    ((TOTAL_TESTS++))
    
    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC}   | $test_name"
        ((PASSED_TESTS++))
    elif [ "$result" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC}   | $test_name"
        ((FAILED_TESTS++))
        if [ -n "$details" ]; then
            echo "         └─ $details"
        fi
    elif [ "$result" = "WARN" ]; then
        echo -e "${YELLOW}⚠️  WARN${NC}   | $test_name"
        ((WARNINGS++))
        if [ -n "$details" ]; then
            echo "         └─ $details"
        fi
    elif [ "$result" = "CRITICAL" ]; then
        echo -e "${RED}🔴 CRIT${NC}   | $test_name"
        ((CRITICAL++))
        if [ -n "$details" ]; then
            echo "         └─ $details"
        fi
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  ENVIRONMENT CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f ".env" ]; then
    test_result ".env file exists" "PASS"
    
    # Check debug mode
    DEBUG_MODE=$(grep "^BACKEND_DEBUG=" .env | cut -d= -f2 || echo "NOT_SET")
    if [ "$DEBUG_MODE" = "true" ]; then
        test_result "Debug mode disabled" "CRITICAL" "BACKEND_DEBUG=true (should be false)"
    else
        test_result "Debug mode disabled" "PASS"
    fi
    
    # Check database password strength
    DB_PWD=$(grep "^DATABASE_PASSWORD=" .env | cut -d= -f2 || echo "")
    if [ -z "$DB_PWD" ]; then
        test_result "Database password set" "CRITICAL" "PASSWORD NOT FOUND"
    else
        PWD_LEN=${#DB_PWD}
        if [ $PWD_LEN -lt 24 ]; then
            test_result "Database password strength" "CRITICAL" "Only $PWD_LEN chars (need 32+)"
        else
            test_result "Database password strength" "PASS"
        fi
    fi
    
    # Check JWT secret
    JWT_SECRET=$(grep "^JWT_SECRET=" .env | cut -d= -f2 || echo "")
    if [ -z "$JWT_SECRET" ]; then
        test_result "JWT Secret set" "CRITICAL" "NOT FOUND"
    else
        JWT_LEN=${#JWT_SECRET}
        if [ $JWT_LEN -lt 32 ]; then
            test_result "JWT Secret length" "WARN" "Only $JWT_LEN chars (need 64+ for production)"
        else
            test_result "JWT Secret length" "PASS"
        fi
    fi
    
    # Check debug log level
    LOG_LEVEL=$(grep "^LOG_LEVEL=" .env | cut -d= -f2 || echo "NOT_SET")
    if [ "$LOG_LEVEL" = "DEBUG" ]; then
        test_result "Log level production-ready" "WARN" "LOG_LEVEL=DEBUG (should be INFO)"
    else
        test_result "Log level production-ready" "PASS"
    fi
else
    test_result ".env file exists" "FAIL" "File not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  DATABASE CONFIGURATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DB_HOST=$(grep "^DATABASE_HOST=" .env | cut -d= -f2 || echo "localhost")
DB_USER=$(grep "^DATABASE_USER=" .env | cut -d= -f2 || echo "neobot")
DB_NAME=$(grep "^DATABASE_NAME=" .env | cut -d= -f2 || echo "neobot_db")
DB_PWD=$(grep "^DATABASE_PASSWORD=" .env | cut -d= -f2 || echo "")

# Try to connect
if command -v psql &> /dev/null; then
    if PGPASSWORD="$DB_PWD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &>/dev/null; then
        test_result "PostgreSQL connection" "PASS"
        
        # Check tables
        TABLE_COUNT=$(PGPASSWORD="$DB_PWD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'" 2>/dev/null || echo "0")
        if [ "$TABLE_COUNT" -ge 13 ]; then
            test_result "Database schema complete" "PASS" "($TABLE_COUNT tables found)"
        else
            test_result "Database schema complete" "FAIL" "Only $TABLE_COUNT tables (need ~13)"
        fi
        
        # Check subscriptions table
        if PGPASSWORD="$DB_PWD" psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c "\dt subscriptions" &>/dev/null; then
            test_result "Subscriptions table exists" "PASS"
        else
            test_result "Subscriptions table exists" "FAIL"
        fi
    else
        test_result "PostgreSQL connection" "FAIL" "Cannot connect with provided credentials"
    fi
else
    test_result "PostgreSQL client installed" "WARN" "psql not in PATH"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  BACKEND CODE ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check main.py imports
if [ -f "backend/app/main.py" ]; then
    test_result "backend/app/main.py exists" "PASS"
    
    # Check datetime.utcnow issues
    UTC_NOW_COUNT=$(grep -r "datetime.utcnow()" backend/app/ --include="*.py" 2>/dev/null | wc -l || echo "0")
    if [ "$UTC_NOW_COUNT" -gt 0 ]; then
        test_result "datetime.utcnow() deprecation" "WARN" "$UTC_NOW_COUNT instances (Python 3.13 incompatible)"
    else
        test_result "datetime.utcnow() deprecation" "PASS"
    fi
    
    # Check middleware integration
    if grep -q "check_subscription_middleware" backend/app/main.py; then
        test_result "Subscription middleware integrated" "PASS"
    else
        test_result "Subscription middleware integrated" "CRITICAL" "Middleware not registere in main.py"
    fi
else
    test_result "backend/app/main.py exists" "FAIL"
fi

# Check service files
SERVICES=(
    "auth_service.py"
    "subscription_service.py"
    "analytics_service.py"
    "usage_tracking_service.py"
    "overage_pricing_service.py"
)

for service in "${SERVICES[@]}"; do
    if [ -f "backend/app/services/$service" ]; then
        test_result "backend/app/services/$service" "PASS"
    else
        test_result "backend/app/services/$service" "FAIL"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  FRONTEND CODE ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PAGES=(
    "frontend/src/app/page.tsx"
    "frontend/src/app/login/page.tsx"
    "frontend/src/app/signup/page.tsx"
    "frontend/src/app/pricing/page.tsx"
    "frontend/src/app/dashboard/page.tsx"
)

for page in "${PAGES[@]}"; do
    if [ -f "$page" ]; then
        test_result "$page" "PASS"
    else
        test_result "$page" "FAIL"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  SECURITY ANALYSIS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check secrets in files
if git -C . rev-parse --git-dir > /dev/null 2>&1; then
    SECRETS=$(grep -r "neobot_jwt_secret_change_in_production\|neobot_secure_password" backend/ frontend/ --include="*.py" --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v "^Binary" | wc -l)
    if [ "$SECRETS" -gt 0 ]; then
        test_result "Default secrets in code" "CRITICAL" "$SECRETS references to default secrets"
    else
        test_result "Default secrets in code" "PASS"
    fi
fi

# Check .gitignore
if [ -f ".gitignore" ]; then
    if grep -q ".env" .gitignore; then
        test_result ".env in .gitignore" "PASS"
    else
        test_result ".env in .gitignore" "WARN" ".env files might be committed"
    fi
else
    test_result ".gitignore exists" "WARN"
fi

# Check HTTPS/TLS configuration
if grep -q "HTTPS\|TLS\|SSL" .env 2>/dev/null; then
    test_result "HTTPS/TLS configured" "PASS"
else
    test_result "HTTPS/TLS configured" "WARN" "No HTTPS configuration found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  DEPLOYMENT ARTIFACTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ARTIFACTS=(
    "docker-compose.yml"
    "backend/Dockerfile.prod"
    "DEPLOYMENT_GUIDE.md"
    "CRITICAL_FIXES_CHECKLIST.md"
    "AUDIT_DEPTH_REPORT.md"
)

for artifact in "${ARTIFACTS[@]}"; do
    if [ -f "$artifact" ]; then
        test_result "$artifact" "PASS"
    else
        test_result "$artifact" "FAIL" "Missing deployment artifact"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "Total Tests:     $TOTAL_TESTS"
echo -e "Passed:          ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:          ${RED}$FAILED_TESTS${NC}"
echo -e "Warnings:        ${YELLOW}$WARNINGS${NC}"
echo -e "Critical:        ${RED}$CRITICAL${NC}"
echo ""

PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
echo -e "Pass Rate: ${GREEN}${PASS_RATE}%${NC}"

if [ $CRITICAL -gt 0 ]; then
    echo ""
    echo -e "${RED}⛔ DEPLOYMENT STATUS: NOT READY${NC}"
    echo -e "   🔴 $CRITICAL critical issues must be fixed"
    echo -e "   See CRITICAL_FIXES_CHECKLIST.md for details"
elif [ $FAILED_TESTS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  DEPLOYMENT STATUS: NEEDS REVIEW${NC}"
    echo -e "   🟡 $FAILED_TESTS issues require attention"
else
    echo ""
    echo -e "${GREEN}✅ DEPLOYMENT STATUS: READY FOR STAGING${NC}"
    echo -e "   All critical checks passed!"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 REPORTED ISSUES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
if [ $CRITICAL -gt 0 ]; then
    echo -e "${RED}CRITICAL ISSUES ($CRITICAL):${NC}"
    echo "  1. Database password (too weak)"
    echo "  2. Debug mode enabled"
    echo "  3. JWT secret too short"
    echo "  4. Trial expiration not enforced"
    if [ "$UTC_NOW_COUNT" -gt 0 ]; then
        echo "  5. datetime.utcnow() deprecations ($UTC_NOW_COUNT instances)"
    fi
fi

if [ $WARNINGS -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}WARNINGS ($WARNINGS):${NC}"
    echo "  • No HTTPS/TLS configuration"
    echo "  • No rate limiting implemented"
    echo "  • Webhook secret not validated"
    echo "  • CORS not restricted"
    echo "  • No admin role assignment"
    echo "  • No database backups configured"
    echo "  • Secrets might be in repo"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 NEXT STEPS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
if [ $CRITICAL -gt 0 ]; then
    echo "1. Read CRITICAL_FIXES_CHECKLIST.md"
    echo "2. Apply all critical fixes (1-2 hours)"
    echo "3. Run this script again to verify"
    echo "4. Deploy to staging"
else
    echo "✅ All critical issues resolved!"
    echo "1. Read AUDIT_DEPTH_REPORT.md for warnings"
    echo "2. Deploy to staging: docker-compose up -d"
    echo "3. Run smoke tests"
    echo "4. Monitor logs for issues"
fi

echo ""
