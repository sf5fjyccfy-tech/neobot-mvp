import httpx
import os
from typing import Optional

NOTCHPAY_PUBLIC_KEY = os.getenv("NOTCHPAY_PUBLIC_KEY")
NOTCHPAY_API_URL = "https://api.notchpay.co"

class NotchPayService:
    """Service de paiement NotchPay pour Cameroun"""
    
    async def create_payment(self, amount: int, currency: str, customer_email: str, 
                            customer_phone: str, reference: str) -> dict:
        """
        Créer un lien de paiement NotchPay
        
        Args:
            amount: Montant en FCFA (ex: 20000)
            currency: XAF (franc CFA)
            customer_email: Email client
            customer_phone: Numéro WhatsApp client
            reference: ID unique transaction
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{NOTCHPAY_API_URL}/payments",
                json={
                    "amount": amount,
                    "currency": currency,
                    "email": customer_email,
                    "phone": customer_phone,
                    "reference": reference,
                    "callback": f"https://votre-domaine.com/webhook/notchpay",
                    "description": f"Abonnement NéoBot - {amount} FCFA"
                },
                headers={
                    "Authorization": f"Bearer {NOTCHPAY_PUBLIC_KEY}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    "success": True,
                    "payment_url": data["authorization_url"],
                    "reference": data["reference"]
                }
            else:
                return {
                    "success": False,
                    "error": response.text
                }
    
    async def verify_payment(self, reference: str) -> dict:
        """Vérifier statut paiement"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{NOTCHPAY_API_URL}/payments/{reference}",
                headers={"Authorization": f"Bearer {NOTCHPAY_PUBLIC_KEY}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "status": data["status"],  # pending, complete, failed
                    "amount": data["amount"]
                }
            else:
                return {"success": False, "error": response.text}
