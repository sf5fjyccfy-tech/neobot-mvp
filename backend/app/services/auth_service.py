"""Authentication helpers for password hashing and JWT token lifecycle."""

from datetime import datetime, timedelta, timezone
from typing import Any
import os
import secrets
import uuid

from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.models import User, RevokedToken
from app.utils.security import verify_password, get_password_hash as hash_password

_jwt_secret_env = os.getenv("JWT_SECRET", "")
if not _jwt_secret_env:
    import logging as _logging
    import sys as _sys
    _logging.getLogger(__name__).critical(
        "SECURITE CRITIQUE : JWT_SECRET n'est pas défini dans les variables d'environnement. "
        "Utilisez une clé forte en production. Démarrage refusé."
    )
    # Refus de démarrage en production. Si tu es en dev, définis JWT_SECRET dans .env.
    _sys.exit(1)
SECRET_KEY = _jwt_secret_env
ALGORITHM = "HS256"
# 60 min par défaut — le refresh token (30j) assure la persistance de session.
# 7 jours était trop long : un token volé restait valide une semaine sans révocation possible.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))  # 1h par défaut


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate a user by email/password and return the user if valid."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token with unique JTI for blacklisting."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    # JTI unique pour pouvoir révoquer un token précis sans invalider tous les autres
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decode a JWT access token; return payload or None if invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def is_token_revoked(db: Session, jti: str) -> bool:
    """Vérifie si un JTI est dans la blacklist (token révoqué via logout)."""
    return db.query(RevokedToken).filter(RevokedToken.jti == jti).first() is not None


def revoke_token(db: Session, jti: str, user_id: int, expires_at: datetime) -> None:
    """Ajoute un JTI à la blacklist. Appelé au logout."""
    entry = RevokedToken(jti=jti, user_id=user_id, expires_at=expires_at)
    db.add(entry)
    db.commit()


def purge_expired_revoked_tokens(db: Session) -> int:
    """Supprime les tokens révoqués dont le JWT a déjà expiré (inutiles en blacklist)."""
    count = db.query(RevokedToken).filter(
        RevokedToken.expires_at < datetime.now(timezone.utc)
    ).delete()
    db.commit()
    return count


def get_password_hash(password: str) -> str:
    """Hash plaintext password using app security settings."""
    return hash_password(password)
