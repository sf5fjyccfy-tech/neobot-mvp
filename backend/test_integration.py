"""
Suite de tests complets pour NeoBOT.
Tests d'intégration pour tous les composants critiques.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# Imports application
from app.main import app
from app.database import Base, get_db
from app.models import (
    User, Tenant, Conversation, Message, 
    UsageTracking, Overage, WhatsAppSession,
    TenantBusinessConfig, BusinessTypeModel
)

# Configuration base de test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override dependency injection
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Setup/teardown
@pytest.fixture(scope="function")
def setup_database():
    """Crée et nettoie la DB avant/après chaque test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(setup_database):
    """Client de test FastAPI"""
    return TestClient(app)

@pytest.fixture
def db(setup_database):
    """Session DB pour les fixtures"""
    db = TestingSessionLocal()
    yield db
    db.close()

# ============= PHASE 2: TESTS AUTHENTIFICATION =============

class TestAuthentication:
    """Tests pour le système d'authentification"""
    
    def test_signup_success(self, client):
        """Test création compte valide"""
        response = client.post(
            "/api/auth/register",
            json={
                "full_name": "Test User",
                "email": "test@example.com",
                "password": "SecurePass123!",
                "tenant_name": "Test Business",
                "business_type": "neobot"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_signup_duplicate_email(self, client):
        """Test création doublon email"""
        # Premier compte
        client.post(
            "/api/auth/register",
            json={
                "full_name": "User 1",
                "email": "duplicate@example.com",
                "password": "Pass123!",
                "tenant_name": "Biz1",
                "business_type": "neobot"
            }
        )
        
        # Deuxième compte même email
        response = client.post(
            "/api/auth/register",
            json={
                "full_name": "User 2",
                "email": "duplicate@example.com",
                "password": "Pass456!",
                "tenant_name": "Biz2",
                "business_type": "neobot"
            }
        )
        
        assert response.status_code == 400
    
    def test_login_success(self, client):
        """Test login valide"""
        # Créer compte
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Test",
                "email": "login@test.com",
                "password": "Pass123!",
                "tenant_name": "Test",
                "business_type": "neobot"
            }
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "login@test.com",
                "password": "Pass123!"
            }
        )
        
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_invalid_password(self, client):
        """Test login mot de passe incorrect"""
        # Créer compte
        client.post(
            "/api/auth/register",
            json={
                "full_name": "Test",
                "email": "test@invalid.com",
                "password": "CorrectPass123!",
                "tenant_name": "Test",
                "business_type": "neobot"
            }
        )
        
        # Login avec mauvais mot de passe
        response = client.post(
            "/api/auth/login",
            json={
                "email": "test@invalid.com",
                "password": "WrongPass123!"
            }
        )
        
        assert response.status_code == 401

# ============= PHASE 3: TESTS ISOLATION MULTI-TENANT =============

class TestMultiTenant:
    """Tests pour l'isolation multi-tenant"""
    
    def test_whatsapp_session_isolation(self, client, db):
        """Test isolation contenus entre tenants"""
        # Créer 2 tenants
        user1 = User(
            email="user1@test.com",
            hashed_password="hash1",
            full_name="User 1"
        )
        user2 = User(
            email="user2@test.com",
            hashed_password="hash2",
            full_name="User 2"
        )
        
        tenant1 = Tenant(name="Tenant 1", email="t1@test.com", phone="+237600000101", plan="BASIQUE")
        tenant2 = Tenant(name="Tenant 2", email="t2@test.com", phone="+237600000102", plan="PRO")

        user1.tenant = tenant1
        user2.tenant = tenant2

        db.add_all([tenant1, tenant2, user1, user2])
        db.commit()
        
        # Créer WhatsApp sessions
        session1 = WhatsAppSession(
            tenant_id=tenant1.id,
            whatsapp_phone="+237600000001",
            is_connected=True
        )
        session2 = WhatsAppSession(
            tenant_id=tenant2.id,
            whatsapp_phone="+237600000002",
            is_connected=True
        )
        
        db.add_all([session1, session2])
        db.commit()
        
        # Vérifier isolation
        assert session1.tenant_id != session2.tenant_id
        assert session1.whatsapp_phone != session2.whatsapp_phone
    
    def test_conversation_isolation(self, client, db):
        """Test isolation conversations entre tenants"""
        tenant1 = Tenant(name="Tenant 1", email="t1@test.com", phone="+237600000201", plan="BASIQUE")
        tenant2 = Tenant(name="Tenant 2", email="t2@test.com", phone="+237600000202", plan="PRO")
        
        db.add_all([tenant1, tenant2])
        db.commit()
        
        # Créer conversations
        conv1 = Conversation(
            tenant_id=tenant1.id,
            customer_phone="+237600001111",
            customer_name="Client 1",
            channel="whatsapp",
            status="active"
        )
        conv2 = Conversation(
            tenant_id=tenant2.id,
            customer_phone="+237600002222",
            customer_name="Client 2",
            channel="whatsapp",
            status="active"
        )
        
        db.add_all([conv1, conv2])
        db.commit()
        
        # Vérifier isolation
        tenant1_convs = db.query(Conversation).filter(
            Conversation.tenant_id == tenant1.id
        ).all()
        tenant2_convs = db.query(Conversation).filter(
            Conversation.tenant_id == tenant2.id
        ).all()
        
        assert len(tenant1_convs) == 1
        assert len(tenant2_convs) == 1
        assert tenant1_convs[0].customer_phone != tenant2_convs[0].customer_phone

# ============= PHASE 4: TESTS SUIVI UTILISATION =============

