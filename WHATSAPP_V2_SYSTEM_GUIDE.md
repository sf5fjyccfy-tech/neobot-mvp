# NéoBot WhatsApp Service v2.0 - System Guide

## 🎯 Vue d'Ensemble

Le nouveau système WhatsApp pour NéoBot résout **TOUS** les problèmes de sessions expirées :

✅ **Auto-détection** des sessions expirées  
✅ **Nettoyage automatique** tous les jours (cron)  
✅ **Réparation d'erreurs 405** intégrée  
✅ **Génération automatique** de nouveaux QR codes  
✅ **API de gestion** pour monitoring  
✅ **Logs détaillés** pour debug  

---

## 📁 Fichiers Déployés

### Service Principal
- **`index_fixed.js`** - Nouvelle version robuste du service WhatsApp
  - Détecte les sessions expirées
  - Auto-correction de l'erreur 405
  - Gestion complète des événements Baileys
  - Endpoints API pour gestion

### Scripts d'Automatisation
- **`reset_whatsapp_automatic.sh`** - Nettoyage et redémarrage automatique
  - Vérificationde santé de la session
  - Suppression sécurisée des dossiers expirés
  - Redémarrage du service
  - Attente du nouveau QR
  
- **`start_whatsapp_v2.sh`** - Démarrage intelligent du service
  - Vérification des dépendances
  - Nettoyage préalable si nécessaire
  - Démarrage avec détection d'erreurs
  - Affichage des informations d'utilisation

- **`setup_auto_cleanup.sh`** - Configuration du cleanup automatique
  - Active le cron pour vérification horaire
  - Crée les fichiers de log
  - Configure l'environnement

### API de Session
- **`api_session_management.js`** - Endpoints REST pour gérer les sessions
  - `resetSessionAPI()` - Réinitialisation complète
  - `deleteSessionForTenant()` - Suppression selective
  - `getSessionsInfo()` - Informations détaillées
  - `isSessionExpired()` - Vérification d'expiration
  - `cleanupTempFiles()` - Nettoyage des fichiers
  - `handle405Error()` - Gestion automatique erreur 405

### Configuration
- **`.env.cleanup`** - Variables de configuration
  - SESSION_TIMEOUT: 3600000 ms (1 heure)
  - MAX_RETRIES: 5 tentatives
  - AUTO_CLEANUP_ENABLED: true

---

## 🚀 Démarrage Rapide

### 1. Installation et Configuration (UNE SEULE FOIS)

```bash
# Aller au répertoire WhatsApp
cd /home/tim/neobot-mvp/whatsapp-service

# Installer les dépendances
npm install

# Configurer le cleanup automatique
bash setup_auto_cleanup.sh
```

**Pour les utilisateurs sudo** (si setup échoue):
```bash
sudo bash setup_auto_cleanup.sh
```

### 2. Démarrage du Service

```bash
# Méthode 1 : Via le nouveau script intelligent
bash /home/tim/neobot-mvp/whatsapp-service/start_whatsapp_v2.sh

# Méthode 2 : Direct avec npm (après npm install)
cd /home/tim/neobot-mvp/whatsapp-service
npm start
```

### 3. Attendre le QR Code

Le service affichera un banner comme :
```
╔════════════════════════════════════════════╗
║  📱 SCANNER LE CODE QR                    ║
║  ✅ Appareil: NéoBot WhatsApp Service    ║
║  ⏱️  Valide: 60 secondes                   ║
║                                            ║
║  Instructions:                             ║
║  1. Ouvrez WhatsApp sur votre téléphone  ║
║  2. Allez dans: Paramètres → Appareils  ║
║  3. Cliquez sur "Connecter un appareil" ║
║  ...etc...                                 ║
╚════════════════════════════════════════════╝
```

**Scannez le QR code qui apparaît en dessous du banner!**

---

## 🛠️ Commandes Disponibles

### Gestion du Service

```bash
# Démarrer
bash /home/tim/neobot-mvp/whatsapp-service/start_whatsapp_v2.sh

# Arrêter
pkill -f "node.*index.js"

# Forcer l'arrêt
pkill -9 -f "node.*index.js"

# Vérifier l'état
ps aux | grep -E "node.*index|npm start"
```

