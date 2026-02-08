from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm # Rétablissement de l'import
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Tenant, PlanType
from app.services.auth_service import verify_password, create_access_token

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class UserLogin(BaseModel): # Modèle Pydantic laissé pour /register
    username: str
    password: str

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    tenant_name: str
    business_type: Optional[str] = "autre"

# Helper function 
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

@router.post("/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user_data.email)
    if db_user:
        raise HTTPException(status_code=400, detail="L\'e-mail est déjà enregistré.")

    # 1. Créer le Tenant
    db_tenant = Tenant(
        name=user_data.tenant_name,
        email=user_data.email, 
        business_type=user_data.business_type,
        phone="À_DEFINIR" 
    )
    db_tenant.activate_trial()
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)

    # 2. Créer l\'utilisateur principal (admin)
    from app.services.auth_service import get_password_hash
    hashed_password = get_password_hash(user_data.password)

    db_user = User(
        tenant_id=db_tenant.id,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_superuser=True if user_data.email == "tim@neobot.ai" else False 
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return {"message": "Utilisateur et Tenant créés avec succès.", "tenant_id": db_tenant.id}

@router.post("/token")
# Rétablissement du format de formulaire standard
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_email(db, form_data.username) 
    if not user or not verify_password(form_data.password, user.hashed_password): 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Créer le token
    access_token_expires = timedelta(minutes=60*24)
    access_token = create_access_token(
        data={"sub": user.email, "tenant_id": user.tenant_id, "user_id": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "tenant_id": user.tenant_id}
