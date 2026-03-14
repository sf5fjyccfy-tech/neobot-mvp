# 🎯 NEOBOT MVP - PLAN D'ACTION STRUCTURÉ
**Date**: 11 Février 2026  
**Status**: Phase 1-9 COMPLÉTÉES ✅ | Phase LANDING EN COURS 🔴

---

## 📊 ÉTAT ACTUEL DU PROJET

### ✅ COMPLÉTÉ (Phases 1-9)
- Authentication système (JWT + tenant isolation)
- Multi-tenant data isolation garantie
- Usage tracking + quota system
- Overage billing (charge + continue model)
- Frontend config UI (business forms)
- Dashboard avec UsageDisplay widget
- Analytics complète (7 endpoints, 4 composants)
- Tests d'intégration (20+ cas)
- Déploiement automatisé staging

### 🔴 À FAIRE IMMÉDIAT (MVP Phase 1)
**Priorité 1 - BLOQUANT (Cette session)**
1. Landing Page (présentation + CTA)
2. Pricing Page (plans + tarifs confirmés)
3. Business Types Structures (Restaurant, E-commerce)
4. 7-Day Free Trial Logic
5. Personas Customisables (AI tone)

**Priorité 2 - IMPORTANT (Session suivante)**
6. Payment Gateway (Stripe Sandbox)
7. Admin Panel (gérer tenants)
8. Support templates (emails)
9. Terms + Privacy Policy pages
10. Performance optimization

**Priorité 3 - FUTUR (Après Phase 2)**
11. Photo upload (S3 integration)
12. Multi-language support
13. Reservation system (restaurants)
14. Advanced analytics (AI insights)

---

## 🏗️ ARCHITECTURE - QUI PARLE À QUI

```
FRONTEND (Next.js) 
  ├─ Landing Page (public)
  ├─ Pricing Page (public/authenticated)
  ├─ Login/Signup (public)
  ├─ Dashboard (authenticated)
  │  ├─ Config (business setup)
  │  ├─ Conversations (messages en temps réel)
  │  ├─ Analytics (stats)
  │  └─ Settings (persona, WhatsApp QR)
  └─ (Future) Admin Panel
         ↓ HTTPS + JWT
BACKEND (FastAPI)
  ├─ /api/auth/* (login, signup, logout)
  ├─ /api/tenants/* (CRUD + isolation)
  ├─ /api/tenants/{id}/business/config (business setup)
  ├─ /api/tenants/{id}/whatsapp/* (QR, session)
  ├─ /api/tenants/{id}/usage/* (quotas)
  ├─ /api/tenants/{id}/analytics/* (stats)
  ├─ /api/tenants/{id}/subscriptions/* (trial, plans)
  ├─ /api/whatsapp/webhook (reçoit messages)
  └─ /api/admin/* (gérer tenants - future)
         ↓
DATABASE (PostgreSQL)
  ├─ users (auth)
  ├─ tenants (multi-tenant)
  ├─ business_configs (menus, horaires, etc)
  ├─ subscriptions (plan + trial tracking)
  ├─ usage_tracking (messages count)
  ├─ overages (billing)
  ├─ conversations (chats)
  ├─ messages (historique)
  └─ whatsapp_sessions (phone mapping)
         ↓
WHATSAPP SERVICE (Node.js + Baileys)
  → Gère N sessions par tenant
  → Reçoit/envoie messages
  → QR code management
```

---

## 🎬 10 ÉTAPES - EXÉCUTION LOGIQUE

### ✅ ÉTAPE 1-9: COMPLÉTÉES PHASES 1-9

### 🔴 ÉTAPE 10: LANDING PAGE (2-3h) **← MAINTENANT**

**Fichiers à créer:**
```
frontend/src/app/page.tsx                    (Landing page)
frontend/src/components/landing/Header.tsx   (Nav + hero)
frontend/src/components/landing/Features.tsx (Features section)
frontend/src/components/landing/CTA.tsx      (Call-to-action)
frontend/src/components/landing/Footer.tsx   (Footer)
```

