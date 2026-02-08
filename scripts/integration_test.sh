#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        🚀 NEOBOT INTEGRATION TEST - FULL SYSTEM CHECK          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ========== PHASE 1: BACKEND STARTUP TEST ==========
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 1: BACKEND STARTUP TEST"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "🚀 Démarrage du backend en arrière-plan..."
cd /home/tim/neobot-mvp/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   PID: $BACKEND_PID"
echo "   Attente de démarrage (10s)..."
sleep 10

# Check if backend is running
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ Backend process running${NC}"
else
    echo -e "   ${RED}❌ Backend process failed to start${NC}"
    cat /tmp/backend.log | tail -20
    exit 1
fi

# Test health endpoint
echo ""
echo "🧪 Test: Health endpoint..."
HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
if [ -z "$HEALTH" ]; then
    echo -e "   ${RED}❌ No response from /health${NC}"
    echo "   Attente supplémentaire..."
    sleep 5
    HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
fi

if echo "$HEALTH" | grep -q "healthy\|status"; then
    echo -e "   ${GREEN}✅ Backend health check: OK${NC}"
    echo "   Response: $HEALTH"
else
    echo -e "   ${YELLOW}⚠️ Backend responding but no health data${NC}"
fi

echo ""

# ========== PHASE 2: WHATSAPP SERVICE STARTUP ==========
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 2: WHATSAPP SERVICE STARTUP TEST"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "🚀 Démarrage du service WhatsApp en arrière-plan..."
cd /home/tim/neobot-mvp/whatsapp-service

# Test npm/node installation first
if ! command -v node &>/dev/null; then
    echo -e "   ${RED}❌ Node.js not found${NC}"
    exit 1
fi

if ! command -v npm &>/dev/null; then
    echo -e "   ${RED}❌ npm not found${NC}"
    exit 1
fi

# Verify package.json is correct
MAIN_FILE=$(grep '"main":' package.json | grep -o '"[^"]*"' | tail -1 | tr -d '"')
if [ ! -f "$MAIN_FILE" ]; then
    echo -e "   ${RED}❌ Main entry point not found: $MAIN_FILE${NC}"
    echo "   Fix package.json!"
    exit 1
fi

echo "   Entry point: $MAIN_FILE ✅"
echo "   Starting service..."

npm start > /tmp/whatsapp.log 2>&1 &
WA_PID=$!
echo "   PID: $WA_PID"
echo "   Attente de démarrage (8s pour QR code setup)..."
sleep 8

# Check if service is running
if ps -p $WA_PID > /dev/null 2>&1; then
    echo -e "   ${GREEN}✅ WhatsApp service process running${NC}"
else
    echo -e "   ${RED}❌ WhatsApp service failed to start${NC}"
    echo "   Logs:"
    cat /tmp/whatsapp.log | tail -30
    # Kill backend if WA failed
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Test health endpoint
echo ""
echo "🧪 Test: WhatsApp service health..."
WA_HEALTH=$(curl -s http://localhost:3001/health 2>/dev/null)
if [ -z "$WA_HEALTH" ]; then
    echo -e "   ${YELLOW}⚠️ WhatsApp service not responding yet (waiting for QR scan)${NC}"
else
    if echo "$WA_HEALTH" | grep -q "disconnected\|connected"; then
        echo -e "   ${GREEN}✅ WhatsApp service responding${NC}"
        echo "   Response: $WA_HEALTH"
    fi
fi

echo ""

# ========== PHASE 3: CONFIGURATION VALIDATION ==========
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 3: CONFIGURATION VALIDATION"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check environment variables
echo "🔐 Environment Variables:"
if [ -f /home/tim/neobot-mvp/backend/.env ]; then
    if grep -q "DATABASE_URL" /home/tim/neobot-mvp/backend/.env; then
        echo -e "   ${GREEN}✅ Backend .env configured${NC}"
    fi
fi

if [ -f /home/tim/neobot-mvp/whatsapp-service/.env ]; then
    if grep -q "WHATSAPP_BACKEND_URL" /home/tim/neobot-mvp/whatsapp-service/.env; then
        echo -e "   ${GREEN}✅ WhatsApp .env configured${NC}"
        BACKEND_URL=$(grep "WHATSAPP_BACKEND_URL" /home/tim/neobot-mvp/whatsapp-service/.env | cut -d= -f2)
        echo "   Backend URL: $BACKEND_URL"
    else
        echo -e "   ${RED}❌ WHATSAPP_BACKEND_URL missing${NC}"
    fi
fi

echo ""

# ========== PHASE 4: DEPENDENCIES CHECK ==========
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 4: DEPENDENCIES CHECK"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "🐍 Python packages:"
cd /home/tim/neobot-mvp/backend
python3 -c "
import sys
packages = ['psycopg2', 'fastapi', 'sqlalchemy', 'httpx', 'pydantic']
for pkg in packages:
    try:
        __import__(pkg.replace('-', '_'))
        print(f'   ✅ {pkg}')
    except:
        print(f'   ❌ {pkg} - MISSING!')
" 2>/dev/null

echo ""
echo "🟢 Node.js packages:"
cd /home/tim/neobot-mvp/whatsapp-service
npm list --depth=0 2>/dev/null | grep -E "@whiskeysockets|axios|express|qrcode" | sed 's/^/   /'

echo ""

# ========== PHASE 5: LOGS REVIEW ==========
echo "═══════════════════════════════════════════════════════════════"
echo "PHASE 5: RECENT LOGS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "🔍 Backend logs (last 5 lines):"
tail -5 /tmp/backend.log | sed 's/^/   /'

echo ""
echo "🔍 WhatsApp service logs (last 10 lines):"
tail -10 /tmp/whatsapp.log | sed 's/^/   /'

echo ""

# ========== FINAL STATUS ==========
echo "═══════════════════════════════════════════════════════════════"
echo "FINAL STATUS"
echo "═══════════════════════════════════════════════════════════════"
echo ""

BACKEND_RUNNING=0
WA_RUNNING=0

if ps -p $BACKEND_PID > /dev/null 2>&1; then
    BACKEND_RUNNING=1
    echo -e "✅ Backend:         ${GREEN}RUNNING (PID: $BACKEND_PID)${NC}"
else
    echo -e "❌ Backend:         ${RED}STOPPED${NC}"
fi

if ps -p $WA_PID > /dev/null 2>&1; then
    WA_RUNNING=1
    echo -e "✅ WhatsApp:        ${GREEN}RUNNING (PID: $WA_PID)${NC}"
else
    echo -e "❌ WhatsApp:        ${RED}STOPPED${NC}"
fi

echo ""
echo "📊 Service Endpoints:"
echo "   Backend HTTP:  http://localhost:8000/health"
echo "   WhatsApp HTTP: http://localhost:3001/health"
echo ""

if [ $BACKEND_RUNNING -eq 1 ] && [ $WA_RUNNING -eq 1 ]; then
    echo "✅ INTEGRATION TEST: PASSED"
    echo ""
    echo "📱 NEXT STEP: Scan QR code with WhatsApp when it appears"
    echo "   (Check WhatsApp service logs/terminal for QR code)"
    echo ""
    echo "🛑 To stop services:"
    echo "   kill $BACKEND_PID $WA_PID"
else
    echo "❌ INTEGRATION TEST: FAILED"
    echo ""
    echo "Arrêt des services..."
    kill $BACKEND_PID 2>/dev/null
    kill $WA_PID 2>/dev/null
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ✅ TEST COMPLETED                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
