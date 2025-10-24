#!/bin/bash
echo "🧪 Test WhatsApp Service Réel"
echo "============================="

BASE_URL="http://localhost:3001"

echo "1. Test health service..."
curl -s "$BASE_URL/health" | jq '.'

echo -e "\n2. Créer session pour tenant 1..."
curl -X POST "$BASE_URL/session/create" \
  -H "Content-Type: application/json" \
  -d '{"tenantId": 1, "businessName": "Restaurant Test"}' | jq '.'

echo -e "\n3. Vérifier QR code..."
curl -s "$BASE_URL/session/qr/1" | jq '.'

echo -e "\n4. Lister toutes les sessions..."
curl -s "$BASE_URL/sessions" | jq '.'

echo -e "\n📱 Pour voir le QR code, allez sur: $BASE_URL/session/qr/1"
echo "🔗 Ou connectez-vous via WebSocket sur: ws://localhost:3002"
