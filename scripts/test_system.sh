#!/bin/bash
echo "🧪 Test du système complet NéoBot..."

# Test 1: Health check backend
echo "Test 1: Backend health..."
curl -s http://localhost:8000/health || echo "❌ Backend non accessible"

# Test 2: Health check WhatsApp
echo "Test 2: WhatsApp simulator health..."
curl -s http://localhost:3000/health || echo "❌ WhatsApp simulator non accessible"

# Test 3: Créer un tenant de test
echo "Test 3: Création tenant de test..."
curl -X POST "http://localhost:8000/api/tenants" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Restaurant Test",
       "email": "test@restaurant.cm",
       "phone": "+237600000001",
       "business_type": "restaurant"
     }'

# Test 4: Simuler un message
echo "Test 4: Simulation message WhatsApp..."
curl -X POST "http://localhost:3000/simulate" \
     -H "Content-Type: application/json" \
     -d '{
       "tenant_id": 1,
       "customer_phone": "+237600000000",
       "message": "Bonjour, quel est votre menu ?"
     }'

echo "✅ Tests terminés. Vérifiez les réponses ci-dessus."
