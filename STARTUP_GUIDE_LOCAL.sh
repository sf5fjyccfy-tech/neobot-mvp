#!/bin/bash

###################################################################
# 🚀 NEOBOT - COMPLETE LOCAL STARTUP GUIDE
# 
# This guide shows how to start all NéoBot services locally
# for testing and development.
###################################################################

echo "
╔═══════════════════════════════════════════════════════════════════════╗
║                   🚀 NEOBOT LOCAL STARTUP GUIDE 🚀                    ║
║                   All Services - Step by Step                         ║
╚═══════════════════════════════════════════════════════════════════════╝
"

NEOBOT_HOME="/home/tim/neobot-mvp"
RESET='\033[0m'
BOLD='\033[1m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'

# ===================================================================
# STEP 1: Verify Prerequisites
# ===================================================================

echo -e "${CYAN}[STEP 1]${RESET} Checking prerequisites..."
echo ""

# Check PostgreSQL
if command -v psql &> /dev/null; then
    DB_VERSION=$(psql --version | awk '{print $3}')
    echo -e "${GREEN}✅${RESET} PostgreSQL $DB_VERSION found"
else
    echo -e "${YELLOW}⚠️${RESET} PostgreSQL not found - Install or skip"
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅${RESET} Node.js $NODE_VERSION found"
else
    echo -e "${YELLOW}⚠️${RESET} Node.js not found"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✅${RESET} Python $PYTHON_VERSION found"
else
    echo -e "${YELLOW}⚠️${RESETΒ Python not found"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅${RESET} npm $NPM_VERSION found"
else
    echo -e "${YELLOW}⚠️${RESET} npm not found"
    exit 1
fi

echo ""

# ===================================================================
# STEP 2: Kill Any Running Instances
# ===================================================================

echo -e "${CYAN}[STEP 2]${RESET} Cleaning up old processes..."
echo ""

killall node 2>/dev/null || true
killall python3 2>/dev/null || true
sleep 2
echo -e "${GREEN}✅${RESET} Old processes cleaned"
echo ""

# ===================================================================
# STEP 3: Prepare Directories
# ===================================================================

echo -e "${CYAN}[STEP 3]${RESET} Preparing directories..."
echo ""

mkdir -p $NEOBOT_HOME/logs
mkdir -p $NEOBOT_HOME/whatsapp-service/auth_info_baileys

echo -e "${GREEN}✅${RESET} Directories prepared"
echo ""

# ===================================================================
# SERVICE 1: PostgreSQL Database
# ===================================================================

echo -e "${CYAN}[SERVICE 1]${RESET} Starting PostgreSQL Database..."
echo ""
echo "Command (in separate terminal):"
echo "  ${BOLD}sudo service postgresql start${RESET}"
echo "  Or if using Docker:"
echo "  ${BOLD}docker-compose up -d postgres${RESET}"
echo ""
echo -e "${YELLOW}⏳${RESET} Make sure PostgreSQL is running on localhost:5432"
echo ""

# ===================================================================
# SERVICE 2: Backend (FastAPI)
# ===================================================================

echo -e "${CYAN}[SERVICE 2]${RESET} Starting Backend (FastAPI)..."
echo ""
echo "Command (in Terminal #1):"
echo ""
echo "  ${BOLD}cd $NEOBOT_HOME/backend${RESET}"
echo "  ${BOLD}python3 -m venv venv 2>/dev/null || true${RESET}"
echo "  ${BOLD}source venv/bin/activate${RESET}"
echo "  ${BOLD}pip install -q -r requirements.txt 2>/dev/null || true${RESET}"
echo "  ${BOLD}python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload${RESET}"
echo ""
echo -e "${YELLOW}Expected Output:${RESET}"
echo "  Uvicorn running on http://0.0.0.0:8000"
echo "  Application startup complete"
echo ""
echo -e "${YELLOW}Test Backend:${RESET}"
echo "  ${BOLD}curl http://localhost:8000/health${RESET}"
echo ""

# ===================================================================
# SERVICE 3: Frontend (Next.js)
# ===================================================================

echo -e "${CYAN}[SERVICE 3]${RESET} Starting Frontend (Next.js)..."
echo ""
echo "Command (in Terminal #2):"
echo ""
echo "  ${BOLD}cd $NEOBOT_HOME/frontend${RESET}"
echo "  ${BOLD}npm install 2>&1 | tail -5${RESET}"
echo "  ${BOLD}npm run dev${RESET}"
echo ""
echo -e "${YELLOW}Expected Output:${RESET}"
echo "  ▲ Next.js 14.0.0"
echo "  - ready started server on 0.0.0.0:3000"
echo ""
echo -e "${YELLOW}Test Frontend:${RESET}"
echo "  Open in browser: ${BOLD}http://localhost:3000${RESET}"
echo ""

# ===================================================================
# SERVICE 4: WhatsApp Service (Node.js)
# ===================================================================

