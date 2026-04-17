# NeoBot Server Health Monitoring & Alerting

## Overview

Un système de monitoring en temps réel qui surveille la santé des services NeoBot et **envoie des alertes email via Brevo quand le serveur crash**.

### Services Monitored
- **Frontend** : https://neobot-ai.com/
- **Backend Internal** : http://localhost:8000/health

### Alerte Email
Chaque fois qu'un service passe de `healthy` → `down`, une **alerte email critique** est envoyée à **timpatrick561@gmail.com**.

Quand le service revient en ligne, une **alerte de récupération** est envoyée.

---

## Architecture

### Script Principal
```bash
/root/neobot-mvp/monitoring/health-check.sh
```

**Dépendances** : Aucune (bash pur + curl)

**Fonctionnalités** :
1. Vérifie les endpoints toutes les 5 minutes (via cron)
2. Compare l'état avec le fichier statut précédent
3. Envoie une alerte email si changement d'état
4. Logs tout dans `/root/neobot-mvp/logs/monitoring/health-check.log`

### Cron Job
```bash
/etc/cron.d/neobot-monitoring
```

Lance le script toutes les **5 minutes** avec les variables d'environnement chargées depuis `/root/neobot-mvp/.env`.

---

## Configuration

### Variables d'Environnement (dans `.env`)

```bash
# Brevo API pour les alertes email
BREVO_API_KEY=xkeysib-xxx...

# Destination des alertes
ALERT_EMAIL=timpatrick561@gmail.com
ADMIN_EMAIL=admin@neobot-ai.com
```

### Répertoires

```
/root/neobot-mvp/monitoring/          # Scripts
/root/neobot-mvp/logs/monitoring/     # Logs
├── health-check.log                   # Historique du monitoring
├── cron.log                           # Output du cron job
└── last_status.txt                    # État actuel (pour détection changements)
```

---

## Logs

### Format Log
```
[2026-04-17 23:25:48] [INFO] 🔍 Starting health check...
[2026-04-17 23:25:48] [INFO] ✅ HEALTHY - Frontend
[2026-04-17 23:25:48] [INFO] ✅ HEALTHY - Backend Internal
[2026-04-17 23:25:48] [INFO] ✅ All systems healthy
```

### Consultation des Logs
```bash
ssh root@178.104.163.245
tail -f /root/neobot-mvp/logs/monitoring/health-check.log
tail -f /root/neobot-mvp/logs/monitoring/cron.log  # Output du cron
```

---

## Fonctionnement

### Cycle de Vérification (5 minutes)

1. **Check endpoints**
   - GET https://neobot-ai.com/ → Attend HTTP 200
   - GET http://localhost:8000/health → Attend HTTP 200

2. **Comparer avec l'état précédent**
   - Stocké dans `/root/neobot-mvp/logs/monitoring/last_status.txt`
   - Format : `Frontend=true` ou `Frontend=false`

3. **Détection changements**
   - `true → false` = NOUVEAU DOWN → Email d'alerte critique
   - `false → true` = NOUVEAU UP → Email de récupération

4. **Sauvegarder nouvel état**

---

## Exemple : Ce qui se passe si le serveur crash

### Minute 0 : Tous les services sont up
```
[13:00] ✅ Frontend = HEALTHY
[13:00] ✅ Backend = HEALTHY
```

### Minute 5 : Le backend s'arrête
```
[13:05] ✅ Frontend = HEALTHY
[13:05] ❌ Backend = DOWN (HTTP 000)
        → Email envoyé : "🚨 NeoBot Alert: Backend Internal is DOWN"
```

### Minute 10+ : Tant que le backend est down
```
[13:10] ✅ Frontend = HEALTHY
[13:10] ❌ Backend = DOWN (HTTP 000)
        → (Pas d'email, déjà en alerte)
```

### Minute 15 : Le backend redémarre
```
[13:15] ✅ Frontend = HEALTHY
[13:15] ✅ Backend = HEALTHY
        → Email envoyé : "✅ NeoBot Alert: Backend is BACK ONLINE"
```

---

## Test Manuel

### Tester le script
```bash
ssh root@178.104.163.245
source /root/neobot-mvp/.env
bash /root/neobot-mvp/monitoring/health-check.sh
```

### Vérifier le cron est actif
```bash
systemctl status cron
ps aux | grep "health-check"
```

### Voir les dernières logs
```bash
tail -50 /root/neobot-mvp/logs/monitoring/health-check.log
tail -20 /root/neobot-mvp/logs/monitoring/cron.log
```

---

## Email d'Alerte Format

### Alerte DOWN (Critique)
```
To: timpatrick561@gmail.com
Subject: 🚨 NeoBot Alert: Backend Internal is DOWN

Body:
Backend Internal is not responding. URL: http://localhost:8000/health. 
Action: SSH to VPS and check containers.

Timestamp: 2026-04-17T23:25:48Z
```

### Alerte UP (Récupération)
```
To: timpatrick561@gmail.com
Subject: ✅ NeoBot Alert: Backend Internal is BACK ONLINE

Body:
Backend Internal has recovered and is responding normally.

Timestamp: 2026-04-17T23:25:48Z
```

---

## Troubleshooting

### Les emails ne s'envoient pas

1. Vérifier `BREVO_API_KEY` dans le `.env`
   ```bash
   ssh root@178.104.163.245
   grep BREVO_API_KEY /root/neobot-mvp/.env
   ```

2. Vérifier les logs du script
   ```bash
   tail -50 /root/neobot-mvp/logs/monitoring/health-check.log | grep -i "brevo\|error"
   ```

3. Tester l'API Brevo manuellement
   ```bash
   curl -X POST \
     -H "api-key: $YOUR_KEY" \
     -H "Content-Type: application/json" \
     -d '{"sender":{"name":"Test","email":"admin@neobot-ai.com"},"to":[{"email":"timpatrick561@gmail.com"}],"subject":"Test","htmlContent":"Test"}' \
     https://api.brevo.com/v3/smtp/email
   ```

### Le cron ne s'exécute pas

```bash
# Vérifier que le fichier existe et a les bonnes perms
ls -la /etc/cron.d/neobot-monitoring

# Vérifier que cron est actif
systemctl status cron

# Vérifier le format du cron
cat /etc/cron.d/neobot-monitoring

# Forcer le rechargement
systemctl reload cron
```

### Services détectés comme DOWN alors qu'ils sont UP

1. Vérifier manuellement
   ```bash
   curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/health
   curl -s -o /dev/null -w '%{http_code}' https://neobot-ai.com/
   ```

2. Vérifier le timeout (actuellement 10s)
   ```bash
   # Dans le script
   grep "timeout=" /root/neobot-mvp/monitoring/health-check.sh
   ```

---

## Améliorations Futures

- [ ] Slack webhook pour alertes en temps réel
- [ ] Dashboard grafana avec les métriques de monitoring
- [ ] Tests de performance (response time)
- [ ] Monitoring de la base de données (Neon PostgreSQL)
- [ ] Monitoring du Redis (si utilisé)
- [ ] Webhook custom pour intégrations tierces

---

## Support

Pour toute question ou issue, consulte les logs dans `/root/neobot-mvp/logs/monitoring/`.
