"""
test_route_protection.py — Tests d'isolation et de contrôle d'accès.

Vérifie que TOUTES les routes protégées :
- Retournent 401 sans token
- Retournent 403 si le tenant_id ne correspond pas
- Retournent 200/404 si le tenant est le bon

Routes testées : contacts, tenant_settings, human_detection, setup
"""
import pytest
from tests.conftest import _create_tenant_user, _get_token


def _headers(client, email, password):
    token = _get_token(client, email, password)
    return {"Authorization": f"Bearer {token}"}


# ════════════════════════════════════════════════════════════════
# CONTACTS — /api/tenants/{tenant_id}/contacts
# ════════════════════════════════════════════════════════════════

class TestContactsProtection:

    def test_get_contacts_requires_auth(self, client, regular_user):
        tid = regular_user[0].id
        resp = client.get(f"/api/tenants/{tid}/contacts")
        assert resp.status_code == 401

    def test_get_contacts_wrong_tenant_returns_403(self, client, regular_user, other_user):
        other_tid = other_user[0].id
        h = _headers(client, "user@test.com", "Secure1!")
        resp = client.get(f"/api/tenants/{other_tid}/contacts", headers=h)
        assert resp.status_code == 403

    def test_get_contacts_own_tenant_allowed(self, client, regular_user):
        tid = regular_user[0].id
        h = _headers(client, "user@test.com", "Secure1!")
        resp = client.get(f"/api/tenants/{tid}/contacts", headers=h)
        # 200 (liste vide) ou 500 si le service plante sur SQLite — pas 401/403
        assert resp.status_code not in (401, 403)

    def test_get_disabled_contacts_requires_auth(self, client, regular_user):
        tid = regular_user[0].id
        resp = client.get(f"/api/tenants/{tid}/contacts/disabled")
        assert resp.status_code == 401

    def test_toggle_ai_requires_auth(self, client, regular_user):
        tid = regular_user[0].id
        resp = client.put(
            f"/api/tenants/{tid}/contacts/+237600000001/ai-toggle",
            json={"ai_enabled": False},
        )
        assert resp.status_code == 401

    def test_toggle_ai_wrong_tenant_returns_403(self, client, regular_user, other_user):
        other_tid = other_user[0].id
        h = _headers(client, "user@test.com", "Secure1!")
        resp = client.put(
            f"/api/tenants/{other_tid}/contacts/+237600000001/ai-toggle",
            json={"ai_enabled": False},
            headers=h,
        )
        assert resp.status_code == 403

    def test_bulk_disable_requires_auth(self, client, regular_user):
        tid = regular_user[0].id
        resp = client.post(
            f"/api/tenants/{tid}/contacts/bulk-disable",
            json={"phones": ["+237600000001"]},
        )
        assert resp.status_code == 401

    def test_bulk_enable_requires_auth(self, client, regular_user):
        tid = regular_user[0].id
        resp = client.post(
            f"/api/tenants/{tid}/contacts/bulk-enable",
            json={"phones": ["+237600000001"]},
        )
        assert resp.status_code == 401

    def test_superadmin_can_access_any_tenant(self, client, regular_user, superadmin_user, superadmin_headers):
        tid = regular_user[0].id
        resp = client.get(f"/api/tenants/{tid}/contacts", headers=superadmin_headers)
        assert resp.status_code not in (401, 403)


# ════════════════════════════════════════════════════════════════
# TENANT SETTINGS — /api/tenants/{tenant_id}/settings
# ════════════════════════════════════════════════════════════════

