# 🔍 AUDIT SYSTÈME COMPLET NEOBOT — 18 avril 2026

## Résumé Exécutif

**Pourcentage de vendabilité : 35-40% ⚠️ CRITIQUE**

**Verdict**: Le système n'est **PAS vendable en l'état** aux entreprises. Trop de problèmes critiques bloquent les paiements réels.

---

## 1. ÉTAT INFRASTRUCTURE

### ✅ CE QUI MARCHE

| Composant | Status | Notes |
|-----------|--------|-------|
| **Backend (FastAPI)** | ✅ Healthy | Port 8000, base de données connectée |
| **Frontend (Next.js)** | ⚠️ Unhealthy | Port 3002, répond HTTP 200 mais healthcheck échoue |
| **WhatsApp Service** | ⚠️ Instable | Port 3001, se déconnecte régulièrement |
| **Base de données** | ✅ Healthy | Neon.tech PostgreSQL, connectée |
| **Docker Compose** | ✅ OK | 3 containers, networking configuré |
| **Monitoring** | ✅ OK | Cron + Brevo alertes (déployé) |
| **Reverse Proxy** | ✅ OK | Cloudflare + neobot-ai.com |

### 🔴 CE QUI NE MARCHE PAS OU MAL

| Problème | Sévérité | Impact |
|----------|----------|--------|
| **FRONTEND_URL pointe vers Vercel** | 🔴 CRITIQUE | Paiements cassés, emails cassés, reset password cassé |
| **Korapay en TEST MODE** | 🔴 CRITIQUE | **AUCUN PAIEMENT RÉEL NE PEUT ÊTRE TRAITÉ** |
| **Frontend container unhealthy** | 🟠 HAUTE | Healthcheck échoue (mais page répond) |
| **WhatsApp déconnexions régulières** | 🟠 HAUTE | "Watchdog recovery triggered" toutes les 5-10 min |
| **Database SSL drops** | 🟠 HAUTE | "SSL connection has been closed unexpectedly" |

---

## 2. PROBLÈMES BLOQUANTS POUR LA VENTE

### 🔴 PROBLÈME #1 : FRONTEND_URL Incorrect (CRITIQUE)

**Situation actuelle**:
```
FRONTEND_URL=https://neobot-frontend-psi.vercel.app (MAUVAIS)
Réalité: Frontend tourne sur https://neobot-ai.com
```

**Où c'est utilisé** :
- ✗ **Paiements** : `redirect_url = "{FRONTEND_URL}/pay/{token}/callback"` 
  → Korapay redirige vers la mauvaise URL après paiement
- ✗ **Emails** : Tous les CTAs (boutons) pointent vers Vercel (domain expiré possiblement)
- ✗ **Reset password** : Les liens de reset envoient vers Vercel
- ✗ **Onboarding** : Les utilisateurs ne peuvent pas accéder à leur dashboard

**Impact**: **Les clients qui essaient de payer sont redirigés vers une mauvaise URL et ne peuvent pas finaliser**

**Fix requis** : Changer `.env` sur VPS :
```bash
FRONTEND_URL=https://neobot-ai.com
```
Puis redémarrer les containers.

---

### 🔴 PROBLÈME #2 : Korapay en TEST MODE (CRITIQUE)

**Situation actuelle**:
```
KORAPAY_SECRET_KEY=sk_test_Wyx2Z4qW6XudPNfFSrCLY3PZkfCM1nmpYBCG3YsB
KORAPAY_PUBLIC_KEY=pk_test_kHuPGLfY24U3Qf7NqG1MydXgqA4nXtRVg3w9f8ic
```

**Problème**: Les clés commencent par `sk_test_` et `pk_test_`
- ❌ Aucun paiement réel ne sera accepté
- ❌ Les transactions sont simulées/rejetées
- ❌ L'argent **ne sera jamais reçu sur le compte NeoBot**

**Impact**: **LES ENTREPRISES NE PEUVENT PAS PAYER. AUCUN REVENU POSSIBLE.**

**Fix requis** : 
1. Passer à Korapay Production dans le dashboard Korapay
2. Obtenir les vraies clés `sk_live_*` et `pk_live_*`
3. Remplacer dans `.env` sur VPS
4. Redémarrer

---

### 🟠 PROBLÈME #3 : WhatsApp Déconnexions Fréquentes (HAUTE)

