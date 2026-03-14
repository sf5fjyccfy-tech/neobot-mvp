# 🚀 **PLAN D'IMPLÉMENTATION NEOBOT - ÉTAPES LOGIQUES**

**Basé sur:** Audit complet + Architecture reconnue  
**Objectif:** Implémenter les 5 features critiques sans casser le système  
**Timeline:** 20-25 heures

---

## **PHASE 1: VÉRIFICATIONS & CORRECTIONS CRITIQUES (1-2 heures)**

### **ÉTAPE 1.1: Corriger Pro Plan Pricing**
**Criticité:** 🔴 IMMÉDIATE  
**Temps:** 5 min  
**Fichier:** `backend/app/models.py`  

```python
# AVANT:
"whatsapp_messages": 4000,

# APRÈS (à confirmer):
"whatsapp_messages": 40000,  # Si c'est 40K
# OU
"whatsapp_messages": 4000,   # Si c'est 4K
```

**Action:** Attendre confirmation pour le nombre exact

### **ÉTAPE 1.2: Vérifier Database Users Table**
**Criticité:** 🟠 IMPORTANT  
**Temps:** 10 min  
**Vérification:**
```bash
# Dans psql:
\d users

# Doit avoir:
- id (PK)
- email (unique)
- hashed_password
- tenant_id (FK)
- is_superuser
- created_at
```

**Résultat:**  
✅ Existe ou ❌ À créer

---

## **PHASE 2: AUTHENTICATION FRONTEND (3-4 heures)**

### **ÉTAPE 2.1: Créer Login Page**
**Criticité:** 🔴 CRITIQUE  
**Temps:** 1.5 heures  
**Fichier à créer:** `frontend/src/app/login/page.tsx`  

**Doit inclure:**
- Form: email + password
- Submit → POST `/api/auth/login`
- Success → Save JWT token → Redirect `/dashboard`
- Error → Show error message
- Link to signup page

**Dépendances:** LoginForm component

### **ÉTAPE 2.2: Créer Signup Page**
**Criticité:** 🔴 CRITIQUE  
**Temps:** 1.5 heures  
**Fichier à créer:** `frontend/src/app/signup/page.tsx`  

**Doit inclure:**
- Form: full_name, email, password, tenant_name, business_type
- Submit → POST `/api/auth/register`
- Success → Auto-login + Redirect `/dashboard`
- Error handling

**Dépendances:** SignupForm component

### **ÉTAPE 2.3: Créer Protected Routes**
**Criticité:** 🟠 MAJEUR  
**Temps:** 1 heure  
**Fichier à créer:** `frontend/src/middleware.ts`  

**Logic:**
```typescript
// Vérifier JWT token en chaque requête
// Si pas de token → Redirect /login
// Si token expiré → Clear + Redirect /login
// Si valide → Continue
```

**Protéger:**
- `/dashboard/*`
- `/conversations`
- `/settings`
- `/analytics`
- `/clients`
- `/billing`

### **ÉTAPE 2.4: Implémenter JWT Storage**
**Criticité:** 🟠 MAJEUR  
**Temps:** 30 min  
**Fichier à modifier:** `frontend/src/lib/api.ts`  

**Ajouter:**
```typescript
export const setToken = (token: string) => localStorage.setItem('jwt_token', token);
export const getToken = () => localStorage.getItem('jwt_token');
export const clearToken = () => localStorage.removeItem('jwt_token');

// Inclure token dans tous les requests:
headers: {
  'Authorization': `Bearer ${getToken()}`,
  ...
}
```

---

## **PHASE 3: TENANT MAPPING WHATSAPP (2-3 heures)**

### **ÉTAPE 3.1: Créer Table WhatsApp Sessions**
**Criticité:** 🔴 CRITIQUE  
**Temps:** 30 min  
**Migration SQL:** `backend/migrations/005_whatsapp_sessions.sql`  