**Contenu Landing:**
- ✅ Hero section (titre accrocheur + description)
- ✅ 3 plans affichés (Basique, Standard, Pro)
- ✅ Features list (multi-tenant, AI, analytics, etc)
- ✅ Use cases (Restaurant example, E-commerce example)
- ✅ Testimonials (future: vidéos clients)
- ✅ FAQ
- ✅ CTA buttons ("Essayer gratuitement 7 jours")

### 🔴 ÉTAPE 11: PRICING PAGE (1-2h) **← MAINTENANT**

**Fichiers à créer:**
```
frontend/src/app/pricing/page.tsx        (Pricing page)
frontend/src/components/pricing/PricingCard.tsx (Plan card)
frontend/src/components/pricing/Comparison.tsx  (Feature comparison)
```

**Contenu Pricing:**
- ✅ 3 plans côte à côte
- ✅ Features par plan
- ✅ Price + messages/mois + overage price
- ✅ Comparison table (all features)
- ✅ CTA "S'inscrire" par plan
- ✅ FAQ pricing

### 🟡 ÉTAPE 12: BUSINESS TYPES STRUCTURES (2-3h) **← APRÈS LANDING**

**Backend:**
```
backend/app/models.py:
  ├─ struct_restaurant:
  │  ├─ menu_items (name, price, description, category)
  │  ├─ opening_hours (mon-sun, time ranges)
  │  ├─ delivery_zones (zones, prices)
  │  └─ reservations (enabled, table count, etc)
  │
  └─ struct_ecommerce:
     ├─ products (name, price, description, category, sku)
     ├─ return_policy (days, conditions)
     ├─ warranty_info (duration, coverage)
     └─ shipping (zones, prices, methods)
```

**Frontend:**
```
frontend/src/components/config/RestaurantConfig.tsx
frontend/src/components/config/EcommerceConfig.tsx
frontend/src/components/config/PersonaConfig.tsx
```

### 🟡 ÉTAPE 13: 7-DAY FREE TRIAL LOGIC (1-2h) **← APRÈS LANDING**

**Backend:**
```
/api/tenants/{id}/subscription/trial
  └─ POST: Start trial (set trial_end = today + 7 days)
  └─ GET: Check trial status (remaining days)
  └─ POST: End trial (convert to paid or delete)

database migration:
  subscriptions table:
  ├─ tenant_id
  ├─ plan (basique/standard/pro)
  ├─ trial_start (nullable)
  ├─ trial_end (nullable)
  ├─ is_trial (boolean)
  ├─ status (active/cancelled/expired)
  └─ started_at
```

**Frontend:**
```
Signup form:
  └─ Auto-start trial (7 days Basique plan)
  
Dashboard:
  ├─ Display "7-day trial" badge
  ├─ Show "Days remaining: 5"
  ├─ CTA "Upgrade to Pro" when trial ending
  └─ Auto-redirect to upgrade at trial_end
```

### 🟡 ÉTAPE 14: PERSONAS CUSTOMISABLES (1-2h) **← APRÈS LANDING**

**Backend:**
```
business_configs table:
  ├─ persona_name (ex: "Friendly waiter")
  ├─ persona_tone (professional/friendly/expert/casual/formal)
  ├─ persona_custom_prompt (optional: custom instructions)
  └─ selling_focus ("Vendre", "Informer", "Support")

/api/tenants/{id}/business/config/persona
  └─ POST: Update persona
```

**Frontend:**
```
Settings page:
  ├─ Persona tone selector (5 buttons)
  ├─ Custom persona text input
  ├─ Preview of AI response (test mode)
  └─ Save button
```

### 🟢 ÉTAPE 15: PAYMENT GATEWAY (3-4h) **← PHASE 2**

**Backend:**
```
/api/tenants/{id}/payment/checkout
  └─ POST: Create Stripe session → return checkout_url

/api/webhook/stripe
  └─ POST: Handle payment success/failure
```

**Frontend:**
```
Payment modal:
  ├─ Stripe checkout form
  ├─ Card details input
  └─ Confirmation
```

