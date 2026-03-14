#!/bin/bash

#╔════════════════════════════════════════════════════════════════════╗
#║          NEOBOT WhatsApp - Système Diagnostic Complet             ║
#╚════════════════════════════════════════════════════════════════════╝

# Don't exit on error - we want to continue checking
trap 'echo Error on line $LINENO' ERR

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║    🔍 NEOBOT WhatsApp - SYSTEM DIAGNOSTIC v4.0              ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS="${GREEN}✅${NC}"
FAIL="${RED}❌${NC}"
WARN="${YELLOW}⚠️${NC}"
INFO="${BLUE}ℹ️${NC}"

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
check_pass() {
    echo -e "${PASS} $1"
    ((PASSED++))
}

check_fail() {
    echo -e "${FAIL} $1"
    ((FAILED++))
}

check_warn() {
    echo -e "${WARN} $1"
    ((WARNINGS++))
}

check_info() {
    echo -e "${INFO} $1"
}

# ═══════════════════════════════════════════════════════════════════
# 1. SYSTEM CHECKS
# ═══════════════════════════════════════════════════════════════════

echo "1️⃣  SYSTEM CHECKS"
echo "────────────────────────────────────────────────────────────────"

# Node version
NODE_VERSION=$(node -v)
NODE_MAJOR=$(echo $NODE_VERSION | cut -d'.' -f1 | sed 's/v//')
if [[ $NODE_MAJOR -ge 18 ]]; then
    check_pass "Node.js version: $NODE_VERSION"
else
    check_fail "Node.js version: $NODE_VERSION (require >=v18)"
fi

# NPM version
NPM_VERSION=$(npm -v)
check_pass "NPM version: $NPM_VERSION"

# Platform
PLATFORM=$(uname -s)
check_pass "Platform: $PLATFORM"

# Memory
MEMORY_MB=$(free -m | awk 'NR==2{print $7}')
if [[ $MEMORY_MB -gt 500 ]]; then
    check_pass "Available memory: ${MEMORY_MB}MB"
else
    check_warn "Available memory: ${MEMORY_MB}MB (low)"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# 2. PROJECT STRUCTURE
# ═══════════════════════════════════════════════════════════════════

echo "2️⃣  PROJECT STRUCTURE"
echo "────────────────────────────────────────────────────────────────"

# Check key files
for file in package.json whatsapp-optimized.js .env.example; do
    if [[ -f "$file" ]]; then
        check_pass "Found: $file"
    else
        check_warn "Missing: $file"
    fi
done

# Check directories
if [[ -d "node_modules" ]]; then
    check_pass "node_modules directory exists"
else
    check_warn "node_modules directory missing (run npm install)"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# 3. DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════

echo "3️⃣  DEPENDENCIES"
echo "────────────────────────────────────────────────────────────────"

# Check Baileys
if npm list @whiskeysockets/baileys > /dev/null 2>&1; then
    BAILEYS_VERSION=$(npm list @whiskeysockets/baileys 2>/dev/null | grep '@whiskeysockets/baileys' | head -1 | awk '{print $NF}')
    if [[ "$BAILEYS_VERSION" == *"rc"* ]]; then
        check_warn "@whiskeysockets/baileys: $BAILEYS_VERSION (RC - consider update)"
    else
        check_pass "@whiskeysockets/baileys: $BAILEYS_VERSION"
    fi
else
    check_fail "@whiskeysockets/baileys: NOT INSTALLED"
fi

# Check other critical dependencies
for dep in express axios dotenv qrcode-terminal; do
    if npm list $dep > /dev/null 2>&1; then
        check_pass "$dep: installed"
    else
        check_fail "$dep: NOT INSTALLED"
    fi
done

echo ""

# ═══════════════════════════════════════════════════════════════════
# 4. CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

echo "4️⃣  CONFIGURATION"
echo "────────────────────────────────────────────────────────────────"

if [[ -f ".env" ]]; then
    BACKEND_URL=$(grep BACKEND_URL .env 2>/dev/null || echo "")
    PORT=$(grep WHATSAPP_PORT .env 2>/dev/null || echo "")
    
    if [[ -n "$BACKEND_URL" ]]; then
        check_pass "BACKEND_URL configured"
    else
        check_info "BACKEND_URL: using default (http://localhost:8000)"
    fi
    
    if [[ -n "$PORT" ]]; then
        check_pass "WHATSAPP_PORT configured"
    else
        check_info "WHATSAPP_PORT: using default (3001)"
    fi
else
    check_info ".env file: not found (using defaults)"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# 5. PORT AVAILABILITY
# ═══════════════════════════════════════════════════════════════════

echo "5️⃣  PORT AVAILABILITY"
echo "────────────────────────────────────────────────────────────────"

PORT=${WHATSAPP_PORT:-3001}

if ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    PID=$(ss -tlnp 2>/dev/null | grep ":$PORT" | awk '{print $6}' | cut -d'/' -f1)
    check_fail "Port $PORT is in use (PID: $PID)"
else
    check_pass "Port $PORT is available"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# 6. AUTHENTICATION STATE
# ═══════════════════════════════════════════════════════════════════

echo "6️⃣  AUTHENTICATION STATE"
echo "────────────────────────────────────────────────────────────────"

if [[ -d "auth_info_baileys" ]]; then
    AUTH_FILES=$(find auth_info_baileys -type f | wc -l)
    check_pass "Auth directory exists with $AUTH_FILES credentials"
else
    check_info "Auth directory: empty (new session)"
fi

if [[ -f "sessions.json" ]]; then
    check_pass "Sessions file exists"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# 7. CONNECTIVITY
# ═══════════════════════════════════════════════════════════════════

echo "7️⃣  CONNECTIVITY"
echo "────────────────────────────────────────────────────────────────"

# Check internet connection
if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    check_pass "Internet connectivity: OK"
else
    check_fail "Internet connectivity: FAILED"
fi

# Check WhatsApp API reachability
if timeout 3 curl -s https://api.whatsapp.com > /dev/null 2>&1; then
    check_pass "WhatsApp servers: reachable"
else
    check_warn "WhatsApp servers: might be unreachable (timeout)"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# 8. DISK SPACE
# ═══════════════════════════════════════════════════════════════════

echo "8️⃣  DISK SPACE"
echo "────────────────────────────────────────────────────────────────"

DISK_USAGE=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
DISK_FREE=$(df -h . | tail -1 | awk '{print $4}')

if [[ $DISK_USAGE -lt 90 ]]; then
    check_pass "Disk usage: ${DISK_USAGE}% (Free: $DISK_FREE)"
else
    check_warn "Disk usage: ${DISK_USAGE}% (LOW SPACE - Free: $DISK_FREE)"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# 9. SUMMARY
# ═══════════════════════════════════════════════════════════════════

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                     📋 SUMMARY                               ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║ Passed:   ${GREEN}$PASSED${NC}                                                    ║"
echo "║ Warnings: ${YELLOW}$WARNINGS${NC}                                                    ║"
echo "║ Failed:   ${RED}$FAILED${NC}                                                    ║"
echo "╚═══════════════════════════════════════════════════════════════╝"

echo ""

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}✅ System is ready to start!${NC}"
    echo ""
    echo "Start the service:"
    echo "  node whatsapp-optimized.js"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Please fix the failing checks above.${NC}"
    echo ""
    exit 1
fi
