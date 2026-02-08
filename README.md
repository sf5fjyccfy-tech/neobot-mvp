# 🤖 NeobotMVP

Modern WhatsApp chatbot platform with AI integration (DeepSeek API).

**Status:** ✅ Operational | 🐍 Python 3.10+ | 🚀 Docker-ready

# 🤖 NeobotMVP

Plateforme de chatbot WhatsApp moderne avec intégration IA (API DeepSeek).

**Statut:** ✅ Opérationnel | 🐍 Python 3.10+ | 🚀 Prêt pour Docker

---

## 🚀 Démarrage rapide

```bash
# 1. Installer les dépendances
pip install -r backend/requirements.txt

# 2. Démarrer avec Docker
docker-compose up -d

# 3. Attendre 30 secondes pour PostgreSQL
sleep 30

# 4. Tester le backend
curl http://localhost:8000/health
```

---

## 📁 Structure du projet

```
neobot-mvp/
├── backend/              # Application FastAPI
│   ├── app/
│   │   ├── main.py       # Routes et endpoints principaux
│   │   ├── models.py     # Modèles de base de données
│   │   ├── database.py   # Configuration PostgreSQL
│   │   └── whatsapp_webhook.py  # Gestionnaire de messages
│   └── requirements.txt   # Dépendances Python
│
├── frontend/             # Tableau de bord Next.js
├── whatsapp-service/     # Service WhatsApp Node.js
│
├── docs/                 # Documentation
│   ├── QUICK_START.md
│   ├── INSTALLATION.md
│   ├── TROUBLESHOOTING.md
│   └── WHATSAPP_SETUP.md
│
├── scripts/              # Scripts utiles
│   ├── test_fixes.sh
│   └── verify_system.sh
│
├── learning_materials/   # Contenu éducatif
│   ├── MAIN_PY_BEFORE_AFTER_GUIDE.md
│   ├── FIXES_APPLIED_EXPLAINED.md
│   ├── TESTING_SUCCESS_REPORT.md
│   └── SESSION_SUMMARY.md
│
├── archive/              # Fichiers archivés/anciens
└── docker-compose.yml    # Orchestration des services
```

---

## 🛠️ Services

| Service | Port | Langage | Objectif |
|---------|------|---------|----------|
| Backend | 8000 | Python | API REST, traitement des messages |
| Frontend | 3000 | Node.js | Tableau de bord web |
| WhatsApp | 3001 | Node.js | Gestionnaire WebSocket WhatsApp |
| PostgreSQL | 5432 | - | Base de données |

---

## 📚 Documentation

- **Démarrage rapide:** [docs/QUICK_START.md](docs/QUICK_START.md)
- **Installation:** [docs/INSTALLATION.md](docs/INSTALLATION.md)
- **Matériaux pédagogiques:** Voir le répertoire [learning_materials/](learning_materials/)
- **Dépannage:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## 🔧 Tests

```bash
# Exécuter les tests automatisés
cd /home/tim/neobot-mvp
./scripts/test_fixes.sh

# Vérifier le système
./scripts/verify_system.sh
```

---

## 📊 Fonctionnalités clés

✅ Intégration des messages WhatsApp  
✅ Réponses alimentées par l'IA (DeepSeek)  
✅ Support multi-tenant  
✅ Gestion des quotas de messages  
✅ Tableau de bord web  
✅ Base de données PostgreSQL  

---

## 🚢 Déploiement

Configuré pour Render.com avec `render.yaml`:

```bash
# Pusher pour déployer
git push
```

---

## 💾 Base de données

PostgreSQL 12-alpine via Docker Compose

```bash
# Se connecter à la base de données
psql postgresql://neobot:neobot@localhost:5432/neobot_db
```

---

## 🤝 Contribuer

- Branche: `emergency/rotate-secrets`
- PR vers: `main`
- Révision: Tester localement d'abord

---

## 📞 Support

1. Consultez [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Examinez [learning_materials/](learning_materials/) pour les explications du code
3. Exécutez `./scripts/test_fixes.sh` pour valider

---

**Dernière mise à jour:** Février 2026  
**Version:** MVP  
**Python:** 3.10+


## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r backend/requirements.txt

# 2. Start with Docker
docker-compose up -d

# 3. Wait 30 seconds for PostgreSQL
sleep 30

# 4. Test the backend
curl http://localhost:8000/health
```

---

## 📁 Project Structure

```
neobot-mvp/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── main.py       # Main routes & endpoints
│   │   ├── models.py     # Database models
│   │   ├── database.py   # PostgreSQL config
│   │   └── whatsapp_webhook.py  # Message handler
│   └── requirements.txt   # Python dependencies
│
├── frontend/             # Next.js dashboard
├── whatsapp-service/     # Node.js WhatsApp service
│
├── docs/                 # Documentation
│   ├── QUICK_START.md
│   ├── INSTALLATION.md
│   ├── TROUBLESHOOTING.md
│   └── WHATSAPP_SETUP.md
│
├── scripts/              # Useful scripts
│   ├── test_fixes.sh
│   └── verify_system.sh
│
├── learning_materials/   # Educational content
│   ├── MAIN_PY_BEFORE_AFTER_GUIDE.md
│   ├── FIXES_APPLIED_EXPLAINED.md
│   ├── TESTING_SUCCESS_REPORT.md
│   └── SESSION_SUMMARY.md
│
├── archive/              # Archived/old files
└── docker-compose.yml    # Service orchestration
```

---

## 🛠️ Services

| Service | Port | Language | Purpose |
|---------|------|----------|---------|
| Backend | 8000 | Python | REST API, message processing |
| Frontend | 3000 | Node.js | Web dashboard |
| WhatsApp | 3001 | Node.js | WhatsApp WebSocket handler |
| PostgreSQL | 5432 | - | Database |

---

## 📚 Documentation

- **Quick Start:** [docs/QUICK_START.md](docs/QUICK_START.md)
- **Installation:** [docs/INSTALLATION.md](docs/INSTALLATION.md)
- **Learning Materials:** See [learning_materials/](learning_materials/) directory
- **Troubleshooting:** [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## 🔧 Testing

```bash
# Run automated tests
cd /home/tim/neobot-mvp
./scripts/test_fixes.sh

# Verify system
./scripts/verify_system.sh
```

---

## 📊 Key Features

✅ WhatsApp message integration  
✅ AI-powered responses (DeepSeek)  
✅ Multi-tenant support  
✅ Message quota management  
✅ Web dashboard  
✅ PostgreSQL database  

---

## 🚢 Deployment

Configured for Render.com with `render.yaml`:

```bash
# Push to deploy
git push
```

---

## 💾 Database

PostgreSQL 12-alpine via Docker Compose

```bash
# Connect to database
psql postgresql://neobot:neobot@localhost:5432/neobot_db
```

---

## 🤝 Contributing

- Branch: `emergency/rotate-secrets`
- PR to: `main`
- Review: Test locally first

---

## 📞 Support

1. Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Review [learning_materials/](learning_materials/) for code explanations
3. Run `./scripts/test_fixes.sh` to validate

---

**Last Updated:** February 2026  
**Version:** MVP  
**Python:** 3.10+