### 🔵 ÉTAPE 16-20: FUTURE (After Phase 2)

- Admin panel (manage tenants)
- Advanced analytics
- Photo upload (S3)
- Multi-language
- Reservation system

---

## ⚡ PRIORISATION - CE QUI EST CRITIQUE

### MUST HAVE (avant première vente)
1. ✅ Auth + tenant isolation (FAIT)
2. ✅ Usage tracking + quotas (FAIT)
3. ✅ Billing overages (FAIT)
4. **🔴 Landing Page** (START NOW)
5. **🔴 Pricing Page** (START NOW)
6. **🟡 7-Day Free Trial** (PHASE 1)
7. **🟡 Business Config** (PHASE 1)

### NICE TO HAVE (avant go-live)
8. Personas customisables (PHASE 1)
9. Payment gateway (PHASE 2)
10. Terms + Privacy pages (PHASE 1)

### FUTURE (après première client)
11. Photo upload (PHASE 3)
12. Admin panel (PHASE 3)
13. Multi-language (PHASE 3)
14. Advanced features (PHASE 3+)

---

## 📋 CHECKLIST D'IMPLÉMENTATION

### Landing Page
- [ ] Hero section (title, subtitle, CTA)
- [ ] Features list (3-5 key features)
- [ ] Plans preview (3 cards)
- [ ] Use cases (Restaurant, E-commerce)
- [ ] CTA buttons ("Get started free")
- [ ] Footer (links, copyright)

### Pricing Page
- [ ] Plan cards (side by side)
- [ ] Feature comparison table
- [ ] Toggle yearly/monthly (future)
- [ ] FAQ section
- [ ] CTA buttons

### Business Config
- [ ] Restaurant form (menu, hours, delivery)
- [ ] E-commerce form (products, policies)
- [ ] Generic form (custom fields)
- [ ] Form validation
- [ ] Save to DB

### 7-Day Trial
- [ ] Trial auto-start on signup
- [ ] Trial badge in dashboard
- [ ] Countdown display
- [ ] Trial-end warning
- [ ] Auto-convert logic

### Personas
- [ ] Tone selector (5 options)
- [ ] Custom prompt field
- [ ] Preview button (test AI response)
- [ ] Save to DB
- [ ] Use in webhook (include in prompt)

---

## 🔍 CLARIFICATIONS RÉPONDUES

### 1. Authentication ✅
**Approche**: Password simple (pas OAuth pour MVP)
- Email confirmation: NON (future)
- 2FA: NON (future)
- JWT tokens: OUI (implémenté)

### 2. Tenant Isolation ✅
**Approche**: Tenant ID en JWT + vérification chaque request
- Row-level security: NON (JWT suffisant)
- RBAC: NON (future - just 1 tenant type pour now)

### 3. WhatsApp Service ✅
**Approche**: 1 service Node.js → N sessions par tenant
- Chaque tenant = 1 session Baileys
- Messages routés auto par phone

### 4. Payment ✅
**Approche**: 7-day trial → Stripe Sandbox → upgrade
- Phase 2: Implémentation complète
- MVP: Trial gratuit seulement

### 5. Personas ✅
**Approche**: Champs simples (tone + custom prompt)
- Auto-génère prompt enrichi
- Templates future (Phase 3)

### 6. Photos ✅
**Approche**: Skip pour MVP
- Phase 3: S3 integration
- MVP: Text only

---

## 🎯 RÉSUMÉ EXÉCUTION

**Session ACTUELLE (maintenant):**
1. Create Landing Page
2. Create Pricing Page
3. Database: Add subscriptions table
4. Backend: Add /api/subscriptions/* endpoints

**Session SUIVANTE:**
5. Business Types Structures
6. Personas Customisables
7. 7-Day Free Trial Logic
8. Testing + Bugfixes

**Phase 2 (Prochaine semaine):**
9. Payment Gateway (Stripe)
10. Admin Dashboard
11. Full integration testing
12. Production readiness

---

**Next Step**: Coder Landing Page ✅