```sql
CREATE TABLE whatsapp_sessions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL UNIQUE REFERENCES tenants(id),
    whatsapp_phone VARCHAR(50) NOT NULL UNIQUE,
    baileys_session_file TEXT,
    is_connected BOOLEAN DEFAULT false,
    last_connected_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### **ÉTAPE 3.2: Implémenter Phone → Tenant Mapping**
**Criticité:** 🔴 CRITIQUE  
**Temps:** 1.5 heures  
**Fichier à modifier:** `backend/app/whatsapp_webhook.py`  

**Logic:**
```python
# AVANT (hardcoded):
tenant_id = 1

# APRÈS (dynamic):
def get_tenant_from_phone(phone: str, db: Session) -> int:
    """Map WhatsApp phone number to tenant_id"""
    session = db.query(WhatsAppSession).filter(
        WhatsAppSession.whatsapp_phone == phone
    ).first()
    
    if not session:
        # Phone not registered - return error or default?
        raise HTTPException(status_code=400, detail="Phone not registered")
    
    return session.tenant_id

# Utilisation:
tenant_id = get_tenant_from_phone(message.from, db)
```

### **ÉTAPE 3.3: Ajouter QR Code Endpoint**
**Criticité:** 🟠 MAJEUR  
**Temps:** 1 heure  
**Fichier:** `backend/app/routers/whatsapp.py` (créer si pas existe)  

```python
@router.get("/api/tenants/{tenant_id}/whatsapp/qr")
async def get_whatsapp_qr(tenant_id: int, db: Session = Depends(get_db)):
    """
    Retourne QR code pour connecter WhatsApp au tenant
    Appelé par le dashboard quand client clique "Connecter WhatsApp"
    """
    # Générer ou récupérer session Baileys
    # Retourner QR code si authentification en cours
    # Retourner "connecté" si déjà connecté
```

---

## **PHASE 4: USAGE TRACKING & QUOTAS (3-4 heures)**

### **ÉTAPE 4.1: Créer Table Usage Tracking**
**Criticité:** 🟠 MAJEUR  
**Temps:** 30 min  
**Migration SQL:** `backend/migrations/006_usage_tracking.sql`  

```sql
CREATE TABLE usage_tracking (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    month_year VARCHAR(7) NOT NULL, -- "2026-02"
    whatsapp_messages_used INTEGER DEFAULT 0,
    other_platform_messages_used INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(tenant_id, month_year)
);
```

### **ÉTAPE 4.2: Implémenter Usage Counter**
**Criticité:** 🟠 MAJEUR  
**Temps:** 1.5 heures  
**Fichier à modifier:** `backend/app/whatsapp_webhook.py`  

**Logic:**
```python
async def process_message(message):
    # 1. Receive message
    # 2. Get tenant_id
    # 3. CHECK QUOTA:
    #    - Get plan limits
    #    - Get usage this month
    #    - Compare: usage < limit?
    #    - If over: DISCONNECT bot (ou bloquer)
    # 4. Process message
    # 5. INCREMENT usage (user message + AI response = 2)
```

### **ÉTAPE 4.3: Ajouter Usage Endpoints**
**Criticité:** 🟠 MAJEUR  
**Temps:** 1 heure  
**Fichier:** `backend/app/routers/usage.py` (créer)  

```python
@router.get("/api/tenants/{tenant_id}/usage")
async def get_usage(tenant_id: int, db: Session = Depends(get_db)):
    """
    Retourne usage du mois courant
    Utilisé par analytics page
    Format: {
        "plan": "Pro",
        "limit": 40000,
        "used": 12345,
        "percent": 31,
        "remaining": 27655,
        "overage": 0,
        "overage_cost": 0
    }
    """

@router.get("/api/tenants/{tenant_id}/usage/history")
async def get_usage_history(tenant_id: int, db: Session = Depends(get_db)):
    """
    Retourne historique usage (derniers 12 mois)
    Pour graphique analytics
    """
