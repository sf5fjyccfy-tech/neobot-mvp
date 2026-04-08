"""
Subscription API Router
Endpoints for managing subscriptions, trials, and plan upgrades
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Optional
from datetime import datetime

from app.database import get_db
from app.services.subscription_service import SubscriptionService
from app.models import Subscription
from app.dependencies import get_current_user, get_tenant_from_request

router = APIRouter(prefix="/api/tenants/{tenant_id}/subscription", tags=["Subscription"])


@router.post("/trial/start")
async def start_trial(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict:
    """
    Démarrer un essai gratuit de 14 jours pour un tenant

    - **tenant_id**: Tenant ID
    - Returns trial information with dates
    """
    # Verify tenant ownership
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another tenant's subscription"
        )

    result = await SubscriptionService.start_trial(db, tenant_id, trial_days=14)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to start trial")
        )
    
    return result


@router.get("/status")
async def get_subscription_status(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict:
    """
    Get subscription status for a tenant
    
    Returns:
    - plan: Current plan (essential, business, enterprise)
    - is_trial: Whether in trial period
    - days_remaining: Days left in trial (if applicable)
    - status: Subscription status (active, paused, cancelled)
    """
    # Verify tenant ownership
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another tenant's subscription"
        )
    
    subscription = await SubscriptionService.get_subscription(db, tenant_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found. Please start a trial first."
        )
    
    return {
        "tenant_id": tenant_id,
        "plan": subscription.plan,
        "is_trial": subscription.is_trial,
        "status": subscription.status,
        "trial_start_date": subscription.trial_start_date,
        "trial_end_date": subscription.trial_end_date,
        "days_remaining": subscription.days_remaining
    }


@router.get("/trial/check")
async def check_trial(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict:
    """
    Check if trial is still active and get detailed status
    
    Returns:
    - is_trial: Whether in trial
    - is_active: Whether service is active
    - is_expired: Whether trial has expired
    - days_remaining: Days until trial ends
    """
    # Verify tenant ownership
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another tenant's subscription"
        )
    
    return await SubscriptionService.check_trial_status(db, tenant_id)


@router.post("/upgrade")
async def upgrade_from_trial(
    tenant_id: int,
    plan: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict:
    """
    Upgrade from trial to a paid plan
    
    - **tenant_id**: Tenant ID
    - **plan**: Target plan (essential, business, enterprise)
    - Payment would be processed separately (Phase 2)
    """
    # Verify tenant ownership
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another tenant's subscription"
        )
    
    result = await SubscriptionService.upgrade_from_trial(db, tenant_id, plan)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to upgrade")
        )
    
    return result


@router.post("/change-plan")
async def change_plan(
    tenant_id: int,
    plan: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict:
    """
    Change subscription plan (for existing paid subscribers)
    
    - **tenant_id**: Tenant ID
    - **plan**: New plan (essential, business, enterprise)
    - Can upgrade or downgrade at any time
    """
    # Verify tenant ownership
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another tenant's subscription"
        )
    
    result = await SubscriptionService.change_plan(db, tenant_id, plan)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to change plan")
        )
    
    return result


@router.post("/cancel")
async def cancel_subscription(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict:
    """
    Cancel a subscription
    
    - **tenant_id**: Tenant ID
    - Service will stop immediately after cancellation
    - No refunds for remaining balance
    """
    # Verify tenant ownership
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access another tenant's subscription"
        )
    
    result = await SubscriptionService.cancel_subscription(db, tenant_id)
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to cancel subscription")
        )
    
    return result


# ============= ADMIN ENDPOINTS =============

@router.get("/admin/all")
async def get_all_subscriptions(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict:
    """
    [ADMIN ONLY] Get all subscriptions in the system
    
    Returns list of all active subscriptions with stats
    """
    # Verify admin access
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from sqlalchemy import select
    
    stmt = select(Subscription).where(Subscription.status == "active")
    result = await db.execute(stmt)
    subscriptions = result.scalars().all()
    
    return {
        "total_active": len(subscriptions),
        "by_plan": {
            "essential": len([s for s in subscriptions if s.plan == "essential"]),
            "business": len([s for s in subscriptions if s.plan == "business"]),
            "enterprise": len([s for s in subscriptions if s.plan == "enterprise"])
        },
        "trials": len([s for s in subscriptions if s.is_trial]),
        "paid": len([s for s in subscriptions if not s.is_trial])
    }


@router.get("/admin/expiring-trials")
async def get_expiring_trials(
    days_remaining: int = 2,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict:
    """
    [ADMIN ONLY] Get trials expiring soon
    
    - **days_remaining**: Number of days to check ahead
    - Returns list of tenants with trials expiring soon
    """
    # Verify admin access
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    from datetime import timedelta
    from sqlalchemy import select
    
    cutoff_date = datetime.now() + timedelta(days=days_remaining)
    
    stmt = select(Subscription).where(
        (Subscription.is_trial == True) &
        (Subscription.trial_end_date <= cutoff_date)
    )
    result = await db.execute(stmt)
    subscriptions = result.scalars().all()
    
    return {
        "expiring_soon": len(subscriptions),
        "trials": [
            {
                "tenant_id": s.tenant_id,
                "plan": s.plan,
                "trial_end_date": str(s.trial_end_date)
            }
            for s in subscriptions
        ]
    }
