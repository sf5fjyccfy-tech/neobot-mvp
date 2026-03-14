# 🔍 CHECKLIST PRÉ-TEST SYSTÈME RAG

**Date**: 2025-01-14  
**Objectif**: Vérifier tous les éléments avant tests réels  
**Temps estimé**: 5-10 minutes

---

## ✅ VÉRIFICATIONS PRÉ-TEST

### 1. Fichiers Créés
```bash
echo "Vérification des fichiers..."

# Knowledge Base Service
[ -f /home/tim/neobot-mvp/backend/app/services/knowledge_base_service.py ] && echo "✅ knowledge_base_service.py" || echo "❌ knowledge_base_service.py MANQUANT"

# AI Service RAG
[ -f /home/tim/neobot-mvp/backend/app/services/ai_service_rag.py ] && echo "✅ ai_service_rag.py" || echo "❌ ai_service_rag.py MANQUANT"

# Setup Router
[ -f /home/tim/neobot-mvp/backend/app/routers/setup.py ] && echo "✅ setup.py routers" || echo "❌ setup.py routers MANQUANT"

# Test Scripts
[ -f /home/tim/neobot-mvp/test_rag_system.sh ] && echo "✅ test_rag_system.sh" || echo "❌ test_rag_system.sh MANQUANT"

# Documentation
[ -f /home/tim/neobot-mvp/NEOBOT_INTELLIGENT_RAG.md ] && echo "✅ NEOBOT_INTELLIGENT_RAG.md" || echo "❌ NEOBOT_INTELLIGENT_RAG.md MANQUANT"

[ -f /home/tim/neobot-mvp/PHASE_5_INTELLIGENT_COMPLETE.md ] && echo "✅ PHASE_5_INTELLIGENT_COMPLETE.md" || echo "❌ PHASE_5_INTELLIGENT_COMPLETE.md MANQUANT"
```

### 2. Sintaxe Python
```bash
echo ""
echo "Vérification de la syntaxe Python..."

cd /home/tim/neobot-mvp/backend

# Vérifier knowledge_base_service.py
python -m py_compile app/services/knowledge_base_service.py && echo "✅ knowledge_base_service.py - Syntaxe OK" || echo "❌ Erreur de syntaxe"

# Vérifier ai_service_rag.py
python -m py_compile app/services/ai_service_rag.py && echo "✅ ai_service_rag.py - Syntaxe OK" || echo "❌ Erreur de syntaxe"

# Vérifier setup.py
python -m py_compile app/routers/setup.py && echo "✅ setup.py - Syntaxe OK" || echo "❌ Erreur de syntaxe"

# Vérifier main.py (modifié)
python -m py_compile app/main.py && echo "✅ main.py - Syntaxe OK" || echo "❌ Erreur de syntaxe"

# Vérifier whatsapp_webhook.py (modifié)
python -m py_compile app/whatsapp_webhook.py && echo "✅ whatsapp_webhook.py - Syntaxe OK" || echo "❌ Erreur de syntaxe"
```

### 3. Imports dans main.py
```bash
echo ""
echo "Vérification des imports dans main.py..."

grep -q "from .routers.setup import router as setup_router" /home/tim/neobot-mvp/backend/app/main.py && echo "✅ Import setup_router" || echo "❌ Import setup_router MANQUANT"

grep -q "app.include_router(setup_router)" /home/tim/neobot-mvp/backend/app/main.py && echo "✅ Routeur setup enregistré" || echo "❌ Routeur setup NOT enregistré"
```

### 4. Imports dans whatsapp_webhook.py
```bash
echo ""
echo "Vérification des imports dans whatsapp_webhook.py..."

grep -q "from .services.ai_service_rag import generate_ai_response_with_db" /home/tim/neobot-mvp/backend/app/whatsapp_webhook.py && echo "✅ Import generate_ai_response_with_db" || echo "❌ Import MANQUANT"

grep -q "generate_ai_response_with_db(" /home/tim/neobot-mvp/backend/app/whatsapp_webhook.py && echo "✅ Fonction RAG appelée" || echo "❌ Fonction RAG NOT appelée"
```

