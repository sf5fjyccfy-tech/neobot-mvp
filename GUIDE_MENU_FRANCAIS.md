# 🎮 GUIDE COMPLET - COMMENT UTILISER LE MENU MASTER_COMMANDS.SH

> Un guide pas-à-pas pour utiliser le script interactif

---

## ⚡ Démarrage rapide

```bash
cd /home/tim/neobot-mvp
./scripts/MASTER_COMMANDS.sh
```

Voilà! Tu vois le menu interactif avec 12 options.

---

## 📋 Les 12 Options Expliquées

### 🔹 Option 1: Vérifier l'état du système
**Commande:** `1`

**Qu'est-ce que ça fait:**
- Affiche la version de Python installée
- Affiche la version de Node.js installée
- Affiche la version de Docker
- Vérifie quels ports sont utilisés (8000, 3001, 5432)
- Affiche les dépendances Python installées
- Affiche les packages npm installés

**Quand l'utiliser:**
- Au démarrage pour vérifier que tout est prêt
- Si tu as des doutes sur les versions installées

**Exemple de résultat:**
```
Python 3.10.12
Node.js v24.2.0
npm 11.3.0
Docker version 4.x.x
```

---

### 🔹 Option 2: Diagnostic complet
**Commande:** `2`

**Qu'est-ce que ça fait:**
- Lance un test complet de 8 phases
- Teste les imports Python
- Teste les dépendances Python
- Teste les variables d'environnement (.env)
- Teste Node.js
- Teste les routes FastAPI
- Teste la configuration de la base de données
- Teste la configuration Docker

**Quand l'utiliser:**
- Si le système ne fonctionne pas
- Pour identifier exactement où est le problème
- Avant de commencer les services

**Exemple de résultat:**
```
✅ database.py imports OK
✅ psycopg2-binary présent
❌ Erreur: Variable X manquante
```

---

### 🔹 Option 3: Démarrer tous les services (intégré)
**Commande:** `3`

**Qu'est-ce que ça fait:**
- Lance tous les services en même temps
- PostgreSQL (la base de données)
- FastAPI Backend (port 8000)
- Service WhatsApp (port 3001)
- Affiche les logs
- Montre le code QR pour WhatsApp

**Quand l'utiliser:**
- C'est l'option que tu veux pour tester le système complet
- Le plus simple si tu ne veux pas ouvrir 3 terminaux

**Ce que tu vois:**
```
Starting PostgreSQL...
Starting Backend on port 8000...
Starting WhatsApp Service on port 3001...
Show QR code: [code QR affiché]
Scan with your WhatsApp phone!
```

**Après avoir scanné le QR:**
- Les messages de WhatsApp arrivent au backend
- Le bot répond

---

### 🔹 Option 4: Démarrer backend uniquement
**Commande:** `4`

**Qu'est-ce que ça fait:**
- Lance uniquement le serveur FastAPI
- Port 8000
- Recharge automatiquement si tu modifies le code

**Quand l'utiliser:**
- Si tu veux tester juste le backend
- Pour développer/modifier le code Python
- Les changements se reload automatiquement

**Exemple:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     API documentation at http://localhost:8000/docs
```

**Tu peux ensuite:**
```bash
curl http://localhost:8000/health
# Reçoit: {"status":"healthy"}
```

---

### 🔹 Option 5: Démarrer service WhatsApp uniquement
**Commande:** `5`

**Qu'est-ce que ça fait:**
- Lance le service Baileys WhatsApp
- Port 3001
- Affiche un code QR

**Quand l'utiliser:**
- Si tu veux tester juste WhatsApp
- Pour développer le service Node.js

**Ce que tu vois:**
```
Starting WhatsApp Service...
Scan this QR code with your WhatsApp phone:
[code QR]
Client ready!
```

---

### 🔹 Option 6: Exécuter les tests d'intégration
**Commande:** `6`

**Qu'est-ce que ça fait:**
- Lance les tests automatisés
- Teste si tous les composants marchent ensemble
- Envoie et reçoit des messages de test
- Vérifie que tout est connecté

**Quand l'utiliser:**
- Pour vérifier que le système marche bien
- Avant de déployer en production
- Après avoir fait des modifications

**Exemple:**
```
Phase 1: Checking dependencies... ✅
Phase 2: Starting services... ✅
Phase 3: Health checks... ✅
Phase 4: Testing message flow... ✅
Phase 5: Verifying responses... ✅
All tests passed! ✅
```

---

### 🔹 Option 7: Afficher les logs récents
**Commande:** `7`

**Qu'est-ce que ça fait:**
- Affiche les 20 dernières lignes ou erreurs d'un log
- Logs du backend
- Logs du service WhatsApp

**Quand l'utiliser:**
- Pour voir ce qui s'est passé
- Pour identifier les erreurs
- Pour comprendre pourquoi quelque chose ne marche pas

**Exemple:**
```
Backend Logs:
INFO: Message received from 1234567890
INFO: Processing with BrainOrchestrator
INFO: Calling DeepSeek API...
INFO: Response sent back
```

---

### 🔹 Option 8: Vérifier l'état Git
**Commande:** `8`

**Qu'est-ce que ça fait:**
- Affiche la branche Git actuelle
- Affiche les 5 derniers commits
- Affiche l'état du répertoire de travail

**Quand l'utiliser:**
- Pour vérifier que les changements sont bien sauvegardés
- Pour vérifier la branche sur laquelle tu travailles
- Avant de faire un push

**Exemple:**
```
Branche actuelle: emergency/rotate-secrets