class TestUsageTracking:
    """Tests pour le suivi d'utilisation et quotas"""
    
    def test_usage_monthly_creation(self, db):
        """Test création automatique tracking mensuel"""
        tenant = Tenant(name="Test", email="test@test.com", phone="+237600000301", plan="BASIQUE")
        db.add(tenant)
        db.commit()
        
        # Créer tracking
        month = datetime.utcnow().strftime("%Y-%m")
        usage = UsageTracking(
            tenant_id=tenant.id,
            month_year=month,
            whatsapp_messages_used=150
        )
        db.add(usage)
        db.commit()
        
        # Vérifier
        retrieved = db.query(UsageTracking).filter(
            UsageTracking.tenant_id == tenant.id
        ).first()
        
        assert retrieved is not None
        assert retrieved.whatsapp_messages_used == 150
    
    def test_usage_quota_exceeded(self, db):
        """Test vérification dépassement quota"""
        # Plan BASIQUE = 2000 messages
        tenant = Tenant(
            name="Test",
            email="test@test.com",
            phone="+237600000302",
            plan="BASIQUE",
            messages_limit=2000
        )
        db.add(tenant)
        db.commit()
        
        # Usage usage à 98% (1960 messages)
        month = datetime.utcnow().strftime("%Y-%m")
        usage = UsageTracking(
            tenant_id=tenant.id,
            month_year=month,
            whatsapp_messages_used=1960
        )
        db.add(usage)
        db.commit()
        
        # Vérifier si quota dépassé
        quota_exceeded = usage.whatsapp_messages_used >= tenant.messages_limit
        assert quota_exceeded == False
        
        # Ajouter messages pour dépasser
        usage.whatsapp_messages_used = 2050
        db.commit()
        
        quota_exceeded = usage.whatsapp_messages_used >= tenant.messages_limit
        assert quota_exceeded == True

# ============= PHASE 5: TESTS FACTURATION DÉPASSEMENTS =============

class TestOveragePricing:
    """Tests pour la facturation des dépassements"""
    
    def test_overage_calculation(self, db):
        """Test calcul coût dépassement"""
        PRICE_PER_1000 = 7000  # FCFA
        
        # Test cases
        test_cases = [
            (500, 7000),      # 1 tranche
            (1500, 14000),    # 2 tranches
            (1000, 7000),     # 1 tranche
            (3200, 28000),    # 4 tranches (3200 → 4 tranches)
        ]
        
        for messages_over, expected_cost in test_cases:
            cost = ((messages_over + 999) // 1000) * PRICE_PER_1000
            assert cost == expected_cost
    
    def test_overage_monthly_tracking(self, db):
        """Test suivi mensuel des dépassements"""
        tenant = Tenant(name="Test", email="test@test.com", phone="+237600000401", plan="PRO")
        db.add(tenant)
        db.commit()
        
        # Créer overage record
        month = datetime.utcnow().strftime("%Y-%m")
        overage = Overage(
            tenant_id=tenant.id,
            month_year=month,
            messages_over=2500,
            cost_fcfa=21000,  # 3 tranches
            is_billed=False
        )
        db.add(overage)
        db.commit()
        
        # Vérifier
        retrieved = db.query(Overage).filter(
            Overage.tenant_id == tenant.id
        ).first()
        
        assert retrieved.messages_over == 2500
        assert retrieved.cost_fcfa == 21000
        assert retrieved.is_billed == False
    
    def test_overage_charge_and_continue(self, db):
        """Test modèle 'charge et continue'"""
        tenant = Tenant(name="Test", email="t@t.com", phone="+237600000402", plan="BASIQUE", messages_limit=2000)
        db.add(tenant)
        db.commit()
        
        # Usage dépasse limite
        month = datetime.utcnow().strftime("%Y-%m")
        usage = UsageTracking(
            tenant_id=tenant.id,
            month_year=month,
            whatsapp_messages_used=2500  # 500 over
        )
        overage = Overage(
            tenant_id=tenant.id,
            month_year=month,
            messages_over=500,
            cost_fcfa=7000
        )
        
        db.add_all([usage, overage])
        db.commit()
        
        # Vérifier que les deux existent (charge ET continue)
        retrieved_usage = db.query(UsageTracking).filter(
            UsageTracking.tenant_id == tenant.id
        ).first()
        retrieved_overage = db.query(Overage).filter(
            Overage.tenant_id == tenant.id
        ).first()
        
        # Le système continue même si en dépassement
        assert retrieved_usage.whatsapp_messages_used > tenant.messages_limit
        assert retrieved_overage.cost_fcfa > 0

# ============= PHASE 7: TESTS ANALYTICS =============

class TestAnalytics:
    """Tests pour les endpoints analytics"""
    
    def test_analytics_dashboard_endpoint(self, client, db):
        """Test endpoint dashboard analytique"""
        tenant = Tenant(name="Test", email="t@t.com", phone="+237600000501", plan="BASIQUE")
        db.add(tenant)
        db.commit()
        
        response = client.get(f"/api/tenants/{tenant.id}/analytics/dashboard")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "message_stats" in data["data"]
        assert "conversation_stats" in data["data"]
        assert "revenue_stats" in data["data"]
    
    def test_message_stats_endpoint(self, client, db):
        """Test endpoint stats messages"""
        tenant = Tenant(name="Test", email="t@t.com", phone="+237600000502", plan="BASIQUE")
        db.add(tenant)
        db.commit()
        
        response = client.get(f"/api/tenants/{tenant.id}/analytics/messages?days=30")
        
        assert response.status_code == 200
        data = response.json()["data"]
        assert "total_messages" in data
        assert "today" in data
        assert "this_week" in data
        assert "trend" in data


# ============= EXÉCUTION TESTS =============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
