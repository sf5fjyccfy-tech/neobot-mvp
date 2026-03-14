#!/bin/bash
cd ~/neobot-mvp/whatsapp-service

echo "🎮 CONTROLEUR SMART WHATSAPP (ES6)"
echo "=================================="

case "$1" in
    start)
        echo "🚀 Démarrage Smart WhatsApp ES6..."
        node whatsapp_stable.mjs 2>&1 | tee -a smart_whatsapp.log &
        echo $! > whatsapp.pid
        echo "✅ PID: $(cat whatsapp.pid)"
        echo "📊 Logs: tail -f smart_whatsapp.log"
        ;;
    
    stop)
        echo "🛑 Arrêt..."
        if [ -f whatsapp.pid ]; then
            kill -9 $(cat whatsapp.pid) 2>/dev/null
            rm -f whatsapp.pid
            echo "✅ Arrêté"
        else
            echo "⚠️  Pas de processus enregistré"
            pkill -f "node.*whatsapp" 2>/dev/null && echo "✅ Processus tués" || echo "✅ Aucun processus trouvé"
        fi
        ;;
    
    restart)
        echo "🔄 Redémarrage..."
        bash $0 stop
        sleep 2
        bash $0 start
        ;;
    
    status)
        echo "📊 État:"
        if [ -f whatsapp.pid ] && kill -0 $(cat whatsapp.pid) 2>/dev/null; then
            echo "✅ En cours d'exécution (PID: $(cat whatsapp.pid))"
            echo "📈 Logs récents:"
            tail -5 smart_whatsapp.log 2>/dev/null || echo "Pas de logs"
        else
            echo "❌ Arrêté"
            rm -f whatsapp.pid 2>/dev/null
        fi
        
        echo ""
        echo "📁 Sessions:"
        ls -la auth_info_baileys/ 2>/dev/null || echo "Pas de session"
        
        echo ""
        echo "🌐 Backend NéoBot:"
        if curl -s http://localhost:8000/health > /dev/null; then
            echo "✅ Backend accessible"
        else
            echo "❌ Backend injoignable"
        fi
        ;;
    
    newqr)
        echo "🔄 Force nouveau QR code..."
        bash $0 stop
        rm -rf auth_info_baileys/ 2>/dev/null
        sleep 2
        bash $0 start
        ;;
    
    logs)
        echo "📋 Logs:"
        tail -50 smart_whatsapp.log 2>/dev/null || echo "Pas de logs"
        ;;
    
    test)
        echo "🧪 Test backend..."
        curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ Backend injoignable"
        
        echo ""
        echo "🧪 Test endpoint WhatsApp..."
        curl -s -X POST http://localhost:8000/api/tenants/1/whatsapp/message \
          -H "Content-Type: application/json" \
          -d '{"phone":"237612345678","message":"test"}' | python3 -m json.tool 2>/dev/null || echo "❌ Endpoint WhatsApp injoignable"
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|newqr|logs|test}"
        echo ""
        echo "🔧 Commandes:"
        echo "  start   - Démarrer Smart WhatsApp"
        echo "  stop    - Arrêter proprement"
        echo "  restart - Redémarrer"
        echo "  status  - Vérifier l'état + backend"
        echo "  newqr   - Forcer nouveau QR code"
        echo "  logs    - Voir les logs"
        echo "  test    - Tester le backend"
        exit 1
        ;;
esac
