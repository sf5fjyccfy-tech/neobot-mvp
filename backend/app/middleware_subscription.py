"""
Subscription Status Middleware
Enforces trial and subscription limitations on protected endpoints
"""

from fastapi import Request, HTTPException, status
from datetime import datetime, timezone
import logging
from typing import List

logger = logging.getLogger(__name__)

# Public endpoints that don't require active subscription
PUBLIC_ENDPOINTS = [
    "/health",
    "/openapi.json",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/me",
    "/docs",
    "/redoc",
]

# Endpoints that require active subscription
PROTECTED_ENDPOINTS = [
    "/api/tenants/",
    "/api/conversations/",
    "/api/messages/",
    "/api/analytics/",
    "/webhook/",
]


async def check_subscription_middleware(request: Request, call_next):
    """
    Middleware to check subscription status and block access if needed
    
    Rules:
    1. If trial expired → block with 402 Payment Required
    2. If subscription cancelled → block with 402
    3. If subscription paused → block with 402
    
    Allows:
    - Authenticated users with active subscription
    - Authenticated users still in trial period
    - Public endpoints (login, register, health)
    """
    
    # Skip checks for public endpoints
    if any(request.url.path.startswith(ep) for ep in PUBLIC_ENDPOINTS):
        return await call_next(request)
    
    # For protected endpoints, check subscription status
    if any(request.url.path.startswith(ep) for ep in PROTECTED_ENDPOINTS):
        try:
            # Get tenant_id from JWT token or header
            auth_header = request.headers.get("authorization", "")
            tenant_id = request.headers.get("x-tenant-id", "")
            
            # If no tenant ID, we'll let the endpoint-level auth handle it
            if not tenant_id and not auth_header:
                return await call_next(request)
            
            # Get database connection
            from app.database import SessionLocal
            from app.services.subscription_service import SubscriptionService
            
            if not tenant_id:
                # Let endpoint extract tenant from JWT
                return await call_next(request)
            
            # Check subscription status
            db = SessionLocal()
            try:
                sub_status = await SubscriptionService.check_trial_status(db, int(tenant_id))
                
                # If subscription is not active
                if not sub_status.get("is_active"):
                    raise HTTPException(
                        status_code=status.HTTP_402_PAYMENT_REQUIRED,
                        detail="Your trial has expired or subscription is inactive. Please upgrade."
                    )
                
                # If trial is expiring soon, warn in response header
                days_left = sub_status.get("days_remaining", 0)
                if 0 < days_left <= 7 and sub_status.get("is_trial"):
                    request.state.warning = f"Trial expires in {days_left} days"
                
            finally:
                db.close()
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            # Don't block access if check fails - let endpoint handle it
            pass
    
    response = await call_next(request)
    
    # Add warning header if trial is expiring soon
    if hasattr(request.state, "warning"):
        response.headers["X-Trial-Warning"] = request.state.warning
    
    return response
