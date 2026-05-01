"""
Subscription Status Middleware
Vérifie que le tenant a un abonnement actif (trial valide ou subscription active)
avant de traiter les requêtes sur les endpoints protégés.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from datetime import datetime
from sqlalchemy import select
import logging

logger = logging.getLogger(__name__)

PUBLIC_PREFIXES = (
    "/health",
    "/api/health",
    "/openapi.json",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/docs",
    "/redoc",
    "/webhook/",
)

SUBSCRIPTION_REQUIRED_PREFIXES = (
    "/api/tenants/",
    "/api/analytics/",
    "/api/agents/",
    "/api/conversations/",
    "/api/contacts/",
    "/api/messages/",
    "/api/whatsapp/",
    "/api/neopay/payment-links",
)


class SubscriptionMiddleware(BaseHTTPMiddleware):
    """
    Middleware léger : extrait tenant_id depuis JWT, vérifie subscription en DB.
    Si trial expiré ou subscription inactive → 402 Payment Required.
    En cas d'erreur inattendue → fail-open (laisser passer, l'endpoint gère).
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        if not any(path.startswith(p) for p in SUBSCRIPTION_REQUIRED_PREFIXES):
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)

        token = auth_header[7:]
        tenant_id = self._extract_tenant_id(token)
        if tenant_id is None:
            return await call_next(request)

        # Fast-path : tenant 1 (NéoBot admin) bypass toujours
        if tenant_id == 1:
            return await call_next(request)

        # Vérifier subscription — toujours fail-open en cas d'erreur
        block_reason: str | None = None
        trial_warning: str | None = None

        try:
            from app.database import SessionLocal
            from app.models import Subscription, User

            db = SessionLocal()
            try:
                # Superadmin bypass
                is_sa = self._is_superadmin_db(token, db)
                if is_sa:
                    return await call_next(request)

                sub = db.execute(
                    select(Subscription).where(Subscription.tenant_id == tenant_id)
                ).scalar_one_or_none()

                if sub is None:
                    block_reason = "Aucun abonnement actif. Veuillez activer votre compte."
                else:
                    is_active = sub.status == "active"
                    if sub.is_trial and sub.trial_end_date:
                        today = datetime.now().date()
                        trial_end = sub.trial_end_date
                        if hasattr(trial_end, 'date'):
                            trial_end = trial_end.date()
                        elif isinstance(trial_end, str):
                            trial_end = datetime.fromisoformat(trial_end).date()
                        if today > trial_end:
                            is_active = False
                        elif is_active:
                            days_left = (trial_end - today).days
                            if 0 < days_left <= 7:
                                trial_warning = f"Trial expire dans {days_left} jour(s)"

                    if not is_active:
                        block_reason = "Votre période d'essai est expirée ou votre abonnement est inactif."
            finally:
                db.close()

        except Exception as e:
            # Fail-open : en cas d'erreur DB transitoire, laisser passer
            # L'endpoint gérera ses propres erreurs DB
            logger.warning(f"SubscriptionMiddleware: erreur non-critique, fail-open: {e}")
            return await call_next(request)

        if block_reason:
            return JSONResponse(
                status_code=402,
                content={"detail": block_reason},
            )

        response = await call_next(request)
        if trial_warning:
            response.headers["X-Trial-Warning"] = trial_warning
        return response

    @staticmethod
    def _extract_tenant_id(token: str) -> int | None:
        try:
            from app.services.auth_service import decode_access_token
            payload = decode_access_token(token)
            if payload:
                return payload.get("tenant_id")
        except Exception:
            pass
        return None

    @staticmethod
    def _is_superadmin_db(token: str, db_session) -> bool:
        try:
            from app.services.auth_service import decode_access_token
            from app.models import User
            payload = decode_access_token(token)
            if not payload:
                return False
            user_id = payload.get("user_id")
            if not user_id:
                return False
            user = db_session.query(User).filter(User.id == user_id).first()
            return bool(user and user.is_superadmin)
        except Exception:
            return False
