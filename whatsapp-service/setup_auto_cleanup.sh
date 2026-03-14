#!/bin/bash

# ╔════════════════════════════════════════════════════════════════════╗
# ║                    Setup Cleanup Automatique                       ║
# ║          Configure le nettoyage automatique des sessions            ║
# ╚════════════════════════════════════════════════════════════════════╝

SCRIPT_DIR="/home/tim/neobot-mvp"
CLEANUP_SCRIPT="$SCRIPT_DIR/reset_whatsapp_automatic.sh"
CRONTAB_JOB="0 * * * * $CLEANUP_SCRIPT cron >> $SCRIPT_DIR/whatsapp-service/cron_check.log 2>&1"

echo "═══════════════════════════════════════════════════════════════════"
echo "🛠️  Configuration du cleanup automatique pour NéoBot WhatsApp"
echo "═══════════════════════════════════════════════════════════════════"

# 1. Rendre le script executable
echo "📝 Rendre le script exécutable..."
chmod +x "$CLEANUP_SCRIPT"

# 2. Ajouter au crontab
echo "⏰ Ajout au crontab (toutes les heures)..."

# Vérifier si déjà présent
if crontab -l 2>/dev/null | grep -q "$CLEANUP_SCRIPT"; then
    echo "✅ Déjà présent dans crontab"
else
    (crontab -l 2>/dev/null; echo "$CRONTAB_JOB") | crontab -
    if [ $? -eq 0 ]; then
        echo "✅ Ajouté au crontab"
    else
        echo "❌ Erreur ajout au crontab"
    fi
fi

# 3. Créer les fichiers de log
echo "📋 Création des fichiers de log..."
touch "$SCRIPT_DIR/whatsapp-service/cleanup.log"
touch "$SCRIPT_DIR/whatsapp-service/cron_check.log"

# 4. Afficher la configuration
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "✅ Configuration terminée!"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "📌 Commandes disponibles:"
echo ""
echo "  Service WhatsApp:"
echo "    npm start                        - Démarrer le service"
echo "    pkill -f 'node.*index.js'        - Arrêter le service"
echo ""
echo "  Nettoyage manuel:"
echo "    bash $CLEANUP_SCRIPT manual      - Nettoyage immédiat"
echo ""
echo "  Vérification/Logs:"
echo "    tail -f $SCRIPT_DIR/whatsapp-service/cleanup.log"
echo "    tail -f $SCRIPT_DIR/whatsapp-service/cron_check.log"
echo ""
echo "  Tâches cron:"
echo "    crontab -l                       - Voir les crons"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
