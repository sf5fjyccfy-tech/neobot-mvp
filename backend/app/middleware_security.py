"""
Security Headers Middleware — NeoBot
Injecte les headers HTTP de sécurité sur toutes les réponses.
HSTS, X-Frame-Options, CSP, X-Content-Type-Options, etc.
"""
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injecte les headers de sécurité OWASP sur chaque réponse.
    N'impacte pas les performances — O(1) par requête.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # ✅ PRESERVE CORS headers ajoutés par CORSMiddleware
        cors_headers = {k: v for k, v in response.headers.items() if k.lower().startswith('access-control')}

        # ── Anti-clickjacking ──────────────────────────────────────────────────
        response.headers["X-Frame-Options"] = "DENY"

        # ── Anti-MIME sniffing ─────────────────────────────────────────────────
        response.headers["X-Content-Type-Options"] = "nosniff"

        # ── XSS filter (navigateurs anciens) ──────────────────────────────────
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # ── Referrer leak control ──────────────────────────────────────────────
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # ── HSTS — HTTPS forcé 1 an, sous-domaines inclus ─────────────────────
        # Ne s'active QU'en production (dev = localhost HTTP sinon boom)
        if os.getenv("APP_ENV", "development") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # ── Permissions-Policy — désactive les APIs non utilisées ─────────────
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), "
            "usb=(), bluetooth=(), accelerometer=(), gyroscope=()"
        )

        # ── Content-Security-Policy ────────────────────────────────────────────
        # Note : Next.js gère le CSP côté front. Ici c'est le backend API.
        # L'API ne sert pas de HTML/JS — on peut être strict.
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "frame-ancestors 'none'"
        )

        # ── Cache control sur les endpoints auth ──────────────────────────────
        if request.url.path.startswith("/api/auth/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"

        # ✅ RESTORE CORS headers (sinon CORSMiddleware ne sert à rien)
        response.headers.update(cors_headers)

        return response
