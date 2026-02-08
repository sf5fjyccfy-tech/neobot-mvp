"""
API pour la gestion du QR code WhatsApp
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import logging
from app.services.whatsapp_manager import whatsapp_manager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/whatsapp/status")
async def get_whatsapp_status():
    """Obtenir le statut WhatsApp"""
    return whatsapp_manager.get_status()

@router.post("/whatsapp/restart")
async def restart_whatsapp():
    """Redémarrer la connexion WhatsApp"""
    whatsapp_manager.restart_connection()
    return {"status": "restarting"}

@router.websocket("/whatsapp/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour les mises à jour en temps réel"""
    await websocket.accept()
    
    def status_listener(status):
        """Envoyer les mises à jour via WebSocket"""
        try:
            asyncio.run(websocket.send_text(json.dumps(status)))
        except:
            pass
    
    # Ajouter le listener
    whatsapp_manager.add_connection_listener(status_listener)
    
    # Envoyer le statut initial
    await websocket.send_text(json.dumps(whatsapp_manager.get_status()))
    
    try:
        while True:
            # Garder la connexion ouverte
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket déconnecté")
    except Exception as e:
        logger.error(f"Erreur WebSocket: {e}")

@router.get("/whatsapp/connect", response_class=HTMLResponse)
async def whatsapp_connect_page():
    """Page de connexion WhatsApp intégrée"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NéoBot - Connexion WhatsApp</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 500px; 
                margin: 50px auto; 
                padding: 20px;
                text-align: center;
            }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
            #qrCode { margin: 20px 0; }
            button { 
                padding: 10px 20px; 
                background: #007bff; 
                color: white; 
                border: none; 
                border-radius: 5px; 
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>🔗 Connexion WhatsApp</h1>
        <div id="status" class="status disconnected">Déconnecté</div>
        
        <div id="qrCode"></div>
        
        <button onclick="restartConnection()">🔄 Redémarrer</button>
        
        <script>
            const ws = new WebSocket(`ws://${window.location.host}/api/whatsapp/ws`);
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                updateStatus(data);
            };
            
            function updateStatus(status) {
                const statusDiv = document.getElementById('status');
                const qrDiv = document.getElementById('qrCode');
                
                if (status.connected) {
                    statusDiv.textContent = '✅ WhatsApp connecté';
                    statusDiv.className = 'status connected';
                    qrDiv.innerHTML = '';
                } else if (status.qr_code) {
                    statusDiv.textContent = '📱 Scannez le QR Code';
                    statusDiv.className = 'status disconnected';
                    qrDiv.innerHTML = `<img src="data:image/png;base64,${status.qr_code}" alt="QR Code">`;
                } else {
                    statusDiv.textContent = '❌ Déconnecté';
                    statusDiv.className = 'status disconnected';
                    qrDiv.innerHTML = '';
                }
            }
            
            function restartConnection() {
                fetch('/api/whatsapp/restart', { method: 'POST' });
            }
            
            // Charger le statut initial
            fetch('/api/whatsapp/status')
                .then(r => r.json())
                .then(updateStatus);
        </script>
    </body>
    </html>
    """
