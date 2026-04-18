# 📚 CENSUS COMPLET DU PROJET NEOBOT
**Date:** 17 avril 2026  
**Projet:** NeoBot MVP — SaaS d'agents IA conversationnels sur WhatsApp

---

## 📊 STRUCTURE GÉNÉRALE

```
neobot-mvp/
├── backend/              # FastAPI Python — Core du système
├── frontend/             # Next.js React/TypeScript — UI
├── whatsapp-service/     # Node.js Baileys — WhatsApp integration
├── docs/                 # Documentation
├── scripts/              # Scripts de maintenance
├── logs/                 # Logs runtime
├── .env                  # Variables d'environnement
├── docker-compose.yml    # Orchestration locale
└── [Documenti guides]    # Rapports/guides de déploiement
```

---

# 🔧 BACKEND — FastAPI (Python)

## 📁 Répertoires principaux

### `backend/app/main.py` — ENTRY POINT CRITIQUE
- **Rôle:** Point d'entrée FastAPI, initialisation app
- **Responsabilités:**
  - Démarrage uvicorn sur port 8000
  - Configuration CORS (7 origins autorisées)
  - Middleware de sécurité (HSTS, CSP, X-Frame-Options, etc.)
  - Middleware rate limiting (limite 3/minute sur auth)
  - Middleware subscription (vérification du plan)
  - Initialisation Sentry (monitoring d'erreurs)
  - Vérification migrations base de données
  - Chargement des services (email, business KB)
  - Enregistrement de tous les routers
- **Impact:** Si cassé → Toute l'app est down

### `backend/app/database.py` — GESTION BDD
- **Rôle:** Configuration PostgreSQL/Neon
- **Responsabilités:**
  - Création engine SQLAlchemy (connexion pool)
  - Configuration pool (5 base + 10 overflow)
  - Pool pre-ping (détection connexions périmées)
  - Pool recycle (3600s = 1h)
  - Event listeners pour vérification connexion
  - SessionLocal factory (dependency injection)
  - Fonction `init_db()` pour création tables
- **Issue Actuelle:** 🔴 **SSL errors après 1h** (pool_recycle + channel_binding)
- **Impact:** Base de données inaccessible = 500 errors

### `backend/app/models.py` — MODÈLES SQLALCHEMY
- **Rôle:** Définition des tables database
- **Modèles définies:**
  - `User` (utilisateurs, email, password, tenant_id)
  - `Tenant` (clients SaaS, plan, business_type)
  - `Agent` (agents IA, 5 types: Libre, RDV, Support, Vente, Qualification)
  - `Conversation` (historique messages)
  - `Message` (messages entrants/sortants)
  - `Contact` (clients des tenants)
  - `WhatsAppSession` (état connexion WhatsApp par tenant)
  - `Subscription` (plan, trial, facturation)
  - `Overage` (dépassements messages)
  - `LoginAttempt` (brute force tracking)
  - `RefreshToken` (tokens JWT)
  - Plus 10+ modèles pour analytics, KB, etc.
- **Impact:** Structure données == Structure business

### `backend/app/routers/` — ENDPOINTS API

#### Authentification (`auth.py`)
- **Endpoints:**
  - `POST /api/auth/register` — Inscription (⚠️ demande 3 champs de trop)
  - `POST /api/auth/login` — Connexion
  - `POST /api/auth/refresh` — Renouveler JWT
  - `POST /api/auth/logout` — Déconnexion
  - `POST /api/auth/forgot-password` — Récupération mot de passe
  - `POST /api/auth/reset-password` — Reset password
  - `POST /api/auth/admin-login` — Login superadmin
  - `POST /api/auth/admin-login/verify` — Verify TOTP
- **Status:** ⚠️ **Endpoint /signup n'existe pas** (404)

#### WhatsApp (`whatsapp.py`, `whatsapp_qr.py`)
- **Endpoints:**
  - `POST /api/tenants/{id}/whatsapp/session/mark-connected` — Marquer connecté
  - `POST /api/tenants/{id}/whatsapp/session/mark-disconnected` — Marquer déconnecté
  - `GET /api/tenants/{id}/whatsapp/qr` — Récupérer QR code
- **Status:** ⚠️ Service connecté mais messages entrants rejetés (401)

#### Agents (`agents.py`)
- **Endpoints:**
  - `POST /api/tenants/{id}/agents` — Créer agent
  - `GET /api/tenants/{id}/agents` — Lister agents
  - `PUT /api/tenants/{id}/agents/{agent_id}` — Mettre à jour
  - `DELETE /api/tenants/{id}/agents/{agent_id}` — Supprimer
- **Status:** ✅ Fonctionnel

#### Conversations (`conversations.py`)
- **Endpoints:**
  - `GET /api/tenants/{id}/conversations` — Historique
  - `GET /api/tenants/{id}/conversations/{conv_id}` — Détail
- **Status:** ✅ Fonctionnel

#### Billing/Paiements (`neopay.py`)
- **Endpoints:**
  - `POST /api/tenants/{id}/payment/initiate` — Initier paiement Korapay
  - `POST /api/webhooks/korapay` — Webhook Korapay callback
  - `GET /api/tenants/{id}/payment/status` — Vérifier statut
- **Status:** ✅ Intégration Korapay OK (Mobile Money + Cartes)

#### Analytics (`analytics.py`)
- **Endpoints:**
  - `GET /api/tenants/{id}/analytics/overview` — Stats générales
  - `GET /api/tenants/{id}/analytics/messages` — Message analytics
- **Status:** ✅ Fonctionnel

#### Configuration (`setup.py`, `tenant_settings.py`, `business.py`)
- **Endpoints:**
  - `POST /api/tenants/{id}/setup` — Setup initial tenant
  - `GET/PUT /api/tenants/{id}/settings` — Paramètres tenant
  - `POST /api/business/types` — Types de business
- **Status:** ✅ Fonctionnel

#### Admin (`admin.py`)
- **Endpoints:**
  - `GET /api/admin/tenants` — Liste tenants (superadmin only)
  - `POST /api/admin/tenants/{id}/impersonate` — Impersonation
  - `PUT /api/admin/tenants/{id}/plan` — Changer plan
- **Status:** ✅ Fonctionnel (superadmin protection ✅)

#### Autres routers
- `demo.py` — Endpoint de démo sans auth (tests)
- `monitoring.py` — `/health` check
- `sentry_webhook.py` — Webhook Sentry monitoring
- `contacts.py` — Gestion contacts
- `usage.py` — Tracking utilisation
- `overage.py` — Gestion dépassements
- `subscription.py` — Plans et facturation
- `neo_assistant.py` — NeoAssistant (assistant IA interne)
- `human_detection.py` — Détection escalade humaine

### `backend/app/services/` — LOGIQUE MÉTIER (50+ fichiers)

#### Core Intelligence
- **`ai_service.py`** — Appels API DeepSeek (LLM principal)
- **`ai_service_rag.py`** — RAG (Retrieval Augmented Generation)
- **`intelligent_conversation.py`** — Logique réponses intelligentes
- **`agent_service.py`** — Gestion agents (5 types)
- **`intent_classifier.py`** — Classification intents utilisateur

#### WhatsApp & Communication
- **`whatsapp_service.py`** — Communication WhatsApp (receive/send)
- **`whatsapp_mapping_service.py`** — Mapping tenant ↔ numéro WhatsApp
- **`conversation_memory_service.py`** — Historique conversations

#### Business Logic
- **`knowledge_base_service.py`** — Base de connaissance tenant
- **`business_kb_service.py`** — Types de business (8 types pré-définis)
- **`crm_service.py`** — Gestion CRM (contacts, interactions)
- **`contact_filter_service.py`** — Filtrage contacts (duplos, validation)

#### Payments & Pricing
- **`korapay_service.py`** — Intégration Korapay (Mobile Money + Cartes)
- **`neopay_service.py`** — Système de paiement interne
- **`overage_pricing_service.py`** — Calcul dépassements

#### Monitoring & Analytics
- **`usage_tracking_service.py`** — Tracking utilisation (messages, API calls)
- **`monitoring_service.py`** — Health checks, monitoring
- **`analytics_service.py`** — Stats et rapports
- **`report_service.py`** — Génération rapports

#### Email & Notifications
- **`email_service.py`** — Envoi emails Brevo (bienvenue, reset, etc.)
- **`escalation_service.py`** — Escalade vers humain

#### Auth & Sécurité
- **`auth_service.py`** — JWT, password hashing, tokens
- **`subscription_service.py`** — Gestion abonnements et plans
- **`session_expiration_checker.py`** — Vérification expiration sessions

#### Advanced Features (Optional/Not Used)
- `redis_service.py` — Cache Redis (optionnel, pas utilisé actuellement)
- `dual_mode_engine.py`, `hybrid_intelligence.py`, `rocket_brain.py` — Expérimental
- `claude_service.py` — Anthropic Claude (fallback LLM)
- `campay_service.py` — Alternative payment provider (pas utilisé)

### `backend/app/middleware_*.py` — MIDDLEWARE

#### `middleware_security.py`
- Ajoute headers de sécurité:
  - X-Frame-Options: DENY
  - X-Content-Type-Options: nosniff
  - X-XSS-Protection: 1; mode=block
  - Referrer-Policy: strict-origin-when-cross-origin
  - Strict-Transport-Security: max-age=31536000 (HSTS)
  - Permissions-Policy: Disable géolocalisation, microphone, caméra, etc.
  - Content-Security-Policy: default-src 'none'

#### `middleware_subscription.py`
- Vérifie que tenant a plan actif
- Bloque requests si subscription expirée
- Tracking usage pour facturation

#### CORS Middleware (`main.py`)
- Permet 7 origins:
  - https://neobot-ai.com
  - https://www.neobot-ai.com
  - https://neobot-frontend-psi.vercel.app
  - http://localhost:3000, :3002
  - http://127.0.0.1:3000, :3002

### `backend/app/whatsapp_webhook.py` — WEBHOOK WHATSAPP

- **Endpoint:** `POST /api/v1/webhooks/whatsapp`
- **Rôle:** Recevoir messages de WhatsApp service, traiter, envoyer réponse
- **Flow:**
  1. Reçoit message JSON du service WhatsApp
  2. Vérifie signature HMAC (WHATSAPP_WEBHOOK_SECRET)
  3. Résout tenant contexte (tenant_id)
  4. Charge agent pour tenant
  5. Envoie message à AI (DeepSeek)
  6. Récupère réponse
  7. Envoie réponse via WhatsApp service
- **Issue Actuelle:** 🔴 **Signature validation échoue (HTTP 401)** car WEBHOOK_SECRET vide

### `backend/app/dependencies.py` — DEPENDENCY INJECTION

- **`get_db()`** — Session base de données
- **`get_current_user()`** — Utilisateur courant (JWT auth)
- **`get_superadmin_user()`** — Superadmin only (is_superadmin = TRUE en DB)
- **`get_tenant_id()`** — Tenant courant (from auth token)
- **`limiter.limit()`** — Rate limiting decorator

### `backend/app/limiter.py` — RATE LIMITING

- Limites appliquées:
  - Auth endpoints: 3 requêtes/minute (brute force protection)
  - API générales: Dépend du plan
- Utilise `slowapi` library

### `backend/app/http_client.py` — HTTP CLIENT GLOBAL

- Connection pooling pour requêtes sortantes
- Utilisé par ai_service, korapay_service, etc.
- Évite de créer 100+ sessions HTTP

---

# 🎨 FRONTEND — Next.js (React/TypeScript)

## Architecture

### `frontend/src/app/` — PAGES (Next.js App Router)

#### Pages Authentification
- **`signup/page.tsx`** — Inscription utilisateur
  - Form: email, password, full_name, tenant_name, business_type
  - Appelle POST `/api/auth/register`
  - Issue: Endpoint est `/register`, pas `/signup` (mais route est OK)

- **`login/page.tsx`** — Connexion utilisateur
  - Form: email, password
  - Appelle POST `/api/auth/login`
  - JWT token stocké dans localStorage

- **`forgot-password/page.tsx`** — Mot de passe oublié

- **`reset-password/page.tsx`** — Reset password via token

#### Pages Main
- **`page.tsx`** — Landing page (accueil public)

- **`dashboard/page.tsx`** — Dashboard principal (après login)
  - Stats utilisation
  - Agents actifs
  - Messages réçus/envoyés
  - Plan actuel

#### Pages Configuration
- **`config/page.tsx`** — Configuration du bot
  - Connexion WhatsApp (scan QR)
  - Paramètres agents
  - KB (knowledge base) personnalisée

- **`agent/page.tsx`** — Création/édition agents
  - Sélect type agent (5 types)
  - Prompt personnalisé
  - Paramètres comportement

#### Pages Analytics
- **`analytics/page.tsx`** — Stats et rapports
  - Messages par jour
  - Revenue
  - Top clients
  - Heatmaps conversions

#### Pages Billing
- **`billing/page.tsx`** — Plans et facturation
  - Current plan
  - Upgrade/downgrade
  - Historique factures
  - Payment method

#### Pages Admin
- **`admin/page.tsx`** — Superadmin dashboard
  - Liste tous tenants
  - Impersonation
  - Monitoring global

- **`admin/login/page.tsx`** — Login superadmin (2FA TOTP)

- **`admin/credits/page.tsx`** — Gestion credits admin

#### Autres Pages
- **`conversations/page.tsx`** — Historique conversations
- **`settings/page.tsx`** — Paramètres utilisateur
- **`pricing/page.tsx`** — Page pricing
- **`status/page.tsx`** — Status page système
- **`legal/page.tsx`** — Mentions légales

#### Pages Paiement
- **`pay/[token]/page.tsx`** — Page paiement (Korapay)
- **`pay/[token]/callback/page.tsx`** — Callback paiement

### `frontend/src/components/` — COMPOSANTS RÉUTILISABLES

#### Auth Components
- **`auth/LoginForm.tsx`** — Form login
- **`auth/SignupForm.tsx`** — Form signup

#### Config Components
- **`config/BusinessConfigForm.tsx`** — Form config business
- **`config/WhatsAppQRDisplay.tsx`** — Affiche QR code WhatsApp

#### Dashboard Components
- **`dashboard/UsageDisplay.tsx`** — Affichage usage (messages)

#### Analytics Components
- **`analytics/MessageChart.tsx`** — Graphe messages par jour
- **`analytics/RevenueStats.tsx`** — Stats revenue
- **`analytics/StatsGrid.tsx`** — Grid statistiques
- **`analytics/TopClients.tsx`** — Top clients

#### UI Components
- **`ui/AppShell.tsx`** — Layout principal (nav, sidebar)
- **`ui/NeoAssistant.tsx`** — Chat avec NeoBot (assistant interne)
- **`ui/NeoChat.tsx`** — Component chat universel
- **`ui/NeoBotLogo.tsx`** — Logo branding
- **`ui/NeoTour.tsx`** — Onboarding tour
- **`ui/StatCard.tsx`** — Card statistiques (réutilisable)
- **`ui/GalaxyCanvas.tsx`** — Animation background (cosmétique)
- **`ui/CookieBanner.tsx`** — Consentement cookies
- **`ui/Skeleton.tsx`** — Loading skeleton

#### WhatsApp Components
- **`whatsapp/WhatsAppConnect.tsx`** — Setup WhatsApp connexion

### `frontend/src/lib/` — UTILITAIRES

#### `lib/api.ts` — CLIENT API PRINCIPAL
- Wrapper axios/fetch pour communicer avec backend
- Gère JWT token depuis localStorage
- Re-authentification automatique (refresh token)
- Base URL: `NEXT_PUBLIC_API_URL` (env variable)
- Methodes:
  - `login(email, password)`
  - `signup(data)`
  - `getAgents(tenantId)`
  - `createAgent(tenantId, agentData)`
  - `sendMessage(conversation, message)`
  - `getAnalytics(tenantId)`
  - etc.

#### `lib/neoConfig.ts` — CONFIG FRONTEND
- URLs API, Korapay, etc.
- Feature flags
- Constants globales

### `frontend/src/types/index.ts` — TYPES TYPESCRIPT

- `User` interface
- `Tenant` interface
- `Agent` interface (5 types)
- `Conversation` interface
- `Message` interface
- `Plan` enum (BASIC, PROFESSIONAL, ENTERPRISE)
- Etc.

### `frontend/src/hooks/` — CUSTOM HOOKS

- `useIsMobile.ts` — Detect mobile viewport

### `frontend/middleware.ts` — MIDDLEWARE NEXTJS

- Route protection (check JWT before accessing protected pages)
- Redirect to login si pas auth
- Impersonation support (session storage token)

### Configuration Files

- **`next.config.js`** — Config Next.js
  - Redirects, rewrites
  - Image optimization
  - API proxy settings

- **`tailwind.config.js`** — Tailwind CSS config

- **`tsconfig.json`** — TypeScript config

- **`package.json`** — Dependencies npm
  - axios, react-query, zustand (state), etc.

- **`vercel.json`** — Deployment config Vercel

---

# 📱 WHATSAPP SERVICE — Node.js/Baileys

## Fichiers Principaux

### `whatsapp-service/whatsapp-production.js` — ENTRY POINT
- **Rôle:** Service WhatsApp Baileys — Bridge WhatsApp ↔ Backend
- **Responsabilités:**
  - Connexion WhatsApp via Baileys (authentification)
  - Gestion sessions par tenant
  - Réception messages entrants
  - Envoi messages sortants
  - Webhook vers backend (`POST /api/v1/webhooks/whatsapp`)
  - Keep-alive backend (GET `/health` chaque 14min)
  - Reconnection automatique
  - Logging détaillé
  
### Architecture WhatsApp
```
WhatsApp Client (téléphone)
        ↓
   Baileys (Node.js)
        ↓ (reçoit messages)
whatsapp-production.js
        ↓ (envoie webhook)
Backend FastAPI
        ↓ (process, appelle LLM)
        ↓ (récupère réponse)
whatsapp-production.js
        ↓ (envoie message)
   Baileys
        ↓
WhatsApp Client (réponse)
```

### Configuration Webhooks
- **Webhook URL:** `${BACKEND_URL}/api/v1/webhooks/whatsapp`
- **Signature HMAC:** Headers `x-webhook-signature`
- **Secret:** `WHATSAPP_WEBHOOK_SECRET` (neobot_whatsapp_secret_2024)
- **Issue:** 🔴 **Backend reject tous les webhooks (HTTP 401)** car secret vide

### Package.json
- **Dependencies:**
  - `@whiskeysockets/baileys` — WhatsApp protocol
  - `axios` — HTTP client
  - `pino` — Logging
  - `express` — Webserver basique (optionnel, pour health checks)
  - `node-cache` — In-memory cache
  - `pm2` — Process manager

### Autres Fichiers
- `index.js`, `index_production.js`, `whatsapp-optimized.js` — Variants (legacy)
- `start.sh`, `start-clean.sh` — Scripts démarrage
- `diagnostic.sh` — Diagnostic service
- `control_whatsapp.sh` — Control script
- `package.json` — Dependencies
- `auth_info_baileys/` — Dossier auth (stockage clés de session)

---

# 🗄️ DATABASE — PostgreSQL (Neon)

## Structure BDD

### Tenants (Clients SaaS)
```sql
Table: tenants
- id INT PRIMARY KEY
- name STRING (nom du business)
- email EMAIL
- phone STRING
- business_type STRING (8 types: retail, services, e-commerce, etc.)
- plan ENUM (BASIC, PROFESSIONAL, ENTERPRISE)
- messages_used INT
- messages_limit INT
- created_at TIMESTAMP
- is_active BOOLEAN
```

### Users
```sql
Table: users
- id INT PRIMARY KEY
- tenant_id INT FK→tenants
- email EMAIL UNIQUE
- hashed_password STRING
- full_name STRING
- is_active BOOLEAN
- is_superadmin BOOLEAN (true only for id=8)
- created_at TIMESTAMP
```

### Agents (IA Conversationnels)
```sql
Table: agents
- id INT PRIMARY KEY
- tenant_id INT FK→tenants
- type ENUM (5 types: Libre, RDV&Suivi, Support&FAQ, Vente, Qualification)
- name STRING
- prompt_system TEXT (prompt technique de l'agent)
- temperature FLOAT (0.0-1.0)
- max_tokens INT
- is_active BOOLEAN
- created_at TIMESTAMP
```

### WhatsAppSessions
```sql
Table: whatsapp_sessions
- id INT PRIMARY KEY
- tenant_id INT FK→tenants UNIQUE
- phone_number STRING
- is_connected BOOLEAN
- last_activity TIMESTAMP
```

### Conversations
```sql
Table: conversations
- id INT PRIMARY KEY
- tenant_id INT FK→tenants
- contact_phone STRING
- agent_id INT FK→agents
- started_at TIMESTAMP
- last_message_at TIMESTAMP
- status ENUM (ongoing, closed, pending_human)
```

### Messages
```sql
Table: messages
- id INT PRIMARY KEY
- conversation_id INT FK→conversations
- direction ENUM (inbound, outbound)
- sender_phone STRING
- text TEXT
- timestamp TIMESTAMP
- is_ai_generated BOOLEAN
```

### Subscriptions
```sql
Table: subscriptions
- id INT PRIMARY KEY
- tenant_id INT FK→tenants
- plan STRING (BASIC, PROFESSIONAL, ENTERPRISE)
- status ENUM (active, expired, paused)
- is_trial BOOLEAN
- trial_end_date DATE
- next_billing_date DATE
```

### Overages
```sql
Table: overages
- id INT PRIMARY KEY
- tenant_id INT FK→tenants
- messages_count INT
- amount_usd DECIMAL
- paid_at TIMESTAMP
```

### Plus
- `login_attempts` — Brute force protection
- `refresh_tokens` — JWT management
- `contacts` — Contacts management
- `analytics_*` — Analytics tables
- Etc.

## Connection URL
```
postgresql://neondb_owner:npg_QBelE5R1vbYi@ep-holy-voice-abmgb09o-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

**Issue:** 🔴 `channel_binding=require` cause SSL errors après 1h (Neon ne le supporte pas)

---

# 📋 CONFIGURATION & VARIABLES D'ENVIRONNEMENT

## `.env` (Racine du projet)

```env
# DATABASE
DATABASE_URL=postgresql://neondb_owner:npg_QBelE5R1vbYi@ep-holy-voice-abmgb09o-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_TIMEOUT=30

# LLM (DeepSeek API)
DEEPSEEK_API_KEY=sk-9dcd03b870a741cfa2823f5c0ea96c5f
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT=30

# BACKEND
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_ENV=production
BACKEND_DEBUG=false
BACKEND_RELOAD=false
BACKEND_URL=https://api.neobot-ai.com

# WHATSAPP
WHATSAPP_PORT=3001
WHATSAPP_BACKEND_URL=http://localhost:8000
WHATSAPP_SERVICE_URL=http://whatsapp:3001
WHATSAPP_WEBHOOK_SECRET=neobot_whatsapp_secret_2024
WHATSAPP_RECONNECT_TIMEOUT=30
WHATSAPP_MAX_RETRIES=5

# FRONTEND
FRONTEND_PORT=3000
FRONTEND_URL=https://neobot-ai.com
NEXT_PUBLIC_API_URL=http://localhost:8000

# CORS (7 origins)
ALLOWED_ORIGINS=https://neobot-ai.com,https://www.neobot-ai.com,https://neobot-frontend-psi.vercel.app,http://localhost:3000,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3002

# LOGGING
LOG_DIR=/root/neobot-mvp/logs
LOG_LEVEL=INFO

# SENTRY (Error tracking)
SENTRY_DSN=https://examplePublicKey@o0.ingest.sentry.io/0
APP_ENV=production

# EMAIL (Brevo transactionnel)
BREVO_API_KEY=xkeysib-placeholder
BREVO_SENDER_EMAIL=neobot@neobot-ai.com

# PAIEMENTS (Korapay - Mobile Money + Cartes)
KORAPAY_SECRET_KEY=placeholder
KORAPAY_PUBLIC_KEY=placeholder
```

---

# 🚀 INFRASTRUCTURE & DEPLOYMENT

## VPS (Production)
- **IP:** 178.104.163.245 (Hetzner)
- **OS:** Ubuntu
- **Backend:** uvicorn port 8000
- **WhatsApp:** Node.js port 3001
- **Database:** Neon PostgreSQL (cloud, SSL required)
- **Frontend:** Vercel (neobot-frontend-psi.vercel.app)

## Local Development
- Docker Compose setup available
- PostgreSQL local available
- All services runnable locally

## Files Importants

### Docker
- **`docker-compose.yml`** — Local dev setup (backend, frontend, whatsapp, postgres)
- **`backend/Dockerfile.prod`** — Production backend image
- **`frontend/Dockerfile.prod`** — Production frontend image
- **`whatsapp-service/Dockerfile.prod`** — Production WhatsApp image

### Deployment
- **`deploy-vps.sh`** — Déploiement VPS
- **`deploy-staging.sh`** — Déploiement staging
- **`setup-vps.sh`** — Setup initial VPS
- **`render.yaml`** — Config Render.com (alternative hosting)

### Scripts Utils
- **`start.sh`** — Start all services
- **`stop.sh`** — Stop all services
- **`reset_whatsapp_automatic.sh`** — Reset WhatsApp session

---

# 📊 MONITORING & OBSERVABILITÉ

## Sentry (Error Tracking)
- Toutes les exceptions FastAPI loggées automatiquement
- Dashboard: https://sentry.io/
- Intégration: `sentry_sdk.init()` dans `main.py`

## Logging
- **Backend:** Logs écrits dans `/root/neobot-mvp/logs/backend.log`
- **WhatsApp:** Logs dans `/root/neobot-mvp/logs/whatsapp.log`
- **Format:** ISO 8601 timestamp, level, message

## Health Checks
- **Backend:** `GET /health` — Check DB + services
- **WhatsApp:** `GET /health` — Check connection
- **Liveness:** Endpoints respond within 5s

---

# 🔐 SÉCURITÉ

## Authentification
- JWT tokens (Bearer header)
- Access tokens (15min TTL)
- Refresh tokens (7 days TTL)
- Stored in `refresh_tokens` table
- localStorage (frontend) — INSECURE, devrait être httpOnly cookies

## Autorisation
- `@get_current_user()` — Vérifier JWT
- `@get_superadmin_user()` — Vérifier is_superadmin (DB check)
- `@get_tenant_id()` — Tenant contexte
- Middleware subscription — Vérifier plan actif

## Rate Limiting
- Auth endpoints: 3/minute
- Slowapi library

## Security Headers
- HSTS: 31536000s (1 year, preload)
- CSP: default-src 'none'
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: Tout désactivé

## Signature Validation
- Webhooks Korapay: HMAC signature obligatoire
- Webhooks WhatsApp: HMAC signature obligatoire (🔴 **BROKEN**)

---

# 🎯 ÉLÉMENTS CRITIQUES (À SURVEILLER)

| Composant | Rôle | Status | Risk |
|-----------|------|--------|------|
| `backend/app/main.py` | Entry point FastAPI | ✅ Running | 🔴 Si cassé = tout down |
| `backend/app/database.py` | Connexion BDD | ⚠️ SSL errors après 1h | 🔴 Critique |
| `backend/app/whatsapp_webhook.py` | Webhook entrant | ❌ 401 Unauthorized | 🔴 **Bot non fonctionnel** |
| `whatsapp-service/whatsapp-production.js` | Service WhatsApp | ✅ Connecté | ⚠️ Webhook auth échoue |
| `frontend/lib/api.ts` | Client API | ✅ Fonctionne | ⚠️ Endpoints mismatch |
| `backend/app/routers/auth.py` | Authentification | ⚠️ Endpoint /signup manquant | 🔴 Inscription ne marche pas |
| `backend/app/services/ai_service.py` | Appels DeepSeek LLM | ✅ OK | ⚠️ Clé API importante |
| `backend/app/services/korapay_service.py` | Paiements | ✅ OK | ⚠️ Clés de paiement importantes |

---

# 📚 DOCUMENTATION PROJET

## Guides Importants
- **`DIAGNOSTIC_COMPLET_2026_04_17.md`** — Census des 5 problèmes critiques
- **`README.md`** — Vue d'ensemble projet
- **`docs/`** — Dossier documentation
- **`backend/app/README.md`** — Doc backend
- **`whatsapp-service/DEPLOYMENT_GUIDE_v7.md`** — Guide WhatsApp

## Rapports Passés (Historique)
- Plusieurs rapports audit/diagnostic (à nettoyer)
- Guides déploiement Render, Oracle (alternatives non utilisées)

---

## ✅ RÉSUMÉ EXÉCUTIF

**NeoBot est un SaaS complèt avec:**
1. ✅ **Backend robuste** (FastAPI) — Mais 5 issues critiques
2. ✅ **Frontend moderne** (Next.js) — Mais endpoint mismatch
3. ✅ **WhatsApp integration** (Baileys) — Mais webhook auth échoue
4. ✅ **Paiements** (Korapay) — Fonctionnel
5. ✅ **Analytics** — Implémenté
6. ✅ **Monitoring** (Sentry) — En place
7. ❌ **Mais NOT fonctionnel en production** — 5 blockers critiques à fixer

**Priorité:** Fixer les 5 problèmes dans [DIAGNOSTIC_COMPLET_2026_04_17.md](DIAGNOSTIC_COMPLET_2026_04_17.md)
