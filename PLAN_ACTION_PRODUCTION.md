# 🛠️ PLAN D'ACTION IMMÉDIAT - NÉOBOT

**Créé:** 10 Février 2026  
**Priorité:** CRITIQUE → IMPORTANTE → À FAIRE  
**Objectif:** Préparer le système pour production en 2-3 semaines

---

## 🚨 PROBLÈMES CRITIQUES À RÉSOUDRE

### 1. 🔴 **SÉCURITÉ: Secrets en clair dans .env**

**Status:** ❌ DANGEREUX  
**Risque:** Accès non-autorisé à votre API et base de données

**Affecte:**
```
backend/.env:
  - DEEPSEEK_API_KEY (clé API 50$+/mois d'usage frauduleux possible)
  - DATABASE_URL=postgresql://neobot:neobot_secure_password@...
  - JWT_SECRET=neobot_jwt_secret_change_in_production

whatsapp-service/.env:
  - WHATSAPP_BACKEND_URL exposée
  - Pas de protection
```

**À FAIRE - 30 minutes:**

```bash
# 1. Créer .env.example (sans secrets)
cp backend/.env backend/.env.example
# Remplacer valeurs réelles par placeholders

# 2. Ajouter .env à .gitignore
echo ".env" >> /home/tim/neobot-mvp/.gitignore
echo ".env.local" >> /home/tim/neobot-mvp/.gitignore

# 3. Vérifier que .env n'est PAS commité
git status | grep ".env"  # Ne doit rien afficher

# 4. Stocker secrets dans variables système
# Export avant de lancer les services:
export DEEPSEEK_API_KEY="sk-xxxx..."
export DATABASE_URL="postgresql://..."
export JWT_SECRET="changé-en-production"
```

**En Production:**
```bash
# Option 1: AWS Systems Manager Parameter Store
aws ssm get-parameter --name /neobot/deepseek-key

# Option 2: Vault d'HashiCorp
vault kv get secret/neobot/deepseek

# Option 3: Docker secrets (Swarm)
docker secret create neobot_api_key -

# Option 4: Variables d'environnement du système
# Dans /etc/environment ou systemd service file
```

**Vérification:**
```bash
# Vérifier que secrets ne sont pas en git:
git log --all --full-history -- backend/.env | head
# Résultat ne doit rien afficher (ou montrer suppression)
```

---

### 2. 🔴 **DEBUG MODE en Production**

**Status:** ❌ ACTIVÉ INUTILEMENT  
**Impact:** Expose les sql queries et stack traces

**Fichier:** `backend/.env`

```env
# ❌ ACTUELLEMENT:
BACKEND_DEBUG=true         # Expose les erreurs complètes
DEBUG_MODE=true            # Affiche TOUTES les SQL queries
LOG_LEVEL=DEBUG            # Trop verbeux
BACKEND_ENV=development    # Mode dev

# ✅ À CHANGER EN:
BACKEND_DEBUG=false        # Cache les erreurs détaillées
DEBUG_MODE=false           # Ne pas afficher SQL
LOG_LEVEL=INFO             # Moins verbeux
BACKEND_ENV=production     # Mode production
```

**À FAIRE - 5 minutes:**

```bash
# Créer fichier .env.production
cat > /tmp/.env.production << 'EOF'
# Production Settings
BACKEND_DEBUG=false
DEBUG_MODE=false
LOG_LEVEL=INFO
BACKEND_ENV=production

# Garder les autres configs identiques
DATABASE_URL=postgresql://neobot:${DB_PASSWORD}@localhost:5432/neobot_db
DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
# etc...
EOF

# Tester configuration:
export BACKEND_DEBUG=false
export DEBUG_MODE=false
# Lancer le service et vérifier pas de debug output
```

---

### 3. 🟠 **Code dupliqué - À nettoyer**

**Status:** ⚠️ Mauvaise hygiène

