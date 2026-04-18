# 🔍 DIAGNOSTIC COMPLET — NEOBOT PRODUCTION (VPS 178.104.163.245)

**Date:** 17 avril 2026  
**Environnement:** Production VPS (Hetzner) + Neon PostgreSQL  
**Status:** ⚠️ **FONCTIONNEL MAIS CASSÉ** — Plusieurs bloqueurs critiques

---

## 📋 RÉSUMÉ EXÉCUTIF

| Composant | Status | Severity | Blocage |
|-----------|--------|----------|---------|
| Backend (FastAPI) | ✅ Running | - | ✅ Fonctionnel |
| WhatsApp Service | ✅ Running | 🔴 Critical | ❌ **Messages reçus OK, envoyés KO** |
| Database | ✅ Connected | 🔴 Critical | ⚠️ **SSL errors périodiques** |
| Auth Endpoints | ⚠️ Existe | 🔴 Critical | ❌ **/signup N'EXISTE PAS** |
| API Schema | ❌ Mismatch | 🟡 High | ❌ **Trop de champs requis** |
| Environment Loading | ⚠️ Partial | 🟡 High | ⚠️ **python-dotenv parse error** |

---

## 🔴 PROBLÈME #1 : WhatsApp Webhook REJETTE les messages (401 Unauthorized)

### Symptômes
- ✅ WhatsApp service connecté (status: connected=true)
- ✅ Messages entrants reçus par backend
- ❌ **Backend retourne HTTP 401 "Invalid webhook signature"**
- ❌ WhatsApp logs: `Primary webhook endpoint failed { error: '' }`
- ❌ **Messages ne sont PAS envoyés aux clients**

### Root Cause
```python
# whatsapp_webhook.py ligne 35
WEBHOOK_SECRET = os.getenv("WHATSAPP_WEBHOOK_SECRET") or os.getenv("WHATSAPP_SECRET_KEY") or ""
```

**Le backend charge WEBHOOK_SECRET=`""`** (string vide au lieu du secret) parce que:
1. Le processus uvicorn actuel (PID 58444) ne demarre pas avec les variables d'env exportées
2. python-dotenv échoue à parser le fichier .env (parsing error ligne 24)
3. WHATSAPP_WEBHOOK_SECRET n'est pas disponible en tant que variable d'environnement OS
4. La signature est vide → validation échoue → HTTP 401

### Vérification
```bash
# Sur VPS:
ps aux | grep uvicorn
# Montre: python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 1
# SANS export des variables d'env

# Donc:
echo $WHATSAPP_WEBHOOK_SECRET  # Vide!
```

### Impact
- ⚠️ Les messages entrants sont reçus mais ignorés
- ⚠️ Les clients n'ont pas de réponse automatique
- ⚠️ **Le bot est en lecture-seule**

### Fix (IMMÉDIAT)
Redémarrer le backend avec les variables d'env exportées :
```bash
# Sur VPS:
source /root/neobot-mvp/.venv/bin/activate
export WHATSAPP_WEBHOOK_SECRET='neobot_whatsapp_secret_2024'
export DATABASE_URL='postgresql://...'
# ... autres variables ...
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

---

## 🔴 PROBLÈME #2 : Database SSL "SSL connection has been closed unexpectedly"

### Symptômes
```
psycopg2.OperationalError: SSL connection has been closed unexpectedly
```
Apparaît dans les logs ~1 heure après le démarrage du backend.

### Root Cause
```python
# database.py ligne 35
pool_recycle=3600  # Recycler les connexions après 3600 secondes (1 heure)
```

Et dans .env :
```
DATABASE_URL=postgresql://...?sslmode=require&channel_binding=require
```

**Neon ferme les connexions idle après ~10-15 minutes.**
- À 3600s (1h), le backend essaie de recycler une connexion vieille de 1h
- Neon l'a fermée il y a longtemps
- SQLAlchemy tente de faire `rollback()` sur une connexion fermée
- **Résultat: `SSL connection has been closed unexpectedly`**

### Impact
- ⚠️ Erreurs de base de données intermittentes
- ⚠️ Les requêtes API échouent aléatoirement après 1h
- ⚠️ Les utilisateurs voient des "500 Internal Server Error"

### Fix
**Option A (RAPIDE):** Réduire pool_recycle
```env
# Change de 3600s à 600s (10 minutes)
DATABASE_POOL_RECYCLE=600
```

**Option B (MEILLEUR):** Supprimer `channel_binding=require` (non supporté par Neon)
```env
# Change de:
DATABASE_URL=postgresql://...?sslmode=require&channel_binding=require

