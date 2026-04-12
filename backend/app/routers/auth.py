"""
Routers d'authentification - Login et Register
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import timedelta, datetime, timezone
from pydantic import BaseModel, EmailStr
from typing import Optional
import os, io, base64
import re

import pyotp
import qrcode
import logging

from app.database import get_db
from app.models import User, Tenant, PlanType, Subscription, AgentType, PLAN_LIMITS, LoginAttempt, RefreshToken
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    revoke_token,
    decode_access_token,
)
from app.services.agent_service import AgentService
from app.dependencies import get_current_user
from app.limiter import limiter

import secrets
import hashlib

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# ── Constantes anti-brute-force ───────────────────────────────────────────────
_MAX_FAILED_ATTEMPTS = 10
_LOCKOUT_WINDOW_MINUTES = 5
_LOCKOUT_DURATION_MINUTES = 15
_REFRESH_TOKEN_EXPIRE_DAYS = 30

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

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    # access_token est dans le Bearer header — on l'extrait dans le endpoint
    pass


def _derive_tenant_phone(email: str) -> str:
    """Generate a deterministic placeholder phone for tenants created via API register."""
    local_part = email.split("@", 1)[0]
    safe_local = "".join(ch for ch in local_part if ch.isalnum())
    return f"unknown-{safe_local[:20]}"


def _validate_password_strength(password: str) -> None:
    """Vérifie la complexité du mot de passe. Min 8 caractères."""
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Mot de passe : minimum 8 caractères requis",
        )


def _check_brute_force(db: Session, ip: str) -> None:
    """Bloque l'IP si elle a échoué ≥10 fois dans les 5 dernières minutes."""
    window_start = datetime.now(timezone.utc) - timedelta(minutes=_LOCKOUT_WINDOW_MINUTES)
    recent_fails = (
        db.query(func.count(LoginAttempt.id))
        .filter(
            LoginAttempt.ip_address == ip,
            LoginAttempt.success == False,  # noqa: E712
            LoginAttempt.attempted_at >= window_start,
        )
        .scalar()
    )
    if recent_fails >= _MAX_FAILED_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Trop de tentatives de connexion échouées. "
                f"Réessayez dans {_LOCKOUT_DURATION_MINUTES} minutes."
            ),
            headers={"Retry-After": str(_LOCKOUT_DURATION_MINUTES * 60)},
        )


def _log_login_attempt(db: Session, ip: str, email: str, success: bool) -> None:
    """Enregistre une tentative de connexion (succès ou échec)."""
    attempt = LoginAttempt(ip_address=ip, email=email, success=success)
    db.add(attempt)
    try:
        db.commit()
    except Exception:
        db.rollback()


def _purge_old_attempts(db: Session) -> None:
    """Supprime les tentatives > 24h pour éviter la croissance infinie de la table."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    db.query(LoginAttempt).filter(LoginAttempt.attempted_at < cutoff).delete()
    try:
        db.commit()
    except Exception:
        db.rollback()


def _issue_refresh_token(db: Session, user_id: int) -> str:
    """Émet un refresh token sécurisé (rotation complète — révoque les anciens)."""
    # Révoquer tous les refresh tokens existants non expirés pour cet utilisateur
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False,  # noqa: E712
    ).update({"revoked": True, "revoked_at": datetime.now(timezone.utc)})

    raw = secrets.token_hex(32)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(rt)
    db.commit()
    return raw


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: int
    tenant_id: int
    is_superadmin: bool = False

# ========== ENDPOINTS ==========

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authentifie un utilisateur et retourne un token JWT + refresh token.
    Anti-brute force : bloque apres 10 echecs en 5 min.
    """
    ip = request.client.host if request.client else "unknown"

    # Anti-brute-force : verif AVANT authenticate_user
    _check_brute_force(db, ip)

    user = authenticate_user(db, body.email, body.password)

    if not user:
        _log_login_attempt(db, ip, body.email, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Bloquer les tenants suspendus AVANT d'emettre un token
    tenant_check = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if tenant_check and tenant_check.is_suspended:
        _log_login_attempt(db, ip, body.email, success=False)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Compte suspendu. Raison : {tenant_check.suspension_reason or 'Contactez le support'}",
        )

    # Login reussi
    _log_login_attempt(db, ip, body.email, success=True)
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "tenant_id": user.tenant_id}
    )
    refresh_tok = _issue_refresh_token(db, user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_tok,
        "token_type": "bearer",
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "is_superadmin": bool(getattr(user, "is_superadmin", False)),
    }