**Fichiers à supprimer:**
```bash
# Dans backend/app/:
rm -f /home/tim/neobot-mvp/backend/app/whatsapp_webhook_clean_commented.py
rm -f /home/tim/neobot-mvp/backend/app/database_clean_commented.py
rm -f /home/tim/neobot-mvp/backend/app/main_clean_commented.py
rm -f /home/tim/neobot-mvp/backend/app/services/auth_service_fixed.py
rm -f /home/tim/neobot-mvp/backend/app/services/auth_service_old.py

# Vérifier ce qui reste:
ls -la /home/tim/neobot-mvp/backend/app/*.py | wc -l  # Doit être <40 fichiers
```

**À FAIRE - 5 minutes:**

```bash
# Sauvegarder backup avant:
tar -czf /tmp/backend_backup.tar.gz /home/tim/neobot-mvp/backend/

# Supprimer les doublons:
find /home/tim/neobot-mvp/backend -name "*_clean_commented.py" -delete
find /home/tim/neobot-mvp/backend -name "*_fixed.py" -delete
find /home/tim/neobot-mvp/backend -name "*_old.py" -delete

# Vérifier git:
cd /home/tim/neobot-mvp
git status  # Doit montrer les fichiers supprimés
git add -A
git commit -m "Clean: remove duplicate and commented files"
```

---

### 4. 🟠 **TODOs à finaliser - Message quotas**

**Status:** ⚠️ Non-critique mais important

**Fichiers:** `backend/app/whatsapp_webhook.py`

**Problème:** Les limites de messages par jour/mois ne sont pas vérifiées

**À FAIRE - 2 heures:**

```python
# Dans whatsapp_webhook.py, fonction handle_message():

# ❌ ACTUELLEMENT: Pas de vérification
# ✅ À AJOUTER:

def check_message_limit(tenant_id: int, db: Session):
    """Vérifier si le client a dépassé ses limites"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    
    if not tenant:
        raise ValueError(f"Tenant {tenant_id} not found")
    
    # Check 1: Limite mensuelle
    if tenant.messages_used >= tenant.messages_limit:
        raise HTTPException(
            status_code=402,  # Payment Required
            detail=f"Quota dépassé: {tenant.messages_used}/{tenant.messages_limit}"
        )
    
    # Check 2: Limite quotidienne (optionnel)
    today = datetime.now().date()
    today_messages = db.query(Message).filter(
        Message.created_at >= datetime.combine(today, time.min),
        Message.conversation.has(Conversation.tenant_id == tenant_id)
    ).count()
    
    daily_limit = tenant.messages_limit // 30  # Répartir sur 30 jours
    if today_messages >= daily_limit:
        logger.warning(f"Daily quota approaching for tenant {tenant_id}")
    
    return True

# À appeler dans handle_message():
check_message_limit(tenant_id, db)  # Avant d'appeler l'IA
```

---

## ⚠️ PROBLÈMES IMPORTANTS

### 5. **Rate Limiting absent**

**Status:** ⚠️ À AJOUTER

**Risque:** Quelqu'un peut envoyer 10,000 messages/seconde et vous ruiner

**À FAIRE - 45 minutes:**

```bash
# 1. Installer SlowAPI
cd /home/tim/neobot-mvp/backend
pip install slowapi

# 2. Ajouter au main.py:

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# 3. Appliquer sur les endpoints sensibles:

@app.post("/api/whatsapp/message")
@limiter.limit("100/minute")  # Max 100 messages par minute par IP
async def whatsapp_message(request: Request, ...):
    # endpoint logic
    pass

@app.get("/api/health")
@limiter.limit("1000/minute")  # Health checks peuvent être plus fréquent
async def health():
    pass
```

---

### 6. **Monitoring absent**

**Status:** ⚠️ À CONFIGURER

**Risque:** Vous ne saurez pas quand le système tombe en panne

**À FAIRE - 2-3 heures:**

```bash
# 1. Installer Sentry pour les erreurs
pip install sentry-sdk

# 2. Configurer dans main.py:

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your_sentry_key@sentry.io/project_id",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,  # Sampler 10% des requêtes
    environment="production"
)

# 3. Vous recevrez des emails pour chaque erreur
# 4. Dashboard sur https://sentry.io pour voir toutes les erreurs
```

**Alternative gratuit:** Sentry gratuit offre 5,000 erreurs/mois

---

### 7. **CORS trop ouvert**

**Status:** ⚠️ À restreindre

