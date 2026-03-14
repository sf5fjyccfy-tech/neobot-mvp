#!/bin/bash

##########################################################################
#  🚀 NéoBot WhatsApp Legacy Launcher (compat mode)                       #
##########################################################################

Mode="${1:-mock}"

case "$Mode" in
    mock)
        export WHATSAPP_MODE=mock
        echo "🧪 Starting in MOCK mode (compatibility)..."
        ;;
    official)
        if [ -z "$WHATSAPP_PHONE_NUMBER_ID" ] || [ -z "$WHATSAPP_ACCESS_TOKEN" ]; then
            echo "❌ Error: Missing WHATSAPP credentials"
            echo "Set:"
            echo "  export WHATSAPP_PHONE_NUMBER_ID='your-id'"
            echo "  export WHATSAPP_ACCESS_TOKEN='your-token'"
            exit 1
        fi
        export WHATSAPP_MODE=official
        echo "📱 Starting in OFFICIAL mode (compatibility)..."
        ;;
    clean)
        pkill -f "whatsapp-service-v6-dual-mode.js" 2>/dev/null || true
        pkill -f "whatsapp-production.js" 2>/dev/null || true
        rm -rf auth_info_baileys
        npm install 2>/dev/null
        echo "✅ Cleaned! Run: $0 mock"
        exit 0
        ;;
    *)
        echo "Usage: $0 {mock|official|clean}"
        exit 1
        ;;
esac

cd "$(dirname "$0")"
echo "⚠️  v6 launcher is deprecated. Redirecting to whatsapp-production.js"
node whatsapp-production.js
