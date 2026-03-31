# Migration NéoBot — Render + Cloudflare → Oracle Free Tier

> **À exécuter à partir de 10 clients payants.** Oracle Free Tier offre 2 OCPU + 24 GB RAM ARM, disque persistent, sans limite de temps.

---

## Versions exactes (à vérifier le jour J avec `python --version`, `node --version`)

| Composant | Version actuelle | Vérifier avec |
|-----------|-----------------|---------------|
| Python | 3.11+ | `python3 --version` |
| Node.js | 20+ | `node --version` |
| PostgreSQL (Neon) | 16 | Neon dashboard |
| npm | 10+ | `npm --version` |

---

## Architecture cible Oracle

```
Internet
   │
   ▼
Cloudflare (DNS proxy + CDN)
   │
   ├── neobot.app          → Oracle VM (frontend Next.js, port 3002 → Nginx → 443)
   ├── api.neobot.app      → Oracle VM (backend FastAPI, port 8000 → Nginx → 443)
   └── wa.neobot.app       → Oracle VM (service WhatsApp, port 3001 → Nginx → 443)

Oracle VM ARM (1 instance Free Tier — 4 OCPU 24 GB)
   ├── neobot-backend  (uvicorn, systemd service)
   ├── neobot-whatsapp (node, systemd service)
   ├── neobot-frontend (next start, systemd service)
   └── Nginx (reverse proxy + SSL Certbot)

Base de données : Neon PostgreSQL (rester sur Neon — Oracle DB Free Tier est Oracle SQL, incompatible)
```

---

## Variables d'environnement par service

### Backend FastAPI (`/etc/neobot/backend.env`)

```env
APP_ENV=production
DATABASE_URL=postgresql://neondb_owner:PASSWORD@ep-xxx.eu-west-2.aws.neon.tech/neondb?sslmode=require
JWT_SECRET=<générer avec: openssl rand -hex 32>
KORAPAY_SECRET_KEY=sk_live_...
KORAPAY_PUBLIC_KEY=pk_live_...
KORAPAY_WEBHOOK_SECRET=<générer avec: openssl rand -hex 32>
KORAPAY_ENCRYPTION_KEY=<clé live Korapay>
BREVO_API_KEY=xkeysib-...
BREVO_SENDER_EMAIL=contact@neobot-ai.com
BREVO_TPL_WELCOME=1
BREVO_TPL_PAYMENT=2
BREVO_TPL_EXPIRY=3
BREVO_TPL_INACTIVITY=4
SENTRY_DSN=https://...@o4511077033377792.ingest.de.sentry.io/...
DEEPSEEK_API_KEY=sk-...
FRONTEND_URL=https://neobot.app
ALLOWED_ORIGINS=https://neobot.app,https://www.neobot.app
INTERNAL_API_KEY=<générer avec: openssl rand -hex 32>
NEOPAY_ALERT_EMAIL=neobot561@gmail.com
WHATSAPP_SERVICE_URL=http://localhost:3001
WHATSAPP_WEBHOOK_SECRET=<même que Korapay webhook ou générer>
ADMIN_WHATSAPP=+237694256267
SUPERADMIN_EMAILS=timpatrick561@gmail.com
```

### Service WhatsApp Node.js (`/etc/neobot/whatsapp.env`)

```env
NODE_ENV=production
DATABASE_URL=<même URL Neon>
SENTRY_DSN=<DSN projet whatsapp sur sentry.io>
WHATSAPP_BACKEND_URL=http://localhost:8000
WHATSAPP_WEBHOOK_SECRET=<même que backend>
INTERNAL_API_KEY=<même que backend>
PORT=3001
```

### Frontend Next.js (`/etc/neobot/frontend.env`)

```env
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api.neobot.app
NEXT_PUBLIC_SENTRY_DSN=<DSN projet frontend sur sentry.io>
PORT=3002
```

---

## Procédure de migration (étape par étape)

### Étape 1 — Préparer l'instance Oracle

```bash
# Connexion SSH
ssh -i ~/.ssh/oracle_key ubuntu@<IP_ORACLE>

# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installer Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Installer Python 3.11 + venv
sudo apt install -y python3.11 python3.11-venv python3-pip

# Installer Nginx + Certbot
sudo apt install -y nginx certbot python3-certbot-nginx

# Installer Git
sudo apt install -y git
```

### Étape 2 — Cloner et configurer le projet

```bash
# Cloner le repo
git clone https://github.com/sf5fjyccfy-tech/neobot-mvp.git /opt/neobot
cd /opt/neobot

# Backend
cd backend
python3.11 -m venv /opt/neobot/.venv
source /opt/neobot/.venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run build

# WhatsApp service
cd ../whatsapp-service
npm install
```

