# 🔍 DIAGNOSTIC COMPLET - NEOBOT MVP

**Date:** February 2026  
**Objectif:** Identifier et résoudre TOUS les problèmes du projet

---

## 📋 CHECKLIST DES PROBLÈMES À INVESTIGUER

### 1. Backend Python (`/backend/app/`)
- [ ] Imports corrects?
- [ ] Database connection?
- [ ] Environment variables chargées?
- [ ] FastAPI routes opérationnelles?
- [ ] WhatsApp webhook configuration?

### 2. Baileys WhatsApp Service
- [ ] Service Node.js qui démarre?
- [ ] Connexion à WhatsApp Web?
- [ ] QR Code génération?
- [ ] Session persistence?
- [ ] Possibilité d'envoyer/recevoir des messages?

### 3. PostgreSQL Database
- [ ] Server démarrant?
- [ ] Tables créées?
- [ ] Connection pooling configuré?
- [ ] psycopg2-binary driver disponible?

### 4. Configuration & Secrets
- [ ] .env file présent?
- [ ] Variables d'environnement correctes?
- [ ] DeepSeek API key présent?
- [ ] Baileys configuration complète?

### 5. Integration
- [ ] Backend ↔ Database OK?
- [ ] Backend ↔ WhatsApp Service OK?
- [ ] WhatsApp Service ↔ Baileys OK?
- [ ] Message flow complet?

---

## 🚀 COMMANDES DE DIAGNOSTIC

```bash
# Test 1: Python imports
cd /home/tim/neobot-mvp/backend
python3 -c "from app.database import SessionLocal; print('✅ Database OK')"

# Test 2: FastAPI startup
cd /home/tim/neobot-mvp/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test 3: WhatsApp service
cd /home/tim/neobot-mvp/whatsapp-service
npm start

# Test 4: Health check
curl http://localhost:8000/health
curl http://localhost:3001/health
```

---

## 🎯 PROBLÈME BAILEYS SPÉCIFIQUE

### Description du problème:
"Baileys ne marchait pas et donc je ne pouvais plus connecter le service whatsapp avec le bot"

### Causes possibles:
1. **WhatsApp authentification échouée** - Session expirée ou invalide
2. **Baileys dépendance brisée** - Version incompatible ou package manquant
3. **QR Code timeout** - Délai d'authentification dépassé
4. **Webhook URL incorrect** - Backend pas accessible depuis WhatsApp service
5. **CORS issues** - Restrictions d'origine bloquant les requests

### À investiguer:
```bash
# Vérifier Baileys version
cd /home/tim/neobot-mvp/whatsapp-service
npm list @whiskeysockets/baileys

# Vérifier session files
ls -la /home/tim/neobot-mvp/whatsapp-service/sessions/

# Vérifier si Socket.io est disponible (dépendance Baileys)
npm list socket.io-client

# Test de connexion WhatsApp
curl -X POST http://localhost:3001/message \
  -H "Content-Type: application/json" \
  -d '{"phone": "+33...", "message": "test"}'
```

---

## 🔧 PLANS DE RÉSOLUTION

### Pour Baileys:
1. Vérifier et upgrade Baileys à version stable
2. Nettoyer les anciennes sessions
3. Générer nouveau QR code
4. Tester authentification
5. Valider webhook communication

### Pour Backend:
1. Vérifier .env variables
2. Tester PostgreSQL connection
3. Valider tous les imports
4. Tester FastAPI startup
5. Valider routes endpoints

### Pour Integration:
1. Tester Backend ↔ Database
2. Tester Backend ↔ WhatsApp Service
3. Tester message flow E2E
4. Valider error handling

---

## 📊 STATUS ACTUEL

- Backend: `fastapi` démarre? TBD
- Database: `PostgreSQL` accessible? TBD
- WhatsApp Service: `Node.js + Baileys` fonctionnel? TBD
- Integration: Message flow complet? TBD

---

À remplir au fur et à mesure du diagnostic...
