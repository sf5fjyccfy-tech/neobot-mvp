# 🔍 AUDIT COMPLET NEOBOT - RAPPORT DÉTAILLÉ

**Date:** 11 février 2026  
**Statut:** VÉRIFICATION EN COURS  
**Objectif:** Valider l'alignement entre le code actuel et les spécifications métier

---

## ✅ **CE QUI FONCTIONNE BIEN**

### 1️⃣ **Database Models** 
✅ **CORRECT** - Tous les modèles existent:
- `Tenant` (avec plan, quota messages)
- `Conversation` (avec tenant_id, customer_phone)
- `Message` (avec direction, is_ai)
- `BusinessTypeModel` (8 types: neobot, restaurant, ecommerce, travel, salon, fitness, consulting, custom)
- `TenantBusinessConfig` (avec products_services JSON, tone, selling_focus)
- `ConversationContext` (pour tracking client interests)

### 2️⃣ **Plan Limits Configuration**
✅ **CORRECT dans models.py:**
```python
BASIQUE: 20,000 FCFA → 2,000 messages/mois ✅
STANDARD: 50,000 FCFA → 2,500 messages/mois ✅
PRO: 90,000 FCFA → 4,000 messages/mois ⚠️ (VOIR ZONE D'OMBRE #1)
```

### 3️⃣ **Business Intelligence Service**
✅ **COMPLET 200+ lignes:**
- `get_business_persona()` → Récupère config business
- `enrich_prompt_with_context()` → Enrichit prompts avec historique + infos client
- `_get_business_instructions()` → 7 types de business instructions (restaurant, ecommerce, travel, salon, fitness, neobot, custom)
- Context enrichment = **WORKING** ✅ (testé avec La Saveur restaurant)

### 4️⃣ **Tenant Business Router**
✅ **4 ENDPOINTS IMPLÉMENTÉS:**
- `POST /api/tenants/{tenant_id}/business/config` → Configurer business ✅
- `GET /api/tenants/{tenant_id}/business/config` → Récupérer config ✅
- `GET /api/business/types` → Lister les 8 business types ✅
- `DELETE /api/tenants/{tenant_id}/business/config` → Supprimer config ✅

### 5️⃣ **WhatsApp Service**
✅ **FONCTIONNEL:**
- Baileys intégré pour multi-tenant (chaque client = session indépendante)
- QR code generation implémenté
- Webhook réception des messages ✅
- Envoi des réponses IA ✅

### 6️⃣ **Frontend Pages Principales**
✅ **EXISTENT:**
- Landing page (page.tsx) → Présentation NéoBot
- Dashboard (dashboard/page.tsx) → Tableau de bord
- Conversations (conversations/page.tsx) → Chat viewer
- Settings (settings/page.tsx) → Paramètres
- Analytics (analytics/page.tsx) → Statistiques

### 7️⃣ **API Helper**
✅ **CORRECT:**
- `lib/api.ts` → Centralized API configuration
- Supporte environment variables (NEXT_PUBLIC_API_URL)
- Fallback to localhost:8000 ✅

---

## ❌ **ERREURS DÉTECTÉES**

### **ERREUR #1: Plan Pro - 4K vs 40K Messages**
**Sévérité:** 🔴 CRITIQUE  
**Localisation:** `backend/app/models.py` ligne ~52  
**Problème:**
```python
PlanType.PRO: {
    "name": "Pro",
    "price_fcfa": 90000,
    "whatsapp_messages": 4000,  # ❌ DEVRAIT ÊTRE 40000 ?
```
**Confirmation nécessaire:** Vous aviez dit "Plan Pro 90,000 FCFA = 40,000 messages/mois"  
**Code actuel:** Dit 4,000 messages  
**À corriger:** Remplacer `4000` par `40000`

---

### **ERREUR #2: Tenant Hardcoding dans Webhook**
**Sévérité:** 🔴 CRITIQUE  
**Localisation:** `backend/app/whatsapp_webhook.py` ligne 271-272  
**Problème:**
```python
# TODO: Map phone number to tenant (for now hardcode tenant_id = 1)
tenant_id = 1  # Default tenant for testing
```
**Impact:** TOUS les messages de TOUS les clients vont au tenant 1 (NéoBot)!  
**Conséquence:**
- Client A (restaurant) envoie message → Va à NéoBot ❌
- Client B (ecommerce) envoie message → Va à NéoBot ❌
- Le bot NéoBot répondrait à tous ❌

**À Faire:** Implémenter mapping phone → tenant_id

---

## ⚠️ **ZONES D'OMBRE (Questions à résoudre)**

### **ZONE D'OMBRE #1: Messages Plan Pro**
❓ **Plan Pro: 4,000 ou 40,000 messages/mois?**
- Code dit: 4,000
- Vous aviez dit: 40,000
- Avec: "Plan Pro 90K = 40,000 messages"
→ **Confirmation à donner** ✋

### **ZONE D'OMBRE #2: Login/Signup Frontend**
❌ **Manquent complètement**  
**État actuel:** 
- Pas de page `/app/login`
- Pas de page `/app/signup`
- Pas de composant d'auth en Next.js moderne
- Code auth ancien existe au backend (`app/api/auth.py`) mais pas intégré frontend

**Ce qui existe:**
- Backend: `/api/auth/login` → Prend form data (username/password)
- Backend: `/api/auth/register` → Prend UserCreate model
- Frontend: RIEN (pages manquantes!)