# Vers:
DATABASE_URL=postgresql://...?sslmode=require
```

---

## 🔴 PROBLÈME #3 : Endpoint `/api/auth/signup` N'EXISTE PAS (404 Not Found)

### Symptômes
```bash
curl -X POST http://178.104.163.245:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test1234!"}'

# Résultat:
# HTTP/1.1 404 Not Found
# {"error":"Not Found","status":"error","timestamp":"..."}
```

### Root Cause
L'endpoint s'appelle **`/api/auth/register`** pas `/signup`.

```python
# backend/app/routers/auth.py ligne 208
@router.post("/register", response_model=TokenResponse)  # ← C'est ici qu'il faut appeler
async def register(request: Request, body: RegisterRequest, ...):
    ...
```

Le router est préfixé avec `/api/auth` donc le chemin complet est:
- ✅ `/api/auth/register` ← CORRECT
- ❌ `/api/auth/signup` ← N'EXISTE PAS

### Impact
- ❌ Frontend ne peut pas inscrire les utilisateurs si elle appelle `/signup`
- ❌ Les utilisateurs reçoivent une erreur 404 à l'inscription

### Fix
**Option A (Frontend):** Utiliser le bon endpoint
```javascript
// Change de:
fetch('/api/auth/signup', {...})

// Vers:
fetch('/api/auth/register', {...})
```

**Option B (Backend):** Ajouter un alias `/signup` qui appelle `/register` (NOT RECOMMENDED)

---

## 🟡 PROBLÈME #4 : `/api/auth/register` demande trop de champs (422 Validation Error)

### Symptômes
```bash
curl -X POST http://178.104.163.245:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@test.com","password":"Test1234!"}'

# Résultat:
# HTTP/1.1 422 Unprocessable Content
# {"detail":[
#   {"type":"missing","loc":["body","full_name"],"msg":"Field required"},
#   {"type":"missing","loc":["body","tenant_name"],"msg":"Field required"},
#   {"type":"missing","loc":["body","business_type"],"msg":"Field required"}
# ]}
```

### Root Cause
```python
# backend/app/routers/auth.py ligne 48-52
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str              # ← Requis (pas optionnel)
    tenant_name: str            # ← Requis
    business_type: str          # ← Requis
    whatsapp_number: str | None = None  # ← Optionnel
```

L'endpoint demande **5 champs** mais la plupart des frontends n'envoient que **2** (email + password).

### Impact
- ❌ Inscription échoue si le frontend n'envoie que email + password
- ❌ Validation 422 Unprocessable Content
- ⚠️ Mauvaise UX — on demande trop d'informations au signup

### Fix
**Option A (RAPIDE - Backend):** Rendre les champs optionnels avec defaults
```python
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = "User"              # Default
    tenant_name: str = None              # Optionnel
    business_type: str = "autre"         # Default
    whatsapp_number: str | None = None
```

**Option B (Frontend):** Envoyer tous les champs requis
```javascript
{
  "email": "user@example.com",
  "password": "Test1234!",
  "full_name": "John Doe",
  "tenant_name": "My Business",
  "business_type": "retail"
}
```

---

## 🟡 PROBLÈME #5 : python-dotenv ne peut pas parser le fichier `.env` (ligne 24)

### Symptômes
```
Python-dotenv could not parse statement starting at line 24
```
Répété 4+ fois dans les logs du backend.

### Root Cause
Ligne 24 du `.env` est:
```
ALLOWED_ORIGINS=https://neobot-ai.com,https://www.neobot-ai.com,https://neobot-frontend-psi.vercel.app,http://localhost:3000,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3002
```

Elle est trop longue et python-dotenv ne peut pas la parser (limite de caractères ou format incorrect).

### Impact
- ⚠️ Les variables ne sont pas chargées via `load_dotenv()`
- ✅ Mais elles SONT disponibles en tant que variables OS (probablement via un script d'init)
- ⚠️ Logs pollués avec des warnings

### Current Status
**Les CORS origins SONT chargés correctement** (voir logs):
```
CORS allow_origins : ['https://neobot-ai.com', 'https://www.neobot-ai.com', 
                       'https://neobot-frontend-psi.vercel.app', 
                       'http://localhost:3000', 'http://localhost:3002', 
                       'http://127.0.0.1:3000', 'http://127.0.0.1:3002']
```

Donc le problème python-dotenv n'empêche pas CORS de fonctionner.

### Fix (OPTIONNEL - pour nettoyer les logs)
Mettre les origines CORS entre quotes:
```env
# Change de:
ALLOWED_ORIGINS=https://neobot-ai.com,https://www.neobot-ai.com,...

