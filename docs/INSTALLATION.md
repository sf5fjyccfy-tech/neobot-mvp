# 🚀 NéoBot - WhatsApp Assistant avec IA

**Version:** 1.0.0 Beta  
**Statut:** Production-Ready

---

## 📋 Architecture

```
┌─────────────────────────────────────────────┐
│           Frontend (Next.js)                │
│        http://localhost:3000                │
└──────────────┬──────────────────────────────┘
               │
┌──────────────▼──────────────────────────────┐
│          Backend (FastAPI)                  │
│       http://localhost:8000                 │
└──────┬────────────────────────────┬─────────┘
       │                            │
       ▼                            ▼
┌──────────────┐         ┌──────────────────┐
│  PostgreSQL  │         │ WhatsApp Service │
│  :5432       │         │  http://3001     │
└──────────────┘         └──────────────────┘
                                  │
                                  ▼
                          ┌─────────────────┐
                          │ Baileys/WhatsApp│
                          │  (Real WhatsApp)│
                          └─────────────────┘
```

---

## 🛠️ Installation rapide

### Option 1: Docker (Recommandé)

```bash
# Copier et personnaliser les variables d'environnement
cp .env.example .env
# Éditer .env avec tes clés API

# Lancer tous les services
docker-compose up -d

# Vérifier le statut
curl http://localhost:8000/health
curl http://localhost:3001/health
```

### Option 2: Installation locale

#### **Prérequis:**
- Node.js 20+
- Python 3.10+
- PostgreSQL 12+

#### **Étape 1: Backend**

```bash
cd backend

# Créer l'environnement Python
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Initialiser la DB
python3 -c "from app.database import init_db; init_db()"

# Démarrer le serveur
uvicorn app.main:app --reload --port 8000
```

#### **Étape 2: WhatsApp Service**

```bash
cd whatsapp-service

# Installer les dépendances Node
npm install

# Démarrer le service
npm start
```

#### **Étape 3: Frontend**

```bash
cd frontend

# Installer les dépendances
npm install

# Démarrer le serveur dev
npm run dev
```

---

## 🔐 Variables d'environnement

Crée un fichier `.env` à la racine:

```env
# Database
DATABASE_URL=postgresql://neobot:password@localhost:5432/neobot_db

# API Keys
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx

# Ports
BACKEND_PORT=8000
WHATSAPP_PORT=3001
FRONTEND_PORT=3000

# Config
DEBUG_MODE=true
APP_ENV=development
```

---

## 📡 API Endpoints

### **Health Checks**

```bash
# Backend health
curl http://localhost:8000/health

# WhatsApp service health
curl http://localhost:3001/health
```

### **Tenants**

```bash
# Créer un tenant
curl -X POST http://localhost:8000/api/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mon Business",
    "email": "owner@business.com",
    "phone": "+237123456789",
    "business_type": "restaurant"
  }'

# Récupérer un tenant
curl http://localhost:8000/api/tenants/1
```

### **Messages WhatsApp**

```bash
# Webhook: recevoir un message et générer une réponse
curl -X POST http://localhost:8000/api/whatsapp/message \
  -H "Content-Type: application/json" \
  -d '{
    "from": "237123456789",
    "message": "Bonjour!",
    "tenant_id": 1
  }'
```

### **Conversations**

```bash
# Lister les conversations
curl http://localhost:8000/api/conversations/1

# Récupérer les messages
curl http://localhost:8000/api/messages/1
```

---

## 🤖 Fonctionnalités

- ✅ Connexion WhatsApp via Baileys (real WhatsApp, pas API officielle)
- ✅ Réception de messages en temps réel
- ✅ Réponses générées par DeepSeek AI
- ✅ Fallback intelligent si l'IA est indisponible
- ✅ Gestion multi-tenant (plusieurs businesses)
- ✅ Stockage des conversations en PostgreSQL
- ✅ Dashboard pour monitorer les messages
- ✅ Health checks et monitoring

---

## 🧪 Tests

### Test de flux complet

```bash
# 1. Démarrer tous les services
docker-compose up -d

# 2. Attendre la connexion WhatsApp
# Vous verrez un QR code dans les logs du service WhatsApp
# Scannez-le avec WhatsApp mobile

# 3. Envoyer un message de test
curl -X POST http://localhost:8000/api/whatsapp/message \
  -H "Content-Type: application/json" \
  -d '{
    "from": "237123456789",
    "message": "Bonjour, comment ça va?",
    "tenant_id": 1
  }'

# 4. Vérifier la réponse
curl http://localhost:8000/api/messages/1
```

### Logs en temps réel

```bash
# Backend
docker logs -f neobot_backend

# WhatsApp service
docker logs -f neobot_whatsapp

# Frontend
docker logs -f neobot_frontend

# PostgreSQL
docker logs -f neobot_postgres
```

---

## 🚨 Troubleshooting

### "Database connection refused"

```bash
# Vérifier que PostgreSQL est en cours
docker-compose ps postgres

# Redémarrer PostgreSQL
docker-compose restart postgres
```

### "WhatsApp: Code 405/408 error"

```bash
# Supprimer les credentials WhatsApp et relancer
rm -rf auth_info_baileys/*
docker-compose restart whatsapp

# Attendre le QR code et scannez
```

### "DeepSeek API error"

```bash
# Vérifier la clé API dans .env
cat .env | grep DEEPSEEK_API_KEY

# Vérifier le solde de la clé
curl -H "Authorization: Bearer sk-xxxx" \
  https://api.deepseek.com/v1/models
```

### Frontend ne charge pas

```bash
# Vérifier que les variables d'environnement sont définies
echo $NEXT_PUBLIC_API_URL

# Redémarrer le frontend
docker-compose restart frontend
```

---

## 📊 Monitoring

### Dashboard
http://localhost:3000

### API Documentation
http://localhost:8000/docs

### WhatsApp Service Status
http://localhost:3001/status

### PostgreSQL
Connectez-vous avec:
- **Host:** localhost
- **Port:** 5432
- **User:** neobot
- **Password:** neobot_secure_password
- **Database:** neobot_db

---

## 🔄 Mise à jour

Pour mettre à jour les services:

```bash
# Arrêter les services
docker-compose down

# Mettre à jour le code
git pull origin main

# Relancer
docker-compose up -d
```

---

## 📦 Déploiement Production

Pour un déploiement en production:

1. **Variables d'environnement sécurisées**
   ```bash
   # Utiliser des secrets dans le cloud (AWS Secrets Manager, etc.)
   ```

2. **SSL/HTTPS**
   ```bash
   # Configurer Nginx ou Traefik comme reverse proxy
   ```

3. **Monitoring**
   ```bash
   # Ajouter Prometheus, Grafana, etc.
   ```

4. **Backups**
   ```bash
   # Configurer des backups automatiques de PostgreSQL
   ```

---

## 📞 Support

- **Documentation:** [Voir wiki](./docs/)
- **Issues:** [GitHub Issues](https://github.com/yourrepo/issues)
- **Email:** support@neobot.io

---

## 📄 Licence

MIT License - Voir [LICENSE](./LICENSE) pour les détails.

---

**Dernière mise à jour:** 17 Décembre 2025  
**Version:** 1.0.0 Beta