@router.post("/register", response_model=TokenResponse)
@limiter.limit("3/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Enregistre un nouvel utilisateur et retourne un token JWT
    Auto-starts 14-day trial with Essential plan
    """
    # Validation de la complexité du mot de passe
    _validate_password_strength(body.password)
    # Vérifier si l'email existe déjà
    existing_user = db.query(User).filter(User.email == body.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé",
        )
    
    # Créer le tenant
    new_tenant = Tenant(
        name=body.tenant_name,
        email=body.email,
        phone=_derive_tenant_phone(body.email),
        business_type=body.business_type or "autre",
        plan=PlanType.BASIC,
        messages_used=0,
        messages_limit=PLAN_LIMITS[PlanType.BASIC]["whatsapp_messages"],  # source: PLAN_LIMITS
    )
    db.add(new_tenant)
    db.flush()  # Pour obtenir l'ID du tenant
    
    # Créer l'utilisateur
    hashed_password = get_password_hash(body.password)
    new_user = User(
        tenant_id=new_tenant.id,
        email=body.email,
        hashed_password=hashed_password,
        full_name=body.full_name,
        is_active=True,
    )
    db.add(new_user)
    
    # AUTO-START 14-DAY TRIAL
    trial_start = datetime.now(timezone.utc).date()
    trial_end = trial_start + timedelta(days=14)

    subscription = Subscription(
        tenant_id=new_tenant.id,
        plan="BASIC",  # Uniformisé avec neopay_service.py — was: "essential"
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

    # Créer le token JWT + refresh token
    access_token = create_access_token(
        data={"sub": new_user.email, "user_id": new_user.id, "tenant_id": new_user.tenant_id}
    )
    refresh_tok = _issue_refresh_token(db, new_user.id)

    # Email de bienvenue — en background pour ne pas bloquer la réponse
    from app.services.email_service import send_welcome_email, send_confirmation_email
    background_tasks.add_task(
        send_welcome_email,
        to_email=new_user.email,
        user_name=new_user.full_name or new_user.email.split("@")[0],
        tenant_name=new_tenant.name,
        trial_end_date=trial_end,
    )

    # Email de confirmation — génère un token SHA-256 à usage unique
    # Wrappé en try/except : si la colonne n'existe pas encore en prod (migration en retard),
    # l'inscription réussit quand même — email de confirmation absent, mais compte créé.
    try:
        raw_verification_token = secrets.token_urlsafe(32)
        new_user.email_verification_token = hashlib.sha256(raw_verification_token.encode()).hexdigest()
        db.commit()
        BACKEND_URL = os.getenv("BACKEND_URL", "https://api.neobot-ai.com")
        verification_link = f"{BACKEND_URL}/api/auth/verify-email?token={raw_verification_token}"
        background_tasks.add_task(
            send_confirmation_email,
            to_email=new_user.email,
            confirmation_link=verification_link,
        )
    except Exception as _verif_exc:
        import logging as _log
        _log.getLogger(__name__).warning(
            "Email verification token non sauvegardé (migration DB en attente ?) : %s", _verif_exc
        )
        db.rollback()

    return {
        "access_token": access_token,
        "refresh_token": refresh_tok,
        "token_type": "bearer",
        "user_id": new_user.id,
        "tenant_id": new_user.tenant_id,
    }

# ======================== REFRESH / LOGOUT ========================

@router.post("/refresh")
async def refresh_token_endpoint(
    body: RefreshRequest,
    db: Session = Depends(get_db),
):
    """
    Échange un refresh token valide contre un nouveau access token + refresh token (rotation).
    Le refresh token précédent est immédiatement révoqué.
    """
    token_hash = hashlib.sha256(body.refresh_token.encode()).hexdigest()
    now = datetime.now(timezone.utc)

    stored = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
            RefreshToken.expires_at > now,
        )
        .first()
    )
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide ou expiré — veuillez vous reconnecter",
        )

    user = db.query(User).filter(User.id == stored.user_id, User.is_active == True).first()  # noqa: E712
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable")

    # Rotation complète : le refresh token courant est révoqué dans _issue_refresh_token
    new_access = create_access_token(
        data={"sub": user.email, "user_id": user.id, "tenant_id": user.tenant_id}
    )
    new_refresh = _issue_refresh_token(db, user.id)  # révoque l'ancien en interne

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Révoque l'access token courant (via JTI) et tous les refresh tokens actifs.
    Le client doit supprimer ses tokens locaux.
    """
    auth_header = request.headers.get("Authorization", "")
    raw_token = auth_header.removeprefix("Bearer ").strip()

    if raw_token:
        payload = decode_access_token(raw_token)
        if payload:
            jti = payload.get("jti")
            exp_ts = payload.get("exp")
            if jti and exp_ts:
                expires = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
                try:
                    revoke_token(db, jti, current_user.id, expires)
                except Exception:
                    pass  # Déjà révoqué ou expiré — pas bloquant

    # Révoquer tous les refresh tokens actifs de l'utilisateur
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.revoked == False,  # noqa: E712
    ).update({"revoked": True, "revoked_at": datetime.now(timezone.utc)})
    db.commit()

    return {"message": "Déconnexion réussie"}