### Nettoyage et Reset

```bash
# Reset IMMÉDIAT de la session
bash /home/tim/neobot-mvp/reset_whatsapp_automatic.sh manual

# Vérification cron (automatique hourly)
bash /home/tim/neobot-mvp/reset_whatsapp_automatic.sh cron
```

### API REST

```bash
# Health check
curl http://localhost:3001/health

# Status détaillé
curl http://localhost:3001/status

# Infos sessions
curl http://localhost:3001/api/whatsapp/session-info

# Réinitialiser session (RESET)
curl -X POST http://localhost:3001/api/whatsapp/reset-session

# Supprimer session d'un tenant
curl -X POST http://localhost:3001/api/whatsapp/delete-tenant/1
```

---

## 📊 Fichiers de Logs

```bash
# Logs du service principal
tail -f /home/tim/neobot-mvp/whatsapp-service/whatsapp.log

# Logs du cleanup automatique
tail -f /home/tim/neobot-mvp/whatsapp-service/cleanup.log

# Logs des vérifications cron
tail -f /home/tim/neobot-mvp/whatsapp-service/cron_check.log

# Historique de session
tail -f /home/tim/neobot-mvp/whatsapp-service/session_history.log
```

---

## 🔄 Flux Automatique

### 1. Démarrage Normal
```
Service demarre
  ↓
Charge la session existante (si ok)
  ↓
Génère QR (si nouvelle session)
  ↓
Scanner avec WhatsApp
  ↓
CONNECTÉ ✅
```

### 2. Session Expirée (Détection Automatique)
```
Service détecte expiration
  ↓
Arrête proprement
  ↓
Supprime les dossiers auth_info_baileys/ et .wwebjs_auth/
  ↓
Redémarre le service
  ↓
Génère NOUVEAU QR
  ↓
Scanner et CONNECTÉ ✅
```

### 3. Erreur 405 (Gestion Automatique)
```
Erreur 405 reçue
  ↓
Auto-cleanup triggeré
  ↓
Supprime sessions corrompues
  ↓
Redémarre
  ↓
Nouveau QR généré
  ↓
Reconnexion réussie ✅
```

### 4. Vérification Cron (Horaire)
```
Chaque heure (via cron)
  ↓
Vérifie santé de la session
  ↓
SI EXPIRÉE → Lance cleanup immédiat
SINON → Continue sans interruption
  ↓
Logs enregistrés
```

---

## ⚙️ Configuration Avancée

### Modifier le Timeout

Éditer `/home/tim/neobot-mvp/whatsapp-service/index_fixed.js`:

```javascript
// Ligne ~20
const SESSION_TIMEOUT = 3600000; // Augmenter pour laisser plus de temps
```

### Modifier la Fréquence de Vérification Cron

```bash
# Voir la config actuelle
crontab -l

# Éditer
crontab -e

# Changer la ligne à:
# Toutes les 30 minutes:
*/30 * * * * /home/tim/neobot-mvp/reset_whatsapp_automatic.sh cron

# Toutes les 6 heures:
0 */6 * * * /home/tim/neobot-mvp/reset_whatsapp_automatic.sh cron
```

### Désactiver Cleanup Automatique

```bash
# Commenter la ligne dans crontab:
crontab -e
# Ajouter # au début de la ligne
```

---

## 🚨 Troubleshooting Avancé

### Problème: Service démarre mais pas de QR affiché

```bash
# 1. Vérifier les logs
tail -50 /home/tim/neobot-mvp/whatsapp-service/whatsapp.log

# 2. Chercher "SCANNER LE CODE QR"
grep "SCANNER" /home/tim/neobot-mvp/whatsapp-service/whatsapp.log

# 3. Si rien → Force reset
bash /home/tim/neobot-mvp/reset_whatsapp_automatic.sh manual

# 4. Relancer
bash /home/tim/neobot-mvp/whatsapp-service/start_whatsapp_v2.sh
```

### Problème: Erreur 405 persiste

