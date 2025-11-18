# 🔐 Gestion des Secrets & API Keys - NéoBot MVP

## 📋 Résumé Exécutif

Ce projet contient des secrets sensibles (API keys, credentials de DB) qui doivent être **masqués et protégés**.

- ✅ Les fichiers `.env` sont dans `.gitignore` (non committés)
- ✅ Les `.env.example` et `.env.production.example` montrent la structure
- ✅ Les clés réelles sont chargées via variables d'environnement
- ✅ Production utilise GitHub Secrets ou un vault

---

## 🔑 Secrets du Projet

| Secret | Usage | Protection | Where |
|--------|-------|-----------|-------|
| `DEEPSEEK_API_KEY` | IA - DeepSeek API | ✅ `.env` masqué | `backend/.env` |
| `DATABASE_URL` | PostgreSQL connection | ✅ `.env` masqué | `backend/.env` |
| `WHATSAPP_SERVICE_URL` | WhatsApp service | ⚠️ Local seulement | `backend/.env` |

---

## 📁 Structure des Fichiers

### Local Development
```
backend/
├── .env                    ← ❌ NE PAS committer (contient vraies clés)
├── .env.example            ← ✅ Safe - montre structure dev
└── .gitignore              ← Exclut .env automatiquement
```

### Production
```
backend/
├── .env.production.example ← ✅ Safe - montre structure prod
└── Secret Management        → GitHub Secrets / Vault
```

---

## 🚀 Utilisation Locale (Development)

### 1️⃣ Créer le fichier `.env` local

```bash
cd backend

# Copier depuis l'exemple
cp .env.example .env

# Éditer avec tes vraies valeurs locales
nano .env
```

### 2️⃣ Contenu du `.env` local

```properties
# Development
DATABASE_URL=postgresql://neobot:password@localhost:5432/neobot
DEEPSEEK_API_KEY=sk-9dcd03b870a741cfa2823f5c0ea96c5f
WHATSAPP_SERVICE_URL=http://localhost:3001
```

### 3️⃣ Lancer l'app

```bash
cd backend

# Option 1: Charger .env automatiquement (FastAPI + dotenv)
uvicorn app.main:app --port 8000

# Option 2: Source manuel
source .env
uvicorn app.main:app --port 8000
```

---

## 🏭 Production (GitHub Actions / Docker)

### 1️⃣ Configurer les Secrets GitHub

Aller à: **Repository Settings > Secrets and variables > Actions**

Ajouter les secrets:
```
DEEPSEEK_API_KEY_PROD = sk-xxxx-xxxx-xxxx
DATABASE_URL_PROD = postgresql://...
```

### 2️⃣ Utiliser dans le Workflow

Fichier: `.github/workflows/deploy.yml`

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Production
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY_PROD }}
          DATABASE_URL: ${{ secrets.DATABASE_URL_PROD }}
        run: |
          # Déployer avec les secrets chargés
          docker build -t neobot:latest .
          docker run -e DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY neobot:latest
```

### 3️⃣ Docker Compose Production

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - ENVIRONMENT=production
    ports:
      - "8000:8000"
```

---

## 🔍 Vérifier que les Secrets Sont Chargés

### Local
```bash
cd backend
python3 -c "import os; print(f'API Key: {os.getenv(\"DEEPSEEK_API_KEY\", \"NOT SET\")}')"

# Output:
# API Key: sk-9dcd03b870a741cfa2823f5c0ea96c5f
```

### Production (GitHub)
```bash
# Dans le workflow, les secrets sont automatiquement chargés
echo $DEEPSEEK_API_KEY  # Affiche: sk-****-****-****
```

---

## ✅ Checklist de Sécurité

- [ ] `.env` n'est pas commité (voir `.gitignore`)
- [ ] `.env.example` montre la structure SANS clés réelles
- [ ] Les variables d'environnement sont chargées via `os.getenv()`
- [ ] Les fallback values sont génériques (`sk-test`, `***REDACTED***`)
- [ ] GitHub Secrets sont configurés pour production
- [ ] Docker images n'ont PAS les secrets hardcodés
- [ ] Les logs ne révèlent PAS les secrets (voir ci-dessous)

### Masquer les Secrets dans les Logs

```python
# ✅ BON: Log sans exposer la clé
api_key = os.getenv('DEEPSEEK_API_KEY')
masked_key = f"{api_key[:5]}...{api_key[-4:]}" if api_key else "NOT_SET"
print(f"Using API Key: {masked_key}")  # Output: sk-9cd...c5f

# ❌ MAUVAIS: Expose la clé complète
print(f"Using API Key: {os.getenv('DEEPSEEK_API_KEY')}")  # DANGER!
```

---

## 🛡️ Bonnes Pratiques

### 1. Ne Jamais Committer de Secrets
```bash
# ❌ MAUVAIS
echo "DEEPSEEK_API_KEY=sk-abcd1234..." >> backend/.env
git add backend/.env
git commit -m "Add API key"  # DANGER!

# ✅ BON
echo "DEEPSEEK_API_KEY=sk-abcd1234..." >> backend/.env
git add backend/.env.example
git commit -m "Update config template"  # OK - .env est ignoré
```

### 2. Rotation des Clés
```bash
# Si une clé est compromisée:
1. La régénérer sur https://platform.deepseek.com/api_keys
2. Mettre à jour GitHub Secrets
3. Relancer les déploiements
4. Vérifier les logs d'utilisation
```

### 3. Utiliser des Variables d'Environnement

```python
# ✅ BON: Chargé depuis l'env
api_key = os.getenv('DEEPSEEK_API_KEY')

# ❌ MAUVAIS: Hardcodé dans le code
api_key = "sk-9dcd03b870a741cfa2823f5c0ea96c5f"
```

### 4. .env Local vs Production

```properties
# .env (local dev - NON commité)
DEEPSEEK_API_KEY=sk-9dcd03b870a741cfa2823f5c0ea96c5f

# .env.example (safe - dans le repo)
DEEPSEEK_API_KEY=sk-test

# GitHub Secret (production)
DEEPSEEK_API_KEY_PROD=sk-xxxx-xxxx-xxxx
```

---

## 🔐 Commandes Utiles

### Vérifier que .env est ignoré
```bash
git status  # .env ne doit PAS apparaître
git check-ignore backend/.env  # Doit afficher: backend/.env
```

### Générer un .env sample
```bash
cd backend
cp .env.example .env
# Éditer les valeurs
nano .env
```

### Tester les imports avec secrets
```bash
cd backend
source .env
python3 -c "from app.main import app; print('✅ App loaded with secrets')"
```

### Masquer les secrets dans les outputs
```bash
# Avant de partager un log:
sed 's/sk-[a-f0-9]*/sk-***MASKED***/g' logfile.txt
```

---

## 📞 Support

- **Question sur les secrets?** → Voir `SETUP_SECRETS.md`
- **Besoin de rotationner une clé?** → Contacter l'admin
- **Suspect une fuite de secret?** → Changer immédiatement le secret et notifier l'équipe

---

## 🎯 Résumé

| Action | Local | Production |
|--------|-------|-----------|
| Stocker clés | `.env` (masqué) | GitHub Secrets |
| Partager config | `.env.example` | `.env.production.example` |
| Charger au runtime | `os.getenv()` | `os.getenv()` |
| Fallback value | `sk-test` | Pas de fallback! |
| Logs | Masquer clés | Logs sécurisés |

**Status: ✅ CONFIGURATION SÉCURISÉE**

_Last Updated: 18 Nov 2025_