### Étape 3 — Configurer les fichiers d'environnement

```bash
sudo mkdir -p /etc/neobot
sudo nano /etc/neobot/backend.env    # Coller les variables backend
sudo nano /etc/neobot/whatsapp.env   # Coller les variables WhatsApp
sudo nano /etc/neobot/frontend.env   # Coller les variables frontend
sudo chmod 600 /etc/neobot/*.env
```

### Étape 4 — Créer les services systemd

**Backend** : `/etc/systemd/system/neobot-backend.service`
```ini
[Unit]
Description=NéoBot Backend FastAPI
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/neobot/backend
EnvironmentFile=/etc/neobot/backend.env
ExecStart=/opt/neobot/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Service WhatsApp** : `/etc/systemd/system/neobot-whatsapp.service`
```ini
[Unit]
Description=NéoBot WhatsApp Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/neobot/whatsapp-service
EnvironmentFile=/etc/neobot/whatsapp.env
ExecStart=/usr/bin/node --import ./instrument.js whatsapp-production.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Frontend** : `/etc/systemd/system/neobot-frontend.service`
```ini
[Unit]
Description=NéoBot Frontend Next.js
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/opt/neobot/frontend
EnvironmentFile=/etc/neobot/frontend.env
ExecStart=/usr/bin/npx next start -p 3002
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# Activer et démarrer les services
sudo systemctl daemon-reload
sudo systemctl enable neobot-backend neobot-whatsapp neobot-frontend
sudo systemctl start neobot-backend neobot-whatsapp neobot-frontend

# Vérifier les statuts
sudo systemctl status neobot-backend
sudo systemctl status neobot-whatsapp
sudo systemctl status neobot-frontend
```

### Étape 5 — Configurer Nginx

```nginx
# /etc/nginx/sites-available/neobot
server {
    server_name api.neobot.app;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    server_name wa.neobot.app;
    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    server_name neobot.app www.neobot.app;
    location / {
        proxy_pass http://127.0.0.1:3002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/neobot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# SSL via Certbot
sudo certbot --nginx -d neobot.app -d www.neobot.app -d api.neobot.app -d wa.neobot.app
```

### Étape 6 — Basculer le DNS Cloudflare

Dans Cloudflare dashboard → DNS :

| Type | Nom | Contenu | Proxy |
|------|-----|---------|-------|
| A | neobot.app | `<IP_ORACLE>` | ☁️ Oui |
| CNAME | www | neobot.app | ☁️ Oui |
| A | api | `<IP_ORACLE>` | ☁️ Oui |
| A | wa | `<IP_ORACLE>` | ☁️ Oui |

Attendre 2-5 minutes pour la propagation DNS.

### Étape 7 — Mettre à jour les variables d'environnement

Sur le backend Oracle, mettre à jour `/etc/neobot/backend.env` :
```env
WHATSAPP_SERVICE_URL=https://wa.neobot.app
FRONTEND_URL=https://neobot.app
ALLOWED_ORIGINS=https://neobot.app,https://www.neobot.app
BACKEND_URL=https://api.neobot.app
```

Sur le service WhatsApp :
```env
WHATSAPP_BACKEND_URL=https://api.neobot.app
```

```bash
sudo systemctl restart neobot-backend neobot-whatsapp neobot-frontend
```

---

## Checklist de validation le jour J

- [ ] `curl https://api.neobot.app/health` → `{"status":"healthy"}`
- [ ] `curl https://wa.neobot.app/health` → `{"status":"ok"}`  
- [ ] Frontend accessible sur `https://neobot.app`
- [ ] Login fonctionne, dashboard charge
- [ ] Webhook Korapay reçoit sur `https://api.neobot.app/api/neopay/webhooks/korapay`
- [ ] Sentry reçoit des événements des 3 projets
- [ ] UptimeRobot mis à jour avec les nouvelles URLs Oracle
- [ ] Anciens services Render mis hors ligne (éviter double facturation DNS)
- [ ] Session WhatsApp reconnectée (scan QR si nécessaire — auth migre pas de Neon à serveur local)

---

## Notes importantes

- **Base de données** : rester sur Neon PostgreSQL. Oracle DB Free Tier utilise Oracle SQL (incompatible avec SQLAlchemy PostgreSQL).
- **Session WhatsApp** : sur Oracle, l'auth Baileys sera dans PostgreSQL (Neon) via `pg-auth-state.js` — identique à Render.
- **UptimeRobot** : plus nécessaire sur Oracle (le serveur tourne 24/7 sans sleep). Utile uniquement pour les alertes de disponibilité.
- **Coût résiduel** : Neon free tier (512 MB PostgreSQL), Cloudflare free, Oracle free. Coût = 0€ jusqu'aux limites de stockage Neon.