```bash
# 1. Force cleanup complet
bash /home/tim/neobot-mvp/reset_whatsapp_automatic.sh manual

# 2. Attendre logs
sleep 5
tail -50 /home/tim/neobot-mvp/whatsapp-service/cleanup.log

# 3. Vérifier nouveau démarrage
ps aux | grep "node.*index"

# 4. Si toujours 405 → update Baileys
cd /home/tim/neobot-mvp/whatsapp-service
npm update @whiskeysockets/baileys
```

### Problème: Vieux dossiers de session éviter

```bash
# Forcer suppression physique
sudo rm -rf /home/tim/neobot-mvp/whatsapp-service/auth_info_baileys/
sudo rm -rf /home/tim/neobot-mvp/whatsapp-service/.wwebjs_auth/
sudo rm -rf /home/tim/neobot-mvp/whatsapp-service/session/
sudo rm -rf /home/tim/neobot-mvp/auth_info_baileys/

# Créer frais
mkdir /home/tim/neobot-mvp/whatsapp-service/auth_info_baileys/

# Redémarrer
bash /home/tim/neobot-mvp/whatsapp-service/start_whatsapp_v2.sh
```

---

## 📈 Monitoring en Production

### Dashboard Rapide

```bash
#!/bin/bash
# Créer fichier: /home/tim/neobot-mvp/monitor_whatsapp.sh

while true; do
    clear
    echo "📊 NéoBot WhatsApp Status - $(date)"
    echo "═════════════════════════════════════"
    
    # Service status
    if pgrep -f "node.*index" > /dev/null; then
        echo "✅ Service: RUNNING"
        ps aux | grep "node.*index" | grep -v grep | awk '{print "   PID: " $2 " | MEM: " $6 "kb"}'
    else
        echo "❌ Service: STOPPED"
    fi
    
    # Health check
    echo ""
    echo "Health Check:"
    curl -s http://localhost:3001/health | python3 -m json.tool 2>/dev/null || echo "   ⚠️  Service inaccessible"
    
    # Session info
    echo ""
    echo "Sessions:"
    curl -s http://localhost:3001/api/whatsapp/session-info 2>/dev/null | python3 -m json.tool | head -20
    
    echo ""
    echo "← Up arrow to refresh | Ctrl+C to exit →"
    sleep 10
done
```

Lancer:
```bash
bash /home/tim/neobot-mvp/monitor_whatsapp.sh
```

---

## ✅ Checklist de Déploiement

- [ ] `npm install` exécuté
- [ ] `setup_auto_cleanup.sh` exécuté avec succès
- [ ] Service démarré avec `start_whatsapp_v2.sh`
- [ ] QR code affiché
- [ ] WhatsApp scannée avec succès
- [ ] ✅ Banner de connexion réussie affiché
- [ ] Logs vérifiant "Connecté à WhatsApp"
- [ ] Cron configuré (vérifier avec `crontab -l`)
- [ ] Tests API passants (curl /health)

---

## 🎓 Résumé des Améliorations

| Problème | Avant | Après |
|----------|-------|-------|
| Sessions expirées | Restent en mémoire | Auto-détectées et nettoyées |
| Erreur 405 | Crash service | Auto-recovery (nettoyage + restart) |
| QR code expiré | Pas de nouveau | Auto-régénération |
| Monitoring | Manuel | Cron toutes les heures |
| API de reset | Aucune | 5 endpoints REST |
| Logs | Basiques | Détaillés avec timestamps |

---

## 📞 Support Rapide

```bash
# État actuel du système
curl http://localhost:3001/api/whatsapp/status

# Forcer un reset immédiat
curl -X POST http://localhost:3001/api/whatsapp/reset-session

# Voir les sessions actuelles
curl http://localhost:3001/api/whatsapp/session-info

# Arrêter et relancer (clean)
pkill -f "node.*index.js"
sleep 2
bash /home/tim/neobot-mvp/whatsapp-service/start_whatsapp_v2.sh
```

---

**Version**: 2.0  
**Date**: 12 Mars 2026  
**Statut**: 🟢 Production Ready
