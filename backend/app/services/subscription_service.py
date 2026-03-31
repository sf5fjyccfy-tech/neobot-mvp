"""
Subscription Service
Manages subscription lifecycle, trial periods, and plan upgrades
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class SubscriptionData:
    """Data class for subscription info"""
    def __init__(
        self,
        tenant_id: int,
        plan: str,
        is_trial: bool,
        trial_start_date: str,
        trial_end_date: str,
        status: str,
        days_remaining: Optional[int] = None
    ):
        self.tenant_id = tenant_id
        self.plan = plan
        self.is_trial = is_trial
        self.trial_start_date = trial_start_date
        self.trial_end_date = trial_end_date
        self.status = status
        self.days_remaining = days_remaining


class SubscriptionService:
    """Service for managing subscriptions and trials"""

    @staticmethod
    async def start_trial(
        db: AsyncSession,
        tenant_id: int,
        trial_days: int = 14
    ) -> Dict:
        """
        Start a new trial for a tenant
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            trial_days: Number of days for trial (default 14)
            
        Returns:
            Trial information dict
        """
        from app.models import Subscription
        
        try:
            # Check if subscription already exists
            stmt = select(Subscription).where(Subscription.tenant_id == tenant_id)
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.warning(f"Subscription already exists for tenant {tenant_id}")
                return {
                    "success": False,
                    "error": "Tenant already has a subscription"
                }
            
            # Calculate trial dates
            trial_start = datetime.now().date()
            trial_end = trial_start + timedelta(days=trial_days)
            
            # Create new subscription with trial
            subscription = Subscription(
                tenant_id=tenant_id,
                plan="essential",  # Default plan for new trials
                status="active",
                is_trial=True,
                trial_start_date=trial_start,
                trial_end_date=trial_end,
                subscription_start_date=datetime.now(),
                next_billing_date=trial_end + timedelta(days=1),
                auto_renew=False  # Manual upgrade required after trial
            )
            
            db.add(subscription)
            await db.commit()
            
            logger.info(f"Trial started for tenant {tenant_id}, ends {trial_end}")
            
            return {
                "success": True,
                "tenant_id": tenant_id,
                "plan": "essential",
                "trial_start_date": trial_start.isoformat(),
                "trial_end_date": trial_end.isoformat(),
                "days_remaining": trial_days
            }
            
        except Exception as e:
            logger.error(f"Error starting trial for tenant {tenant_id}: {str(e)}")
            await db.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    async def get_subscription(
        db: AsyncSession,
        tenant_id: int
    ) -> Optional[SubscriptionData]:
        """
        Get subscription info for a tenant
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            
        Returns:
            SubscriptionData object or None
        """
        from app.models import Subscription
        
        try:
            stmt = select(Subscription).where(Subscription.tenant_id == tenant_id)
            result = await db.execute(stmt)
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return None
            
            # Calculate days remaining if in trial
            days_remaining = None
            if subscription.is_trial:
                today = datetime.now().date()
                trial_end = subscription.trial_end_date
                if isinstance(trial_end, str):
                    trial_end = datetime.fromisoformat(trial_end).date()
                days_remaining = (trial_end - today).days
            
            return SubscriptionData(
                tenant_id=subscription.tenant_id,
                plan=subscription.plan,
                is_trial=subscription.is_trial,
                trial_start_date=str(subscription.trial_start_date),
                trial_end_date=str(subscription.trial_end_date),
                status=subscription.status,
                days_remaining=days_remaining
            )
            
        except Exception as e:
            logger.error(f"Error getting subscription for tenant {tenant_id}: {str(e)}")
            return None

    @staticmethod
    async def check_trial_status(
        db: AsyncSession,
        tenant_id: int
    ) -> Dict:
        """
        Check if trial is still active and get status
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            
        Returns:
            Trial status dict with days remaining, is_active, etc
        """
        subscription = await SubscriptionService.get_subscription(db, tenant_id)
        
        if not subscription:
            return {
                "has_subscription": False,
                "is_trial": False,
                "is_active": False
            }
        
        if not subscription.is_trial:
            return {
                "has_subscription": True,
                "is_trial": False,
                "plan": subscription.plan,
                "status": subscription.status,
                "is_active": subscription.status == "active"
            }
        
        # Check trial expiration
        today = datetime.now().date()
        trial_end = datetime.fromisoformat(subscription.trial_end_date).date()
        is_expired = today > trial_end
        days_remaining = max(0, (trial_end - today).days)
        
        return {
            "has_subscription": True,
            "is_trial": True,
            "plan": subscription.plan,
            "status": subscription.status,
            "is_active": not is_expired and subscription.status == "active",
            "is_expired": is_expired,
            "days_remaining": days_remaining,
            "trial_start_date": subscription.trial_start_date,
            "trial_end_date": subscription.trial_end_date
        }

    @staticmethod
    async def upgrade_from_trial(
        db: AsyncSession,
        tenant_id: int,
        plan: str
    ) -> Dict:
        """
        Upgrade from trial to paid plan
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            plan: New plan (essential)
            
        Returns:
            Upgrade result dict
        """
        from app.models import Subscription
        
        if plan not in ["essential", "business", "enterprise"]:
            return {
                "success": False,
                "error": f"Invalid plan: {plan}"
            }
        
        try:
            stmt = select(Subscription).where(Subscription.tenant_id == tenant_id)
            result = await db.execute(stmt)
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return {
                    "success": False,
                    "error": "No subscription found"
                }
            
            # Update subscription
            subscription.plan = plan
            subscription.is_trial = False
            subscription.status = "active"
            subscription.subscription_start_date = datetime.now()
            subscription.next_billing_date = datetime.now().date() + timedelta(days=30)
            subscription.auto_renew = True
            
            await db.commit()
            
            logger.info(f"Tenant {tenant_id} upgraded from trial to {plan} plan")
            
            return {
                "success": True,
                "tenant_id": tenant_id,
                "plan": plan,
                "message": f"Successfully upgraded to {plan} plan"
            }
            
        except Exception as e:
            logger.error(f"Error upgrading tenant {tenant_id}: {str(e)}")
            await db.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    async def change_plan(
        db: AsyncSession,
        tenant_id: int,
        new_plan: str
    ) -> Dict:
        """
        Change subscription plan
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            new_plan: New plan (essential)
            
        Returns:
            Plan change result dict
        """
        from app.models import Subscription
        
        if new_plan not in ["essential", "business", "enterprise"]:
            return {
                "success": False,
                "error": f"Invalid plan: {new_plan}"
            }
        
        try:
            stmt = select(Subscription).where(Subscription.tenant_id == tenant_id)
            result = await db.execute(stmt)
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return {
                    "success": False,
                    "error": "No subscription found"
                }
            
            old_plan = subscription.plan
            subscription.plan = new_plan
            await db.commit()
            
            logger.info(f"Tenant {tenant_id} changed plan from {old_plan} to {new_plan}")
            
            return {
                "success": True,
                "tenant_id": tenant_id,
                "old_plan": old_plan,
                "new_plan": new_plan,
                "message": f"Plan changed from {old_plan} to {new_plan}"
            }
            
        except Exception as e:
            logger.error(f"Error changing plan for tenant {tenant_id}: {str(e)}")
            await db.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    async def cancel_subscription(
        db: AsyncSession,
        tenant_id: int
    ) -> Dict:
        """
        Cancel a subscription
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            
        Returns:
            Cancellation result dict
        """
        from app.models import Subscription
        
        try:
            stmt = select(Subscription).where(Subscription.tenant_id == tenant_id)
            result = await db.execute(stmt)
            subscription = result.scalar_one_or_none()
            
            if not subscription:
                return {
                    "success": False,
                    "error": "No subscription found"
                }
            
            subscription.status = "cancelled"
            subscription.cancelled_at = datetime.now()
            subscription.auto_renew = False
            
            await db.commit()
            
            logger.info(f"Subscription cancelled for tenant {tenant_id}")
            
            return {
                "success": True,
                "tenant_id": tenant_id,
                "message": "Subscription cancelled"
            }
            
        except Exception as e:
            logger.error(f"Error cancelling subscription for tenant {tenant_id}: {str(e)}")
            await db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
