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
    "/api/v1/webhooks/",
    "/webhooks/",
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
    Si trial expiré et pas d'abonnement actif → 402 Payment Required.
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

        block_reason: str | None = None
        trial_warning: str | None = None

        try:
            from app.database import SessionLocal
            from app.models import Subscription, Tenant, User

            db = SessionLocal()
            try:
                # Superadmin bypass
                is_sa = self._is_superadmin_db(token, db)
                if is_sa:
                    return await call_next(request)

                # Charger le tenant pour vérifier subscription_expires_at (source de vérité admin)
                tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
                now = datetime.utcnow()

                # Si l'admin a activé un abonnement payant et qu'il est encore valide → toujours laisser passer
                if tenant and tenant.subscription_expires_at:
                    sub_exp = tenant.subscription_expires_at
                    # Normaliser : si timezone-aware, convertir en naive UTC
                    if hasattr(sub_exp, 'utcoffset') and sub_exp.utcoffset() is not None:
                        from datetime import timezone as _tz
                        sub_exp = sub_exp.astimezone(_tz.utc).replace(tzinfo=None)
                    if sub_exp > now:
                        # Abonnement payant actif → bypass complet
                        return await call_next(request)

                # Vérifier la table Subscription (trial ou abonnement)
                try:
                    sub = db.execute(
                        select(Subscription).where(Subscription.tenant_id == tenant_id)
                    ).scalar_one_or_none()
                except Exception:
                    # Plusieurs subscriptions → prendre la plus récente
                    from sqlalchemy import desc
                    sub = db.query(Subscription).filter(
                        Subscription.tenant_id == tenant_id
                    ).order_by(desc(Subscription.id)).first()

                if sub is None:
                    # Pas de subscription du tout → créer un essai de 14j automatiquement
                    if tenant:
                        from datetime import timedelta
                        trial_end = now + timedelta(days=14)
                        new_sub = Subscription(
                            tenant_id=tenant_id,
                            plan=tenant.plan.value if hasattr(tenant.plan, 'value') else 'BASIC',
                            status="active",
                            is_trial=True,
                            trial_start_date=now,
                            trial_end_date=trial_end,
                            subscription_start_date=now,
                            next_billing_date=trial_end,
                            auto_renew=False,
                        )
                        db.add(new_sub)
                        try:
                            db.commit()
                        except Exception:
                            db.rollback()
                        # Laisser passer — le compte vient d'être activé
                        return await call_next(request)
                    else:
                        block_reason = "Aucun abonnement actif. Veuillez activer votre compte."
                else:
                    is_active = sub.status == "active"

                    if sub.is_trial and sub.trial_end_date:
                        today = now.date()
                        trial_end = sub.trial_end_date
                        if hasattr(trial_end, 'date'):
                            trial_end = trial_end.date()
                        elif isinstance(trial_end, str):
                            trial_end = datetime.fromisoformat(trial_end).date()
                        # Normaliser si timezone-aware
                        if hasattr(trial_end, 'utcoffset'):
                            trial_end = trial_end.date()

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
            logger.warning(f"SubscriptionMiddleware: erreur non-critique, fail-open: {e}")
            return await call_next(request)

        if block_reason:
            logger.warning(f"SubscriptionMiddleware: 402 bloqué — tenant_id={tenant_id} path={path} reason={block_reason}")
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
