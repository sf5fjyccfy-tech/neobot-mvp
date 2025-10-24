# NÉOBOT V2 - GUIDE COMPLET

## 🚀 NOUVEAUX PLANS ET FONCTIONNALITÉS

### Plans Disponibles
- **BASIQUE**: 20,000 FCFA - 1,000 messages - WasenderAPI
- **STANDARD**: 50,000 FCFA - 1,500 messages - WhatsApp Business API  
- **PRO**: 90,000 FCFA - 3,000 messages - WhatsApp Business API Premium

### Essais Gratuits
- **Basique**: 3 jours
- **Standard**: 5 jours  
- **Pro**: 7 jours

## 🔧 CONFIGURATION WHATSAPP

### Plan Basique (WasenderAPI)
```bash
# Configuration automatique avec token NEOBOT partagé
# Aucune configuration client requise
```

### Plans Standard/Pro (Business API)
Les clients doivent fournir leurs propres tokens:

1. **Access Token**: Token d'accès Meta Business
2. **Phone Number ID**: ID du numéro WhatsApp Business

Configuration via API:
```bash
curl -X POST "http://localhost:8000/api/tenants/1/whatsapp/configure" \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "EAAXxx...",
    "phone_number_id": "123456789"
  }'
```

## 💳 PAIEMENTS

### Providers Supportés
- **PawaPay**: Paiements automatisés
- **Orange Money**: Manuel avec confirmation

### Initier un paiement
```bash
curl -X POST "http://localhost:8000/api/tenants/1/payment/initiate"
```

## 📊 ENDPOINTS API PRINCIPAUX

### Gestion Tenants
- `GET /api/tenants` - Liste des tenants
- `POST /api/tenants` - Créer un tenant
- `GET /api/tenants/{id}` - Détails d'un tenant
- `POST /api/tenants/{id}/upgrade` - Changer de plan

### Configuration WhatsApp
- `GET /api/tenants/{id}/whatsapp/status` - Statut WhatsApp
- `POST /api/tenants/{id}/whatsapp/configure` - Configurer tokens

### Messages
- `POST /api/process-message` - Traiter un message WhatsApp

### Plans et Paiements
- `GET /api/plans` - Plans disponibles
- `POST /api/tenants/{id}/payment/initiate` - Initier paiement

## 🔐 SÉCURITÉ

### Chiffrement des Tokens
Les tokens WhatsApp clients sont chiffrés avec Fernet:
```python
from cryptography.fernet import Fernet
# Clé générée automatiquement dans ENCRYPTION_KEY
```

### Variables d'Environnement
```bash
# Base
DATABASE_URL=postgresql://neobot:password123@localhost:5432/neobot
ENCRYPTION_KEY=généré-automatiquement

# APIs
WASENDER_API_KEY=votre-cle-wasender
PAWAPAY_API_KEY=votre-cle-pawapay
ORANGE_MONEY_API_KEY=votre-cle-orange-money
```

## 🧪 TESTS

Lancez les tests complets:
```bash
./test_neobot_v2.sh
```

## 🚀 DÉMARRAGE

1. **Services Docker**:
```bash
docker-compose up -d
```

2. **Backend**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

3. **Tests**:
```bash
./test_neobot_v2.sh
```

## 📈 DIFFÉRENCES V1 → V2

### Nouvelles Fonctionnalités
- ✅ 3 plans tarifaires optimisés
- ✅ WasenderAPI pour plan Basique  
- ✅ Tokens clients chiffrés pour Standard/Pro
- ✅ Service de paiements intégré
- ✅ IA contextuelle améliorée
- ✅ Gestion des limites par plan
- ✅ API complète pour gestion des plans

### Architecture Améliorée
- ✅ Services modulaires (WhatsApp, Payment)
- ✅ Chiffrement sécurisé des credentials
- ✅ Gestion d'erreurs robuste
- ✅ Tests automatisés complets

## 🎯 PROCHAINES ÉTAPES

1. Tester avec vrais clients Basique
2. Intégrer vraies clés WasenderAPI/PawaPay
3. Développer interface frontend pour configuration
4. Déployer en production (Fly.io + Vercel)
