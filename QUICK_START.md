# 🚀 DÉMARRAGE RAPIDE - NEOBOT MVP

## ✅ État Actuel
- **Backend**: ✅ FastAPI (Python) - Port 8000
- **Frontend**: ✅ Next.js (React/TypeScript) - Port 3000  
- **WhatsApp**: ✅ Baileys Service - Port 3001
- **Database**: ✅ PostgreSQL - localhost:5432

---

## 📋 Démarrage en 3 Étapes

### Étape 1️⃣ : Backend FastAPI (Terminal 1)
```bash
cd ~/neobot-mvp/backend
uvicorn app.main:app --port 8000
```

**Output attendu:**
```
INFO:     Started server process [PID]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ **Tester:** `curl http://localhost:8000/health`

---

### Étape 2️⃣ : Frontend Next.js (Terminal 2)
```bash
cd ~/neobot-mvp/frontend
npm run dev
```

**Output attendu:**
```
✓ Ready in 14.1s
- Local:        http://localhost:3000
```

✅ **Tester:** Ouvre http://localhost:3000 dans le navigateur

---

### Étape 3️⃣ : WhatsApp Service (Terminal 3)
```bash
cd ~/neobot-mvp/whatsapp-service
npm start
```

**Output attendu:**
```
🚀 Service WhatsApp en ligne sur http://localhost:3000
⏳ En attente de scan...
[QR Code s'affiche ici]
```

---

## 📱 Connecter WhatsApp (IMPORTANT)

Quand tu lances le service WhatsApp, un **QR Code** s'affiche dans la console.

**Sur ton téléphone:**
1. Ouvre **WhatsApp**
2. Va à **Menu** → **Appareils connectés** → **Connecter un appareil**
3. Scanne le QR Code de la console
4. Attends la connexion (2-3 secondes)

**Tu veras:**
```
✅ WhatsApp connecté ! Prêt à recevoir des messages.
```

---

## 🧪 Tests Rapides

### Backend API
```bash
# Health check
curl http://localhost:8000/health

# API Docs
open http://localhost:8000/docs
```

### Frontend
```bash
# Ouvre dans le navigateur
open http://localhost:3000
```

### WhatsApp Service
```bash
# Health check
curl http://localhost:3001/health

# Créer une nouvelle session
curl -X POST http://localhost:3001/session/create
```

---

## 🔗 Endpoints Clés

| Service | URL | Purpose |
|---------|-----|---------|
| Backend | `http://localhost:8000` | FastAPI REST API |
| Frontend | `http://localhost:3000` | Next.js App |
| WhatsApp | `http://localhost:3001` | Message Service |
| API Docs | `http://localhost:8000/docs` | Swagger UI |

---

## 📊 Architecture

```
User (Browser)
    ↓
Frontend (Next.js:3000)
    ↓
Backend (FastAPI:8000)
    ↓
├─ Database (PostgreSQL)
├─ WhatsApp Service (Baileys:3001)
└─ AI (DeepSeek API)
```

---

## ⚠️ Problèmes Courants

### Frontend affiche 404
**Solution:** Rafraîchis la page (Ctrl+R)

### WhatsApp ne se connecte pas
**Solution:** 
1. Vérifie que tu as scanné le QR code correctement
2. Relance le service: `npm start`
3. Scanne un nouveau QR code

### Backend ne démarre pas
**Solution:**
```bash
# Vérifie que PostgreSQL tourne
sudo systemctl status postgresql

# Redémarre le backend
uvicorn app.main:app --reload --port 8000
```

---

## 🎯 Prochaines Étapes

- [ ] Connecter WhatsApp avec QR code
- [ ] Tester l'envoi de message via API
- [ ] Vérifier la communication Backend ↔ Frontend
- [ ] Configurer GitHub Secrets pour CI/CD
- [ ] Déployer en production

---

## 📚 Documentation

- **SECRETS_MANAGEMENT.md** → Gestion des clés API
- **PROJECT_COMPLETE.md** → État du projet
- **VERIFICATION_COMPLETE.md** → Tests de vérification
- **AUDIT_COMPLETE.md** → Audit technique

---

**Questions ?** Vérifie les logs dans chaque terminal et cherche les messages d'erreur ! 🔍
