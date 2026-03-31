"""
conftest.py — Fixtures partagées pour tous les tests NeoBot.

On utilise une DB SQLite en mémoire pour les tests unitaires/intégration.
Chaque test reçoit une DB vierge et un client HTTP isolés.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool  # Force toutes les connexions à partager la même DB in-memory

from app.main import app
from app.database import Base, get_db
from app.models import User, Tenant, PlanType
from app.services.auth_service import get_password_hash

# ── DB SQLite en mémoire — StaticPool = toutes les connexions partagent la même DB ──
# Sans StaticPool, chaque connexion SQLite crée une DB vide → "no such table"
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Recrée toutes les tables avant chaque test, les supprime après."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Vide le storage du rate limiter AVANT chaque test.

    On accède à _limiter.storage (la référence réelle utilisée par les
    stratégies de rate limiting), pas _storage qui peut être désynchronisé.
    Le .reset() vide les compteurs sans casser les références internes.
    """
    limiter_obj = getattr(app.state, "limiter", None)
    if limiter_obj is not None:
        inner = getattr(limiter_obj, "_limiter", None)
        if inner is not None:
            storage = getattr(inner, "storage", None)
            if storage is not None and hasattr(storage, "reset"):
                storage.reset()
    yield


@pytest.fixture
def db():
    """Session DB directe pour les fixtures bas niveau."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    """Client HTTP FastAPI sans lever d'exception sur les erreurs HTTP."""
    return TestClient(app, raise_server_exceptions=False)


# ── Helpers pour créer des fixtures métier ───────────────────────────────────

def _create_tenant_user(db, email: str, password: str, tenant_name: str, is_superadmin: bool = False):
    """Crée un Tenant + User dans la DB de test et retourne (tenant, user)."""
    tenant = Tenant(
        name=tenant_name,
        email=email,
        phone=f"unknown-{email[:10].replace('@','')}",
        plan=PlanType.BASIC,
        messages_used=0,
        messages_limit=2500,
    )
    db.add(tenant)
    db.flush()

    user = User(
        tenant_id=tenant.id,
        email=email,
        hashed_password=get_password_hash(password),
        full_name="Test User",
        is_active=True,
        is_superadmin=is_superadmin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(tenant)
    return tenant, user


def _get_token(client, email: str, password: str) -> str:
    """Login et retourne l'access_token."""
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


@pytest.fixture
def regular_user(db):
    """Tenant + User standard (tenant_id déterministe)."""
    return _create_tenant_user(db, "user@test.com", "Secure1!", "TestBiz")


@pytest.fixture
def other_user(db):
    """Second Tenant + User pour les tests d'isolation."""
    return _create_tenant_user(db, "other@test.com", "Secure1!", "OtherBiz")


@pytest.fixture
def superadmin_user(db):
    """Superadmin pour les tests de routes admin."""
    return _create_tenant_user(db, "admin@test.com", "Admin1!", "NeoBot", is_superadmin=True)


@pytest.fixture
def auth_headers(client, regular_user):
    """Headers Authorization pour l'utilisateur standard."""
    token = _get_token(client, "user@test.com", "Secure1!")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def superadmin_headers(client, superadmin_user):
    """Headers Authorization pour le superadmin."""
    token = _get_token(client, "admin@test.com", "Admin1!")
    return {"Authorization": f"Bearer {token}"}
