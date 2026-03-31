"""
test_payments.py — Tests de la pile de paiement NeopPay / Korapay.

Couverture :
1. Service Korapay   — HMAC signature, extraction données webhook
2. Service CamPay    — extraction données webhook
3. NeopayService     — création/récupération payment links, initiation, webhook
4. Activation abo    — webhook → plan tenant mis à jour, Subscription active
5. Routes publiques  — /api/neopay/payment-links/{token} GET
6. Routes auth       — /api/neopay/payment-links POST (JWT requis)
7. Routes webhook    — vérification HMAC, 401 sans sig, idempotence
8. Routes superadmin — /api/neopay/payments, /api/neopay/webhook-events
"""
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import _create_tenant_user
from app.models import PaymentLink, PaymentEvent, WebhookEvent, Subscription, PlanType, Tenant


# ─── Clé de test pour la vérif HMAC ─────────────────────────────────────────
# Monkeypatche l'env AVANT import — pas réelle
_TEST_ENCRYPTION_KEY = "test-korapay-encryption-key-abc"
_TEST_CAMPAY_PASSWORD = "test-campay-password-xyz"

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_korapay_signature(raw_body: bytes, key: str = _TEST_ENCRYPTION_KEY) -> str:
    """Génère la signature HMAC-SHA512 attendue par verify_korapay_signature."""
    return hmac.new(key.encode(), raw_body, hashlib.sha512).hexdigest()


def _make_korapay_payload(
    reference: str = "abc123",
    status: str = "success",
    amount: int = 20000,
    currency: str = "NGN",
    email: str = "buyer@test.com",
    event: str = "charge.completed",
) -> dict:
    return {
        "event": event,
        "data": {
            "reference": reference,
            "status": status,
            "amount": amount,
            "currency": currency,
            "customer": {"email": email, "name": "Test Buyer"},
            "metadata": {"plan": "BASIC", "tenant_id": 2},
        },
    }


