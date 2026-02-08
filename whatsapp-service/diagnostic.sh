#!/bin/bash

# 🔧 DIAGNOSTIC SCRIPT FOR WHATSAPP SERVICE

echo "═══════════════════════════════════════════════════════════════"
echo "🔍 WhatsApp Service Diagnostic"
echo "═══════════════════════════════════════════════════════════════"

echo -e "\n1️⃣  Network Connectivity:"
echo "   Testing WhatsApp servers..."
timeout 3 curl -I https://web.whatsapp.com 2>&1 | head -1

echo -e "\n2️⃣  DNS Resolution:"
ping -c 1 api.whatsapp.com 2>&1 | head -1

echo -e "\n3️⃣  Service Status:"
curl -s http://localhost:3001/health | jq . 2>/dev/null || echo "❌ Service not responding"

echo -e "\n4️⃣  Session Directory:"
ls -la /home/tim/neobot-mvp/whatsapp-service/whatsapp_sessions/

echo -e "\n5️⃣  Node Process:"
ps aux | grep "node src/server.js" | grep -v grep || echo "❌ No process found"

echo -e "\n6️⃣  Port 3001:"
netstat -tuln | grep 3001 || lsof -i :3001 || echo "❌ Port not in use"

echo -e "\n═══════════════════════════════════════════════════════════════"
echo "✅ Diagnostic Complete"
echo "═══════════════════════════════════════════════════════════════"