class TestTenantSettingsProtection:

    def test_get_settings_requires_auth(self, client, regular_user):
        tid = regular_user[0].id
        resp = client.get(f"/api/tenants/{tid}/settings")
        assert resp.status_code == 401

    def test_get_settings_wrong_tenant_returns_403(self, client, regular_user, other_user):
        other_tid = other_user[0].id
        h = _headers(client, "user@test.com", "Secure1!")
        resp = client.get(f"/api/tenants/{other_tid}/settings", headers=h)
        assert resp.status_code == 403

    def test_get_settings_own_tenant_allowed(self, client, regular_user):
        tid = regular_user[0].id
        h = _headers(client, "user@test.com", "Secure1!")
        resp = client.get(f"/api/tenants/{tid}/settings", headers=h)
        assert resp.status_code not in (401, 403)

    def test_update_settings_requires_auth(self, client, regular_user):
        tid = regular_user[0].id
        resp = client.put(
            f"/api/tenants/{tid}/settings",
            json={"response_delay_seconds": 30},
        )
        assert resp.status_code == 401

    def test_update_settings_wrong_tenant_returns_403(self, client, regular_user, other_user):
        other_tid = other_user[0].id
        h = _headers(client, "user@test.com", "Secure1!")
        resp = client.put(
            f"/api/tenants/{other_tid}/settings",
            json={"response_delay_seconds": 30},
            headers=h,
        )
        assert resp.status_code == 403

    def test_delete_contact_delay_requires_auth(self, client, regular_user):
        tid = regular_user[0].id
        resp = client.delete(f"/api/tenants/{tid}/settings/contact-delay/+237600000001")
        assert resp.status_code == 401

    def test_get_queue_requires_auth(self, client, regular_user):
        tid = regular_user[0].id
        resp = client.get(f"/api/tenants/{tid}/settings/queue")
        assert resp.status_code == 401


# ════════════════════════════════════════════════════════════════
# HUMAN DETECTION — /api/conversations/{id}/...
# ════════════════════════════════════════════════════════════════

class TestHumanDetectionProtection:

    def test_get_state_requires_auth(self, client):
        resp = client.get("/api/conversations/1/state")
        assert resp.status_code == 401

    def test_mark_human_active_requires_auth(self, client):
        resp = client.post("/api/conversations/1/mark-human-active")
        assert resp.status_code == 401

    def test_mark_human_inactive_requires_auth(self, client):
        resp = client.post("/api/conversations/1/mark-human-inactive")
        assert resp.status_code == 401

    def test_auto_detect_requires_auth(self, client):
        resp = client.post("/api/conversations/1/auto-detect-human")
        assert resp.status_code == 401

    def test_should_ai_respond_requires_auth(self, client):
        resp = client.get("/api/conversations/1/should-ai-respond")
        assert resp.status_code == 401

    def test_get_state_nonexistent_conversation_returns_404(self, client, regular_user, auth_headers):
        """Une conversation inexistante doit retourner 404, pas 403 ni 500."""
        resp = client.get("/api/conversations/99999/state", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_state_other_tenant_conversation_returns_403(self, client, db, regular_user, other_user, auth_headers):
        """Accès à la conversation d'un autre tenant → 403."""
        from app.models import Conversation
        # Créer une conversation appartenant à other_user
        conv = Conversation(
            tenant_id=other_user[0].id,
            customer_phone="+237600000099",
            status="active",
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

        resp = client.get(f"/api/conversations/{conv.id}/state", headers=auth_headers)
        assert resp.status_code == 403


# ════════════════════════════════════════════════════════════════
# SETUP — /api/v1/setup/...  (superadmin only)
# ════════════════════════════════════════════════════════════════

class TestSetupProtection:

    def test_init_profile_requires_auth(self, client):
        resp = client.post("/api/v1/setup/init-neobot-profile")
        assert resp.status_code == 401

    def test_init_profile_regular_user_is_forbidden(self, client, regular_user, auth_headers):
        resp = client.post("/api/v1/setup/init-neobot-profile", headers=auth_headers)
        assert resp.status_code == 403

    def test_get_profile_requires_auth(self, client):
        resp = client.get("/api/v1/setup/profile/1")
        assert resp.status_code == 401

    def test_get_profile_regular_user_is_forbidden(self, client, regular_user, auth_headers):
        resp = client.get("/api/v1/setup/profile/1", headers=auth_headers)
        assert resp.status_code == 403

    def test_superadmin_can_call_setup(self, client, superadmin_user, superadmin_headers):
        # Peut retourner 400/404/500 selon la logique métier, mais PAS 401/403
        resp = client.post(
            "/api/v1/setup/init-neobot-profile",
            params={"tenant_id": superadmin_user[0].id},
            headers=superadmin_headers,
        )
        assert resp.status_code not in (401, 403)
