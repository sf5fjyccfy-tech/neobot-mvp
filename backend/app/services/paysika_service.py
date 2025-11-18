"""
Service d'intégration PaySika avec système de commissions
"""
import requests
import json
from typing import Dict, Optional
from sqlalchemy.orm import Session

class PaysikaService:
    def __init__(self, db: Session):
        self.db = db
        self.api_key = "PSK_TEST_XXX"  # À remplacer par ta clé
        self.base_url = "https://api.paysika.com/v1"
        
        # Configuration commissions
        self.commission_rates = {
            "restaurant": 0.03,  # 3%
            "boutique": 0.04,    # 4% 
            "service": 0.05,     # 5%
            "default": 0.035     # 3.5%
        }
    
    def create_payment_link(self, tenant_id: int, amount: float, 
                          customer_phone: str, description: str) -> Dict:
        """Crée un lien de paiement PaySika avec commission"""
        
        # Récupérer le tenant
        from app.models import Tenant
        tenant = self.db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return {"error": "Tenant non trouvé"}
        
        # Calculer la commission
        commission_rate = self.commission_rates.get(
            tenant.business_type, 
            self.commission_rates["default"]
        )
        commission_amount = amount * commission_rate
        net_amount = amount - commission_amount
        
        # Données pour PaySika
        payment_data = {
            "amount": int(amount * 100),  # PaySika attend des centimes
            "currency": "XAF",
            "description": f"{description} - Via NéoBot",
            "customer_phone": customer_phone,
            "callback_url": "https://ton-api.com/paysika/callback",
            "metadata": {
                "tenant_id": tenant_id,
                "tenant_name": tenant.name,
                "commission_rate": commission_rate,
                "commission_amount": commission_amount,
                "net_amount": net_amount,
                "original_amount": amount
            }
        }
        
        # Appel API PaySika (version simulée pour l'instant)
        try:
            # SIMULATION - À remplacer par l'appel réel à PaySika
            payment_response = self._simulate_paysika_call(payment_data)
            
            # Enregistrer la transaction
            self._record_transaction(
                tenant_id=tenant_id,
                amount=amount,
                commission_rate=commission_rate,
                commission_amount=commission_amount,
                payment_reference=payment_response["reference"],
                customer_phone=customer_phone
            )
            
            return {
                "success": True,
                "payment_url": payment_response["payment_url"],
                "reference": payment_response["reference"],
                "amount": amount,
                "commission": f"{commission_rate*100}%",
                "commission_amount": commission_amount,
                "net_amount": net_amount
            }
            
        except Exception as e:
            return {"error": f"Erreur création paiement: {str(e)}"}
    
    def _simulate_paysika_call(self, payment_data: Dict) -> Dict:
        """Simule l'appel à l'API PaySika (à remplacer par le vrai appel)"""
        # En attendant l'intégration réelle, on simule
        return {
            "reference": f"PSK_{payment_data['amount']}_{payment_data['customer_phone'][-6:]}",
            "payment_url": f"https://paysika.com/pay/simulated/{payment_data['amount']}",
            "status": "pending"
        }
    
    def _record_transaction(self, tenant_id: int, amount: float, 
                          commission_rate: float, commission_amount: float,
                          payment_reference: str, customer_phone: str):
        """Enregistre la transaction avec commission"""
        from app.models import Transaction
        from datetime import datetime
        
        transaction = Transaction(
            tenant_id=tenant_id,
            amount=amount,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            net_amount=amount - commission_amount,
            payment_reference=payment_reference,
            customer_phone=customer_phone,
            status="pending",
            created_at=datetime.utcnow()
        )
        
        self.db.add(transaction)
        self.db.commit()
    
    def handle_webhook(self, webhook_data: Dict) -> Dict:
        """Traite les webhooks PaySika pour mettre à jour le statut des paiements"""
        # À implémenter avec les vrais webhooks PaySika
        reference = webhook_data.get("reference")
        status = webhook_data.get("status")
        
        if reference and status:
            from app.models import Transaction
            transaction = self.db.query(Transaction).filter(
                Transaction.payment_reference == reference
            ).first()
            
            if transaction:
                transaction.status = status
                if status == "success":
                    transaction.paid_at = datetime.utcnow()
                self.db.commit()
                
                return {"success": True, "transaction_updated": True}
        
        return {"success": False, "error": "Transaction non trouvée"}
    
    def get_commission_stats(self, tenant_id: int = None) -> Dict:
        """Retourne les statistiques de commissions"""
        from app.models import Transaction
        from sqlalchemy import func
        
        query = self.db.query(Transaction)
        
        if tenant_id:
            query = query.filter(Transaction.tenant_id == tenant_id)
        
        stats = query.with_entities(
            func.count(Transaction.id).label("total_transactions"),
            func.sum(Transaction.amount).label("total_volume"),
            func.sum(Transaction.commission_amount).label("total_commissions"),
            func.avg(Transaction.commission_rate).label("avg_commission_rate")
        ).first()
        
        return {
            "total_transactions": stats.total_transactions or 0,
            "total_volume": float(stats.total_volume or 0),
            "total_commissions": float(stats.total_commissions or 0),
            "average_commission_rate": float(stats.avg_commission_rate or 0)
        }