Commits récents:
6ae6cc0 - docs: Add comprehensive documentation
4307532 - fix: Complete Baileys WhatsApp fixes
3bc447b - feat: Add pedagogical annotations
```

---

### 🔹 Option 9: Voir la documentation du projet
**Commande:** `9`

**Qu'est-ce que ça fait:**
- Affiche la liste des fichiers de documentation
- Te permet de choisir un fichier à lire
- Affiche le fichier avec `less` (tu peux scroller)

**Quand l'utiliser:**
- Pour lire la documentation
- Pour comprendre comment utiliser le système
- Pour trouver des solutions aux problèmes

**Fichiers disponibles:**
```
- README_COMPREHENSIVE.md
- BAILEYS_COMPLETE_FIX_GUIDE.md
- QUICK_FIX_SUMMARY.md
- PROJECT_STATUS_FINAL.md
- EXPLICATIONS_FRANCAIS.md
[etc.]
```

---

### 🔹 Option 10: Résumé rapide des corrections
**Commande:** `10`

**Qu'est-ce que ça fait:**
- Affiche `QUICK_FIX_SUMMARY.md`
- Un résumé d'une page des 5 problèmes fixés
- Lisible en 2 minutes

**Quand l'utiliser:**
- Pour vérifier rapidement ce qui a été fixé
- Pour rafraîchir ta mémoire

---

### 🔹 Option 11: Vérifier la santé de la base de données
**Commande:** `11`

**Qu'est-ce que ça fait:**
- Vérifie que PostgreSQL est configuré
- Vérifie que le driver psycopg2-binary est installé
- Vérifie que le pool de connexions est configuré

**Quand l'utiliser:**
- Si tu as des problèmes de connexion à la base de données
- Pour vérifier que tout est configuré correctement

**Exemple:**
```
✅ DATABASE_URL configuré
✅ PostgreSQL driver présent
✅ Connection pooling configuré
```

---

### 🔹 Option 12: Réinitialiser et redémarrer
**Commande:** `12`

**Qu'est-ce que ça fait:**
- Arrête tous les services
- Efface les caches
- Prépare le système pour un redémarrage propre

**Quand l'utiliser:**
- Si quelque chose est "bloqué"
- Pour un redémarrage complet
- Après avoir fait des modifications importantes

**Attention:** Cela arrête tout!

---

### 🔹 Option 0: Quitter
**Commande:** `0`

**Qu'est-ce que ça fait:**
- Ferme le menu
- Retour au terminal normal

---

## 💡 Cas d'utilisation courants

### "Je veux juste tester le système"
1. Lance le menu: `./scripts/MASTER_COMMANDS.sh`
2. Choisis option `3` (Démarrer tous les services)
3. Attends que le code QR s'affiche
4. Scanne le code QR avec ton téléphone
5. Envoie un message de test
6. Reçois une réponse du bot ✅

### "Le system ne marche pas"
1. Lance le menu: `./scripts/MASTER_COMMANDS.sh`
2. Choisis option `2` (Diagnostic complet)
3. Lis les erreurs affichées
4. Fais les corrections nécessaires
5. Relance le diagnostic

### "Je veux développer sur le backend"
1. Lance le menu: `./scripts/MASTER_COMMANDS.sh`
2. Choisis option `4` (Backend uniquement)
3. Modifie les fichiers Python
4. Le serveur se reload automatiquement
5. Teste avec `curl` ou Postman

### "Je veux développer sur WhatsApp"
1. Lance le menu: `./scripts/MASTER_COMMANDS.sh`
2. Choisis option `5` (WhatsApp uniquement)
3. Modifie les fichiers Node.js
4. Redémarre le service
5. Teste avec un vrai message WhatsApp

### "Je veux vérifier l'état de tout"
1. Lance le menu: `./scripts/MASTER_COMMANDS.sh`
2. Choisis option `1` (Vérifier l'état)
3. Vois tous les services et versions

---

## ⌨️ Raccourcis de ligne de commande

Au lieu d'utiliser le menu, tu peux appeler directement:

```bash
# Vérifier l'état
./scripts/MASTER_COMMANDS.sh status

