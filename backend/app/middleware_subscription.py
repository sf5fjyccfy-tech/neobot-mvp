"""
Subscription Status Middleware
Vérifie que le tenant a un abonnement actif (trial valide ou subscription active)
avant de traiter les requêtes sur les endpoints protégés.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Routes qui ne nécessitent PAS de subscription active
PUBLIC_PREFIXES = (
    "/health",
    "/api/health",
    "/openapi.json",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/refresh",
    "/docs",
    "/redoc",
    "/webhook/",       # webhooks entrants (Baileys, Korapay)
)

# Routes protégées par la subscription
SUBSCRIPTION_REQUIRED_PREFIXES = (
    "/api/tenants/",
    "/api/analytics/",
)


class SubscriptionMiddleware(BaseHTTPMiddleware):
    """
    Middleware léger : extrait tenant_id depuis JWT, vérifie subscription en DB.
    Si trial expiré ou subscription inactive → 402 Payment Required.
    Ne bloque jamais en cas d'erreur inattendue (let endpoint handle it).
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Bypass sur les routes publiques
        if any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        # Bypass si la route n'est pas dans le périmètre subscription
        if not any(path.startswith(p) for p in SUBSCRIPTION_REQUIRED_PREFIXES):
            return await call_next(request)

        # Extraire le tenant_id depuis le JWT
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return await call_next(request)  # Pas de token → 401 géré par l'endpoint

        token = auth_header[7:]
        tenant_id = self._extract_tenant_id(token)
        if tenant_id is None:
            return await call_next(request)  # Token invalide → 401 géré par l'endpoint

        # Vérifier la subscription — requête sync directe (session non-async)
        try:
            from app.database import SessionLocal
            from app.models import Subscription
            from datetime import datetime

            db = SessionLocal()
            try:
                sub = db.execute(
                    __import__('sqlalchemy').select(Subscription).where(
                        Subscription.tenant_id == tenant_id
                    )
                ).scalar_one_or_none()
            finally:
                db.close()

            if sub is None:
                # Pas d'abonnement → bloquer
                return JSONResponse(
                    status_code=402,
                    content={"detail": "Aucun abonnement actif. Veuillez activer votre compte."},
                )

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

            if not is_active:
                return JSONResponse(
                    status_code=402,
                    content={"detail": "Votre période d'essai est expirée ou votre abonnement est inactif. Veuillez upgrader."},
                )

            # Avertissement trial bientôt expiré (header non bloquant)
            if sub.is_trial and sub.trial_end_date:
                today = datetime.now().date()
                trial_end = sub.trial_end_date
                if hasattr(trial_end, 'date'):
                    trial_end = trial_end.date()
                elif isinstance(trial_end, str):
                    trial_end = datetime.fromisoformat(trial_end).date()
                days_left = (trial_end - today).days
                if 0 < days_left <= 7:
                    request.state.trial_warning = f"Trial expire dans {days_left} jour(s)"

        except Exception as e:
            logger.error(f"SubscriptionMiddleware erreur critique: {e}")
            # Fail-secure : si la DB est down pendant la vérification d'abonnement,
            # on retourne 503 plutôt que de laisser passer (fail-open serait dangereux)
            return JSONResponse(
                status_code=503,
                content={"detail": "Service temporairement indisponible. Veuillez réessayer dans quelques instants."},
            )

        response = await call_next(request)

        if hasattr(request.state, "trial_warning"):
            response.headers["X-Trial-Warning"] = request.state.trial_warning

        return response

    @staticmethod
    def _extract_tenant_id(token: str) -> int | None:
        """Décode le JWT et retourne le tenant_id, ou None si invalide."""
        try:
            from app.services.auth_service import decode_access_token
            payload = decode_access_token(token)
            if payload:
                return payload.get("tenant_id")
        except Exception:
            pass
        return None
