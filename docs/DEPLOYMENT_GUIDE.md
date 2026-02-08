# 🚀 NEOBOT DEPLOYMENT GUIDE

**Version:** 1.0.0 Beta  
**Last Updated:** 17 December 2025

---

## 📋 Pre-Deployment Checklist

- [ ] All code committed to git
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] SSL certificates ready (if HTTPS)
- [ ] Domain name configured
- [ ] Email service configured (if needed)
- [ ] Backup strategy in place
- [ ] Monitoring tools configured

---

## 🐳 Option 1: Docker Compose (Recommended)

### Requirements
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 20GB disk space

### Deployment Steps

#### 1. **Prepare the Server**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Verify Docker
docker --version
docker-compose --version
```

#### 2. **Clone & Configure**

```bash
# Clone repository
git clone https://github.com/yourrepo/neobot-mvp.git
cd neobot-mvp

# Copy environment file
cp .env.example .env

# Edit with your settings
nano .env
```

#### 3. **Start Services**

```bash
# Pull latest images
docker-compose pull

# Start in background
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### 4. **Verify Deployment**

```bash
# Test health checks
curl http://localhost:8000/health
curl http://localhost:3001/health

# Test API
curl http://localhost:8000/api/tenants

# Access dashboard
# Open http://localhost:3000 in browser
```

---

## 🖥️ Option 2: Manual Deployment (VPS/Cloud)

### Server Setup

```bash
# 1. Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 2. Install Python
sudo apt install -y python3.10 python3.10-venv python3-pip

# 3. Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# 4. Clone repo
git clone https://github.com/yourrepo/neobot-mvp.git
cd neobot-mvp
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 -c "from app.database import init_db; init_db()"

# Start server (with systemd)
sudo tee /etc/systemd/system/neobot-backend.service << EOF
[Unit]
Description=NéoBot Backend
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable neobot-backend
sudo systemctl start neobot-backend
```

### WhatsApp Service Setup

```bash
cd whatsapp-service

# Install dependencies
npm install

# Start service (with PM2)
sudo npm install -g pm2

pm2 start index.js --name "neobot-whatsapp"
pm2 startup
pm2 save
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build Next.js
npm run build

# Start service (with PM2)
pm2 start "npm run start" --name "neobot-frontend"
```

---

## 🔒 Security Hardening

### 1. Firewall Configuration

```bash
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 5432       # Block PostgreSQL from outside
```

### 2. SSL/HTTPS Setup

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Configure Nginx to reverse proxy
# ... (see Nginx config below)
```

### 3. Environment Variables Security

```bash
# Create .env file with tight permissions
touch .env
chmod 600 .env

# Never commit .env to git
echo ".env" >> .gitignore
```

### 4. Database Security

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create strong password
ALTER USER neobot WITH PASSWORD 'strong_random_password_here';

# Restrict connections
# Edit /etc/postgresql/*/main/postgresql.conf
# Set: listen_addresses = 'localhost'
```

---

## 📊 Nginx Reverse Proxy Configuration

```nginx
# /etc/nginx/sites-available/neobot

upstream backend {
    server 127.0.0.1:8000;
}

upstream whatsapp {
    server 127.0.0.1:3001;
}

upstream frontend {
    server 127.0.0.1:3000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # API Backend
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WhatsApp Service
    location /whatsapp/ {
        proxy_pass http://whatsapp/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

---

## 📈 Monitoring & Logging

### 1. Application Logging

```bash
# Backend logs
journalctl -u neobot-backend -f

# WhatsApp logs
pm2 logs neobot-whatsapp

# Frontend logs
pm2 logs neobot-frontend
```

### 2. System Monitoring

```bash
# Install Prometheus + Grafana
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v /path/to/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

### 3. Error Tracking

```bash
# Option 1: Sentry
# Sign up at sentry.io
# Add to backend:
import sentry_sdk
sentry_sdk.init("https://xxx@xxx.ingest.sentry.io/xxx")

# Option 2: ELK Stack
# Use existing logs infrastructure
```

---

## 💾 Backup Strategy

### Automated Database Backups

```bash
# Create backup script
cat > /home/user/neobot_backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/backups/neobot"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Database backup
docker exec neobot_postgres pg_dump -U neobot neobot_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "✅ Backup completed: $BACKUP_DIR/db_$DATE.sql.gz"
EOF

chmod +x /home/user/neobot_backup.sh

# Schedule with cron (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/user/neobot_backup.sh
```

### Manual Backup

```bash
# Backup database
docker-compose exec postgres pg_dump -U neobot neobot_db > backup.sql

# Backup authentication folder
tar -czf auth_info_baileys_backup.tar.gz auth_info_baileys/

# Backup configuration
tar -czf config_backup.tar.gz .env backend/.env
```

---

## 🔄 Rolling Updates

### Zero-Downtime Deployment

```bash
# 1. Build new images
docker-compose build

# 2. Pull latest code
git pull origin main

# 3. Update services one by one
docker-compose up -d backend
sleep 5
docker-compose up -d whatsapp
sleep 5
docker-compose up -d frontend

# 4. Health check
curl http://localhost:8000/health
curl http://localhost:3001/health

# 5. Monitor logs
docker-compose logs -f
```

---

## 🚨 Rollback Procedure

```bash
# If something goes wrong:

# 1. Check current status
docker-compose ps

# 2. Revert to previous version
git checkout previous-version
docker-compose down

# 3. Restart with previous images
docker-compose up -d

# 4. Restore database backup if needed
cat backup.sql | docker exec -i neobot_postgres psql -U neobot neobot_db
```

---

## 📞 Post-Deployment Tasks

- [ ] Configure email notifications
- [ ] Setup monitoring alerts
- [ ] Create admin user account
- [ ] Test full workflow end-to-end
- [ ] Configure backups
- [ ] Document deployment
- [ ] Train support team
- [ ] Launch beta testing

---

## 🐛 Troubleshooting Deployment

### "Connection refused"
```bash
# Check if services are running
docker-compose ps

# Restart failed service
docker-compose restart backend
```

### "Database not initialized"
```bash
# Manually initialize
docker-compose exec backend python3 -c "from app.database import init_db; init_db()"
```

### "Out of disk space"
```bash
# Clean up old images
docker image prune -a

# Check disk usage
du -sh *
```

### "High memory usage"
```bash
# Check processes
docker stats

# Limit memory
# Edit docker-compose.yml and add:
# mem_limit: 512m
```

---

## 📋 Deployment Checklist

- [ ] Code reviewed and tested
- [ ] Environment variables configured
- [ ] Database initialized
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Backups configured
- [ ] Monitoring enabled
- [ ] Health checks passing
- [ ] Logs accessible
- [ ] Support trained
- [ ] Documentation updated
- [ ] Go live approved

---

**Support:** contact@neobot.io  
**Status Page:** https://status.neobot.io  
**Documentation:** https://docs.neobot.io
