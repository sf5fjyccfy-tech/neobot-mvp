"""
test_auth.py — Tests du système d'authentification.

Couvre :
- Register : validation complexité mot de passe, doublon email
- Login : succès, mauvais mdp, refresh + logout token
- Brute-force : lockout IP après 10 échecs en 5 min
- JWT blacklist : token révoqué refusé après logout
- Refresh token : rotation, expiration, replay attack
- Routes protégées : 401 sans token
"""
import hashlib
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from tests.conftest import _create_tenant_user, _get_token


# ════════════════════════════════════════════════════════════════
# REGISTER
# ════════════════════════════════════════════════════════════════

class TestRegister:

    def test_register_success_returns_tokens(self, client):
        resp = client.post("/api/auth/register", json={
            "full_name": "Alice",
            "email": "alice@test.com",
            "password": "Secure1!",
            "tenant_name": "AliceBiz",
            "business_type": "service",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_weak_password_too_short(self, client):
        resp = client.post("/api/auth/register", json={
            "full_name": "Bob",
            "email": "bob@test.com",
            "password": "abc",
            "tenant_name": "BobBiz",
            "business_type": "service",
        })
        assert resp.status_code == 422
        assert "8 caractères" in resp.json()["error"]

    def test_register_weak_password_no_uppercase(self, client):
        resp = client.post("/api/auth/register", json={
            "full_name": "Bob",
            "email": "bob@test.com",
            "password": "nouppercase1!",
            "tenant_name": "BobBiz",
            "business_type": "service",
        })
        assert resp.status_code == 422
        assert "majuscule" in resp.json()["error"]

    def test_register_weak_password_no_digit(self, client):
        resp = client.post("/api/auth/register", json={
            "full_name": "Bob", "email": "bob@test.com",
            "password": "NoDigit!!!",
            "tenant_name": "BobBiz", "business_type": "service",
        })
        assert resp.status_code == 422
        assert "chiffre" in resp.json()["error"]

    def test_register_weak_password_no_special(self, client):
        resp = client.post("/api/auth/register", json={
            "full_name": "Bob", "email": "bob@test.com",
            "password": "NoSpecial1",
            "tenant_name": "BobBiz", "business_type": "service",
        })
        assert resp.status_code == 422
        assert "spécial" in resp.json()["error"]

    def test_register_duplicate_email(self, client):
        payload = {
            "full_name": "Carol", "email": "carol@test.com",
            "password": "Secure1!", "tenant_name": "CarolBiz", "business_type": "service",
        }
        client.post("/api/auth/register", json=payload)
        resp = client.post("/api/auth/register", json=payload)
        assert resp.status_code == 400
        assert "déjà utilisé" in resp.json()["error"]


# ════════════════════════════════════════════════════════════════
# LOGIN
# ════════════════════════════════════════════════════════════════

class TestLogin:

    def test_login_success_returns_tokens(self, client, regular_user):
        resp = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "Secure1!",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user_id"] == regular_user[1].id
        assert data["tenant_id"] == regular_user[0].id

    def test_login_wrong_password(self, client, regular_user):
        resp = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "WrongPass1!",
        })
        assert resp.status_code == 401
        assert "WWW-Authenticate" in resp.headers

    def test_login_unknown_email(self, client):
        resp = client.post("/api/auth/login", json={
            "email": "nobody@ghost.com",
            "password": "Secure1!",
        })
        assert resp.status_code == 401

    def test_login_suspended_tenant(self, client, db):
        from app.models import Tenant
        _create_tenant_user(db, "susp@test.com", "Secure1!", "SuspBiz")
        tenant = db.query(Tenant).filter(Tenant.email == "susp@test.com").first()
        tenant.is_suspended = True
        tenant.suspension_reason = "Fraude détectée"
        db.commit()

        resp = client.post("/api/auth/login", json={
            "email": "susp@test.com",
            "password": "Secure1!",
        })
        assert resp.status_code == 403
        assert "suspendu" in resp.json()["error"].lower()


# ════════════════════════════════════════════════════════════════
# BRUTE FORCE
# ════════════════════════════════════════════════════════════════

class TestBruteForce:

    def test_brute_force_lockout_after_10_fails(self, client, regular_user):
        """10 échecs consécutifs → 429 sur la 11e tentative.

        On teste le mécanisme applicatif (LoginAttempt en DB), pas le rate
        limiter réseau (slowapi). On reset slowapi entre les rounds pour éviter
        le conflit avec sa limite de 5/minute.
        """
        from app.main import app as _app

        def _reset_slowapi():
            inner = getattr(getattr(_app.state, "limiter", None), "_limiter", None)
            if inner:
                getattr(inner, "storage", None) and inner.storage.reset()

        # 10 tentatives échouées — en 2 rounds pour contourner la limite réseau
        for i in range(5):
            r = client.post("/api/auth/login", json={
                "email": "user@test.com",
                "password": f"WrongPass{i}!",
            })
            assert r.status_code == 401, f"Tentative {i+1}: attendu 401, reçu {r.status_code}"

        _reset_slowapi()  # Reset réseau — les LoginAttempt DB restent intact

        for i in range(5, 10):
            r = client.post("/api/auth/login", json={
                "email": "user@test.com",
                "password": f"WrongPass{i}!",
            })
            assert r.status_code == 401, f"Tentative {i+1}: attendu 401, reçu {r.status_code}"

        _reset_slowapi()  # Reset réseau pour la 11e tentative

        # 11e : lockout applicatif
        r = client.post("/api/auth/login", json={
            "email": "user@test.com",
            "password": "WrongPassFinal!",
        })
        assert r.status_code == 429
        assert "Retry-After" in r.headers
        detail = r.json()["error"]
        assert "tentatives" in detail.lower()

    def test_successful_login_logs_attempt(self, client, db, regular_user):
        """Un login réussi crée une entrée success=True en DB."""
        from app.models import LoginAttempt
        client.post("/api/auth/login", json={
            "email": "user@test.com", "password": "Secure1!",
        })
        attempt = db.query(LoginAttempt).filter(
            LoginAttempt.email == "user@test.com",
            LoginAttempt.success == True,  # noqa: E712
        ).first()
        assert attempt is not None

    def test_failed_login_logs_attempt(self, client, db, regular_user):
        """Un login raté crée une entrée success=False en DB."""
        from app.models import LoginAttempt
        client.post("/api/auth/login", json={
            "email": "user@test.com", "password": "Wrong1!",
        })
        attempt = db.query(LoginAttempt).filter(
            LoginAttempt.email == "user@test.com",
            LoginAttempt.success == False,  # noqa: E712
        ).first()
        assert attempt is not None


