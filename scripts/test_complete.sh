#!/bin/bash
echo "🧪 Test complet du système"

echo "1. Backend..."
curl -s http://localhost:8000/health || echo "Backend KO"

echo "2. WhatsApp..."
curl -s http://localhost:3000/health || echo "WhatsApp KO"

echo "3. Création tenant..."
curl -X POST http://localhost:8000/api/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Final","email":"final@test.cm","phone":"+237600000000","business_type":"restaurant"}'

echo "4. Simulation message..."
curl -X POST http://localhost:3000/simulate \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":1,"customer_phone":"+237600000000","message":"Bonjour, quel est votre menu ?"}'

echo "✅ Tests terminés"
