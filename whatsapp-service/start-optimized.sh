#!/bin/bash

# 🚀 NEOBOT WhatsApp - Smart Startup Script

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║         🚀 NEOBOT WhatsApp Service - Smart Startup v4.0          ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to kill existing processes
cleanup() {
    echo "🛑 Cleaning up existing processes..."
    pkill -9 -f "whatsapp-service-v6-dual-mode.js" 2>/dev/null || true
    pkill -9 -f "whatsapp-service-v7-professional.js" 2>/dev/null || true
    pkill -9 -f "whatsapp-production.js" 2>/dev/null || true
    sleep 2
}

# ═══════════════════════════════════════════════════════════════════
# STEP 1: Check dependencies
# ═══════════════════════════════════════════════════════════════════

echo "📦 Step 1: Checking dependencies..."
if [[ ! -d "node_modules" ]]; then
    echo "   Installing npm packages..."
    npm install --production
    echo "   ✅ Dependencies installed"
else
    echo "   ✅ Dependencies already installed"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# STEP 2: Run diagnostics
# ═══════════════════════════════════════════════════════════════════

echo "🔍 Step 2: Running system diagnostics..."
echo ""

if [[ -f "diagnostic-system.sh" ]]; then
    chmod +x diagnostic-system.sh
    ./diagnostic-system.sh || true
else
    echo "⚠️  Diagnostic script not found"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# STEP 3: Prepare environment
# ═══════════════════════════════════════════════════════════════════

echo "⚙️  Step 3: Preparing environment..."

# Clean old sessions if requested
if [[ "$1" == "--clean" ]]; then
    echo "   Cleaning old auth files..."
    rm -rf auth_info_baileys .wwebjs_auth sessions.json 2>/dev/null || true
    echo "   ✅ Authentication cache cleared"
fi

# Create env if missing
if [[ ! -f ".env" ]]; then
    echo "   Creating .env file..."
    cat > .env << 'EOF'
# Backend API
BACKEND_URL=http://localhost:8000

# Service Configuration
PORT=3001
TENANT_ID=1
LOG_LEVEL=info

# Session Management
SESSION_TIMEOUT=259200000
EOF
    echo "   ✅ .env file created (update with your settings)"
else
    echo "   ✅ .env file exists"
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
# STEP 4: Cleanup old processes
# ═══════════════════════════════════════════════════════════════════

echo "🛑 Step 4: Cleaning up old processes..."
cleanup
echo "   ✅ Old processes killed"

echo ""

# ═══════════════════════════════════════════════════════════════════
# STEP 5: Start service
# ═══════════════════════════════════════════════════════════════════

echo "🚀 Step 5: Starting WhatsApp service..."
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo ""

# Canonical runtime entrypoint
node whatsapp-production.js

# If we get here, the service stopped
echo ""
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo -e "${RED}Service stopped.${NC}"
echo ""
echo "To restart:"
echo "  bash start-optimized.sh"
echo ""
echo "To reset authentication and start fresh:"
echo "  bash start-optimized.sh --clean"
echo ""
