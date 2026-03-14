#!/bin/bash

# Force restart WhatsApp service - nuclear option
echo "🔥 FORCE RESTART - Nuclear Option"
echo "═══════════════════════════════════════════"

# Check if port 3001 is in use
if lsof -i :3001 >/dev/null 2>&1 || netstat -tlnp 2>/dev/null | grep -q :3001; then
    echo "⚠️  Port 3001 is in use. Killing..."
    fuser -k 3001/tcp 2>/dev/null || echo "fuser failed, trying alternatives..."
fi

# Kill all node processes
echo "🔪 Killing all Node.js processes..."
pkill -9 node 2>/dev/null
pkill -9 -f "whatsapp-production" 2>/dev/null
pkill -9 -f "npm" 2>/dev/null

# Wait for processes to die
sleep 3

# Verify port is free
if lsof -i :3001 >/dev/null 2>&1; then
    echo "❌ Port 3001 STILL IN USE! Manual intervention needed."
    echo "Run: sudo fuser -k 3001/tcp"
    exit 1
fi

echo "✅ Port 3001 is now free"

# Clean up old sessions
echo "🧹 Cleaning old sessions..."
cd "$(dirname "$0")"
rm -rf auth_info_baileys .wwebjs_auth session sessions.json 2>/dev/null

# Remove stale PID file
rm -f whatsapp.pid 2>/dev/null

# Start fresh
echo ""
echo "🚀 Starting WhatsApp Service..."
echo ""

# Start with exec to replace shell process
exec node whatsapp-production.js
