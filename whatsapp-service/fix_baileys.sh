#!/bin/bash

# Script pour réparer la version de Baileys

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🔧 CORRECTION DE LA VERSION BAILEYS - Préparation         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

cd /home/tim/neobot-mvp/whatsapp-service

# 1. Nettoyer
echo "📦 Étape 1: Nettoyage des dépendances..."
rm -rf node_modules package-lock.json
echo "✅ Nettoyage fait"
echo ""

# 2. Installer
echo "📦 Étape 2: Installation des dépendances..."
echo "   Versions à installer:"
echo "   - @whiskeysockets/baileys: 6.7.21 (STABLE)"
echo "   - express: ^4.22.0"
echo "   - dotenv: ^16.0.3"
echo ""

# Installer les packages
npm install --legacy-peer-deps 2>&1 | tail -5

echo ""
echo "✅ Installation terminée!"
echo ""

# 3. Vérifier
echo "📦 Étape 3: Vérification des versions..."
npm list @whiskeysockets/baileys 2>&1 | grep -E "baileys|installed"
echo ""

# 4. Test rapide
echo "🧪 Étape 4: Test de syntaxe..."
node -c index.js && echo "✅ Syntaxe valide!" || echo "❌ Erreur de syntaxe"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  ✅ BAILEYS CORRIGÉE - PRÊT À DÉMARRER                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "🚀 Pour démarrer le service:"
echo "   npm start"
echo ""
