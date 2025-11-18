from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import requests

router = APIRouter()

class PaymentRequest(BaseModel):
    plan: str
    amount: int
    email: str
    business_name: str

class PendingClient(Base):
    __tablename__ = "pending_clients"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    business_name = Column(String(255), nullable=False)
    plan = Column(String(50), nullable=False)
    status = Column(String(50), default="pending_payment")
    created_at = Column(DateTime, default=datetime.utcnow)

@router.post("/api/create-payment")
async def create_payment(payment: PaymentRequest, db: Session = Depends(get_db)):
    """Crée un paiement PaySika et prépare l'activation"""
    
    # 1. Pré-enregistrer le client
    pending_client = PendingClient(
        email=payment.email,
        business_name=payment.business_name,
        plan=payment.plan,
        status="pending_payment"
    )
    db.add(pending_client)
    db.commit()
    db.refresh(pending_client)
    
    # 2. Créer le lien PaySika (simulation - à adapter avec ton compte)
    paysika_url = await create_paysika_payment_link(
        amount=payment.amount,
        client_email=payment.email,
        description=f"NéoBot {payment.plan}",
        callback_url=f"https://ton-site.com/payment-success?client_id={pending_client.id}"
    )
    
    return {
        "payment_url": paysika_url,
        "client_id": pending_client.id,
        "status": "payment_link_created"
    }

async def create_paysika_payment_link(amount: int, client_email: str, description: str, callback_url: str):
    """Crée un lien de paiement PaySika"""
    # À ADAPTER avec les vraies informations de ton compte PaySika
    # Pour l'instant, on simule
    
    # Dans ton dashboard PaySika, tu auras un lien fixe comme :
    # https://pay.paysika.com/merchant/TON_ID/payment/20000
    # On adapte le montant dynamiquement
    
    base_url = "https://pay.paysika.com/merchant/TON_ID_MARCHAND"
    
    # Pour l'instant, on retourne une URL simulée
    # Tu devras remplacer TON_ID_MARCHAND par ton vrai ID PaySika
    return f"{base_url}/payment/{amount}?email={client_email}&description={description}&callback={callback_url}"

@router.get("/payment-success")
async def payment_success(client_id: int, db: Session = Depends(get_db)):
    """Appelé quand PaySika redirige après paiement réussi"""
    
    # 1. Trouver le client
    client = db.query(PendingClient).filter(PendingClient.id == client_id).first()
    if not client:
        raise HTTPException(404, "Client non trouvé")
    
    # 2. Activer le compte (créer un vrai tenant)
    from app.models import Tenant
    tenant = Tenant(
        name=client.business_name,
        email=client.email,
        phone="",  # Le client ajoutera plus tard
        business_type="autre",
        plan="basique"
    )
    tenant.activate_trial()
    db.add(tenant)
    
    # 3. Marquer le paiement comme traité
    client.status = "activated"
    db.commit()
    
    # 4. Rediriger vers la page de bienvenue
    return {
        "status": "success",
        "message": "Votre compte a été activé avec succès !",
        "redirect_url": f"/welcome?tenant_id={tenant.id}"
    }