# ======================== RESET MOT DE PASSE ========================

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@router.post("/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Envoie un email de reset si l'adresse existe.
    Retourne TOUJOURS le même message pour éviter l'énumération d'emails.
    """
    _GENERIC_OK = {"message": "Si cet email est associé à un compte, vous recevrez un lien de réinitialisation dans quelques minutes."}

    user = db.query(User).filter(User.email == body.email.lower().strip()).first()
    if not user or not user.is_active:
        return _GENERIC_OK  # Pas d'information leakage

    # Générer un token sécurisé — stocke le SHA-256 en DB, envoie le clair par email
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    user.reset_token = token_hash
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    reset_link = f"{os.getenv('FRONTEND_URL', 'http://localhost:3002')}/reset-password?token={raw_token}"

    from app.services.email_service import send_password_reset_email
    background_tasks.add_task(send_password_reset_email, user.email, reset_link)

    return _GENERIC_OK


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Réinitialise le mot de passe si le token est valide et non expiré.
    Le token est à usage unique et effacé immédiatement après utilisation.
    """
    _validate_password_strength(request.new_password)

    token_hash = hashlib.sha256(request.token.encode()).hexdigest()

    user = db.query(User).filter(User.reset_token == token_hash).first()

    if not user or not user.reset_token_expires_at:
        raise HTTPException(status_code=400, detail="Lien invalide ou expiré")

    if datetime.now(timezone.utc) > user.reset_token_expires_at.replace(tzinfo=timezone.utc):
        # Nettoyer le token périmé
        user.reset_token = None
        user.reset_token_expires_at = None
        db.commit()
        raise HTTPException(status_code=400, detail="Lien invalide ou expiré")

    # Tout est bon — on met à jour le mot de passe et on invalide le token
    user.hashed_password = get_password_hash(request.new_password)
    user.reset_token = None
    user.reset_token_expires_at = None
    db.commit()

    return {"message": "Mot de passe réinitialisé avec succès. Vous pouvez maintenant vous connecter."}


# ======================== VÉRIFICATION EMAIL ========================

@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """
    Valide le token de vérification email envoyé à l'inscription.
    Le token est à usage unique et effacé après utilisation.
    Redirige vers le frontend avec un paramètre de statut.
    """
    from fastapi.responses import RedirectResponse

    FRONTEND_URL = os.getenv("FRONTEND_URL", "https://neobot-ai.com")

    if not token or len(token) > 256:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?email_verified=invalid")

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user = db.query(User).filter(User.email_verification_token == token_hash).first()

    if not user:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?email_verified=invalid")

    user.email_verified = True
    user.email_verification_token = None
    db.commit()

    return RedirectResponse(url=f"{FRONTEND_URL}/login?email_verified=success")


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
        "is_superadmin": bool(getattr(current_user, "is_superadmin", False)),
        "email_verified": bool(getattr(current_user, "email_verified", True)),
        "tenant_id": current_user.tenant_id,
        "tenant_name": tenant.name if tenant else None,
        "tenant_plan": tenant.get_plan_config().get("name", tenant.plan.value) if tenant else None,
    }


