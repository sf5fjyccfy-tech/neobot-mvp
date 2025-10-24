#!/bin/bash
echo "🧪 Test NéoBot Multi-Business"
echo "============================"

# Test 1: Restaurant (français)
echo "1. Créer restaurant..."
curl -X POST http://localhost:8000/api/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"Restaurant Chez Paul","email":"paul@rest.cm","phone":"+237600000001","business_type":"restaurant"}'

echo -e "\n2. Test message restaurant (français)..."
curl -X POST http://localhost:3000/simulate \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":1,"customer_phone":"+237600111111","message":"Bonjour, quel est votre menu ?"}'

# Test 2: Boutique (anglais)
echo -e "\n3. Créer boutique..."
curl -X POST http://localhost:8000/api/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"Fashion Store","email":"fashion@store.cm","phone":"+237600000002","business_type":"boutique"}'

echo -e "\n4. Test message boutique (anglais)..."
curl -X POST http://localhost:3000/simulate \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":2,"customer_phone":"+237600222222","message":"Hello, what products do you have?"}'

# Test 3: Service
echo -e "\n5. Créer service..."
curl -X POST http://localhost:8000/api/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"Réparation Téléphones","email":"repair@phone.cm","phone":"+237600000003","business_type":"service"}'

echo -e "\n6. Test message service..."
curl -X POST http://localhost:3000/simulate \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":3,"customer_phone":"+237600333333","message":"Je veux réparer mon iPhone"}'

echo -e "\n✅ Test multi-business terminé"
