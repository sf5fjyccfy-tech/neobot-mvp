#!/bin/bash
echo "🧠 Test IA DeepSeek NéoBot"
echo "========================="

# Vérifier l'état de l'IA
echo "1. Test health avec IA..."
curl -s http://localhost:8000/health | jq '.'

echo -e "\n2. Créer restaurant test..."
curl -X POST http://localhost:8000/api/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Restaurant Chez Paul",
    "email":"paul@restaurant.cm",
    "phone":"+237600000001", 
    "business_type":"restaurant"
  }' | jq '.'

echo -e "\n3. Test message menu..."
curl -X POST http://localhost:3000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id":2,
    "customer_phone":"+237600111111",
    "message":"Bonjour, quel est votre menu du jour ?"
  }' | jq '.backend_response.ai_response'

echo -e "\n4. Test message prix..."
curl -X POST http://localhost:3000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id":2,
    "customer_phone":"+237600111111", 
    "message":"Combien coûte le ndolé ?"
  }' | jq '.backend_response.ai_response'

echo -e "\n5. Test conversations..."
curl -s http://localhost:8000/api/conversations/2 | jq '.conversations[0]'

echo -e "\n✅ Test IA terminé"
