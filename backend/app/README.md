# 📚 NéoBot Backend - Guide des Fichiers

## 🗂️ Structure de `/backend/app/`

```
backend/app/
├── main.py                              # ⭐ Point d'entrée principal
├── main_clean_commented.py              # 📖 Version annotée (1000+ commentaires)
│
├── models.py                            # Database ORM models
├── models_clean_commented.py            # 📖 Version annotée complète
│
├── database.py                          # PostgreSQL configuration
├── database_clean_commented.py          # 📖 Version annotée complète
│
├── whatsapp_webhook.py                  # WhatsApp webhook endpoint
├── whatsapp_webhook_clean_commented.py  # 📖 Version annotée complète
│
└── __init__.py                          # Python package marker
```

---

## 📖 Fichiers Annotés (Pour Apprendre)

Si tu veux **compren peu le code**, lis ces fichiers dans cet ordre:

### 1️⃣ **main_clean_commented.py**
**Quoi:** Point d'entrée de l'application FastAPI  
**Contient:** Routes HTTP, endpoints, health checks, intégration IA  
**Taille:** ~600 lignes avec 1000+ commentaires  
**Temps:** 30-45 minutes  
**Pourquoi:** Comprendre comment les requêtes sont routées

### 2️⃣ **models_clean_commented.py**
**Quoi:** Structures de données (ORM SQLAlchemy)  
**Contient:** Tenant, Conversation, Message, PlanType, PLAN_LIMITS  
**Taille:** ~800 lignes avec 1000+ commentaires  
**Temps:** 30-45 minutes  
**Pourquoi:** Comprendre la hiérarchie des données

### 3️⃣ **database_clean_commented.py**
**Quoi:** Configuration PostgreSQL et pool  
**Contient:** Engine, SessionLocal, get_db(), init_db()  
**Taille:** ~600 lignes avec 800+ commentaires  
**Temps:** 20-30 minutes  
**Pourquoi:** Comprendre comment la DB marche

### 4️⃣ **whatsapp_webhook_clean_commented.py**
**Quoi:** Webhook pour recevoir les messages WhatsApp  
**Contient:** Message routing, BrainOrchestrator, DeepSeek fallback  
**Taille:** ~900 lignes avec 1000+ commentaires  
**Temps:** 30-45 minutes  
**Pourquoi:** Comprendre le flux complet d'un message

---

## 🔧 Fichiers Principaux (Non-annotés)

### **main.py**
**Rôle:** Point d'entrée FastAPI  
**Ce qu'il fait:**
- ✅ Crée l'app FastAPI
- ✅ Configure CORS
- ✅ Définit les routes (/health, /api/tenants, /api/conversations, etc.)
- ✅ Intègre le webhook WhatsApp
- ✅ Gère les appels DeepSeek API

**Routes principales:**
```
GET  /health                    ← Health check basique
GET  /api/health                ← Health check complet (DB test)
GET  /api/tenants               ← Liste tous les clients
POST /api/tenants               ← Créer un nouveau client
GET  /api/conversations/{id}    ← Messages d'une conversation
POST /api/v1/webhooks/whatsapp  ← Reçoit messages WhatsApp
```

**À lire:** `main_clean_commented.py` (version annotée)

---

### **models.py**
**Rôle:** Définir la structure des données  
**Ce qu'il définit:**
- ✅ Table `Tenant` (clients/businesses)
- ✅ Table `Conversation` (chats)
- ✅ Table `Message` (textes envoyés)
- ✅ Enum `PlanType` (NEOBOT, BASIQUE, STANDARD, PRO)
- ✅ Dict `PLAN_LIMITS` (config des plans)

**Hiérarchie:**
```
Tenant (1)
  └── Conversations (N)
        └── Messages (N)
```

**À lire:** `models_clean_commented.py` (version annotée)

---

### **database.py**
**Rôle:** Configurer PostgreSQL  
**Ce qu'il configure:**
- ✅ Connection engine (psycopg2 driver)
- ✅ Connection pool (QueuePool)
- ✅ SessionLocal factory
- ✅ Base ORM
- ✅ get_db() dependency injection

**Concepts clés:**
- **Engine**: Le "contrôle" de la DB
- **Pool**: Groupe de connexions réutilisables
- **Session**: Une "conversation" avec la DB
- **psycopg2**: Driver qui traduit Python → PostgreSQL

**À lire:** `database_clean_commented.py` (version annotée)

---

### **whatsapp_webhook.py**
**Rôle:** Recevoir et traiter messages WhatsApp  
**Ce qu'il fait:**
- ✅ Reçoit POST de WhatsApp service
- ✅ Valide les données (Pydantic)
- ✅ Process avec BrainOrchestrator
- ✅ Match patterns (prix, aide, démo)
- ✅ Fallback: appel DeepSeek IA
- ✅ Envoie réponse en background

**Flux d'un message:**
```
Message WhatsApp → webhook endpoint → BrainOrchestrator
                                    → Pattern match?
                                      ├─ OUI: réponse pré-écrite
                                      └─ NON: appel DeepSeek
                                    → background_task: envoyer réponse
```

**À lire:** `whatsapp_webhook_clean_commented.py` (version annotée)

---

## 🎓 Plan d'apprentissage recommandé