# Vers:
ALLOWED_ORIGINS="https://neobot-ai.com,https://www.neobot-ai.com,..."
```

---

## 🟢 VÉRIFICATIONS QUI PASSENT ✅

| Check | Résultat | Details |
|-------|----------|---------|
| Backend Health | ✅ 200 OK | Endpoint `/health` répond |
| WhatsApp Health | ✅ 200 OK | Service Node.js connecté |
| CORS Headers | ✅ Correct | 7 origines chargées |
| Database Connection | ✅ OK | Connexion psycopg2 valide |
| Neon Reachability | ✅ OK | Neon PostgreSQL accessible |
| TLS/Security Headers | ✅ Present | X-Frame-Options, CSP, HSTS, etc. |
| Rate Limiting | ✅ Active | Endpoints /api/auth limités |

---

## 📊 ARCHITECTURE ACTUELLE

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND                                 │
│         neobot-frontend-psi.vercel.app (Vercel)            │
└──────────────────────────┬──────────────────────────────────┘
                           │ CORS OK ✅
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                         │
│       http://178.104.163.245:8000 (Hetzner VPS)            │
│                                                             │
│  ❌ WhatsApp Webhook (SIGNATURE FAILS)                     │
│  ⚠️  Auth Endpoints (Missing /signup, too many fields)    │
│  ⚠️  Database (SSL error after 1h)                        │
│  ✅ Health Checks                                          │
│  ✅ CORS Middleware                                        │
└──────┬──────────────────────────┬──────────────────────────┘
       │                          │
       ▼                          ▼
    WhatsApp Service (3001)    Database (Neon)
    ✅ Connected           ⚠️ SSL Errors
    ❌ Webhook Auth Fails  ✅ Data OK
    ❌ Can't Send Messages
```

---

## 🚀 PRIORITÉS DE FIX (Ordre d'exécution)

### PRIORITY 1 — BLOQUEUR CRITIQUE (30 min)
**WhatsApp Webhook Authentication Failed**
- [ ] **Action:** Redémarrer backend avec variables d'env exportées
- [ ] **Raison:** Messages WhatsApp ne sont pas acceptés (401)
- [ ] **Impact:** Aucun bot ne fonctionne sans ça

```bash
# Créer un script systemd ou un wrapper qui exporte les variables
# Relancer le backend via ce script
```

### PRIORITY 2 — BLOQUEUR (15 min)
**Database SSL Errors**
- [ ] **Action:** Réduire `pool_recycle` de 3600 à 600 (ou supprimer `channel_binding`)
- [ ] **Raison:** Erreurs 500 après 1h d'utilisation
- [ ] **Impact:** Stabilité backend après mise en charge

### PRIORITY 3 — BLOQUEUR (10 min)
**Auth Endpoint Mismatch**
- [ ] **Action 1:** Vérifier que frontend appelle `/api/auth/register` (pas `/signup`)
- [ ] **Action 2:** Si non, corriger endpoint ou ajouter alias
- [ ] **Raison:** Inscription ne fonctionne pas
- [ ] **Impact:** Utilisateurs ne peuvent pas s'inscrire

### PRIORITY 4 — HAUTE (10 min)
**Auth Schema Mismatch**
- [ ] **Action:** Rendre `full_name`, `tenant_name`, `business_type` optionnels (avec defaults)
- [ ] **Raison:** Validation 422 si frontend envoie moins de champs
- [ ] **Impact:** Inscription avec moins de données

### PRIORITY 5 — NETTOYAGE (5 min)
**python-dotenv Parse Error**
- [ ] **Action:** Mettre ALLOWED_ORIGINS entre quotes
- [ ] **Raison:** Nettoyer les logs
- [ ] **Impact:** Aucun (cosmétique)

---

## ✅ CHECKLIST — Avant de déployer les fixes

- [ ] **Backup .env sur VPS** (copier vers /root/neobot-mvp/.env.backup)
- [ ] **Tester chaque fix localement d'abord** (avant sur VPS)
- [ ] **Redémarrer backend après chaque fix**
- [ ] **Vérifier les logs** pendant 5 minutes après redémarrage
- [ ] **Tester WhatsApp webhook** avec un message de test
- [ ] **Tester inscription** avec /api/auth/register

---

## 📝 LOGS CLÉS À SURVEILLER

Après chaque fix, vérifier:

```bash
# WhatsApp: Webhook signature validation
grep "Invalid webhook signature\|✅" /root/neobot-mvp/logs/backend.log | tail -10

# Database: SSL errors
grep "SSL connection\|Exception during reset" /root/neobot-mvp/logs/backend.log | tail -10

# Registration: Field validation
grep "missing\|Field required" /root/neobot-mvp/logs/backend.log | tail -10

# General health
tail -50 /root/neobot-mvp/logs/backend.log
```

---

**Prêt pour les fixes? Dis-moi par où tu veux commencer.**
