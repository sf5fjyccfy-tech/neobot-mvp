"""
Overage Pricing Service - Calcul et gestion des dépassements
Pricing: 1000 messages = 7000 FCFA
"""
from sqlalchemy.orm import Session
from datetime import datetime
from math import ceil
from app.models import Overage, Tenant, PlanType, PLAN_LIMITS
from app.services.usage_tracking_service import UsageTrackingService
import logging

logger = logging.getLogger(__name__)

class OveragePricingService:
    """Service pour calculer et gérer les frais de dépassement"""
    
    # Pricing constant
    PRICE_PER_1000_MESSAGES = 7000  # FCFA
    
    @staticmethod
    def calculate_overage_price(messages_over: int) -> int:
        """
        Calcule le prix d'un nombre de messages au-delà du quota
        
        Pricing:
        - 1-1000 messages over = 7,000 FCFA
        - 1001-2000 messages over = 14,000 FCFA (2 x 7,000)
        - Etc...
        
        Args:
            messages_over: Nombre de messages dépassant la limite
            
        Returns:
            Coût total en FCFA arrondi à la tranche de 1000
        """
        if messages_over <= 0:
            return 0
        
        # Arrondir à 1000
        tranche = ceil(messages_over / 1000)
        cost = tranche * OveragePricingService.PRICE_PER_1000_MESSAGES
        
        logger.info(f"Overage calculation: {messages_over} messages → {tranche} tranches → {cost} FCFA")
        return cost
    
    @staticmethod
    def get_or_create_overage_record(tenant_id: int, db: Session) -> Overage:
        """
        Récupère ou crée l'enregistrement de dépassement pour le mois courant
        """
        month_year = UsageTrackingService.get_current_month()
        
        overage = db.query(Overage).filter(
            Overage.tenant_id == tenant_id,
            Overage.month_year == month_year
        ).first()
        
        if not overage:
            overage = Overage(
                tenant_id=tenant_id,
                month_year=month_year,
                messages_over=0,
                cost_fcfa=0,
                is_billed=False,
            )
            db.add(overage)
            db.commit()
            db.refresh(overage)
            logger.info(f"✅ Created overage record for tenant {tenant_id}, month {month_year}")
        
        return overage
    
    @staticmethod
    def update_overage_cost(tenant_id: int, db: Session):
        """
        Met à jour le coût de dépassement basé sur l'usage actuel
        Appelé après chaque message pour recalculer les frais
        """
        # Récupérer l'usage actuel
        usage_summary = UsageTrackingService.get_usage_summary(tenant_id, db)
        
        if usage_summary.get("error"):
            logger.warning(f"Cannot update overage for tenant {tenant_id}: {usage_summary['error']}")
            return
        
        overage_messages = usage_summary.get("overage_messages", 0)
        
        # Récupérer l'enregistrement de dépassement
        overage = OveragePricingService.get_or_create_overage_record(tenant_id, db)
        
        # Calculer le nouveau coût
        new_cost = OveragePricingService.calculate_overage_price(overage_messages)
        
        # Mettre à jour
        overage.messages_over = overage_messages
        overage.cost_fcfa = new_cost
        overage.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"📊 Updated overage for tenant {tenant_id}: {overage_messages} msgs over → {new_cost} FCFA")
    
    @staticmethod
    def get_overage_summary(tenant_id: int, db: Session) -> dict:
        """
        Retourne un résumé des frais de dépassement
        """
        # Récupérer l'usage
        usage_summary = UsageTrackingService.get_usage_summary(tenant_id, db)
        
        if usage_summary.get("error"):
            return {"error": usage_summary["error"]}
        
        # Récupérer l'enregistrement de dépassement
        overage = OveragePricingService.get_or_create_overage_record(tenant_id, db)
        
        return {
            "tenant_id": tenant_id,
            "month_year": overage.month_year,
            "usage_percent": usage_summary["percent"],
            "over_limit": usage_summary["over_limit"],
            "overage_messages": usage_summary["overage_messages"],
            "overage_cost_fcfa": overage.cost_fcfa,
            "is_billed": overage.is_billed,
            "billed_at": overage.billed_at,
            "message": (
                f"⚠️  {usage_summary['overage_messages']} messages over limit → {overage.cost_fcfa} FCFA"
                if usage_summary["over_limit"]
                else "✅ Pas de dépassement"
            )
        }
    
    @staticmethod
    def mark_overage_as_billed(tenant_id: int, db: Session):
        """
        Marque un dépassement comme facturé
        Appelé par le système de paiement après paiement réussi
        """
        overage = OveragePricingService.get_or_create_overage_record(tenant_id, db)
        
        overage.is_billed = True
        overage.billed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"✅ Marked overage as billed for tenant {tenant_id}")
    
    @staticmethod
    def get_monthly_overages(db: Session, month_year: str = None) -> list:
        """
        Retourne tous les dépassements pour un mois donné
        Utile pour la facturation et le reporting
        """
        if month_year is None:
            month_year = UsageTrackingService.get_current_month()
        
        overages = db.query(Overage).filter(
            Overage.month_year == month_year,
            Overage.messages_over > 0
        ).all()
        
        return [
            {
                "tenant_id": o.tenant_id,
                "messages_over": o.messages_over,
                "cost_fcfa": o.cost_fcfa,
                "is_billed": o.is_billed,
            }
            for o in overages
        ]
    
    @staticmethod
    def get_unbilled_overages(db: Session) -> list:
        """
        Retourne tous les dépassements non facturés
        Utile pour le système de facturation
        """
        overages = db.query(Overage).filter(
            Overage.is_billed == False,
            Overage.messages_over > 0
        ).all()
        
        total_fcfa = sum(o.cost_fcfa for o in overages)
        
        return {
            "count": len(overages),
            "total_fcfa": total_fcfa,
            "overages": [
                {
                    "tenant_id": o.tenant_id,
                    "month_year": o.month_year,
                    "cost_fcfa": o.cost_fcfa,
                }
                for o in overages
            ]
        }