echo -e "${CYAN}[SERVICE 4]${RESET} Starting WhatsApp Service (Node.js)..."
echo ""
echo "Command (in Terminal #3):"
echo ""
echo "  ${BOLD}cd $NEOBOT_HOME/whatsapp-service${RESET}"
echo "  ${BOLD}npm install 2>&1 | tail -5${RESET}"
echo "  ${BOLD}npm start${RESET}"
echo ""
echo -e "${YELLOW}Expected Output:${RESET}"
echo "  🚀 NEOBOT - WhatsApp Service PRODUCTION v3.0"
echo "  Backend: http://localhost:8000"
echo "  Tenant: 1"
echo "  Port: 3001"
echo "  ✅ API Endpoints:"
echo "    GET  /health"
echo "    GET  /status"
echo "    etc..."
echo ""
echo "  Then waiting for QR code scan:"
echo "  📱 SCANNER LE QR CODE"
echo ""
echo -e "${YELLOW}What to Do Next:${RESET}"
echo "  1. Open WhatsApp on your phone"
echo "  2. Go to: Settings → Linked Devices"
echo "  3. Click: \"Link a Device\""
echo "  4. Scan the QR code from terminal #3"
echo "  5. Wait for: ✅ WHATSAPP CONNECTÉ ✅"
echo ""
echo -e "${YELLOW}Test WhatsApp Service:${RESET}"
echo "  ${BOLD}curl http://localhost:3001/health${RESET}"
echo ""

# ===================================================================
# FINAL STATUS CHECK
# ===================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                     📋 QUICK SERVICE CHECKLIST                        ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

echo "Terminal #1 - Backend:"
echo "  Command: ${BOLD}cd backend && source venv/bin/activate && python3 -m uvicorn main:app --reload${RESET}"
echo "  Port: 8000"
echo "  Check: ${BOLD}curl http://localhost:8000/health${RESET}"
echo ""

echo "Terminal #2 - Frontend:"
echo "  Command: ${BOLD}cd frontend && npm run dev${RESET}"
echo "  Port: 3000"
echo "  Check: ${BOLD}Open http://localhost:3000 in browser${RESET}"
echo ""

echo "Terminal #3 - WhatsApp Service:"
echo "  Command: ${BOLD}cd whatsapp-service && npm start${RESET}"
echo "  Port: 3001"
echo "  Check: ${BOLD}curl http://localhost:3001/health${RESET}"
echo "  Action: Scan QR code with WhatsApp"
echo ""

# ===================================================================
# INTEGRATION TEST
# ===================================================================

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                    🧪 INTEGRATION TEST FLOW                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

echo "Once all 3 services are running:"
echo ""
echo "1. Check Backend Health:"
echo "   ${BOLD}curl http://localhost:8000/health${RESET}"
echo ""
echo "2. Check WhatsApp Status:"
echo "   ${BOLD}curl http://localhost:3001/health${RESET}"
echo ""
echo "3. Open Frontend:"
echo "   ${BOLD}http://localhost:3000${RESET}"
echo ""
echo "4. Send Test Message (via WhatsApp):"
echo "   Send any message to the connected WhatsApp account"
echo "   Watch the logs in Terminal #3 for incoming message"
echo ""
echo "5. Check Message in Backend:"
echo "   ${BOLD}curl http://localhost:8000/api/whatsapp/messages${RESET}"
echo ""

# ===================================================================
# TROUBLESHOOTING QUICK REFERENCE
# ===================================================================

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                  🔧 QUICK TROUBLESHOOTING                             ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

echo "Backend won't start:"
echo "  ${BOLD}cd backend && python3 -m pip install --upgrade pip${RESET}"
echo "  ${BOLD}pip install -r requirements.txt${RESET}"
echo ""

echo "Frontend npm issues:"
echo "  ${BOLD}cd frontend && rm -rf node_modules package-lock.json && npm install${RESET}"
echo ""

echo "WhatsApp service errors:"
echo "  ${BOLD}cd whatsapp-service && npm run clean && npm install${RESET}"
echo "  ${BOLD}npm start${RESET}"
echo ""

echo "Port already in use:"
echo "  ${BOLD}lsof -ti:8000 | xargs kill -9${RESET}  # Kill port 8000"
echo "  ${BOLD}lsof -ti:3000 | xargs kill -9${RESET}  # Kill port 3000"
echo "  ${BOLD}lsof -ti:3001 | xargs kill -9${RESET}  # Kill port 3001"
echo ""

# ===================================================================
# USEFUL COMMANDS
# ===================================================================

echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                   📚 USEFUL DEVELOPMENT COMMANDS                      ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""

echo "View WhatsApp logs in real-time:"
echo "  ${BOLD}tail -f whatsapp-service/whatsapp-service.log${RESET}"
echo ""

echo "Reset WhatsApp service (get new QR code):"
echo "  ${BOLD}curl -X POST http://localhost:3001/api/whatsapp/reset-session${RESET}"
echo ""

echo "Check all running processes:"
echo "  ${BOLD}ps aux | grep 'python3\\|node\\|npm'${RESET}"
echo ""

echo "Kill all NéoBot services:"
echo "  ${BOLD}killall python3 node 2>/dev/null || true${RESET}"
echo ""

echo ""
echo "╔═══════════════════════════════════════════════════════════════════════╗"
echo "║                  ✅ YOU'RE READY TO START!                            ║"
echo "║                                                                       ║"
echo "║  Start 3 terminals and run each command above in order.               ║"
echo "║  Watch for all services to show ✅ HEALTHY status.                   ║"
echo "║  Scan the QR code with WhatsApp to authenticate.                     ║"
echo "║  Then test the complete flow!                                        ║"
echo "╚═══════════════════════════════════════════════════════════════════════╝"
echo ""
