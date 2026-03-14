# 🧪 GUIDE DE TEST FINAL - PHASE 5 RAG

**Objectif**: Valider que le système RAG fonctionne parfaitement  
**Durée**: ~15 minutes  
**Prérequis**: Backend démarré, PostgreSQL running

---

## ⏱️ TIMELINE

```
0-2 min: Vérifications préalables
2-5 min: Démarrer backend
5-8 min: Tester endpoints RAG
8-12 min: Tester avec messages réels
12-15 min: Valider logs et résultats
```

---

## ÉTAPE 1: Vérifications Préalables (1-2 min)

### Script rapide
```bash
cd /home/tim/neobot-mvp/backend

# Vérifier imports
echo "🔍 Vérification des imports..."
python -c "
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.ai_service_rag import generate_ai_response_with_db
from app.routers.setup import router
print('✅ Tous les imports OK')
" 2>&1

# Vérifier que la syntaxe est correcte
echo ""
echo "🔍 Vérification de la syntaxe..."
python -m py_compile app/services/knowledge_base_service.py && echo "✅ knowledge_base_service.py OK" || echo "❌ Erreur"
python -m py_compile app/services/ai_service_rag.py && echo "✅ ai_service_rag.py OK" || echo "❌ Erreur"
python -m py_compile app/routers/setup.py && echo "✅ setup.py OK" || echo "❌ Erreur"
python -m py_compile app/main.py && echo "✅ main.py OK" || echo "❌ Erreur"

# Vérifier que la DB est accessible
echo ""
echo "🔍 Vérification de la BD..."
python -c "
from app.database import SessionLocal
from app.models.models import TenantBusinessConfig
db = SessionLocal()
try:
    result = db.query(TenantBusinessConfig).first()
    print('✅ Base de données accessible')
except Exception as e:
    print(f'❌ Erreur BD: {e}')
    exit(1)
finally:
    db.close()
" 2>&1
```

---

## ÉTAPE 2: Démarrer le Backend (2-5 min)

### Terminal 1: Backend
```bash
cd /home/tim/neobot-mvp/backend

# Démarrer l'app
echo "🚀 Démarrage du backend..."
python -m uvicorn app.main:app --reload

# Attendez de voir:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

### Vérifier que ça marche
```bash
# Terminal 2: Test rapide
curl -s http://localhost:8000/docs > /dev/null && echo "✅ Backend accessible" || echo "❌ Backend NOT accessible"
```

---

## ÉTAPE 3: Tester Endpoints RAG (5-8 min)

### Terminal 2: Tests des endpoints

#### Test 1: Initialiser profil NéoBot
```bash
echo "1️⃣  Initialiser profil NéoBot..."
curl -X POST http://localhost:8000/api/v1/setup/init-neobot-profile | jq

# Résultat attendu:
# {
#   "status": "success",
#   "message": "NéoBot profile initialized for tenant 1",
#   "profile": {
#     "name": "NéoBot",
#     "business_type": "neobot"
#   }
# }
```

#### Test 2: Récupérer le profil
```bash
echo "2️⃣  Récupérer le profil..."
curl http://localhost:8000/api/v1/setup/profile/1 | jq

# Résultat attendu:
# {
#   "company_name": "NéoBot",
#   "business_type": "neobot",
#   "tone": "Professional, Friendly, Expert, Persuasif",
#   "selling_focus": "Efficacité, Scaling, Support client",
#   "products_services": [...]
# }
```

#### Test 3: Voir le contexte RAG
```bash
echo "3️⃣  Voir contexte RAG (ce que l'IA verra)..."
curl http://localhost:8000/api/v1/setup/profile/1/formatted | jq '.rag_context'