@router.post("/resend-verification")
@limiter.limit("3/hour")  # évite le flood d'emails
async def resend_verification(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Renvoie l'email de vérification si le compte n'est pas encore confirmé."""
    if current_user.email_verified:
        return {"message": "Email déjà vérifié."}

    raw_token = secrets.token_urlsafe(32)
    current_user.email_verification_token = hashlib.sha256(raw_token.encode()).hexdigest()
    db.commit()

    BACKEND_URL = os.getenv("BACKEND_URL", "https://api.neobot-ai.com")
    verification_link = f"{BACKEND_URL}/api/auth/verify-email?token={raw_token}"

    from app.services.email_service import send_confirmation_email
    try:
        await send_confirmation_email(
            to_email=current_user.email,
            confirmation_link=verification_link,
        )
    except Exception as exc:
        logger.warning("Renvoi email vérification échoué : %s", exc)
        raise HTTPException(status_code=502, detail="Erreur lors de l'envoi de l'email. Réessayez.")

    return {"message": "Email de vérification renvoyé."}


# ======================== ADMIN 2FA ========================
# Endpoint séparé du login normal — réduit la surface d'attaque
# Toute tentative d'entrée par cet endpoint sans TOTP valide est impossible

_SUPERADMIN_ALLOWLIST = {
    e.strip().lower()
    for e in os.getenv("SUPERADMIN_EMAILS", "").split(",")
    if e.strip()
}

_AUTH_FAIL = lambda: HTTPException(status_code=401, detail="Email ou mot de passe incorrect")


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminVerifyRequest(BaseModel):
    challenge_token: str
    totp_code: str


class TotpConfirmRequest(BaseModel):
    setup_token: str
    totp_code: str


@router.post("/admin-login")
@limiter.limit("5/minute")
async def admin_login(
    request: Request,
    body: AdminLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Step 1 — Login superadmin.
    Retourne challenge_token (TOTP déjà actif) ou setup_token (premier setup).
    N'expose jamais pourquoi ça échoue (pas de fuite d'info).
    """
    # Vérification allowlist (env SUPERADMIN_EMAILS)
    if _SUPERADMIN_ALLOWLIST and body.email.lower() not in _SUPERADMIN_ALLOWLIST:
        raise _AUTH_FAIL()

    user = authenticate_user(db, body.email, body.password)
    if not user or not user.is_superadmin or not user.is_active:
        raise _AUTH_FAIL()

    from app.services.auth_service import decode_access_token  # noqa: avoid circular at module level

    if user.totp_enabled:
        # TOTP configuré → challenge token (5 min, accès restreint)
        token = create_access_token(
            data={"purpose": "totp_challenge", "user_id": user.id},
            expires_delta=timedelta(minutes=5),
        )
        return {"status": "totp_required", "challenge_token": token}
    else:
        # Première connexion → setup token (10 min)
        token = create_access_token(
            data={"purpose": "totp_setup", "user_id": user.id},
            expires_delta=timedelta(minutes=10),
        )
        return {"status": "setup_required", "setup_token": token}


@router.post("/admin-login/verify")
@limiter.limit("5/minute")
async def admin_verify_totp(
    request: Request,
    body: AdminVerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Step 2 — Vérifie le code TOTP et retourne le JWT complet (session 1h).
    """
    from app.services.auth_service import decode_access_token

    payload = decode_access_token(body.challenge_token)
    if not payload or payload.get("purpose") != "totp_challenge":
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    user = db.query(User).filter(
        User.id == payload.get("user_id"),
        User.is_superadmin == True,  # noqa: E712
        User.is_active == True,
    ).first()
    if not user or not user.totp_enabled or not user.totp_secret:
        raise HTTPException(status_code=401, detail="Configuration 2FA invalide")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(body.totp_code.strip(), valid_window=1):
        raise HTTPException(status_code=401, detail="Code incorrect ou expiré")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "tenant_id": user.tenant_id},
        expires_delta=timedelta(hours=1),  # Session admin = 1h max
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "is_superadmin": True,
    }


@router.get("/admin/totp-setup")
async def admin_totp_get_qr(
    setup_token: str,
    db: Session = Depends(get_db),
):
    """
    Génère un nouveau secret TOTP + QR code PNG (base64).
    Appelé une seule fois lors du premier setup.
    """
    from app.services.auth_service import decode_access_token

    payload = decode_access_token(setup_token)
    if not payload or payload.get("purpose") != "totp_setup":
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    user = db.query(User).filter(
        User.id == payload.get("user_id"),
        User.is_superadmin == True,  # noqa: E712
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="Utilisateur non trouvé")

    secret = pyotp.random_base32()
    user.totp_secret = secret  # stocké mais totp_enabled=False jusqu'à confirmation
    db.commit()

    uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.email,
        issuer_name="NéoBot Admin",
    )
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    return {
        "qr_data_url": qr_data_url,
        "secret": secret,  # Affiché une seule fois — backup manuel obligatoire
    }


@router.post("/admin/totp-confirm")
async def admin_totp_confirm(
    request: TotpConfirmRequest,
    db: Session = Depends(get_db),
):
    """
    Confirme le code TOTP de setup → active le 2FA et retourne le JWT complet.
    """
    from app.services.auth_service import decode_access_token

    payload = decode_access_token(request.setup_token)
    if not payload or payload.get("purpose") != "totp_setup":
        raise HTTPException(status_code=401, detail="Token invalide ou expiré")

    user = db.query(User).filter(
        User.id == payload.get("user_id"),
        User.is_superadmin == True,  # noqa: E712
    ).first()
    if not user or not user.totp_secret:
        raise HTTPException(status_code=401, detail="Setup non initialisé")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(request.totp_code.strip(), valid_window=1):
        raise HTTPException(status_code=401, detail="Code incorrect")

    user.totp_enabled = True
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id, "tenant_id": user.tenant_id},
        expires_delta=timedelta(hours=1),
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "is_superadmin": True,
    }
