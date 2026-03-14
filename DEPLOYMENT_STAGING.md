# 📦 GUIDE DE DÉPLOIEMENT STAGING - NeoBOT

Ce guide explique comment déployer NeoBOT sur l'environnement STAGING.

## 🎯 Objectifs du staging
- Test tous les services dans un environnement proche de production
- Validation des migrations de base de données
- Test multi-tenant en conditions réelles
- Vérification performance + stabilité
- Tests de charge et d'intégration

---

## 📋 PHASE 1: PRÉPARATION ENVIRONNEMENT

### 1.1 Serveur staging requis
```bash
# Configuration minimale:
- CPU: 2 cores
- RAM: 4GB
- Stockage: 20GB
- OS: Ubuntu 20.04 LTS
- Ports: 8000 (backend), 3000 (frontend), 5432 (postgres), 3001 (whatsapp)
```

### 1.2 Installation dépendances système
```bash
# SSH sur serveur staging
ssh user@staging.example.com

# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installer dépendances
sudo apt install -y \
  python3.10 \
  python3-pip \
  postgresql \
  postgresql-contrib \
  nodejs \
  npm \
  curl \
  git \
  build-essential

# Vérifier versions
python3 --version  # doit être 3.10+
node --version     # doit être 16+
```

---

## 🗄️ PHASE 2: CONFIGURATION BASE DE DONNÉES

### 2.1 Créer base de données staging
```bash
# Se connecter à PostgreSQL
sudo -u postgres psql

# Créer BD et utilisateur
CREATE DATABASE neobot_staging;
CREATE USER neobot_staging WITH PASSWORD 'staging_password_change_me';

# Permissions
ALTER ROLE neobot_staging SET client_encoding TO 'utf8';
ALTER ROLE neobot_staging SET default_transaction_isolation TO 'read committed';
ALTER ROLE neobot_staging SET default_transaction_deferrable TO on;
ALTER ROLE neobot_staging SET default_time_zone TO 'UTC';

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE neobot_staging TO neobot_staging;

# Quitter
\q
```

### 2.2 Configurer fichier .env backend
```bash
# Créer .env
cat > backend/.env << 'EOF'
# Base de données
DATABASE_URL=postgresql://neobot_staging:staging_password_change_me@localhost/neobot_staging

# API Keys
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_KEY=your_openai_key

# JWT
SECRET_KEY=your_staging_secret_key_min_32_chars

# Environment
ENVIRONMENT=staging
DEBUG=False

# Frontend URL
FRONTEND_URL=https://app-staging.example.com

# Baileys WhatsApp
BAILEYS_SESSION_DIR=/home/user/neobot-sessions

# Logging
LOG_LEVEL=INFO
EOF

chmod 600 backend/.env
```

### 2.3 Exécuter migrations
```bash
cd backend

# Installer dépendances Python
pip install -r requirements.txt

# Exécuter migrations Alembic
alembic upgrade head

# Vérifier tables créées
python << 'EOF'
from app.database import engine, Base
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print("✅ Tables créées:", tables)
EOF
```

---

## 🚀 PHASE 3: CONFIGURATION FRONTEND

### 3.1 Cloner et installer frontend
```bash
cd /home/user/neobot-mvp/frontend

# Installer dépendances
npm install

# Créer .env.local
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=https://api-staging.example.com
NEXT_PUBLIC_ENV=staging
EOF
```

### 3.2 Build frontend
```bash
# Build production
npm run build

# Vérifier fichiers .next créés
ls -la .next/
```

---

## 🔧 PHASE 4: CONFIGURATION SERVICES

### 4.1 Créer systemd services

**Backend service (/etc/systemd/system/neobot-backend.service):**
```ini
[Unit]
Description=NeoBOT Backend
After=postgresql.service

[Service]
Type=notify
User=neobot
WorkingDirectory=/home/neobot/neobot-mvp/backend
Environment="PATH=/home/neobot/.venv/bin"
ExecStart=/home/neobot/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Frontend service (/etc/systemd/system/neobot-frontend.service):**
```ini
[Unit]
Description=NeoBOT Frontend
After=neobot-backend.service

[Service]
Type=simple
User=neobot
WorkingDirectory=/home/neobot/neobot-mvp/frontend
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm start
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**WhatsApp Service (/etc/systemd/system/neobot-whatsapp.service):**
```ini
[Unit]
Description=NeoBOT WhatsApp Service
After=neobot-backend.service

[Service]
Type=simple
User=neobot
WorkingDirectory=/home/neobot/neobot-mvp/whatsapp-service
ExecStart=/usr/bin/node index.js
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4.2 Enregistrer et démarrer services
```bash
# Recharger systemd
sudo systemctl daemon-reload