**Actuellement:**
```python
CORSMiddleware(...,
    allow_origins=["*"],  # ⚠️ N'importe qui peut appeler votre API
)
```

**À FAIRE - 5 minutes:**

```python
# ✅ À CHANGER EN:
CORSMiddleware(
    app,
    allow_origins=[
        "https://app.votre-domaine.com",
        "https://votre-domaine.com",
        "http://localhost:3000",  # Dev seulement
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)
```

---

## 🟢 À FAIRE - MOINS URGENT

### 8. **Backup PostgreSQL**

```bash
# Scriptcron quotidien:
0 2 * * * /home/tim/backup_neobot.sh

# Fichier /home/tim/backup_neobot.sh:

#!/bin/bash
BACKUP_DIR="/backups/neobot"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="neobot_db_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

pg_dump -U neobot -h localhost neobot_db | \
  gzip > "$BACKUP_DIR/$FILENAME"

# Conserver seulement 30 jours
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

# Copier vers AWS S3 (si disponible)
aws s3 cp "$BACKUP_DIR/$FILENAME" s3://votre-bucket/neobot-backups/

echo "Backup créé: $FILENAME"
```

---

### 9. **Dashboard Frontend**

**Status:** ⚠️ Non fonctionnel pour le moment

**À FAIRE:** Vérifier communication Frontend ↔ Backend

```bash
# 1. Vérifier que Frontend appelle le bon backend:
grep -r "http://localhost:8000" /home/tim/neobot-mvp/frontend/

# 2. Configuration API Frontend
# NEXT_PUBLIC_API_URL doit pointer vers votre backend
```

---

## 📋 CHECKLIST FINALE

### Avant de déployer en production:

```
SÉCURITÉ:
  ☐ .env.example créé (sans secrets)
  ☐ .env ajouté à .gitignore
  ☐ DEBUG_MODE=false
  ☐ BACKEND_DEBUG=false
  ☐ CORS restreint
  ☐ JWT_SECRET changé
  ☐ Rate limiting ajouté
  ☐ Passwords postgre forts

CODE:
  ☐ Code dupliqué supprimé
  ☐ TODOs finalisés (quotas)
  ☐ Aucune erreur ci-dessus
  ☐ Tests locaux OK
  ☐ Tests avec 100+ messages OK

INFRASTRUCTURE:
  ☐ Monitoring (Sentry) configuré
  ☐ Backups PostgreSQL en place
  ☐ SSL/HTTPS certificats prêts
  ☐ Domaine configuré
  ☐ Load balancer prêt (optional)

DOCUMENTATION:
  ☐ README.md à jour
  ☐ API docs (Swagger) accèssible
  ☐ Runbooks pour incidents
  ☐ Contact support défini
```

---

## ⏱️ CHRONOLOGIE PROPOSÉE

### **Semaine 1** (Cette semaine)
- [ ] Jour 1: Sécuriser les secrets (1h)
- [ ] Jour 2: Désactiver debug mode (30min)
- [ ] Jour 3: Nettoyer code dupliqué (1h)
- [ ] Jour 4-5: Ajouter rate limiting (2h)

### **Semaine 2**
- [ ] Configurer monitoring Sentry (2h)
- [ ] Implémenter quotas messages (3h)
- [ ] Tests charge 1000 messages (4h)
- [ ] Configurer backups DB (2h)

### **Semaine 3**
- [ ] Déployer version test (4h)
- [ ] Tests failover et recovery (4h)
- [ ] Documentation production (2h)
- [ ] Onboarding 1er client pilot (8h)

---

## 💡 RÉSUMÉ

**L'audit montre:**
- ✅ **95% du système marche**
- ✅ **Fonctionnalité core prête**
- ❌ **Mais sécurité à revoir**
- ❌ **Monitoring absent**

**Actions urgentes (48h):**
1. Sécuriser secrets (.env)
2. Désactiver DEBUG
3. Nettoyer code

**Après, vous pouvez:**
1. Déployer MVP (3-5 clients)
2. Collecter feedback
3. Scale progressivement

**Budget temps avant prod:** 20-30 heures de travail

---

**Document créé:** 10/02/2026 18:00 UTC

