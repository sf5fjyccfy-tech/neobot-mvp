#!/bin/bash

# NéoBot WhatsApp Setup - Interactive Guide

set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🔗 NéoBot WhatsApp Service - Setup Guide          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check port
PORT=3001
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "❌ Port $PORT est déjà utilisé"
    echo "Tuant le processus..."
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Clean auth if requested
if [ "$1" = "clean" ]; then
    echo "🧹 Nettoyage de la session d'authentification..."
    rm -rf whatsapp-service/auth_info_baileys
    echo "✅ Done"
fi

# Start service
echo ""
echo "🚀 Démarrage du service WhatsApp..."
echo ""

cd whatsapp-service

# Check npm packages
if [ ! -d "node_modules" ]; then
    echo "📦 Installation des dépendances..."
    npm install --silent
    echo "✅ Dépendances installées"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ Service démarrant sur http://localhost:$PORT"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Prochaines étapes:"
echo "  1️⃣  Attends 5-10 secondes pour le QR code"
echo "  2️⃣  Ouvre: http://localhost:$PORT/qr"
echo "  3️⃣  Scanne avec ton téléphone WhatsApp"
echo "  4️⃣  ✅ Connexion active!"
echo ""
echo "Endpoints:"
echo "  • Health: http://localhost:$PORT/health"
echo "  • QR Web: http://localhost:$PORT/qr"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

npm start