# Démarrer services
sudo systemctl start neobot-backend
sudo systemctl start neobot-frontend
sudo systemctl start neobot-whatsapp

# Activer au démarrage
sudo systemctl enable neobot-backend neobot-frontend neobot-whatsapp

# Vérifier statuts
sudo systemctl status neobot-backend
sudo systemctl status neobot-frontend
sudo systemctl status neobot-whatsapp
```

---

## ✅ PHASE 5: TESTS DE SANTÉ

### 5.1 Tester backend
```bash
# Vérifier health endpoint
curl http://localhost:8000/health | jq '.'

# Devrait retourner:
# {
#   "status": "ok",
#   "version": "1.0.0"
# }
```

### 5.2 Tester frontend
```bash
# Vérifier page d'accueil
curl -I http://localhost:3000

# Devrait retourner 200
```

### 5.3 Tests intégration
```bash
cd backend

# Exécuter suite de tests
bash ../run_tests.sh

# Tous les tests doivent passer ✅
```

### 5.4 Test endpoints critiques
```bash
# 1. Inscription
curl -X POST http://api-staging.example.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "TestPass123!",
    "tenant_name": "Test Biz"
  }'

# 2. Vérifier usage tracking
curl http://api-staging.example.com/api/tenants/1/usage

# 3. Vérifier analytics
curl http://api-staging.example.com/api/tenants/1/analytics/dashboard
```

---

## 📊 PHASE 6: MONITORING

### 6.1 Logs
```bash
# Backend
sudo journalctl -u neobot-backend -f

# Frontend  
sudo journalctl -u neobot-frontend -f

# WhatsApp
sudo journalctl -u neobot-whatsapp -f
```

### 6.2 Métriques
```bash
# Utilisation ressources
htop

# Connexions DB
ps aux | grep postgres

# Ports en écoute
netstat -tlnp | grep -E ':(8000|3000|3001|5432)'
```

---

## 🔐 PHASE 7: SÉCURITÉ STAGING

### 7.1 Firewall
```bash
# Autoriser seulement ports essentiels
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw allow 5432/tcp # PostgreSQL (local seulement)
```

### 7.2 HTTPS avec Let's Encrypt
```bash
# Installer certbot
sudo apt install certbot python3-certbot-nginx

# Créer certificat
sudo certbot certonly --standalone -d api-staging.example.com
sudo certbot certonly --standalone -d app-staging.example.com
```

### 7.3 Variables sensibles
```bash
# Vérifier que .env est NOT en git
grep -r "DATABASE_URL" .git/

# Devrait retourner rien
# Sinon: git rm --cached backend/.env
```

---

## 📝 CHECKLIST DÉPLOIEMENT

- [ ] Serveur préparé (2 CPU, 4GB RAM)
- [ ] PostgreSQL installé et configuré
- [ ] Base neobot_staging créée
- [ ] Backend .env configuré
- [ ] Frontend .env.local configuré
- [ ] Migrations exécutées avec succès
- [ ] Services systemd créés et démarrés
- [ ] Health check backend ✅
- [ ] Frontend accessible
- [ ] Tests intégration passent
- [ ] Logs monitoring en place
- [ ] HTTPS/SSL configuré
- [ ] Firewall configuré
- [ ] Backups DB automatiques en place

---

## 🚨 TROUBLESHOOTING

### Erreur: "connection refused"
```bash
# Vérifier que PostgreSQL tourne
sudo systemctl status postgresql

# Redémarrer si nécessaire
sudo systemctl restart postgresql
```

### Erreur: "port already in use"
```bash
# Trouver process sur le port
lsof -i :8000

# Tuer le process
kill -9 <PID>
```

### Erreur: "migration failed"
```bash
# Vérifier DATABASE_URL
echo $DATABASE_URL

# Réessayer migration avec logs
alembic upgrade head --sql
```

### WhatsApp "connection timeout"
```bash
# Vérifier que le service est en haut
systemctl status neobot-whatsapp

# Vérifier logs
journalctl -u neobot-whatsapp -n 50
```

---

## 📧 Support

Pour questions sur le déploiement:
1. Vérifier les logs: `journalctl -u neobot-* -f`
2. Consulter TROUBLESHOOTING ci-dessus
3. Contacter: support@neobot.app

---

**Version**: 1.0.0  
**Date**: Février 2026  
**Maintenu par**: NeoBOT Team
