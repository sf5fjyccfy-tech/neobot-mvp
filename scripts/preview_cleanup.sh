#!/bin/bash

# Script de PREVIEW pour identifier les fichiers à nettoyer
# N'effectue AUCUNE suppression - affiche simplement ce qui serait supprimé

set -e

REPO_ROOT="/home/tim/neobot-mvp"
REPORT_FILE="/tmp/cleanup_preview_$(date +%s).txt"

echo "🔍 Analyse du repository pour nettoyage..."
echo "Rapport généré: $REPORT_FILE"
echo ""

{
  echo "============================================"
  echo "PREVIEW CLEANUP - $(date)"
  echo "============================================"
  echo ""

  # Catégorie 1: Fichiers de backup et test
  echo "📦 Catégorie 1: Fichiers backup/test (${#})"
  find "$REPO_ROOT" -maxdepth 3 \
    \( -name "*backup*" -o -name "*old*" -o -name "*.bak" \
    -o -name "*test*.py" -o -name "*test*.js" \
    -o -name "*TEMP*" -o -name "*OLD*" \) \
    -type f 2>/dev/null | head -20 | xargs ls -lh
  echo ""

  # Catégorie 2: node_modules et dépendances
  echo "📦 Catégorie 2: node_modules (peut être énorme)"
  find "$REPO_ROOT" -maxdepth 4 -name "node_modules" -type d 2>/dev/null | while read dir; do
    size=$(du -sh "$dir" 2>/dev/null | cut -f1)
    echo "  $dir - Taille: $size"
  done
  echo ""

  # Catégorie 3: Fichiers de log et cache
  echo "📦 Catégorie 3: Logs, cache, temp"
  find "$REPO_ROOT" -type f \
    \( -name "*.log" -o -name "*.tmp" -o -name "*cache*" \) \
    2>/dev/null | head -20 | xargs ls -lh 2>/dev/null
  echo ""

  # Catégorie 4: Dossiers non essentiels
  echo "📦 Catégorie 4: Dossiers potentiellement supprimables"
  echo "  frontend/node_modules: $(du -sh $REPO_ROOT/frontend/node_modules 2>/dev/null | cut -f1 || echo 'N/A')"
  echo "  backend/node_modules: $(du -sh $REPO_ROOT/backend/node_modules 2>/dev/null | cut -f1 || echo 'N/A')"
  echo "  logs/: $(du -sh $REPO_ROOT/logs 2>/dev/null | cut -f1 || echo 'N/A')"
  echo "  whatsapp-service/node_modules: $(du -sh $REPO_ROOT/whatsapp-service/node_modules 2>/dev/null | cut -f1 || echo 'N/A')"
  echo ""

  # Catégorie 5: Fichiers avec patterns inutiles
  echo "📦 Catégorie 5: Fichiers backup Python/JS"
  find "$REPO_ROOT" -maxdepth 5 \
    \( -name "main*.py" -o -name "*_backup*" -o -name "*.pyc" \) \
    -type f 2>/dev/null | head -30
  echo ""

  # Résumé
  echo "============================================"
  echo "RÉSUMÉ"
  echo "============================================"
  TOTAL_SIZE=$(du -sh "$REPO_ROOT" | cut -f1)
  BACKUP_SIZE=$(find "$REPO_ROOT" -type d -name "node_modules" -exec du -sh {} \; 2>/dev/null | awk '{s+=$1} END {print s}')
  echo "Taille totale du repo: $TOTAL_SIZE"
  echo "Taille estimée node_modules: $BACKUP_SIZE"
  echo ""
  echo "✅ Preview terminée sans modification."
  echo "Examine le rapport et valide avant suppression !"

} | tee "$REPORT_FILE"

echo ""
echo "📄 Rapport complet sauvegardé dans: $REPORT_FILE"