### Jour 1: Comprendre la structure (2-3h)

```
1. Lire learning_materials/README.md (orientation)
2. Lire main_clean_commented.py (routes)
3. Lire models_clean_commented.py (données)
4. Lire database_clean_commented.py (DB config)
5. Lire whatsapp_webhook_clean_commented.py (message flow)
```

**Objectif:** 50%+ comprehension ✅

### Jour 2: Hands-on (2-3h)

```
1. Lancer: docker-compose up -d
2. Tester: curl http://localhost:8000/health
3. Envoyer message test via WhatsApp
4. Voir les logs
5. Lire main.py (non-annoté)
6. Commencer à modifier (ajout de logs, etc.)
```

**Objectif:** 70%+ comprehension + expérience

### Jour 3: Approfondissement (3-5h)

```
1. Refactoriser save_message_to_db()
2. Implémenter limit checking
3. Ajouter logging amélioré
4. Écrire tests
5. Ajouter features (ex: persistance des patterns)
```

**Objectif:** 80%+ comprehension + contributions

---

## 🔗 Relations Entre Fichiers

```
main.py
├── importe: models, database, whatsapp_webhook
├── crée: FastAPI app
├── utilise: get_db() de database.py
├── utilise: Tenant, Conversation, Message de models.py
└── inclut: router de whatsapp_webhook.py

whatsapp_webhook.py
├── importe: models, database (pour future use)
├── crée: BrainOrchestrator
└── appelle: DeepSeek API

models.py
├── importe: Base de database.py
├── définit: Classes ORM (Tenant, Conversation, Message)
└── utilisé par: main.py, whatsapp_webhook.py

database.py
├── importe: SQLAlchemy, os, logging
├── crée: Engine, SessionLocal, Base
└── utilisé par: models.py, main.py via get_db()
```

---

## 🚀 Comment Naviguer le Code

### "Je veux comprendre comment un message est reçu"
→ Lis: `whatsapp_webhook_clean_commented.py`

### "Je veux ajouter une nouvelle table"
→ Lis: `models_clean_commented.py`
→ Puis modifie: `models.py`
→ Appelle: `init_db()` (dans main.py)

### "Je veux ajouter une route HTTP"
→ Lis: `main_clean_commented.py`
→ Puis modifie: `main.py`

### "Je veux mejornar les réponses IA"
→ Lis: `whatsapp_webhook_clean_commented.py` (section BrainOrchestrator)
→ Puis modifie: `whatsapp_webhook.py`

### "Je ne comprends pas la DB"
→ Lis: `database_clean_commented.py` et `models_clean_commented.py`

---

## 📊 Métriques du Code

| Fichier | Lignes | Commentaires | Ratio | Type |
|---------|--------|--------------|-------|------|
| main.py | ~400 | ~200 | 1:2 | Routes |
| main_clean_commented.py | ~1200 | ~1000 | 1:1.2 | 📖 Educational |
| models.py | ~137 | ~100 | 1:1.4 | ORM Models |
| models_clean_commented.py | ~900 | ~1000 | 1:0.9 | 📖 Educational |
| database.py | ~84 | ~80 | 1:1 | Config |
| database_clean_commented.py | ~600 | ~800 | 1:0.75 | 📖 Educational |
| whatsapp_webhook.py | ~308 | ~100 | 1:3 | Webhook |
| whatsapp_webhook_clean_commented.py | ~1100 | ~1000 | 1:1.1 | 📖 Educational |

---

## ✅ Checklist: "Je comprends le code"

- [ ] Je sais ce que FastAPI fait
- [ ] Je sais ce qu'un ORM est
- [ ] Je sais ce qu'une "relation" est (1-à-plusieurs)
- [ ] Je sais comment psycopg2 relie Python à PostgreSQL
- [ ] Je sais comment un message WhatsApp est traité
- [ ] Je sais ce qu'un "webhook" est
- [ ] Je sais ce qu'une "session" DB est
- [ ] Je sais ce que "async/await" signifie
- [ ] Je sais ce qu'un "pool" de connexions est
- [ ] Je peux modifier une route HTTP
- [ ] Je peux ajouter une colonne à un modèle
- [ ] Je peux tracer le flux d'un message du début à la fin

**Si tu as ✅ sur 10/12:**
**→ Toi tu as atteint 70%+ comprehension!** 🎉

---

## 🔗 Références Rapides

| Quoi | Où |
|------|------|
| **Routes HTTP** | main.py, main_clean_commented.py |
| **ORM Models** | models.py, models_clean_commented.py |
| **DB Config** | database.py, database_clean_commented.py |
| **Message Flow** | whatsapp_webhook.py, whatsapp_webhook_clean_commented.py |
| **Intégration IA** | whatsapp_webhook.py (section DeepSeek) |
| **Plan Config** | models.py (PLAN_LIMITS dict) |
| **Webhook Endpoint** | whatsapp_webhook.py (@router.post) |
| **Health Checks** | main.py (/health, /api/health) |

---

**Commencer par:** `learning_materials/README.md`  
**Puis:** `backend/app/main_clean_commented.py`  
**Objectif Final:** Lire et comprendre tous les fichiers annotés!

Bonne apprentissage! 🚀