**Logs observés**:
```
[2026-04-17T23:20:20.570Z] [INFO] Watchdog recovery triggered { tenantId: 1, state: 'disconnected' }
[2026-04-17T23:20:26.016Z] [WARN] Disconnect requires auth reset, regenerating QR
```

**Problème** :
- Le service WhatsApp perd la connexion
- Regénère le QR code automatiquement (mauvais pour les clients)
- Les messages peuvent ne pas être envoyés

**Cause probable** :
- WhatsApp/Baileys détecte un comportement suspect
- Logs insuffisants pour diagnostiquer
- Peut être une limite de Baileys ou une violation des règles WhatsApp

**Impact**: 
- ⚠️ Les agents WhatsApp peuvent ne pas répondre pendant 30-60 sec
- ⚠️ Perte de messages possibles
- ⚠️ Clients vont penser que le bot ne marche pas

---

### 🟠 PROBLÈME #4 : Database SSL Drops

**Logs**:
```
psycopg2.OperationalError: SSL connection has been closed unexpectedly
```

**Problème** :
- La connexion PostgreSQL (Neon.tech) se ferme brutalement
- Peut être un timeout de Neon ou une reconnexion défaillante

**Impact**:
- Des requêtes API peuvent échouer
- Perte de data possible (moins probable)
- Utilisateurs voient des erreurs

**Status**: Rare (seulement vu une fois dans les dernières 24h)

---

## 3. VÉRIFICATIONS FONCTIONNELLES

### ✅ Endpoints qui marchent

```bash
GET  /api/health               → 200 OK (database: connected)
GET  /docs                     → 200 OK (API documentation accessible)
GET  http://localhost:3002/    → 200 OK (frontend répond)
GET  https://neobot-ai.com/    → 200 OK (via Cloudflare)
```

### ❓ Endpoints pas testés à fond (besoin de vrais tokens)

| Endpoint | Status | Notes |
|----------|--------|-------|
| `POST /api/auth/register` | Accessible | Pas testé complètement |
| `POST /api/auth/login` | Accessible | Pas testé complètement |
| `GET /api/tenants/me` | Accessible | Nécessite JWT valide |
| `POST /api/neopay/payment-links` | Accessible | **Teste MODE TEST Korapay** |
| `POST /api/neopay/webhooks/korapay` | Accessible | **HMAC requis** |

---

## 4. CAPACITÉS FONCTIONNELLES

### ✅ Implémenté

- [x] Inscription utilisateur (Register)
- [x] Login/authentification
- [x] Gestion Tenants
- [x] 5 types d'agents (Libre, RDV, Support, FAQ, Vente, Qualification)
- [x] WhatsApp QR scanning
- [x] Conversations WhatsApp
- [x] Dashboard admin
- [x] Système de paiement (Korapay)
- [x] Brevo emails
- [x] Monitoring & alertes (bash + cron)
- [x] Analytics basique
- [x] Reset password par email

### ⚠️ Fonctionnel mais fragile

- **WhatsApp messaging** : Fonctionne mais déconnexions fréquentes
- **Paiements** : Architecture OK mais keys en TEST MODE

### ❌ Non implémenté ou désactivé

| Feature | Status | Notes |
|---------|--------|-------|
| Plans STANDARD/PRO | ❌ Gelés | `available: False` dans models.py |
| YouTube/URL sources | ❌ Désactivé | Seulement Text/PDF |
| SMS alerts | ❌ Non implémenté | Seulement email (Brevo) |
| Slack integration | ❌ Non implémenté | |
| Multiple channels | ❌ Pas testé | Prob OK côté code |
| CRM integration | ❌ Non implémenté | |

---

## 5. PLANS DISPONIBLES

### BASIC (Essential) — SEUL PLAN ACTIF

```
Plan       : BASIC
Disponible : Oui (available: True)
Prix       : 20,000 XAF/mois (environ 50€)
Trial      : 14 jours gratuits
Limites    :
  • 1 agent IA
  • 2,500 messages WhatsApp/mois
  • 3 sources de connaissance (Text + PDF)
  • Rappels RDV automatiques
  • Dashboard 30 jours
```

### STANDARD & PRO — GELÉS

```
STANDARD   : available: False (bientôt disponible)
PRO        : available: False (bientôt disponible)
```

---

## 6. SÉCURITÉ

### ✅ Implémenté