# Diagnostic complet
./scripts/MASTER_COMMANDS.sh diagnostic

# Démarrer tous les services
bash scripts/integration_test.sh

# Démarrer juste le backend
./scripts/MASTER_COMMANDS.sh start-backend

# Démarrer juste WhatsApp
./scripts/MASTER_COMMANDS.sh start-whatsapp

# Tester l'intégration
./scripts/MASTER_COMMANDS.sh test

# Voir les logs
./scripts/MASTER_COMMANDS.sh logs

# Voir l'état Git
./scripts/MASTER_COMMANDS.sh git

# Voir la doc
./scripts/MASTER_COMMANDS.sh docs

# Résumé rapide
./scripts/MASTER_COMMANDS.sh summary

# Vérifier la base de données
./scripts/MASTER_COMMANDS.sh db

# Réinitialiser
./scripts/MASTER_COMMANDS.sh reset
```

---

## 🎯 Flux typique d'utilisation

### Jour 1: Configuration et test
```bash
# 1. Vérifier que tout est installé
./scripts/MASTER_COMMANDS.sh status

# 2. Diagnostic complet
./scripts/MASTER_COMMANDS.sh diagnostic

# 3. Lancer tous les services
bash scripts/integration_test.sh

# 4. Scaner le code QR
[Tu scannes avec ton téléphone]

# 5. Tester: Envoyer un message WhatsApp
[Message reçu par le bot]

# 6. Vérifier la réponse
[Tu reçois une réponse ✅]
```

### Jour 2+: Développement
```bash
# 1. Démarrer juste le backend
./scripts/MASTER_COMMANDS.sh start-backend

# 2. Dans un autre terminal, développer
[Tu modifies le code]

# 3. Le backend se reload automatiquement
[C'est magique!]

# 4. Tester les changements
curl http://localhost:8000/health
```

---

## 🆘 Aide et dépannage

### Le menu ne s'affiche pas
```bash
# Rendre le script exécutable
chmod +x /home/tim/neobot-mvp/scripts/MASTER_COMMANDS.sh

# Relancer
./scripts/MASTER_COMMANDS.sh
```

### Les services ne démarrent pas
```bash
# Vérifie le diagnostic
./scripts/MASTER_COMMANDS.sh diagnostic

# Regarde les erreurs
./scripts/MASTER_COMMANDS.sh logs
```

### Python ne se lance pas
```bash
# Vérifier si Python est installé
python3 --version

# Vérifier les dépendances
pip list | grep fastapi
```

### npm ne fonctionne pas
```bash
# Vérifier si Node.js est installé
node --version

# Réinstaller les packages
cd whatsapp-service
npm install
```

---

## ✅ Checklist de démarrage

- [ ] J'ai 3 terminaux ouverts (optionnel)
- [ ] J'ai lancé le menu: `./scripts/MASTER_COMMANDS.sh`
- [ ] J'ai vérifié l'état avec l'option 1
- [ ] J'ai lancé le diagnostic avec l'option 2
- [ ] Tous les diagnostics sont ✅
- [ ] J'ai lancé tous les services avec l'option 3
- [ ] Un code QR s'est affiché
- [ ] J'ai scanné le code QR avec mon téléphone
- [ ] Le bot s'est lié à mon compte WhatsApp
- [ ] J'ai envoyé un message de test
- [ ] J'ai reçu une réponse du bot

---

**C'est tout! Tu es maintenant un expert du menu! 🎉**

Pour d'autres questions, lis les fichiers:
- `EXPLICATIONS_FRANCAIS.md` - Explication complète
- `BAILEYS_COMPLETE_FIX_GUIDE.md` - Les problèmes détaillés
- `docs/TROUBLESHOOTING.md` - Solutions aux problèmes
