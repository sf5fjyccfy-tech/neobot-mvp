#!/bin/bash

# Script SÉCURISÉ de cleanup
# Nécessite une confirmation explicite avant suppression

set -e

REPO_ROOT="/home/tim/neobot-mvp"
BACKUP_DIR="$HOME/neobot-mvp-backups-$(date +%Y%m%d_%H%M%S)"
CONFIRM_FILE="/tmp/confirm_neobot_delete.txt"

echo "⚠️  Script de nettoyage NéoBot - LECTURE SEULE PAR DÉFAUT"
echo ""

# Vérifier s'il y a une demande de suppression
if [ ! -f "$CONFIRM_FILE" ] || [ "$(cat $CONFIRM_FILE)" != "DELETE_NOW" ]; then
  echo "❌ Suppression non autorisée."
  echo ""
  echo "Pour autoriser la suppression, exécute :"
  echo "  echo 'DELETE_NOW' > $CONFIRM_FILE"
  echo "  bash scripts/apply_cleanup.sh"
  echo ""
  echo "ATTENTION: Cela supprimera les éléments suivants (sans possibilité de récupération) :"
  echo "  • node_modules/ dans tous les dossiers"
  echo "  • Fichiers de backup (*.bak, main_backup*.py, etc.)"
  echo "  • Fichiers de test et de dev"
  echo "  • Fichiers de log"
  exit 1
fi

echo "✅ Suppression autorisée détectée !"
echo "Création d'une sauvegarde de sécurité dans: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Sauvegarde des éléments critiques avant suppression
echo "📦 Sauvegarde de sécurité des node_modules..."
for dir in $(find "$REPO_ROOT" -maxdepth 4 -type d -name "node_modules"); do
  parent=$(dirname "$dir")
  parent_name=$(basename "$parent")
  tar -czf "$BACKUP_DIR/node_modules-$parent_name.tar.gz" -C "$parent" node_modules 2>/dev/null || true
done

echo "🗑️  Suppression des node_modules..."
find "$REPO_ROOT" -maxdepth 4 -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true

echo "🗑️  Suppression des fichiers backup..."
find "$REPO_ROOT" -maxdepth 5 \
  \( -name "*backup*" -o -name "*_old" -o -name "*.bak" \) \
  -type f -delete 2>/dev/null || true

echo "🗑️  Suppression des fichiers .pyc et cache Python..."
find "$REPO_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
find "$REPO_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "🗑️  Suppression des fichiers de log..."
find "$REPO_ROOT/logs" -type f -delete 2>/dev/null || true

echo ""
echo "✅ Nettoyage terminé !"
echo "📁 Sauvegarde créée dans: $BACKUP_DIR"
echo "🔄 Tu peux restaurer avec: tar -xzf $BACKUP_DIR/node_modules-*.tar.gz"
echo ""

# Nettoyer le fichier de confirmation
rm -f "$CONFIRM_FILE"

# Statut final
NEW_SIZE=$(du -sh "$REPO_ROOT" | cut -f1)
echo "Nouvelle taille du repo: $NEW_SIZE"
