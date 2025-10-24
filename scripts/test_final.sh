#!/bin/bash
echo "Test final NéoBot"

echo "1. Test backend health..."
curl -s http://localhost:8000/health

echo -e "\n2. Test WhatsApp health..."
curl -s http://localhost:3000/health

echo -e "\n3. Créer tenant test..."
curl -X POST http://localhost:8000/api/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Restaurant","email":"test@rest.cm","phone":"+237600000000","business_type":"restaurant"}'

echo -e "\n4. Simuler message..."
curl -X POST http://localhost:3000/simulate \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":1,"customer_phone":"+237600000001","message":"Bonjour, quel est votre menu ?"}'

echo -e "\n\nTest terminé!"
