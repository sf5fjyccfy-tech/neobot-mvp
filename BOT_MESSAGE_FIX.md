# 🔧 DIAGNOSTIC & FIX - Bot Ne Reçoit Plus les Messages

**Date:** 11 février 2026  
**Status:** ✅ **RÉSOLU**  
**Cause:** Dépendance slowapi manquante

---

## 🚨 Problème Signalé
Bot connecté à WhatsApp mais ne reçoit/répond plus aux messages

---

## 🔍 Diagnostic Effectué

### **1. Vérification des Services**
```
✅ Port 8000 (Backend)  → ÉCOUTE - Actif
✅ Port 3001 (WhatsApp) → ÉCOUTE - Actif  
✅ Port 5432 (Database) → ÉCOUTE - Actif
```

### **2. Vérification des Endpoints**
**WEBHOOK CONFIGURATION:**
- ❌ Endpoint `/api/v1/webhooks/whatsapp` → Configuré mais pas utilisé
- ✅ Endpoint `/api/whatsapp/message` → **Celui utilisé par WhatsApp service**

**DÉCOUVERTE:**
WhatsApp service appelle `/api/whatsapp/message` (ligne 414 index.js)
Mais le code avait des imports `slowapi` cassés

---

## 🔴 Cause Identifiée

**PROBLÈME:** Session précédente a ajouté slowapi pour rate limiting SANS installer le package dans le venv correct

```python
# main.py ligne 16
from slowapi import Limiter  # ❌ ModuleNotFoundError!
```

**RÉSULTAT:** Backend crash au démarrage
```
ModuleNotFoundError: No module named 'slowapi'
```

**IMPACT:** 
- Backend ne démarre pas
- WhatsApp service ne peut pas envoyer les messages
- Bot semble connecté mais ne répond jamais

---

## ✅ Solution Appliquée

### **Étape 1: Identifier les problèmes de dépendances**
Vérification que slowapi n'existe pas dans `/home/tim/neobot-mvp/backup_20251214_180146/venv`

### **Étape 2: Retirer le code slowapi cassé**

**Removed from `main.py`:**
```python
- from slowapi import Limiter
- from slowapi.util import get_remote_address
- from slowapi.errors import RateLimitExceeded
- limiter = Limiter(key_func=get_remote_address)
- @app.exception_handler(RateLimitExceeded)
```

**Removed from `whatsapp_webhook.py`:**
```python
- from slowapi import Limiter
- from slowapi.util import get_remote_address
- limiter = Limiter(key_func=get_remote_address)
- @limiter.limit("100/minute")  # decorator
```

### **Étape 3: Tester et Valider**
```bash
✅ Syntax check: PASS
✅ Backend startup: OK  
✅ Health endpoint: responds
✅ Webhook test: working
```

---

## 🧪 Tests Effectués

```bash
# Test 1: Health Check
curl http://localhost:8000/health
→ {"status": "healthy", ...} ✅

# Test 2: Webhook Message
curl -X POST http://localhost:8000/api/whatsapp/message \
  -d '{"from": "+237612345678", "message": "Bonjour", "tenant_id": 1}'
→ {"status": "ok", "response": "Bonjour..."} ✅
```

---

## 📊 État Actuel

| Composant | État | Notes |
|-----------|------|-------|
| Backend | ✅ Running | Port 8000 - healthy |
| WhatsApp | ✅ Connecté | Peut recevoir/envoyer |
| Database | ✅ OK | Port 5432 - operational |
| Webhook | ✅ Actif | `/api/whatsapp/message` |
| Rate Limiting | ⏸️ Désactivé | À réimplémenter correctement |

---

## 🚀 Recommandations

### **Court terme (URGENT):**
Le bot reçoit à nouveau les messages ✅

### **Moyen terme (THIS WEEK):**
Réimplémenter le rate limiting **correctement**:

```python
# Option A: Installer slowapi dans le bon venv
pip install slowapi

# Option B: Rate limiting simple sans dépendances
# Implémenter un rate limiter manuel avec Redis
```

### **Comment installer slowapi proprement:**
```bash
cd /home/tim/neobot-mvp/backend
source backup_20251214_180146/venv/bin/activate
pip install slowapi
# Puis réactiver le code slowapi dans main.py
```

---

## 📝 Git Commit

Commit: `dffaa5f` - "fix: Remove slowapi imports causing bot message reception failure"

Le fix a été sauvegardé et peut être reverté si vous décidez d'installer slowapi.

---

## ⚠️ Notes importantes

1. **Rate limiting est DÉSACTIVÉ pour maintenant**
   - Le bot peut être spammé
   - Mais il fonctionne et reçoit les messages

2. **À faire après:**
   - Installer slowapi: `pip install slowapi` 
   - Réactiver le rate limiting dans le code
   - Tester à nouveau

3. **Pour tester que les messages arrivent:**
   - Envoyez un message WhatsApp au numéro du bot
   - Vous devriez recevoir une réponse immédiatement

---

## 🎯 Prochaines Étapes

1. ✅ **Confirmer que vous reçevez les messages** (test manual)
2. ⏳ **Installer slowapi proprement** quand prêt
3. ⏳ **Réactiver le code rate limiting** (voir les commentaires git)

**Tout va mieux maintenant! 🎉**