# ════════════════════════════════════════════════════════════════
# REFRESH TOKEN
# ════════════════════════════════════════════════════════════════

class TestRefreshToken:

    def test_refresh_returns_new_tokens(self, client, regular_user):
        login = client.post("/api/auth/login", json={
            "email": "user@test.com", "password": "Secure1!",
        }).json()
        old_refresh = login["refresh_token"]

        resp = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["refresh_token"] != old_refresh   # rotation — nouveau token

    def test_refresh_old_token_invalid_after_rotation(self, client, regular_user):
        """Après rotation, le refresh token précédent doit être rejeté (replay attack)."""
        login = client.post("/api/auth/login", json={
            "email": "user@test.com", "password": "Secure1!",
        }).json()
        old_refresh = login["refresh_token"]

        # Rotation
        client.post("/api/auth/refresh", json={"refresh_token": old_refresh})

        # Rejeu avec l'ancien token
        resp = client.post("/api/auth/refresh", json={"refresh_token": old_refresh})
        assert resp.status_code == 401

    def test_refresh_invalid_token_rejected(self, client):
        resp = client.post("/api/auth/refresh", json={"refresh_token": "totalement_faux"})
        assert resp.status_code == 401

    def test_refresh_stores_hash_not_plaintext(self, client, db, regular_user):
        """Le token brut ne doit pas se trouver dans la DB — seulement son hash SHA-256."""
        from app.models import RefreshToken as RTModel
        login = client.post("/api/auth/login", json={
            "email": "user@test.com", "password": "Secure1!",
        }).json()
        raw = login["refresh_token"]

        stored = db.query(RTModel).filter(RTModel.revoked == False).first()  # noqa: E712
        assert stored is not None
        assert stored.token_hash != raw                           # pas le clair
        assert stored.token_hash == hashlib.sha256(raw.encode()).hexdigest()


# ════════════════════════════════════════════════════════════════
# LOGOUT + BLACKLIST JWT
# ════════════════════════════════════════════════════════════════

class TestLogout:

    def test_logout_revokes_access_token(self, client, regular_user):
        """Après logout, le même access_token doit être refusé sur /me."""
        login = client.post("/api/auth/login", json={
            "email": "user@test.com", "password": "Secure1!",
        }).json()
        token = login["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Avant logout — /me accessible
        r = client.get("/api/auth/me", headers=headers)
        assert r.status_code == 200

        # Logout
        r = client.post("/api/auth/logout", headers=headers)
        assert r.status_code == 200

        # Après logout — même token refusé
        r = client.get("/api/auth/me", headers=headers)
        assert r.status_code == 401

    def test_logout_revokes_all_refresh_tokens(self, client, db, regular_user):
        """Après logout, le refresh token doit aussi être révoqué en DB."""
        from app.models import RefreshToken as RTModel
        login = client.post("/api/auth/login", json={
            "email": "user@test.com", "password": "Secure1!",
        }).json()
        token = login["access_token"]
        raw_refresh = login["refresh_token"]

        client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})

        # Tenter un refresh avec l'ancien token
        resp = client.post("/api/auth/refresh", json={"refresh_token": raw_refresh})
        assert resp.status_code == 401

    def test_logout_without_token_returns_401(self, client):
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 401


# ════════════════════════════════════════════════════════════════
# /ME — AUTHENTICATION GUARD
# ════════════════════════════════════════════════════════════════

class TestAuthMe:

    def test_me_without_token_returns_401(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client):
        resp = client.get("/api/auth/me", headers={"Authorization": "Bearer faketoken"})
        assert resp.status_code == 401

    def test_me_returns_correct_user(self, client, regular_user, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "user@test.com"
        assert data["tenant_id"] == regular_user[0].id


# ════════════════════════════════════════════════════════════════
# RESET MOT DE PASSE — COMPLEXITÉ
# ════════════════════════════════════════════════════════════════

class TestResetPasswordStrength:

    def test_reset_weak_password_rejected(self, client):
        """Le reset-password doit aussi valider la complexité."""
        resp = client.post("/api/auth/reset-password", json={
            "token": "any_token",
            "new_password": "weakpwd",  # trop faible
        })
        # 422 si la validation complexity échoue AVANT la vérif du token
        assert resp.status_code == 422