- [x] JWT authentication
- [x] Password hashing (bcrypt)
- [x] CORS configuré
- [x] Rate limiting (slowapi)
- [x] HMAC verification for webhooks
- [x] SSL/TLS via Cloudflare
- [x] Secrets in environment variables (pas hardcodés)

### ⚠️ À vérifier

- [ ] CSRF protection
- [ ] SQL injection (SQLAlchemy paramétré, looks safe)
- [ ] XSS (à vérifier dans frontend)
- [ ] Secrets dans les logs (Sentry)
- [ ] Database backups automatiques

---

## 7. PERFORMANCE

### Infrastructure
- **Disk** : 15GB/38GB utilisé (40%) ✅ OK
- **Memory** : 1GB/3.7GB utilisé (27%) ✅ OK
- **Containers memory limits** : Backend 512MB, WhatsApp 400MB, OK
- **Response times** : API répond en <1s ✅ OK

### Limitations actuelles
- [ ] Pas d'auto-scaling (VPS unique)
- [ ] Pas de CDN pour assets statiques (Cloudflare only)
- [ ] Pas de caching Redis/Memcached
- [ ] Database: Neon.tech serverless (peut avoir des lags)

---

## 8. TESTS RÉELS EFFECTUÉS

### ✅ Testé et confirmé

| Test | Résultat |
|------|----------|
| API health endpoint | ✅ 200 OK |
| Frontend HTTP | ✅ 200 OK |
| WhatsApp service responsive | ✅ OK (mais se déconnecte) |
| Docker networking | ✅ OK (après recréation) |
| Brevo email API | ✅ OK (alertes envoyées) |
| Monitoring cron job | ✅ OK (5 min interval) |

### ❌ Pas pu tester complètement

| Test | Blocage |
|------|---------|
| Signup → Login → Paiement | Timeout/erreur (nécessite debugging) |
| Korapay callback | TEST MODE (simulation seulement) |
| WhatsApp message flow end-to-end | Service instable |
| Database backup recovery | Pas d'accès psql sur VPS |

---

## 9. SCORE DE VENDABILITÉ DÉTAILLÉ

### Par domaine (0-100%)

| Domaine | Score | Notes |
|---------|-------|-------|
| **Infrastructure** | 85% | Stable mais WhatsApp instable |
| **Authentification** | 80% | JWT OK mais pas testé complètement |
| **Paiements** | 0% | **CRITIQUE: Mode TEST** |
| **WhatsApp/Messaging** | 50% | Marche mais déconnexions |
| **Features/Agents** | 70% | 5 agents, fonctionnels mais limites |
| **Email/Notifications** | 85% | Brevo OK |
| **Analytics** | 60% | Basique, 30 jours |
| **Security** | 75% | JWT, hashing, HMAC OK |
| **Performance** | 80% | Responsive, pas de scaling |
| **Documentation** | 70% | Code + README existants |
| **Monitoring/DevOps** | 85% | Alertes emails + cron |

### **Score global : 35-40%**

---

## 10. ROADMAP POUR LA VENTE

### Phase 1 : CRITIQUE (Jour 1) ⚠️⚠️⚠️

**Doit être fait AVANT de vendre à même UNE entreprise:**

1. [ ] **FIX FRONTEND_URL**
   - Changer `.env` : `FRONTEND_URL=https://neobot-ai.com`
   - Restart containers: `docker-compose restart`
   - Test: Vérifier callback paiement fonctionne

2. [ ] **FIX KORAPAY PRODUCTION**
   - Aller sur dashboard Korapay
   - Passer en mode Production
   - Obtenir clés sk_live_* et pk_live_*
   - Updater `.env`
   - Restart containers
   - Test: Faire un vrai paiement de test

3. [ ] **STABILISER WHATSAPP**
   - Diagnostiquer pourquoi service se déconnecte
   - Vérifier logs: `docker logs neobot_whatsapp | grep -i error`
   - Possibles causes:
     - Baileys version incompatible
     - WhatsApp rejette requests (rate limit)
     - Connexion à Neon.tech timeoute
   - Implémenter reconnexion automatique plus robuste

4. [ ] **TEST COMPLET SIGNUP → PAIEMENT**
   - Créer utilisateur
   - Vérifier email reçu
   - Vérifier liens email marchent
   - Initier paiement
   - Vérifier redirection post-paiement OK
   - Vérifier subscription activée en DB

