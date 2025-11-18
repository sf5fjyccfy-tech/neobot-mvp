"""
Service de gestion WhatsApp avec Baileys
"""
import asyncio
import subprocess
import os
import json
from typing import Dict, Any, Optional

class WhatsAppService:
    def __init__(self):
        self.process = None
        self.status = "disconnected"
        self.qr_code = ""
        self.connected = False
        
    async def start_whatsapp(self):
        """Démarrer le service WhatsApp Baileys"""
        try:
            if self.process and self.process.poll() is None:
                return {"success": True, "message": "Déjà en cours"}
            
            # Démarrer le service Baileys
            baileys_path = os.path.join(os.path.dirname(__file__), '../../whatsapp-service')
            if not os.path.exists(baileys_path):
                return {"success": False, "message": "Service Baileys non trouvé"}
            
            self.process = subprocess.Popen(
                ['node', 'index.js'],
                cwd=baileys_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.status = "waiting_qr"
            return {"success": True, "message": "Service WhatsApp démarré"}
            
        except Exception as e:
            self.status = "error"
            return {"success": False, "message": f"Erreur: {str(e)}"}
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtenir le statut WhatsApp"""
        # En production, on lirait depuis un fichier partagé ou WebSocket
        # Pour le MVP, on simule
        return {
            "status": self.status,
            "qrCode": self.qr_code,
            "connected": self.connected
        }
    
    async def disconnect(self):
        """Déconnecter WhatsApp"""
        try:
            if self.process:
                self.process.terminate()
                self.process.wait(timeout=10)
            self.status = "disconnected"
            self.connected = False
            self.qr_code = ""
            return {"success": True, "message": "Déconnecté"}
        except Exception as e:
            return {"success": False, "message": f"Erreur: {str(e)}"}

# Instance globale
whatsapp_service = WhatsAppService()