### 5. Database Schema
```bash
echo ""
echo "Vérification du schéma database..."

cd /home/tim/neobot-mvp/backend

# Vérifier que TenantBusinessConfig existe
python -c "
from app.models.models import TenantBusinessConfig
print('✅ Modèle TenantBusinessConfig disponible')
" 2>&1 | grep -q "✅" && echo "✅ Modèle TenantBusinessConfig OK" || echo "❌ Modèle TenantBusinessConfig NOT trouvé"
```

### 6. Services Chargeable
```bash
echo ""
echo "Vérification que les services peuvent être chargés..."

cd /home/tim/neobot-mvp/backend

# Vérifier KnowledgeBaseService
python -c "
from app.services.knowledge_base_service import KnowledgeBaseService
print('✅ KnowledgeBaseService importable')
" 2>&1 | grep -q "✅" && echo "✅ KnowledgeBaseService chargeable" || echo "❌ Erreur chargement"

# Vérifier ai_service_rag
python -c "
from app.services.ai_service_rag import generate_ai_response_with_db
print('✅ generate_ai_response_with_db importable')
" 2>&1 | grep -q "✅" && echo "✅ ai_service_rag chargeable" || echo "❌ Erreur chargement"

# Vérifier setup router
python -c "
from app.routers.setup import router
print('✅ Setup router importable')
" 2>&1 | grep -q "✅" && echo "✅ Setup router chargeable" || echo "❌ Erreur chargement"
```

### 7. Backend Startup
```bash
echo ""
echo "Vérification du démarrage du backend..."

cd /home/tim/neobot-mvp/backend

# Test import de main
python -c "
from app.main import app
print('✅ Application importable et initialisée')
print(f'Routes: {len(app.routes)} registered')
" 2>&1 | head -5

# Vérifier les routes setup
python -c "
from app.main import app
routes = [r.path for r in app.routes]
setup_routes = [r for r in routes if 'setup' in r]
if setup_routes:
    print(f'✅ Setup routes trouvées: {len(setup_routes)}')
    for r in setup_routes:
        print(f'   - {r}')
else:
    print('❌ Pas de setup routes trouvées')
" 2>&1
```

### 8. Fichier Test Script
```bash
echo ""
echo "Vérification du script de test..."

[ -x /home/tim/neobot-mvp/test_rag_system.sh ] && echo "✅ test_rag_system.sh exécutable" || echo "⚠️  test_rag_system.sh NOT exécutable --> chmod +x"

[ -s /home/tim/neobot-mvp/test_rag_system.sh ] && echo "✅ test_rag_system.sh non vide" || echo "❌ test_rag_system.sh VIDE"
```

---

## 🏃 EXÉCUTER CETTE CHECKLIST

