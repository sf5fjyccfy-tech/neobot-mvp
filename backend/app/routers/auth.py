"""
Routers d'authentification - Login et Register
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel, EmailStr

from app.database import get_db
from app.models import User, Tenant, PlanType, Subscription
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_password_hash,
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ========== SCHEMAS ==========
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    tenant_name: str
    business_type: str


def _derive_tenant_phone(email: str) -> str:
    """Generate a deterministic placeholder phone for tenants created via API register."""
    local_part = email.split("@", 1)[0]
    safe_local = "".join(ch for ch in local_part if ch.isalnum())
    return f"unknown-{safe_local[:20]}"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    tenant_id: int

# ========== ENDPOINTS ==========

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authentifie un utilisateur et retourne un token JWT
    """
    user = authenticate_user(db, request.email, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Créer le token
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "tenant_id": user.tenant_id}
    )
    
    # Mettre à jour last_login
    user.last_login = __import__('datetime').datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "tenant_id": user.tenant_id,
    }

@router.post("/register", response_model=TokenResponse)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Enregistre un nouvel utilisateur et retourne un token JWT
    Auto-starts 7-day trial with Basique plan
    """
    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé",
        )
    
    # Créer le tenant
    new_tenant = Tenant(
        name=request.tenant_name,
        email=request.email,
        phone=_derive_tenant_phone(request.email),
        business_type=request.business_type or "autre",
        plan=PlanType.BASIQUE,
        messages_used=0,
        messages_limit=2000,  # BASIQUE = 2000 messages
    )
    db.add(new_tenant)
    db.flush()  # Pour obtenir l'ID du tenant
    
    # Créer l'utilisateur
    hashed_password = get_password_hash(request.password)
    new_user = User(
        tenant_id=new_tenant.id,
        email=request.email,
        hashed_password=hashed_password,
        full_name=request.full_name,
        is_active=True,
    )
    db.add(new_user)
    
    # AUTO-START 7-DAY TRIAL
    trial_start = datetime.now(timezone.utc).date()
    trial_end = trial_start + timedelta(days=7)
    
    subscription = Subscription(
        tenant_id=new_tenant.id,
        plan="basique",
        status="active",
        is_trial=True,
        trial_start_date=trial_start,
        trial_end_date=trial_end,
        subscription_start_date=datetime.now(timezone.utc),
        next_billing_date=trial_end + timedelta(days=1),
        auto_renew=False  # Manual upgrade after trial
    )
    db.add(subscription)
    
    db.commit()
    
    # Créer le token
    access_token = create_access_token(
        data={"sub": new_user.email, "user_id": new_user.id, "tenant_id": new_user.tenant_id}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "tenant_id": new_user.tenant_id,
    }

@router.get("/me")
async def get_current_user_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les infos de l'utilisateur actuel
    Nécessite un token valide dans Authorization header
    """
    tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()

    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "tenant_id": current_user.tenant_id,
        "tenant_name": tenant.name if tenant else None,
        "tenant_plan": tenant.plan.value if tenant else None,
    }
