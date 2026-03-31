"""
test_security_headers.py — Vérifie les headers HTTP de sécurité.

Le SecurityHeadersMiddleware doit ajouter ces headers sur chaque réponse :
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy
- Content-Security-Policy (frame-ancestors)

test_ai_cache.py intégré ici pour garder les tests de service groupés.
"""
import pytest


class TestSecurityHeaders:

    def _headers_from(self, client, path="/api/health"):
        return client.get(path).headers

    def test_x_frame_options_deny(self, client):
        h = self._headers_from(client)
        assert h.get("x-frame-options", "").upper() == "DENY"

    def test_x_content_type_options_nosniff(self, client):
        h = self._headers_from(client)
        assert h.get("x-content-type-options", "").lower() == "nosniff"

    def test_xss_protection_header(self, client):
        h = self._headers_from(client)
        assert "1" in h.get("x-xss-protection", "")

    def test_referrer_policy(self, client):
        h = self._headers_from(client)
        assert "strict-origin" in h.get("referrer-policy", "")

    def test_permissions_policy_present(self, client):
        h = self._headers_from(client)
        assert "permissions-policy" in h

    def test_csp_frame_ancestors(self, client):
        h = self._headers_from(client)
        csp = h.get("content-security-policy", "")
        assert "frame-ancestors" in csp

    def test_auth_endpoints_no_cache(self, client):
        """Les réponses /api/auth/* doivent avoir Cache-Control: no-store."""
        resp = client.post("/api/auth/login", json={"email": "x@x.com", "password": "x"})
        cc = resp.headers.get("cache-control", "")
        assert "no-store" in cc

    def test_headers_present_on_error_responses(self, client):
        """Les headers sécurité doivent être présents même sur les 404/401."""
        h = client.get("/api/route_qui_nexiste_pas").headers
        assert h.get("x-frame-options", "").upper() == "DENY"

    def test_headers_present_on_401(self, client):
        h = client.get("/api/auth/me").headers
        assert h.get("x-content-type-options", "").lower() == "nosniff"


# ════════════════════════════════════════════════════════════════
# SERVICE IA — cache TTL
# ════════════════════════════════════════════════════════════════

class TestAIServiceCache:

    def test_cache_hit_returns_same_value(self):
        """_cache_set puis _cache_get retourne la même valeur."""
        from app.services.ai_service import _cache_set, _cache_get, _cache_key
        key = _cache_key("system_prompt", "bonjour")
        _cache_set(key, "Bonjour !")
        assert _cache_get(key) == "Bonjour !"

    def test_cache_miss_returns_none(self):
        from app.services.ai_service import _cache_get, _cache_key
        key = _cache_key("system", "un_message_never_seen_xyz")
        assert _cache_get(key) is None

    def test_cache_expiry(self):
        """Une entrée dont l'expiration est passée doit être ignorée."""
        import time
        from app.services.ai_service import _AI_CACHE, _cache_key, _cache_get
        key = _cache_key("sys", "expired_msg")
        # Injecter directement avec une expiration dans le passé
        _AI_CACHE[key] = ("cached_val", time.monotonic() - 1)
        assert _cache_get(key) is None

    def test_cache_key_differs_on_different_inputs(self):
        from app.services.ai_service import _cache_key
        k1 = _cache_key("sys1", "msg")
        k2 = _cache_key("sys2", "msg")
        k3 = _cache_key("sys1", "msg2")
        assert k1 != k2
        assert k1 != k3

    def test_cache_eviction_at_max_size(self):
        """Au-delà de _CACHE_MAX_SIZE, les entrées les plus anciennes sont éjectées."""
        from app.services.ai_service import _AI_CACHE, _cache_set, _cache_key, _CACHE_MAX_SIZE
        # Remplir jusqu'au max
        for i in range(_CACHE_MAX_SIZE):
            _cache_set(_cache_key(f"s{i}", "m"), f"v{i}")
        first_key = _cache_key("s0", "m")
        # Ajouter une entrée de plus → la première doit disparaître
        _cache_set(_cache_key("overflow", "m"), "overflow_val")
        assert first_key not in _AI_CACHE
        assert len(_AI_CACHE) <= _CACHE_MAX_SIZE


# ════════════════════════════════════════════════════════════════
# AUTH SERVICE — JTI + revocation
# ════════════════════════════════════════════════════════════════

class TestAuthServiceTokens:

    def test_access_token_contains_jti(self):
        import json, base64
        from app.services.auth_service import create_access_token
        token = create_access_token({"sub": "test@test.com", "user_id": 1, "tenant_id": 1})
        parts = token.split(".")
        # Padding base64
        payload = json.loads(base64.b64decode(parts[1] + "==").decode())
        assert "jti" in payload
        assert len(payload["jti"]) == 36  # UUID4 format

    def test_two_tokens_have_different_jtis(self):
        import json, base64
        from app.services.auth_service import create_access_token
        data = {"sub": "test@test.com", "user_id": 1, "tenant_id": 1}
        t1 = create_access_token(data)
        t2 = create_access_token(data)
        p1 = json.loads(base64.b64decode(t1.split(".")[1] + "=="))
        p2 = json.loads(base64.b64decode(t2.split(".")[1] + "=="))
        assert p1["jti"] != p2["jti"]

    def test_revoke_token_marks_jti_as_revoked(self, db):
        from datetime import datetime, timezone, timedelta
        from app.services.auth_service import create_access_token, revoke_token, is_token_revoked
        import json, base64
        token = create_access_token({"sub": "x@x.com", "user_id": 1, "tenant_id": 1})
        parts = token.split(".")
        payload = json.loads(base64.b64decode(parts[1] + "=="))
        jti = payload["jti"]
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        assert not is_token_revoked(db, jti)
        revoke_token(db, jti, user_id=1, expires_at=exp)
        assert is_token_revoked(db, jti)

    def test_password_validation_accepts_strong_password(self):
        from app.routers.auth import _validate_password_strength
        # Ne doit pas lever d'exception
        _validate_password_strength("StrongP@ss1")

    def test_password_validation_rejects_all_weakness_types(self):
        from app.routers.auth import _validate_password_strength
        from fastapi import HTTPException
        weak_cases = [
            ("short1!", "8 caractères"),            # trop court
            ("nouppercase1!", "majuscule"),          # pas de majuscule
            ("NoDigit!!!", "chiffre"),               # pas de chiffre
            ("NoSpecial1", "spécial"),               # pas de spécial
        ]
        for pwd, expected_detail in weak_cases:
            with pytest.raises(HTTPException) as exc_info:
                _validate_password_strength(pwd)
            assert expected_detail in exc_info.value.detail, (
                f"Attendu '{expected_detail}' dans le détail pour '{pwd}', "
                f"reçu: '{exc_info.value.detail}'"
            )
