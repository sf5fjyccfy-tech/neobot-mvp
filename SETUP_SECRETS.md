# 🔐 Configuration des Secrets - NéoBot

## ⚠️ Important : Sécurité des clés API

**Les fichiers `.env` ne doivent JAMAIS être committés dans le repository.**

Tous les fichiers `.env` sont ignorés par `.gitignore`. Utilise toujours `backend/.env.example` comme modèle.

## 📋 Setup pour le Développement Local

### Étape 1: Copier le fichier exemple
```bash
cd backend
cp .env.example .env
```

### Étape 2: Remplir les vraies valeurs
Édite `backend/.env` et remplace les placeholders :

```properties
# PostgreSQL (local ou remote)
DATABASE_URL=postgresql://neobot:password@localhost:5432/neobot

# Clé DeepSeek (génère la tienne sur https://platform.deepseek.com/api_keys)
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxx

# Service WhatsApp
WHATSAPP_SERVICE_URL=http://localhost:3001
```

### Étape 3: Lancer l'application
```bash
cd backend
set -o allexport; source .env; set +o allexport
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 🚀 Setup pour la Production

### Optio 1: GitHub Secrets (Recommandé pour CI/CD)
1. Ajoute tes secrets dans GitHub: Settings → Secrets and variables → Actions
2. Dans ton workflow GitHub Actions, expose-les comme variables d'environnement:
   ```yaml
   env:
     DATABASE_URL: ${{ secrets.DATABASE_URL }}
     DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
     WHATSAPP_SERVICE_URL: ${{ secrets.WHATSAPP_SERVICE_URL }}
   ```

### Optio 2: Fichier .env en Runtime (Docker)
```bash
docker run -e DATABASE_URL='...' -e DEEPSEEK_API_KEY='...' neobot:latest
```

### Optio 3: Vault HashiCorp ou AWS Secrets Manager
Pour les déploiements d'entreprise, utilise un gestionnaire de secrets centralisé.

## 🔑 Rotation des Clés

Si une clé a été exposée :

1. **DeepSeek API Key**: 
   - Revoque la clé exposée sur https://platform.deepseek.com/api_keys
   - Génère une nouvelle clé
   - Mets à jour `.env` localement
   - Mets à jour le secret GitHub Actions

2. **DATABASE_URL**:
   - Change le mot de passe PostgreSQL
   - Mets à jour `.env`

## 📝 Vérification

Pour vérifier que les secrets sont bien chargés dans le process uvicorn :
```bash
# Retrouve le PID d'uvicorn
PID=$(pgrep -f "uvicorn app.main:app" | head -n1)

# Vérifie les variables d'environnement
tr "\0" "\n" < /proc/$PID/environ | grep -E "DATABASE_URL|DEEPSEEK_API_KEY"
```

## ❌ Ce qu'il NE FAUT PAS faire

- ❌ Ne commitez JAMAIS `.env` réel
- ❌ Ne partagez JAMAIS les clés API par email, chat, ou forum public
- ❌ Ne laissez JAMAIS les clés en clair dans les logs
- ❌ Ne commitez JAMAIS `auth_info_baileys/` (sessions WhatsApp)

## ✅ Bonnes Pratiques

- ✓ Utilise `.env.example` comme modèle documenté
- ✓ Mets les secrets dans un gestionnaire sécurisé (GitHub Secrets, Vault, etc.)
- ✓ Effectue la rotation régulière des clés
- ✓ Audite les changements de secrets avec `git log --all --full-history -- .env`