```

---

## **PHASE 5: OVERAGE PRICING (2 heures)**

### **ÉTAPE 5.1: Créer Table Overages**
**Criticité:** 🟡 IMPORTANT  
**Temps:** 20 min  
**Migration SQL:** `backend/migrations/007_overages.sql`  

```sql
CREATE TABLE overages (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    month_year VARCHAR(7) NOT NULL,
    messages_over INTEGER DEFAULT 0,
    cost_fcfa INTEGER DEFAULT 0,
    is_billed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### **ÉTAPE 5.2: Implémenter Overage Calculation**
**Criticité:** 🟡 IMPORTANT  
**Temps:** 1.5 heures  
**Fichier à crèer:** `backend/app/services/overage_service.py`  

```python
class OverageService:
    OVERAGE_PRICE = 7000  # per 1000 messages
    
    @staticmethod
    def calculate_overage(tenant_id: int, usage: int, plan_limit: int):
        """
        Si usage > limit:
            messages_over = usage - limit
            cost = (messages_over / 1000) * 7000
        """
        if usage <= plan_limit:
            return 0, 0
        
        over = usage - plan_limit
        # Round up to nearest 1000
        over_rounded = ceil(over / 1000) * 1000
        cost = (over_rounded / 1000) * OVERAGE_PRICE
        
        return over, cost
```

---

## **PHASE 6: FRONTEND BUSINESS CONFIGURATION (2-3 heures)**

### **ÉTAPE 6.1: Créer Configuration Page**
**Criticité:** 🟠 MAJEUR  
**Temps:** 2 heures  
**Fichier à créer:** `frontend/src/app/clients/config/page.tsx`  

**Doit avoir:**
- SELECT: Business Type (restaurant, ecommerce, etc.)
- TEXT: Company Name
- TEXTAREA: Company Description
- SELECT: Tone (Professional, Friendly, Expert)
- TEXT: Selling Focus

**Pour RESTAURANT (si sélectionné):**
- TABLE: Menu Items (add/edit/delete)
  - Nom, Prix, Description
- TEXTAREA: Horaires ouverture
- CHECKBOX: Livraison? + zones
- CHECKBOX: Réservations?

**Pour ECOMMERCE (si sélectionné):**
- TABLE: Products (add/edit/delete)
  - Nom, Prix, Description, Catégorie
- CHECKBOX: Accepte retours?
- TEXT: Garantie info

### **ÉTAPE 6.2: Créer QR Code Display**
**Criticité:** 🟠 MAJEUR  
**Temps:** 1 heure  
**Fichier à créer:** `frontend/src/components/whatsapp/QRCodeDisplay.tsx`  

**Logic:**
```typescript
// 1. Au load: GET /api/tenants/{id}/whatsapp/qr
// 2. Si QR reçu: Afficher l'image
// 3. Si "connecté": Afficher "✅ Connecté"
// 4. Si erreur: Afficher "❌ Erreur - Essayer again"
// 5. Poll toutes les 5 secondes pour vérifier connection status
```

---

## **PHASE 7: ANALYTICS & DASHBOARD (2-3 heures)**

### **ÉTAPE 7.1: Implémenter Analytics Endpoints**
**Criticité:** 🟠 MAJEUR  
**Temps:** 1.5 heures  
**Fichier à créer:** `backend/app/routers/analytics.py`  

```python
@router.get("/api/tenants/{tenant_id}/analytics/summary")
async def get_analytics_summary(tenant_id: int, db: Session = Depends(get_db)):
    """
    Retourne résumé pour dashboard
    {
        "messages_today": 42,
        "conversations_active": 5,
        "response_rate": 95,
        "avg_response_time": "1.2s",
        "plan": "Pro",
        "usage_percent": 31
    }
    """

@router.get("/api/tenants/{tenant_id}/analytics/messages-daily")
async def get_messages_daily(tenant_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Retourne messages par jour (pour graphique)"""
```

### **ÉTAPE 7.2: Mettre à jour Dashboard**
**Criticité:** 🟡 IMPORTANT  
**Temps:** 1 heure  
**Fichier à modifier:** `frontend/src/app/dashboard/page.tsx`  

**Ajouter widgets:**
- Messages aujourd'hui (vs hier)
- Conversations actives
- Taux de réponse AI
- Quota usage (bar chart)
- Plan info (avec bouton upgrade)

---

## **PHASE 8: TESTS INTÉGRATION (3-4 heures)**

### **ÉTAPE 8.1: Test Login/Signup Flow**
**Criticité:** 🔴 CRITIQUE  
**Temps:** 1 heure  

```
1. Signup nouveau user
   → Créé dans DB ✓
   → Créé tenant ✓
   → Auto-login ✓
   → Redirige dashboard ✓

2. Logout
   → Clear token ✓
   → Redirige login ✓

3. Login
   → Accepte credentials ✓
   → Génère JWT ✓
   → Redirige dashboard ✓

4. Protected routes
   → Sans token: redirige login ✓
   → Avec token expiré: clear + redirige ✓
```

### **ÉTAPE 8.2: Test Tenant Isolation**
**Criticité:** 🔴 CRITIQUE  
**Temps:** 1 heure  

```
1. User A configure restaurant
2. User B configure ecommerce
3. Message arrive WhatsApp
   → Route à user A ✓ (pas user B)
4. User A voit uniquement ses conversations ✓
5. User B voit uniquement ses conversations ✓
```

### **ÉTAPE 8.3: Test Quota & Usage**
**Criticité:** 🔴 CRITIQUE  
**Temps:** 1 heure  

```
1. Setup user avec Pro plan (40K limit)
2. Envoyer 40K messages
3. Vérifier usage = 40K ✓
4. Envoyer 1 message de plus
   → Auto-disconnect ✓
   → OU bloquer ✓
5. Overage calculation correct ✓
```

### **ÉTAPE 8.4: Test Business Intelligence**
**Criticité:** 🟠 MAJEUR  
**Temps:** 1 heure  

```
1. Configure restaurant avec pizza, pasta
2. Customer demande "vous avez des plats?"
3. Bot répond avec menu réel ✓
4. Persona = restaurant tone ✓
5. Switching to ecommerce
6. Customer demande "catalogue?"
7. Bot répond avec products ✓
8. Persona = ecommerce tone ✓
```

---

## **PHASE 9: DEPLOYMENT STAGING (1-2 heures)**

### **ÉTAPE 9.1: Vérifier Migrations**
- Toutes les migrations SQL exécutées ✓
- Données test chargées ✓

### **ÉTAPE 9.2: Vérifier Discord Documentation**
- Update API docs ✓
- Update setup instructions ✓

### **ÉTAPE 9.3: Staging Deployment**
```bash
# Backend
git push
Deploy to staging server
Run migrations
Test endpoints

# Frontend
npm run build
Deploy to staging
Test e2e
```

---

## 📋 **SUMMARY - ORDER D'EXÉCUTION**

```
1️⃣  PHASE 1 (1h): Corrections critiques
    └─ Plan Pro pricing
    └─ Vérifier users table

2️⃣  PHASE 2 (3-4h): Auth Frontend
    └─ Login page
    └─ Signup page
    └─ Protected routes
    └─ JWT storage

3️⃣  PHASE 3 (2-3h): Tenant Mapping
    └─ WhatsApp sessions table
    └─ Phone → tenant mapping
    └─ QR code endpoint

4️⃣  PHASE 4 (3-4h): Usage Tracking
    └─ Usage table
    └─ Counter logic
    └─ Usage endpoints

5️⃣  PHASE 5 (2h): Overage Pricing
    └─ Overages table
    └─ Calculation service

6️⃣  PHASE 6 (2-3h): Frontend Config
    └─ Configuration page
    └─ QR code display

7️⃣  PHASE 7 (2-3h): Analytics
    └─ Analytics endpoints
    └─ Dashboard update

8️⃣  PHASE 8 (3-4h): Testing
    └─ Login/signup flow
    └─ Tenant isolation
    └─ Quota limits
    └─ Business intelligence

9️⃣  PHASE 9 (1-2h): Deployment
    └─ Staging
    └─ Documentation
    └─ Go-live

TOTAL: ~20-25 heures
```

---

## ✅ **CHECKLIST AVANT CODING**

- [ ] Pro Plan: 4K ou 40K? (Confirmé)
- [ ] Database `users` table vérifié
- [ ] JWT secret key sécurisé
- [ ] SMS/Email service pour reset password? (À définir)
- [ ] Stripe integration pour paiement? (Phase future ou MVP?)
- [ ] Admin panel? (Phase future ou MVP?)

---