**À Faire:**
1. Créer `frontend/src/app/login/page.tsx`
2. Créer `frontend/src/app/signup/page.tsx`
3. Créer composant `LoginForm`
4. Créer composant `SignupForm`
5. Implémenter JWT token storage + routing protégé

### **ZONE D'OMBRE #3: Tenant Mapping WhatsApp**
❌ **Comment le WhatsApp service sait quel tenant c'est?**

**Actuellement:** Hardcoded à tenant 1

**À définir ensemble:**
- iPhone WhatsApp Account 1 → Tenant ID?
- iPhone WhatsApp Account 2 → Tenant ID?
- Comment faire le mapping?

**Options:**
- A: Store dans DB `whatsapp_sessions` (phone ↔ tenant_id) ?
- B: Store dans env variables?
- C: Autre approche?

### **ZONE D'OMBRE #4: User/Tenant Relationship**
❌ **Comment un utilisateur se connecte à son tenant?**

**Manque:**
- Table `users` - Je vois dans le code qu'elle existe (`app/models.py`), mais pas vérifiée
- Relation `User.tenant_id` - ✅ Existe dans auth.py
- Mais: Comment verify que l'utilisateur peut accéder au tenant?

**À Vérifier:**
- Middleware d'authentification qui extrait tenant_id du JWT
- Vérification que le user peut vraiment accéder GET/PATCH du tenant

### **ZONE D'OMBRE #5: Overage Pricing - 7000 F per 1000 messages**
❓ **Quand on calcule le surcoût, c'est:**
- Basique → Overage? (oui)
- Standard → Pas d'overage? (ou possibilité aussi?)
- Pro → Pas d'overage? (40K suffisant)

**Code implémenté:** Pas trouvé la logique d'overage!

**À Faire:**
- Ajouter calcul de surcoût
- Ajouter alerte client avant déconnexion
- Implémenter déconnexion après limite

---

## 🔐 **SÉCURITÉ - Tenant Isolation**

**État:**
- ✅ Database: FK constraints par tenant_id exist
- ❌ API: Pas de vérification JWT en tous endpoints
- ❌ Webhook: tenant_id hardcoded = NO ISOLATION
- ⚠️ Frontend: Pas de routes protégées

**À Faire:**
1. Middleware JWT global
2. Extract tenant_id from JWT
3. Verify user appartient au tenant
4. Reject si pas autorisé

---

## 📋 **FEATURES MANQUANTES**

### **FRONTEND:**
- [ ] Login page + form
- [ ] Signup page + form
- [ ] Protected routes (dashboard redirects to login if not auth)
- [ ] JWT token storage (localStorage/cookies)
- [ ] Configuration page (formulaire pour setup products/horaires)
- [ ] QR code display (WhatsApp connection)

### **BACKEND:**
- [ ] Phone → Tenant mapping
- [ ] JWT middleware for all protected routes
- [ ] Overage pricing calculation
- [ ] Usage tracking per month
- [ ] Alerts when quota 80%, 100%
- [ ] Bot auto-disconnect when limit reached

### **DATABASE:**
- [ ] Verify `users` table exists
- [ ] Add `usage_tracking` table (messages par jour/mois)
- [ ] Add `subscriptions` table (plan history)
- [ ] Add `whatsapp_sessions` table (phone ↔ tenant mapping)

---

## 🎯 **RÉSUMÉ GÉNÉRAL**

| Aspect | État | Criticité |
|--------|------|-----------|
| Database Models | ✅ OK | - |
| Business Intelligence | ✅ OK | - |
| Tenant Config Routes | ✅ OK | - |
| WhatsApp Service | ✅ Fonctionnel | - |
| Frontend Pages (landing, dashboard) | ✅ OK | - |
| **Plan Pricing** | ❌ PRO = 4K vs 40K? | 🔴 CRITIQUE |
| **Tenant Mapping** | ❌ HARDCODED à 1 | 🔴 CRITIQUE |
| **Login/Signup Frontend** | ❌ MANQUANTS | 🔴 CRITIQUE |
| **JWT Auth** | ⚠️ Partial (backend only) | 🟠 MAJEUR |
| **Overage Pricing** | ❌ NOT IMPL | 🟠 MAJEUR |
| **Usage Tracking** | ❌ NOT IMPL | 🟠 MAJEUR |

---

## ✋ **QUESTIONS POUR VOUS**

1. **Pro Plan:** 4,000 ou 40,000 messages/mois? (Corriger le code)
2. **Tenant Mapping:** Comment faire le mapping phone → tenant_id?
3. **Overage:** Quand on atteint la limite, on facture automatiquement l'overage ou on déconnecte direct?
4. **Usage Tracking:** Besoin de logs détaillés (par jour) ou juste le total du mois?
5. **Auth:** Vous avez préférence JWT (tokens) ou sessions (cookies)?

---

## 📊 **ESTIMATION DE TRAVAIL**

- **Corrections petites** (pro plan prix): 5 min
- **Frontend Auth pages**: 2-3 heures
- **Tenant mapping WebhatsApp**: 2-3 heures
- **JWT middleware + protected routes**: 2-3 heures
- **Usage tracking**: 3-4 heures
- **Overage logic**: 2 heures
- **Testing complet**: 3-4 heures

**TOTAL:** ~20-25 heures

---