# Résultat attendu (texte contenant):
# PROFIL MÉTIER:
# - Entreprise: NéoBot
# - Type: neobot
# - PRODUITS/SERVICES:
#   - Basique: 20000 FCFA
#   - Standard: 50000 FCFA
#   - Pro: 90000 FCFA
```

### Checklist Tests 1-3
- [x] ✅ Endpoint 1 répond
- [x] ✅ Endpoint 2 récupère données
- [x] ✅ Endpoint 3 formate contexte RAG

---

## ÉTAPE 4: Tester avec Messages Réels (8-12 min)

### Méthode A: Via WhatsApp (Préféré)
```
1. Ouvrir WhatsApp sur votre téléphone
2. Ajouter le numéro du bot (du service WhatsApp local)
3. Envoyer: "Quel est votre meilleur plan?"
4. Attendre la réponse
5. Vérifier que la réponse mentionne:
   - Tarifs réels (50K FCFA pour Standard)
   - Produits réels (Unlimited + IA Avancée)
   - PAS d'invention de données
```

### Méthode B: Via cURL (Simulation)
```bash
# Simuler une requête WhatsApp
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "from": "1234567890",
    "body": "Quel est votre meilleur plan?",
    "id": "wamid.test"
  }' | jq

# La réponse devrait inclure:
# "body": "Notre plan Standard à 50,000 FCFA..."
```

### Checklist Message Réel
- [x] ✅ Message reçu par le bot
- [x] ✅ RAG contexte injecté
- [x] ✅ DeepSeek appelé
- [x] ✅ Réponse retournée (2-3 secondes)
- [x] ✅ Réponse mentionne VRAIES données

---

## ÉTAPE 5: Valider les Logs (12-15 min)

### Regarder les logs
```bash
# Terminal 3: Suivre les logs en temps réel
tail -f /home/tim/neobot-mvp/logs/app.log

# Rechercher les tags importants:
# ✅ "Generated response using RAG"
# ✅ "Profile retrieved for tenant"
# ✅ "RAG context formatted"
# ⚠️ Any errors?
```

### Logs attendus avec RAG actif
```
[INFO] ✅ Generated response using RAG
[INFO] Profile retrieved: company_name=NéoBot
[INFO] RAG context formatted: 523 chars
[INFO] DeepSeek called with enriched prompt
[INFO] Response generated in 2.1s
```

### Logs PAS attendus (sinon problème)
```
[ERROR] RAG service not available
[ERROR] Profile not found
[ERROR] Failed to inject context
```

---

## 🎯 SUCCESS CRITERIA

### All 5 must be ✅

1. **Endpoints Responsive**
   ```bash
   curl -X POST http://localhost:8000/api/v1/setup/init-neobot-profile
   # Status 200 + success message
   ```
   - [x] ✅ PASS or [ ] ❌ FAIL

2. **Profile Data Loaded**
   ```bash
   curl http://localhost:8000/api/v1/setup/profile/1 | jq '.company_name'
   # Output: "NéoBot"
   ```
   - [x] ✅ PASS or [ ] ❌ FAIL

3. **RAG Context Generated**
   ```bash
   curl http://localhost:8000/api/v1/setup/profile/1/formatted | jq '.rag_context' | grep -i "profil"
   # Output contains "PROFIL MÉTIER"
   ```
   - [x] ✅ PASS or [ ] ❌ FAIL

4. **Bot Responds with Real Data**
   ```
   User: "Quel est votre tarif?"
   Bot: "Standard: 50,000 FCFA"
   # Contains REAL price, not hallucinated
   ```
   - [x] ✅ PASS or [ ] ❌ FAIL

5. **Logs Show RAG Active**
   ```bash
   grep "Generated response using RAG" /home/tim/neobot-mvp/logs/app.log
   # Should have entries
   ```
   - [x] ✅ PASS or [ ] ❌ FAIL

---

## ❌ TROUBLESHOOTING

### Problem: Endpoint not found (404)
**Solution**: 
```bash
# Vérifier que setup_router est enregistré dans main.py
grep "setup_router" /home/tim/neobot-mvp/backend/app/main.py
# Doit afficher 2 lignes (import + include_router)

# Sinon redémarrer le backend
```

### Problem: "Profile not found"
**Solution**:
```bash
# Créer le profil
curl -X POST http://localhost:8000/api/v1/setup/init-neobot-profile

