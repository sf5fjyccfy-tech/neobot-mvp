"""
Usage Tracking Service - Suivi de l'utilisation mensuelle
"""
from sqlalchemy.orm import Session
from datetime import datetime
from app.models import UsageTracking, Tenant, PlanType, PLAN_LIMITS
import logging

logger = logging.getLogger(__name__)

class UsageTrackingService:
    """Service pour tracker et gérer l'utilisation des messages"""
    
    @staticmethod
    def get_current_month() -> str:
        """Retourne le mois courant au format YYYY-MM"""
        now = datetime.utcnow()
        return f"{now.year:04d}-{now.month:02d}"
    
    @staticmethod
    def get_or_create_monthly_tracking(tenant_id: int, db: Session) -> UsageTracking:
        """
        Récupère ou crée l'enregistrement de suivi pour le mois courant
        """
        month_year = UsageTrackingService.get_current_month()
        
        tracking = db.query(UsageTracking).filter(
            UsageTracking.tenant_id == tenant_id,
            UsageTracking.month_year == month_year
        ).first()
        
        if not tracking:
            tracking = UsageTracking(
                tenant_id=tenant_id,
                month_year=month_year,
                whatsapp_messages_used=0,
                other_platform_messages_used=0,
            )
            db.add(tracking)
            db.commit()
            db.refresh(tracking)
            logger.info(f"✅ Created monthly tracking for tenant {tenant_id}, month {month_year}")
        
        return tracking
    
    @staticmethod
    def increment_whatsapp_usage(tenant_id: int, count: int, db: Session):
        """
        Incrémente l'usage WhatsApp d'un tenant
        
        Args:
            tenant_id: ID du tenant
            count: Nombre de messages à ajouter (généralement 1 pour message user + 1 pour réponse AI)
            db: Session de base de données
        """
        tracking = UsageTrackingService.get_or_create_monthly_tracking(tenant_id, db)
        tracking.whatsapp_messages_used += count
        tracking.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"📊 Tenant {tenant_id}: WhatsApp usage +{count}, total: {tracking.whatsapp_messages_used}")
    
    @staticmethod
    def get_usage_summary(tenant_id: int, db: Session) -> dict:
        """
        Retourne un résumé de l'usage du mois courant
        
        Returns:
            {
                "tenant_id": 1,
                "plan": "Pro",
                "plan_limit": 40000,
                "whatsapp_used": 12345,
                "other_used": 0,
                "total_used": 12345,
                "remaining": 27655,
                "percent": 31,
                "over_limit": False,
                "overage_messages": 0
            }
        """
        # Récupérer le tenant
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return {"error": "Tenant not found"}
        
        # Récupérer l'usage du mois
        tracking = UsageTrackingService.get_or_create_monthly_tracking(tenant_id, db)
        
        # Récupérer la limite du plan
        plan_config = PLAN_LIMITS.get(tenant.plan, PLAN_LIMITS[PlanType.BASIC])
        plan_limit = plan_config["whatsapp_messages"]
        
        # Calculer le résumé
        total_used = tracking.whatsapp_messages_used + tracking.other_platform_messages_used
        
        # Gérer les limites illimitées (-1)
        if plan_limit == -1:  # Illimité
            remaining = -1
            percent = 0
            overage = 0
            over_limit = False
        else:
            remaining = max(0, plan_limit - total_used)
            percent = int((total_used / plan_limit) * 100) if plan_limit > 0 else 0
            overage = max(0, total_used - plan_limit)
            over_limit = total_used > plan_limit
        
        return {
            "tenant_id": tenant_id,
            "plan": plan_config["name"],
            "plan_limit": plan_limit,
            "whatsapp_used": tracking.whatsapp_messages_used,
            "other_used": tracking.other_platform_messages_used,
            "total_used": total_used,
            "remaining": remaining,
            "percent": percent,
            "over_limit": over_limit,
            "overage_messages": overage,
        }
    
    @staticmethod
    def check_quota_exceeded(tenant_id: int, db: Session) -> bool:
        """
        Vérifie si le quota du tenant est dépassé
        
        Returns:
            True si usage > limit, False sinon
        """
        summary = UsageTrackingService.get_usage_summary(tenant_id, db)
        return summary.get("over_limit", False)
    
    @staticmethod
    def get_usage_history(tenant_id: int, months: int = 12, db: Session = None) -> list:
        """
        Retourne l'historique de l'usage sur les N derniers mois
        """
        if db is None:
            return []
        
        tracking_list = db.query(UsageTracking).filter(
            UsageTracking.tenant_id == tenant_id
        ).order_by(UsageTracking.month_year.desc()).limit(months).all()
        
        return [
            {
                "month_year": t.month_year,
                "whatsapp_messages": t.whatsapp_messages_used,
                "other_messages": t.other_platform_messages_used,
                "total": t.whatsapp_messages_used + t.other_platform_messages_used,
            }
            for t in tracking_list
        ]
