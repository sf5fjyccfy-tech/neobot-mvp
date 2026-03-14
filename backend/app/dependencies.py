"""
Shared dependencies for API endpoints
Handles JWT validation and extracting current user/tenant
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import jwt
from datetime import datetime
import logging
import os
from dotenv import load_dotenv

from app.database import get_db
from app.models import User, Tenant

load_dotenv()
logger = logging.getLogger(__name__)

security = HTTPBearer()

# Get JWT secret from environment
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"


async def get_current_user(
    credentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate JWT token, return current user
    
    Raises HTTPException if token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    return user


async def get_tenant_from_request(
    current_user: User = Depends(get_current_user),
) -> int:
    """
    Extract tenant_id from current user
    """
    return current_user.tenant_id


def verify_tenant_access(
    tenant_id: int,
    current_user: User = Depends(get_current_user)
) -> bool:
    """
    Verify that current user has access to the specified tenant
    """
    if current_user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this tenant"
        )
    return True


async def verify_tenant(
    tenant_id: int,
    db: Session = Depends(get_db)
) -> int:
    """
    Verify that tenant exists in database
    """
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant {tenant_id} not found"
        )
    return tenant_id