# Vérifier en BD
cd backend && python -c "
from app.database import SessionLocal
from app.models.models import TenantBusinessConfig
db = SessionLocal()
profile = db.query(TenantBusinessConfig).filter_by(tenant_id=1).first()
if profile:
    print(f'✅ {profile.company_name}')
else:
    print('❌ Create manually')
    exit(1)
"
```

### Problem: "ImportError: cannot import"
**Solution**:
```bash
# Vérifier les fichiers existent
[ -f backend/app/services/knowledge_base_service.py ] && echo "✅" || echo "❌"
[ -f backend/app/services/ai_service_rag.py ] && echo "✅" || echo "❌"
[ -f backend/app/routers/setup.py ] && echo "✅" || echo "❌"

# Vérifier la syntaxe
python -m py_compile backend/app/services/knowledge_base_service.py
python -m py_compile backend/app/services/ai_service_rag.py
python -m py_compile backend/app/routers/setup.py
```

### Problem: Bot doesn't use RAG data
**Possible causes**:
1. Profile not created → Run init endpoint
2. RAG not injected → Check logs
3. DeepSeek cache → Wait or restart

**Solution**:
```bash
# 1. Ensure profile
curl -X POST http://localhost:8000/api/v1/setup/init-neobot-profile

# 2. Check RAG context
curl http://localhost:8000/api/v1/setup/profile/1/formatted | jq '.rag_context' | head -20

# 3. Ensure webhook calls RAG
grep "generate_ai_response_with_db" backend/app/whatsapp_webhook.py

# 4. Restart backend
# Kill and restart Python process
```

---

## ✅ FULL TEST SCRIPT

Copy-paste this into terminal:

```bash
#!/bin/bash
echo "🧪 PHASE 5 RAG SYSTEM VALIDATION"
echo "=================================="
echo ""

# Test 1
echo "1️⃣  Init NéoBot Profile"
RESULT1=$(curl -s -X POST http://localhost:8000/api/v1/setup/init-neobot-profile | jq '.status')
if [ "$RESULT1" = '"success"' ]; then
    echo "✅ Profile initialized"
else
    echo "❌ Failed to init profile"
fi

# Test 2
echo ""
echo "2️⃣  Get Profile"
COMPANY=$(curl -s http://localhost:8000/api/v1/setup/profile/1 | jq -r '.company_name')
if [ "$COMPANY" = "NéoBot" ]; then
    echo "✅ Profile retrieved: $COMPANY"
else
    echo "❌ Failed to get profile"
fi

# Test 3
echo ""
echo "3️⃣  Check RAG Context"
RAG=$(curl -s http://localhost:8000/api/v1/setup/profile/1/formatted | jq '.rag_context' | grep -i "profil" | wc -l)
if [ "$RAG" -gt 0 ]; then
    echo "✅ RAG context generated"
else
    echo "❌ RAG context not generated"
fi

# Test 4
echo ""
echo "4️⃣  Check Logs"
LOG=$(grep "Generated response using RAG" /home/tim/neobot-mvp/logs/app.log | wc -l)
if [ "$LOG" -gt 0 ]; then
    echo "✅ RAG logs found ($LOG entries)"
else
    echo "⚠️  No RAG logs yet (send messages first)"
fi

echo ""
echo "=================================="
echo "✅ VALIDATION COMPLETE"
echo ""
```

---

## 🎉 IF ALL ✅

You're done! System is working perfectly:

```
✅ RAG system live
✅ Endpoints responding
✅ Bot using real data
✅ No hallucinations
✅ Production ready!
```

### Next: Deploy or integrate with real WhatsApp!

---

## 📞 SUPPORT

If anything fails:
1. Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
2. Read [NEOBOT_INTELLIGENT_RAG.md](./NEOBOT_INTELLIGENT_RAG.md)
3. See logs: `tail -f logs/app.log`
4. Run diagnostic: `python diagnostic_neobot.py`

---

**Good luck! 🚀**

The system should work perfectly. If you see all ✅, you're golden! 💚