### Copier et coller:
```bash
#!/bin/bash
# Script de vérification complet

set -e
cd /home/tim/neobot-mvp

echo "======================================"
echo "📋 CHECKLIST PRÉ-TEST SYSTÈME RAG"
echo "======================================"
echo ""

# 1. Fichiers
echo "1️⃣  VÉRIFICATION DES FICHIERS"
[ -f backend/app/services/knowledge_base_service.py ] && echo "✅ knowledge_base_service.py" || echo "❌ MANQUANT"
[ -f backend/app/services/ai_service_rag.py ] && echo "✅ ai_service_rag.py" || echo "❌ MANQUANT"
[ -f backend/app/routers/setup.py ] && echo "✅ setup.py" || echo "❌ MANQUANT"
[ -f test_rag_system.sh ] && echo "✅ test_rag_system.sh" || echo "❌ MANQUANT"
[ -f NEOBOT_INTELLIGENT_RAG.md ] && echo "✅ NEOBOT_INTELLIGENT_RAG.md" || echo "❌ MANQUANT"
[ -f PHASE_5_INTELLIGENT_COMPLETE.md ] && echo "✅ PHASE_5_INTELLIGENT_COMPLETE.md" || echo "❌ MANQUANT"

echo ""
echo "2️⃣  VÉRIFICATION DE LA SYNTAXE"
cd backend
python -m py_compile app/services/knowledge_base_service.py && echo "✅ knowledge_base_service.py" || echo "❌ Erreur"
python -m py_compile app/services/ai_service_rag.py && echo "✅ ai_service_rag.py" || echo "❌ Erreur"
python -m py_compile app/routers/setup.py && echo "✅ setup.py" || echo "❌ Erreur"
python -m py_compile app/main.py && echo "✅ main.py" || echo "❌ Erreur"
python -m py_compile app/whatsapp_webhook.py && echo "✅ whatsapp_webhook.py" || echo "❌ Erreur"

echo ""
echo "3️⃣  VÉRIFICATION DES IMPORTS"
grep -q "from .routers.setup import router as setup_router" app/main.py && echo "✅ setup_router importé" || echo "❌ NOT importé"
grep -q "app.include_router(setup_router)" app/main.py && echo "✅ setup_router enregistré" || echo "❌ NOT enregistré"
grep -q "from .services.ai_service_rag import generate_ai_response_with_db" app/whatsapp_webhook.py && echo "✅ RAG fonction importée" || echo "❌ NOT importée"

echo ""
echo "4️⃣  VÉRIFICATION DES SERVICES (Import Test)"
python -c "from app.services.knowledge_base_service import KnowledgeBaseService; print('✅ KnowledgeBaseService')" 2>/dev/null || echo "❌ KnowledgeBaseService"
python -c "from app.services.ai_service_rag import generate_ai_response_with_db; print('✅ ai_service_rag')" 2>/dev/null || echo "❌ ai_service_rag"
python -c "from app.routers.setup import router; print('✅ setup router')" 2>/dev/null || echo "❌ setup router"

echo ""
echo "5️⃣  VÉRIFICATION DE L'APPLICATION"
python -c "from app.main import app; print(f'✅ Application chargée ({len(app.routes)} routes)')" 2>/dev/null || echo "❌ Erreur chargement app"

echo ""
echo "======================================"
echo "✅ VÉRIFICATIONS COMPLÈTES"
echo "======================================"
echo ""
echo "🚀 PRÊT POUR LES TESTS!"
echo ""
```

### Ou directement:
```bash
# Depuis /home/tim/neobot-mvp
cd /home/tim/neobot-mvp/backend

# Test rapide des imports
python -c "
print('📋 TEST RAPIDE DES IMPORTS')
print('=' * 40)
try:
    from app.services.knowledge_base_service import KnowledgeBaseService
    print('✅ KnowledgeBaseService importable')
except Exception as e:
    print(f'❌ KnowledgeBaseService: {e}')

try:
    from app.services.ai_service_rag import generate_ai_response_with_db
    print('✅ generate_ai_response_with_db importable')
except Exception as e:
    print(f'❌ generate_ai_response_with_db: {e}')

try:
    from app.routers.setup import router
    print('✅ Setup router importable')
except Exception as e:
    print(f'❌ Setup router: {e}')

try:
    from app.main import app
    print(f'✅ Application: {len(app.routes)} routes')
except Exception as e:
    print(f'❌ Application: {e}')

print('=' * 40)
print('✅ SI TOUS ✅ ALORS PRÊT POUR TESTS')
" 2>&1
```

---

## 🎯 SI TOUT ✅

Alors lancer:
```bash
cd /home/tim/neobot-mvp

# Démarrer backend
cd backend
python -m uvicorn app.main:app --reload &
sleep 3

# Exécuter tests
cd ..
./test_rag_system.sh

# Envoyer messages WhatsApp
# Verifier les réponses utilisent vraies données
```

## ⚠️ SI ❌ QUELQUE CHOSE

1. **Erreur d'import**: Vérifier les imports dans `main.py` et `whatsapp_webhook.py`
2. **Syntaxe**: Vérifier espa
ces/indentation dans les fichiers créés
3. **Fichiers manquants**: Recréer via tools (create_file)
4. **Database**: Vérifier que PostgreSQL tourne et tables existent

---

✅ **Cette checklist = Confiance avant tests réels**

Exécutez cette vérification complète avant de lancer les vrais tests! 🚀