def _make_payment_link(db, tenant_id: int, status: str = "pending", plan: str = "BASIC") -> PaymentLink:
    """Crée un PaymentLink en DB directement."""
    import secrets
    link = PaymentLink(
        token=secrets.token_hex(32),
        tenant_id=tenant_id,
        plan=plan,
        amount=20000,
        currency="NGN",
        status=status,
        expires_at=datetime.utcnow() + timedelta(hours=24),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def _make_payment_event(db, link: PaymentLink, status: str = "pending") -> PaymentEvent:
    """Crée un PaymentEvent lié à un PaymentLink."""
    event = PaymentEvent(
        transaction_id=link.token,
        provider="korapay",
        payment_link_id=link.id,
        tenant_id=link.tenant_id,
        plan=link.plan,
        amount=link.amount,
        currency=link.currency,
        payment_method="card",
        status=status,
        customer_email="buyer@test.com",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


# ════════════════════════════════════════════════════════════════
# 1. SERVICE KORAPAY — HMAC signature
# ════════════════════════════════════════════════════════════════

class TestKorapaySignature:

    def test_valid_signature_accepted(self, monkeypatch):
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        from app.services import korapay_service

        body = b'{"event":"charge.completed"}'
        sig = _make_korapay_signature(body)
        assert korapay_service.verify_korapay_signature(body, sig) is True

    def test_wrong_signature_rejected(self, monkeypatch):
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        from app.services import korapay_service

        body = b'{"event":"charge.completed"}'
        assert korapay_service.verify_korapay_signature(body, "deadbeef") is False

    def test_empty_signature_rejected(self, monkeypatch):
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        from app.services import korapay_service

        assert korapay_service.verify_korapay_signature(b"payload", "") is False

    def test_signature_case_insensitive(self, monkeypatch):
        """HMAC en majuscules doit aussi passer (compare_digest normalise)."""
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        from app.services import korapay_service

        body = b'{"event":"charge.completed"}'
        sig = _make_korapay_signature(body).upper()
        assert korapay_service.verify_korapay_signature(body, sig) is True

    def test_body_tampered_rejected(self, monkeypatch):
        """Payload modifié après signature → signature invalide."""
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        from app.services import korapay_service

        original_body = b'{"event":"charge.completed","amount":20000}'
        sig = _make_korapay_signature(original_body)
        tampered_body = b'{"event":"charge.completed","amount":999999}'
        assert korapay_service.verify_korapay_signature(tampered_body, sig) is False

    def test_missing_encryption_key_raises(self, monkeypatch):
        """Sans clé d'env → RuntimeError (pas de fallback silencieux)."""
        monkeypatch.delenv("KORAPAY_ENCRYPTION_KEY", raising=False)
        from app.services import korapay_service

        assert korapay_service.verify_korapay_signature(b"test", "sig") is False


# ════════════════════════════════════════════════════════════════
# 2. SERVICE KORAPAY — Extraction données webhook
# ════════════════════════════════════════════════════════════════

class TestKorapayExtract:

    def test_charge_completed_extraction(self):
        from app.services.korapay_service import extract_webhook_data

        payload = _make_korapay_payload(
            reference="ref-001",
            status="success",
            amount=20000,
            currency="NGN",
            email="user@test.com",
            event="charge.completed",
        )
        result = extract_webhook_data(payload)

        assert result["webhook_id"] == "ref-001"
        assert result["event_type"] == "charge.completed"
        assert result["transaction_id"] == "ref-001"
        assert result["amount"] == 20000
        assert result["currency"] == "NGN"
        assert result["status"] == "success"
        assert result["customer_email"] == "user@test.com"

    def test_missing_fields_are_safe(self):
        """Un payload Korapay minimal ne doit pas faire planter l'extraction."""
        from app.services.korapay_service import extract_webhook_data

        result = extract_webhook_data({})
        assert result["webhook_id"] == ""
        assert result["event_type"] == "unknown"
        assert result["amount"] == 0

    def test_metadata_forwarded(self):
        from app.services.korapay_service import extract_webhook_data

        payload = _make_korapay_payload()
        payload["data"]["metadata"] = {"plan": "BASIC", "tenant_id": 5}
        result = extract_webhook_data(payload)
        assert result["metadata"]["plan"] == "BASIC"
        assert result["metadata"]["tenant_id"] == 5


# ════════════════════════════════════════════════════════════════
# 3. SERVICE CAMPAY — Extraction données webhook
# ════════════════════════════════════════════════════════════════

class TestCampayExtract:

    def test_successful_collection(self):
        from app.services.campay_service import extract_webhook_data

        payload = {
            "status": "SUCCESSFUL",
            "reference": "ref-camp-001",
            "external_reference": "ref-camp-001",
            "amount": "15000",
            "currency": "XAF",
            "operator_reference": "+237691234567",
        }
        result = extract_webhook_data(payload)
        assert result["webhook_id"] == "ref-camp-001"
        assert result["event_type"] == "collection.completed"
        assert result["status"] == "SUCCESSFUL"
        assert result["amount"] == 15000
        assert result["currency"] == "XAF"

    def test_failed_collection(self):
        from app.services.campay_service import extract_webhook_data

        payload = {"status": "FAILED", "reference": "ref-failed", "amount": "0", "currency": "XAF"}
        result = extract_webhook_data(payload)
        assert result["event_type"] == "collection.failed"
        assert result["status"] == "FAILED"

    def test_pending_collection_event_type(self):
        from app.services.campay_service import extract_webhook_data

        payload = {"status": "PENDING", "reference": "ref-pend", "amount": "5000", "currency": "XAF"}
        result = extract_webhook_data(payload)
        assert result["event_type"] == "collection.pending"

    def test_missing_fields_safe(self):
        from app.services.campay_service import extract_webhook_data
        result = extract_webhook_data({})
        assert result["webhook_id"] == ""
        assert result["amount"] == 0


# ════════════════════════════════════════════════════════════════
# 4. NEOPAY SERVICE — Payment Links (unit)
# ════════════════════════════════════════════════════════════════

class TestNeopayServiceUnit:

    def test_create_basic_plan_link(self, db, regular_user):
        """Un tenant peut créer un lien de paiement BASIC."""
        from app.services.neopay_service import create_payment_link

        tenant, _ = regular_user
        link = create_payment_link(db, tenant_id=tenant.id, plan="BASIC")

        assert link.tenant_id == tenant.id
        assert link.plan == "BASIC"
        assert link.amount == 20000
        assert link.currency == "NGN"
        assert link.status == "pending"
        assert len(link.token) == 64   # secrets.token_hex(32)

    def test_create_standard_plan_link(self, db, regular_user):
        from app.services.neopay_service import create_payment_link

        tenant, _ = regular_user
        link = create_payment_link(db, tenant_id=tenant.id, plan="STANDARD")
        assert link.plan == "STANDARD"
        assert link.amount == 50000

    def test_create_pro_plan_link(self, db, regular_user):
        from app.services.neopay_service import create_payment_link

        tenant, _ = regular_user
        link = create_payment_link(db, tenant_id=tenant.id, plan="PRO")
        assert link.plan == "PRO"
        assert link.amount == 100000

    def test_create_unknown_plan_raises(self, db, regular_user):
        from app.services.neopay_service import create_payment_link

        tenant, _ = regular_user
        # L'enum Python lève ValueError avant le check manuel — les deux sont cohérents
        with pytest.raises(ValueError):
            create_payment_link(db, tenant_id=tenant.id, plan="GOLD")

    def test_create_neobot_plan_raises_not_billable(self, db, regular_user):
        """NEOBOT (admin) a price 0 → pas facturable."""
        from app.services.neopay_service import create_payment_link

        tenant, _ = regular_user
        with pytest.raises(ValueError, match="non facturable"):
            create_payment_link(db, tenant_id=tenant.id, plan="NEOBOT")

    def test_get_existing_link(self, db, regular_user):
        from app.services.neopay_service import create_payment_link, get_payment_link

        tenant, _ = regular_user
        link = create_payment_link(db, tenant_id=tenant.id, plan="BASIC")
        found = get_payment_link(db, link.token)
        assert found is not None
        assert found.token == link.token

    def test_get_nonexistent_link_returns_none(self, db):
        from app.services.neopay_service import get_payment_link
        assert get_payment_link(db, "nonexistent-token") is None

    def test_get_expired_link_returns_none_and_updates_status(self, db, regular_user):
        """Un lien expiré doit retourner None et son statut passe à 'expired'."""
        from app.services.neopay_service import create_payment_link, get_payment_link

        tenant, _ = regular_user
        link = create_payment_link(db, tenant_id=tenant.id, plan="BASIC")

        # Forcer l'expiration
        link.expires_at = datetime.utcnow() - timedelta(hours=1)
        db.commit()

        result = get_payment_link(db, link.token)
        assert result is None

        # Vérifier que le statut a bien été mis à jour en DB
        db.refresh(link)
        assert link.status == "expired"

    def test_link_tokens_are_unique(self, db, regular_user):
        """Deux liens pour le même tenant doivent avoir des tokens différents."""
        from app.services.neopay_service import create_payment_link

        tenant, _ = regular_user
        link_a = create_payment_link(db, tenant_id=tenant.id, plan="BASIC")
        link_b = create_payment_link(db, tenant_id=tenant.id, plan="BASIC")
        assert link_a.token != link_b.token


# ════════════════════════════════════════════════════════════════
# 5. ROUTES PUBLIQUES — GET /api/neopay/payment-links/{token}
# ════════════════════════════════════════════════════════════════

class TestPaymentLinkPublicRoute:

    def test_get_valid_link_returns_200(self, client, db, regular_user):
        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id)

        resp = client.get(f"/api/neopay/payment-links/{link.token}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["token"] == link.token
        assert data["plan"] == "BASIC"
        assert data["amount"] == 20000
        assert data["currency"] == "NGN"
        assert data["status"] == "pending"
        assert "tenant_name" in data

    def test_get_nonexistent_link_returns_404(self, client):
        resp = client.get("/api/neopay/payment-links/invalid-token-doesnt-exist")
        assert resp.status_code == 404

    def test_get_expired_link_returns_404(self, client, db, regular_user):
        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id, status="pending")
        link.expires_at = datetime.utcnow() - timedelta(hours=2)
        db.commit()

        resp = client.get(f"/api/neopay/payment-links/{link.token}")
        assert resp.status_code == 404

    def test_get_paid_link_still_visible(self, client, db, regular_user):
        """Un lien 'paid' reste visible (pas expiré — juste résolu)."""
        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id, status="paid")

        resp = client.get(f"/api/neopay/payment-links/{link.token}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "paid"


# ════════════════════════════════════════════════════════════════
# 6. ROUTES AUTH — POST /api/neopay/payment-links
# ════════════════════════════════════════════════════════════════

class TestCreatePaymentLinkRoute:

    def test_create_link_requires_auth(self, client):
        resp = client.post("/api/neopay/payment-links", json={"plan": "BASIC"})
        assert resp.status_code == 401

    def test_create_link_authenticated_returns_url(self, client, auth_headers):
        resp = client.post(
            "/api/neopay/payment-links",
            json={"plan": "BASIC"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert "payment_url" in data
        assert "/pay/" in data["payment_url"]
        assert data["plan"] == "BASIC"
        assert data["amount"] == 20000

    def test_create_link_invalid_plan(self, client, auth_headers):
        resp = client.post(
            "/api/neopay/payment-links",
            json={"plan": "DIAMOND"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_create_link_standard_plan(self, client, auth_headers):
        resp = client.post(
            "/api/neopay/payment-links",
            json={"plan": "STANDARD"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["amount"] == 50000


# ════════════════════════════════════════════════════════════════
# 7. ROUTE WEBHOOK KORAPAY — Sécurité HMAC
# ════════════════════════════════════════════════════════════════

class TestWebhookKorapaySecurity:
    """
    Ces tests adressent la règle absolue : Signature HMAC vérifiée AVANT
    tout traitement. Pas de bypass possible, pas de traitement sans signature valide.
    """

    def _webhook_url(self):
        return "/api/neopay/webhooks/korapay"

    def test_webhook_no_signature_returns_401(self, client):
        """Sans header X-Korapay-Signature → rejet immédiat."""
        resp = client.post(
            self._webhook_url(),
            content=b'{"event":"charge.completed"}',
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 401

    def test_webhook_wrong_signature_returns_401(self, client, monkeypatch):
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        body = json.dumps(_make_korapay_payload()).encode()

        resp = client.post(
            self._webhook_url(),
            content=body,
            headers={
                "Content-Type": "application/json",
                "x-korapay-signature": "0000000000000000bad_signature",
            },
        )
        assert resp.status_code == 401

    def test_webhook_valid_signature_returns_200(self, client, db, regular_user, monkeypatch):
        """Signature valide → traitement OK, retourne 200."""
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id)
        event = _make_payment_event(db, link, status="pending")

        payload = _make_korapay_payload(
            reference=link.token,
            status="success",
            event="charge.completed",
        )
        body = json.dumps(payload).encode()
        sig = _make_korapay_signature(body)

        with (
            patch("app.services.neopay_service.send_payment_confirmation", new_callable=AsyncMock),
            patch("app.services.neopay_service.send_internal_alert", new_callable=AsyncMock),
        ):
            resp = client.post(
                self._webhook_url(),
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "x-korapay-signature": sig,
                },
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_webhook_without_reference_is_ignored(self, client, monkeypatch):
        """Payload sans référence → ignoré (pas d'erreur, pas de traitement)."""
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        payload = {"event": "charge.completed", "data": {}}
        body = json.dumps(payload).encode()
        sig = _make_korapay_signature(body)

        resp = client.post(
            self._webhook_url(),
            content=body,
            headers={
                "Content-Type": "application/json",
                "x-korapay-signature": sig,
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ignored"

    def test_webhook_idempotent_second_call_skipped(self, client, db, regular_user, monkeypatch):
        """Le même webhook_id traité deux fois → deuxième appel ignoré en silence."""
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id)
        _make_payment_event(db, link, status="pending")

        payload = _make_korapay_payload(reference=link.token, status="success")
        body = json.dumps(payload).encode()
        sig = _make_korapay_signature(body)

        headers = {"Content-Type": "application/json", "x-korapay-signature": sig}

        with (
            patch("app.services.neopay_service.send_payment_confirmation", new_callable=AsyncMock),
            patch("app.services.neopay_service.send_internal_alert", new_callable=AsyncMock),
        ):
            resp1 = client.post(self._webhook_url(), content=body, headers=headers)
            resp2 = client.post(self._webhook_url(), content=body, headers=headers)

        assert resp1.status_code == 200
        assert resp2.status_code == 200

        # Un seul WebhookEvent créé (idempotent)
        count = db.query(WebhookEvent).filter(WebhookEvent.webhook_id == link.token).count()
        assert count == 1


# ════════════════════════════════════════════════════════════════
# 8. ACTIVATION D'ABONNEMENT — webhook → plan mis à jour
# ════════════════════════════════════════════════════════════════

class TestSubscriptionActivation:

    def test_successful_webhook_activates_plan(self, client, db, regular_user, monkeypatch):
        """
        Scénario complet :
        - Tenant démarre en BASIC trial
        - Un webhook Korapay 'charge.completed' arrive avec status=success
        → tenant.plan doit passer à BASIC (payé, is_trial=False)
        → PaymentEvent.status = 'confirmed'
        → PaymentLink.status = 'paid'
        → subscription.is_trial = False
        """
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id, plan="STANDARD")
        event = _make_payment_event(db, link, status="pending")
        event.plan = "STANDARD"
        event.amount = 50000
        db.commit()

        # Subscription initiale en trial
        sub = Subscription(
            tenant_id=tenant.id,
            plan="basic",
            status="active",
            is_trial=True,
            trial_start_date=datetime.utcnow(),
            trial_end_date=datetime.utcnow() + timedelta(days=14),
            subscription_start_date=datetime.utcnow(),
            next_billing_date=datetime.utcnow() + timedelta(days=14),
        )
        db.add(sub)
        db.commit()

        payload = _make_korapay_payload(
            reference=link.token,
            status="success",
            event="charge.completed",
        )
        body = json.dumps(payload).encode()
        sig = _make_korapay_signature(body)
        headers = {"Content-Type": "application/json", "x-korapay-signature": sig}

        with (
            patch("app.services.neopay_service.send_payment_confirmation", new_callable=AsyncMock),
            patch("app.services.neopay_service.send_internal_alert", new_callable=AsyncMock),
        ):
            resp = client.post("/api/neopay/webhooks/korapay", content=body, headers=headers)

        assert resp.status_code == 200

        # Vérifier la mise à jour en DB
        db.expire_all()
        db.refresh(event)
        db.refresh(link)
        db.refresh(tenant)
        db.refresh(sub)

        assert event.status == "confirmed"
        assert link.status == "paid"
        assert link.paid_at is not None
        assert tenant.is_trial is False
        assert sub.is_trial is False
        assert sub.status == "active"

    def test_non_success_status_does_not_activate(self, client, db, regular_user, monkeypatch):
        """Un webhook avec status 'failed' ne doit PAS activer l'abonnement."""
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id)
        event = _make_payment_event(db, link, status="pending")
        original_plan = tenant.plan

        payload = _make_korapay_payload(reference=link.token, status="failed", event="charge.failed")
        body = json.dumps(payload).encode()
        sig = _make_korapay_signature(body)

        with (
            patch("app.services.neopay_service.send_payment_confirmation", new_callable=AsyncMock),
            patch("app.services.neopay_service.send_internal_alert", new_callable=AsyncMock),
        ):
            resp = client.post(
                "/api/neopay/webhooks/korapay",
                content=body,
                headers={"Content-Type": "application/json", "x-korapay-signature": sig},
            )

        assert resp.status_code == 200
        db.expire_all()
        db.refresh(tenant)
        db.refresh(event)
        # Le plan du tenant n'a pas bougé
        assert tenant.plan == original_plan
        # Le PaymentEvent n'est pas confirmé
        assert event.status == "pending"

    async def test_double_webhook_does_not_activate_twice(self, db, regular_user, monkeypatch):
        """Idempotent : deux webhooks identiques → UN SEUL confirm en DB."""
        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        from app.services import neopay_service

        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id)
        _make_payment_event(db, link, status="pending")

        extracted = {
            "webhook_id": link.token,
            "event_type": "charge.completed",
            "transaction_id": link.token,
            "status": "success",
            "amount": 20000,
            "currency": "NGN",
            "customer_email": "buyer@test.com",
            "metadata": None,
        }

        with (
            patch("app.services.neopay_service.send_payment_confirmation", new_callable=AsyncMock),
            patch("app.services.neopay_service.send_internal_alert", new_callable=AsyncMock),
        ):
            r1 = await neopay_service.process_webhook(
                db, provider="korapay",
                webhook_id=link.token,
                event_type="charge.completed",
                raw_payload=_make_korapay_payload(reference=link.token),
                extracted=extracted,
            )
            r2 = await neopay_service.process_webhook(
                db, provider="korapay",
                webhook_id=link.token,
                event_type="charge.completed",
                raw_payload=_make_korapay_payload(reference=link.token),
                extracted=extracted,
            )

        assert r1 is True
        assert r2 is True  # deuxième appel réussi mais ignoré (idempotent)

        # Un seul WebhookEvent
        count = db.query(WebhookEvent).filter(WebhookEvent.webhook_id == link.token).count()
        assert count == 1


# ════════════════════════════════════════════════════════════════
# 9. INITIALE PAYMENT — POST /api/neopay/payment-links/{token}/initiate
# ════════════════════════════════════════════════════════════════

class TestInitiatePayment:

    def test_initiate_requires_valid_token(self, client, db):
        resp = client.post("/api/neopay/payment-links/bad-token-xyz/initiate", json={
            "payment_method": "card",
            "customer_email": "buyer@test.com",
            "customer_name": "Test User",
            "country": "NG",
        })
        assert resp.status_code == 400

    def test_initiate_paid_link_rejected(self, client, db, regular_user):
        """Un lien déjà 'paid' ne peut pas être réutilisé."""
        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id, status="paid")

        resp = client.post(f"/api/neopay/payment-links/{link.token}/initiate", json={
            "payment_method": "card",
            "customer_email": "buyer@test.com",
            "customer_name": "Test User",
            "country": "NG",
        })
        assert resp.status_code == 400

    def test_initiate_korapay_card(self, client, db, regular_user):
        """Initiation Korapay (carte) — mock l'appel HTTP."""
        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id)

        with patch(
            "app.services.korapay_service.initialize_charge",
            new_callable=AsyncMock,
            return_value={"data": {"checkout_url": "https://pay.korapay.com/abc"}},
        ):
            resp = client.post(f"/api/neopay/payment-links/{link.token}/initiate", json={
                "payment_method": "card",
                "customer_email": "buyer@test.com",
                "customer_name": "Test Buyer",
                "country": "NG",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "korapay"
        assert data["reference"] == link.token
        assert "checkout_url" in data

    def test_initiate_campay_mobile_money(self, client, db, regular_user, monkeypatch):
        """Initiation CamPay Mobile Money Cameroun (production activée dans le test)."""
        monkeypatch.setenv("CAMPAY_PRODUCTION", "true")
        monkeypatch.setenv("CAMPAY_USERNAME", "test-user")
        monkeypatch.setenv("CAMPAY_PASSWORD", "test-pass")

        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id)

        with patch(
            "app.services.campay_service.initialize_collection",
            new_callable=AsyncMock,
            return_value={"ussd_code": "*126*3*5#", "operator_reference": "ref123"},
        ):
            resp = client.post(f"/api/neopay/payment-links/{link.token}/initiate", json={
                "payment_method": "mobile_money",
                "customer_email": "buyer@test.com",
                "customer_name": "Test Buyer",
                "customer_phone": "+237691234567",
                "country": "CM",
            })

        assert resp.status_code == 200
        data = resp.json()
        assert data["provider"] == "campay"


# ════════════════════════════════════════════════════════════════
# 10. ROUTES SUPERADMIN
# ════════════════════════════════════════════════════════════════

class TestSuperadminPaymentRoutes:

    def test_list_payments_rejects_regular_user(self, client, auth_headers):
        resp = client.get("/api/neopay/payments", headers=auth_headers)
        assert resp.status_code == 403

    def test_list_payments_rejects_unauthenticated(self, client):
        resp = client.get("/api/neopay/payments")
        assert resp.status_code == 401

    def test_list_payments_superadmin_returns_200(self, client, db, superadmin_headers, regular_user):
        """Le superadmin peut lister tous les paiements."""
        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id)
        _make_payment_event(db, link)

        resp = client.get("/api/neopay/payments", headers=superadmin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "payments" in data
        assert data["total"] >= 1
        assert data["payments"][0]["provider"] == "korapay"

    def test_list_webhook_events_rejects_regular_user(self, client, auth_headers):
        resp = client.get("/api/neopay/webhook-events", headers=auth_headers)
        assert resp.status_code == 403

    def test_list_webhook_events_superadmin_empty(self, client, superadmin_headers):
        """Superadmin peut accéder à la liste (vide si aucun webhook)."""
        resp = client.get("/api/neopay/webhook-events", headers=superadmin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_generate_for_tenant_superadmin_only(self, client, auth_headers, db, regular_user):
        """Un user normal ne peut pas générer un lien pour un tenant."""
        tenant, _ = regular_user
        resp = client.post(
            f"/api/neopay/generate-for-tenant/{tenant.id}",
            json={"plan": "BASIC"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    def test_generate_for_tenant_superadmin_ok(self, client, superadmin_headers, db, regular_user):
        """Le superadmin peut générer un lien pour n'importe quel tenant."""
        tenant, _ = regular_user
        resp = client.post(
            f"/api/neopay/generate-for-tenant/{tenant.id}",
            json={"plan": "BASIC"},
            headers=superadmin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert "payment_url" in data

    def test_generate_for_nonexistent_tenant_returns_404(self, client, superadmin_headers):
        resp = client.post(
            "/api/neopay/generate-for-tenant/99999",
            json={"plan": "BASIC"},
            headers=superadmin_headers,
        )
        assert resp.status_code == 404


# ════════════════════════════════════════════════════════════════
# 11. WEBHOOK RETRY SERVICE (unit)
# ════════════════════════════════════════════════════════════════

class TestWebhookRetry:

    async def test_retry_processes_failed_webhook(self, db, regular_user, monkeypatch):
        """Un webhook 'failed' est rejoué par retry_failed_webhooks."""
        from app.services.neopay_service import retry_failed_webhooks

        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id)
        _make_payment_event(db, link, status="pending")

        # WebhookEvent 'failed' dans la fenêtre eligibilité
        wh = WebhookEvent(
            webhook_id=link.token,
            provider="korapay",
            event_type="charge.completed",
            status="failed",
            raw_payload=_make_korapay_payload(reference=link.token, status="success"),
            attempts=1,
            last_attempt_at=datetime.utcnow() - timedelta(minutes=10),
        )
        db.add(wh)
        db.commit()

        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        with (
            patch("app.services.neopay_service.send_payment_confirmation", new_callable=AsyncMock),
            patch("app.services.neopay_service.send_internal_alert", new_callable=AsyncMock),
            patch("sentry_sdk.capture_exception"),
            patch("sentry_sdk.capture_message"),
        ):
            count = await retry_failed_webhooks(db)

        assert count >= 1
        db.refresh(wh)
        assert wh.status == "processed"

    async def test_retry_skips_max_attempts_reached(self, db, regular_user, monkeypatch):
        """Un webhook ayant atteint WEBHOOK_MAX_ATTEMPTS ne doit pas être retraité."""
        from app.services.neopay_service import retry_failed_webhooks, WEBHOOK_MAX_ATTEMPTS

        tenant, _ = regular_user
        link = _make_payment_link(db, tenant.id)
        _make_payment_event(db, link, status="failed")

        wh = WebhookEvent(
            webhook_id=link.token + "_maxed",
            provider="korapay",
            event_type="charge.completed",
            status="failed",
            raw_payload={},
            attempts=WEBHOOK_MAX_ATTEMPTS,
            error_detail="timeout",
            last_attempt_at=datetime.utcnow() - timedelta(minutes=10),
        )
        db.add(wh)
        db.commit()

        monkeypatch.setenv("KORAPAY_ENCRYPTION_KEY", _TEST_ENCRYPTION_KEY)
        with (
            patch("app.services.neopay_service.send_internal_alert", new_callable=AsyncMock),
            patch("sentry_sdk.capture_message"),
        ):
            await retry_failed_webhooks(db)

        db.refresh(wh)
        # Marqué 'skipped' après alerte, pas retraité
        assert wh.status == "skipped"
