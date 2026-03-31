"""
Service Tenant ultra-simple - Utilise uniquement les colonnes existantes
"""
import sys
sys.path.append('/home/tim/neobot-mvp/backend')

from sqlalchemy.orm import Session
from app.models import Tenant

class TenantService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_tenant_by_phone(self, phone: str) -> Tenant:
        """Trouver un tenant par son numéro de téléphone (colonne existante)"""
        # Nettoyer le numéro pour la comparaison
        clean_phone = self._clean_phone(phone)
        
        # Chercher exactement d'abord
        tenant = self.db.query(Tenant).filter(Tenant.phone == clean_phone).first()
        
        # Fallback: chercher avec format international
        if not tenant and clean_phone.startswith('237'):
            international_phone = '+' + clean_phone
            tenant = self.db.query(Tenant).filter(Tenant.phone == international_phone).first()
        
        # Fallback: chercher sans le +
        if not tenant and clean_phone.startswith('+'):
            without_plus = clean_phone[1:]
            tenant = self.db.query(Tenant).filter(Tenant.phone == without_plus).first()
            
        return tenant
    
    def get_all_tenants(self):
        """Récupérer tous les tenants"""
        return self.db.query(Tenant).all()
    
    def _clean_phone(self, phone: str) -> str:
        """Nettoyer le numéro de téléphone"""
        if not phone:
            return ""
        # Garder seulement les chiffres et le +
        return ''.join(c for c in phone if c.isdigit() or c == '+')
    
    def create_simple_tenant(self, name: str, email: str, phone: str, business_type: str = "autre"):
        """Créer un nouveau tenant simple"""
        tenant = Tenant(
            name=name,
            email=email,
            phone=phone,
            business_type=business_type,
            plan="essential"
        )
        
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        
        return tenant