### Phase 2 : HAUTE (Semaine 1)

5. [ ] **TESTER AGENTS RÉELS**
   - Scanner QR WhatsApp (vrai numéro)
   - Envoyer messages via agent
   - Vérifier réponses IA
   - Tester tous 5 types d'agents

6. [ ] **TESTER ANALYTICS**
   - Vérifier conversations capturées
   - Vérifier graphiques affichés
   - Vérifier exports

7. [ ] **TESTER BROADCAST EMAILS**
   - Admin send message
   - Vérifier arrive dans WhatsApp

### Phase 3 : MOYENNE (Semaine 2)

8. [ ] **SETUP KORAPAY REVERSEMENT (NeoCaisse)**
   - Configurer payout à seller/tenant
   - Tester transmission argent

9. [ ] **DOCUMENTATION CLIENT**
   - Guide d'onboarding
   - FAQ
   - Support email triage

10. [ ] **SLA & Monitoring**
    - Vérifier Sentry configuré
    - Alertes email marchent
    - Backup plan en cas de panne

---

## 11. RECOMMANDATIONS

### À Faire AVANT de vendre

```
Priorité 1 (Jour 1) — Blockers absolus:
  [ ] Fix FRONTEND_URL
  [ ] Fix Korapay Production
  [ ] Stabiliser WhatsApp
  [ ] Test complet user flow signup→paiement

Priorité 2 (Semaine 1) — QA:
  [ ] Test agents réels (WhatsApp)
  [ ] Test emails + reset password
  [ ] Test analytics
  [ ] Load test (100 users simultanés?)

Priorité 3 (Semaine 2) — Production-ready:
  [ ] Korapay reversement (payout)
  [ ] Database backup automatique
  [ ] Sentry monitoring
  [ ] SSL certificate renewal automation
```

### À vendre à première entreprise

```
Conditions:
  ✓ Toutes les Priorité 1 fixes
  ✓ Oui à Priorité 2 QA
  ✓ Plan BASIC uniquement (Standard/Pro gelés)
  ✓ Trial 14 jours gratuit
  ✓ Support par email (pas 24/7)

Pricing:
  Plan BASIC : 20,000 XAF/mois (≈ 50€)
           ou 49,100 NGN/mois
  Billings : Mensuel (pas annual options)
```

---

## 12. CONCLUSION

**Pourcentage de vendabilité actuel : 35-40%**

### Pourquoi c'est pas vendable

1. ❌ **Korapay en TEST MODE** → Aucun paiement réel possible
2. ❌ **FRONTEND_URL mauvais** → Paiements et emails cassés
3. ❌ **WhatsApp instable** → Service se déconnecte régulièrement
4. ❌ **Pas testé end-to-end** → Pas de certitude que signup→paiement marche

### Potentiel à moyen terme

- ✅ Architecture solide
- ✅ 5 types d'agents implémentés
- ✅ Système de paiement conçu (juste pas en production)
- ✅ Infrastructure stable (Docker OK)
- ✅ Monitoring en place

### Effort estimé pour vendre

```
Jour 1  : Fix FRONTEND_URL + Korapay Production (2-3h)
Jour 2  : Diagnostiquer WhatsApp + stabiliser (4-6h)
Jour 3  : Test complet user flow (2-3h)
Jour 4  : QA agents réels + emails (3-4h)
---
Total   : ~15h pour être prêt pour 1ère vente
```

**Si tu fixes les Priorité 1 aujourd'hui → Tu peux vendre demain.**

---

## 13. LOGS & DIAGNOSTICS

### Backend logs (dernière heure)

```
2026-04-17 23:14:47 — WhatsApp service request error for tenant 1: Name or service not known
2026-04-17 23:25:25 — psycopg2.OperationalError: SSL connection has been closed unexpectedly
```

### WhatsApp logs

```
[2026-04-17T23:20:20.570Z] Watchdog recovery triggered { tenantId: 1, state: 'disconnected' }
[2026-04-17T23:20:26.016Z] Disconnect requires auth reset, regenerating QR
```

### Docker status

```
neobot_backend   : healthy ✅
neobot_frontend  : unhealthy ⚠️ (mais HTTP 200 OK)
neobot_whatsapp  : healthy ✅ (mais logs show déconnexions)
```

---

**Rapport généré le 18 avril 2026**
**Audit par T (Coding Partner)**
