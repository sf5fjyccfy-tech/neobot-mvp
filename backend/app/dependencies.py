"""
Shared dependencies for API endpoints
Handles JWT validation and extracting current user/tenant
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
import logging
from dotenv import load_dotenv

from app.database import get_db
from app.models import User, Tenant
from app.services.auth_service import decode_access_token, is_token_revoked

load_dotenv()
logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Valide le JWT bearer, vérifie la blacklist de révocation, retourne l'utilisateur.
    """
    token = credentials.credentials
    
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
        )

    # Vérifier si le token a été révoqué explicitement (logout)
    jti = payload.get("jti")
    if jti and is_token_revoked(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token révoqué — veuillez vous reconnecter",
        )

    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur introuvable",
        )
    
    return user


async def get_tenant_from_request(
    current_user: User = Depends(get_current_user),
) -> int:
    """
    Extract tenant_id from current user
    """
    return current_user.tenant_id


async def get_superadmin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Réservé exclusivement au super-admin (fondateur)."""
    if not getattr(current_user, "is_superadmin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé au super-administrateur",
        )
    return current_user


def verify_tenant_access(
    tenant_id: int,
    current_user: User = Depends(get_current_user)
) -> bool:
    """Superadmin peut accéder à tous les tenants. Client = uniquement le sien."""
    if getattr(current_user, "is_superadmin", False):
        return True
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
