"""
Service paiement NotchPay - Mode TEST
"""

import httpx
import os
from typing import Dict
from datetime import datetime

class MultiPayService:
    def __init__(self):
        self.notchpay_key = os.getenv("NOTCHPAY_PUBLIC_KEY", "pk_test_demo_key")
        self.notchpay_url = "https://api.notchpay.co"
        
        # Mode simulation si pas de clé
        self.simulation_mode = not self.notchpay_key or self.notchpay_key == "your_notchpay_public_key_here"
    
    def detect_best_provider(self, country_code: str, phone_prefix: str) -> str:
        return "notchpay"
    
    async def create_payment(self, 
                            amount: int,
                            customer_email: str,
                            customer_phone: str,
                            customer_name: str,
                            plan_name: str,
                            tenant_id: int,
                            country_code: str = "CM") -> Dict:
        """Créer paiement NotchPay ou simuler"""
        
        reference = f"neo_{tenant_id}_{plan_name}_{int(datetime.now().timestamp())}"
        
        # MODE SIMULATION (pour tests sans clé API)
        if self.simulation_mode:
            print("⚠️ MODE SIMULATION: Pas de clé NotchPay configurée")
            return {
                "success": True,
                "payment_url": f"https://notchpay.co/demo/pay/{reference}",  # URL fictive
                "reference": reference,
                "provider": "notchpay",
                "methods": ["orange_money", "mtn_money", "express_union"],
                "expires_at": datetime.now().timestamp() + 3600,
                "is_simulation": True
            }
        
        # MODE RÉEL (avec vraie clé)
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.notchpay_url}/payments",
                    json={
                        "amount": amount,
                        "currency": "XAF",
                        "email": customer_email,
                        "phone": customer_phone,
                        "reference": reference,
                        "callback": f"{os.getenv('BASE_URL', 'http://localhost:8000')}/webhook/notchpay",
                        "description": f"Abonnement NéoBot {plan_name.title()} - {customer_name}"
                    },
                    headers={
                        "Authorization": f"Bearer {self.notchpay_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 201:
                    data = response.json()
                    return {
                        "success": True,
                        "payment_url": data["authorization_url"],
                        "reference": reference,
                        "provider": "notchpay",
                        "methods": ["orange_money", "mtn_money", "express_union"],
                        "expires_at": datetime.now().timestamp() + 3600,
                        "is_simulation": False
                    }
                else:
                    print(f"❌ NotchPay error: {response.text}")
                    return {
                        "success": False,
                        "error": f"Erreur NotchPay: {response.status_code}",
                        "provider": "notchpay"
                    }
        
        except Exception as e:
            print(f"🔥 Exception NotchPay: {e}")
            return {"success": False, "error": str(e), "provider": "notchpay"}
    
    async def verify_payment(self, reference: str, provider: str) -> Dict:
        """Vérifier statut paiement"""
        
        # En mode simulation, toujours retourner pending
        if self.simulation_mode:
            return {
                "success": True,
                "status": "pending",
                "amount": 20000,
                "provider": "notchpay",
                "is_simulation": True
            }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.notchpay_url}/payments/{reference}",
                    headers={"Authorization": f"Bearer {self.notchpay_key}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "status": data["status"],
                        "amount": data["amount"],
                        "provider": "notchpay"
                    }
                else:
                    return {"success": False, "error": response.text}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
