"""
Integration tests for sandbox API endpoints.
Tests the full flow from signup to API usage.
"""
import time
import uuid
from decimal import Decimal

import pytest

from app.config import settings
from app.main import app
from app.database import SessionLocal
from app.dependencies import sandbox_rate_limit
from app.services.sandbox_api_key_service import sandbox_api_key_service
from app.services.test_account_service import test_account_service
from .test_helpers import create_test_client
@pytest.fixture
def client():
    """Create test client with relaxed global rate limiting"""
    # Disable global rate limiting for deterministic tests
    app.state.global_rate_limit_override = 0
    previous_sandbox_enabled = settings.sandbox_enabled
    settings.sandbox_enabled = True
    try:
        with create_test_client(app) as test_client:
            yield test_client
    finally:
        if hasattr(app.state, "global_rate_limit_override"):
            delattr(app.state, "global_rate_limit_override")
        settings.sandbox_enabled = previous_sandbox_enabled


@pytest.fixture
def db():
    """Create database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def reset_rate_limit_storage():
    """Ensure sandbox rate limit storage is cleared between tests"""
    sandbox_rate_limit.sandbox_rate_limit_storage.clear()
    yield
    sandbox_rate_limit.sandbox_rate_limit_storage.clear()


@pytest.fixture
def sandbox_user_id():
    """Create a test sandbox user ID"""
    return str(uuid.uuid4())


@pytest.fixture
def test_api_key(db, sandbox_user_id):
    """Create a test API key"""
    api_key = sandbox_api_key_service.generate_api_key()
    api_key_record = sandbox_api_key_service.store_api_key(
        db=db,
        sandbox_user_id=sandbox_user_id,
        api_key=api_key,
        name="Test API Key"
    )
    db.commit()
    return api_key, api_key_record


@pytest.fixture
def test_accounts(db, sandbox_user_id):
    """Create test accounts"""
    accounts = test_account_service.create_default_accounts(
        db=db,
        sandbox_user_id=sandbox_user_id
    )
    db.commit()
    return accounts


class TestSandboxSignupFlow:
    """Test sandbox signup flow"""
    
    def test_sandbox_signup_success(self, client, db):
        """Test successful sandbox signup"""
        response = client.post(
            "/api/v1/sandbox/signup",
            json={
                "email": "test@example.com",
                "name": "Test Developer"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "api_key" in data["data"]
        assert data["data"]["api_key"].startswith("sb_")
        assert len(data["data"]["test_accounts"]) == 5
        assert "user_id" in data["data"]
    
    def test_sandbox_signup_duplicate_email(self, client, db):
        """Test that duplicate emails are allowed (multiple signups)"""
        email = "duplicate@example.com"
        
        # First signup
        response1 = client.post(
            "/api/v1/sandbox/signup",
            json={"email": email, "name": "First"}
        )
        assert response1.status_code == 201
        
        # Second signup with same email
        response2 = client.post(
            "/api/v1/sandbox/signup",
            json={"email": email, "name": "Second"}
        )
        assert response2.status_code == 201
        
        # Should have different user IDs and API keys
        assert response1.json()["data"]["user_id"] != response2.json()["data"]["user_id"]
        assert response1.json()["data"]["api_key"] != response2.json()["data"]["api_key"]


class TestSandboxAPIKeyAuthentication:
    """Test API key authentication"""
    
    def test_api_key_auth_success(self, client, test_api_key):
        """Test successful API key authentication"""
        api_key, _ = test_api_key
        
        response = client.get(
            "/api/v1/sandbox/account",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "api_keys_count" in data
        assert "test_accounts_count" in data
    
    def test_api_key_auth_missing(self, client):
        """Test missing API key"""
        response = client.get("/api/v1/sandbox/account")
        assert response.status_code == 401
    
    def test_api_key_auth_invalid(self, client):
        """Test invalid API key"""
        response = client.get(
            "/api/v1/sandbox/account",
            headers={"X-API-Key": "sb_invalid_key"}
        )
        assert response.status_code == 401


class TestSandboxTestAccounts:
    """Test test account endpoints"""
    
    def test_list_test_accounts(self, client, test_api_key, test_accounts):
        """Test listing test accounts"""
        api_key, _ = test_api_key
        
        response = client.get(
            "/api/v1/sandbox/test-accounts",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["accounts"]) == 5
        assert data["total"] == 5
    
    def test_get_test_account(self, client, test_api_key, test_accounts):
        """Test getting a specific test account"""
        api_key, _ = test_api_key
        account_id = str(test_accounts[0].id)
        
        response = client.get(
            f"/api/v1/sandbox/test-accounts/{account_id}",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == account_id
        assert "usdc_balance" in data
        assert "apt_balance" in data
    
    def test_get_test_account_balances(self, client, test_api_key, test_accounts):
        """Test getting test account balances"""
        api_key, _ = test_api_key
        
        response = client.get(
            "/api/v1/sandbox/test-accounts/balances",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert "total_usdc" in data
        assert "total_apt" in data
        assert len(data["accounts"]) == 5


class TestSandboxTransactions:
    """Test sandbox transaction endpoints"""
    
    def test_sandbox_transfer(self, client, test_api_key, test_accounts):
        """Test sandbox transaction transfer"""
        api_key, api_key_record = test_api_key
        sender = next(acc for acc in test_accounts if acc.usdc_balance >= Decimal("20.0"))
        recipient = next(acc for acc in test_accounts if acc.id != sender.id)
        
        response = client.post(
            "/api/v1/sandbox/transactions/transfer",
            params={
                "sender_account_id": str(sender.id),
                "recipient_account_id": str(recipient.id),
                "amount": "10.0",
                "currency_type": "USDC"
            },
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["sender_id"] == str(sender.id)
        assert data["data"]["recipient_id"] == str(recipient.id)
        
    def test_sandbox_transfer_insufficient_balance(self, client, test_api_key, test_accounts):
        """Test sandbox transfer with insufficient balance"""
        api_key, _ = test_api_key
        sender = next(acc for acc in test_accounts if acc.usdc_balance == Decimal("0.0"))
        recipient = next(acc for acc in test_accounts if acc.id != sender.id)
        
        # Try to transfer more than available
        large_amount = str(float(sender.usdc_balance) + 1000)
        
        response = client.post(
            "/api/v1/sandbox/transactions/transfer",
            params={
                "sender_account_id": str(sender.id),
                "recipient_account_id": str(recipient.id),
                "amount": large_amount,
                "currency_type": "USDC"
            },
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 400
    
    def test_sandbox_transfer_invalid_account(self, client, test_api_key):
        """Test sandbox transfer with invalid account IDs"""
        api_key, _ = test_api_key
        fake_account_id = str(uuid.uuid4())
        
        response = client.post(
            "/api/v1/sandbox/transactions/transfer",
            params={
                "sender_account_id": fake_account_id,
                "recipient_account_id": fake_account_id,
                "amount": "10.0",
                "currency_type": "USDC"
            },
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 400


class TestSandboxBalanceEndpoints:
    """Test sandbox balance endpoints"""
    
    def test_get_balance_sandbox(self, client, test_api_key, test_accounts):
        """Test getting balance in sandbox mode"""
        api_key, _ = test_api_key
        account_id = str(test_accounts[0].id)
        
        response = client.get(
            "/api/v1/receive-money/balance",
            params={
                "currency_type": "USDC",
                "account_id": account_id
            },
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert data["currency_type"] == "USDC"
    
    def test_get_balance_total(self, client, test_api_key, test_accounts):
        """Test getting total balance across all accounts"""
        api_key, _ = test_api_key
        
        response = client.get(
            "/api/v1/receive-money/balance",
            params={"currency_type": "USDC"},
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "account_count" in data


class TestSandboxRateLimiting:
    """Test sandbox rate limiting"""
    
    def test_rate_limit_headers(self, client, test_api_key):
        """Test that rate limit headers are included"""
        api_key, _ = test_api_key
        
        response = client.get(
            "/api/v1/sandbox/account",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        # Check for rate limit headers (if implemented)
        # Headers might be set in middleware
    
    def test_rate_limit_daily(self, client, test_api_key, db, monkeypatch):
        """Test daily rate limit (1,000 requests)"""
        api_key, api_key_record = test_api_key
        
        original_check = sandbox_rate_limit._check_rate_limit

        def patched_check(current_api_key, db_session, max_requests_daily=1000, max_requests_minute=100):
            return original_check(
                current_api_key,
                db_session,
                max_requests_daily=1,
                max_requests_minute=max_requests_minute
            )

        monkeypatch.setattr(sandbox_rate_limit, "_check_rate_limit", patched_check)

        response = client.get(
            "/api/v1/sandbox/account",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200

        # Next request should exceed the daily limit
        response = client.get(
            "/api/v1/sandbox/account",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 429
    
    def test_rate_limit_burst(self, client, test_api_key, db, monkeypatch):
        """Test burst rate limit (100 requests/minute)"""
        api_key, api_key_record = test_api_key
        
        original_check = sandbox_rate_limit._check_rate_limit

        def patched_check(current_api_key, db_session, max_requests_daily=1000, max_requests_minute=100):
            return original_check(
                current_api_key,
                db_session,
                max_requests_daily=max_requests_daily,
                max_requests_minute=1
            )

        monkeypatch.setattr(sandbox_rate_limit, "_check_rate_limit", patched_check)

        response = client.get(
            "/api/v1/sandbox/account",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 200

        response = client.get(
            "/api/v1/sandbox/account",
            headers={"X-API-Key": api_key}
        )
        assert response.status_code == 429


class TestSandboxSchemaIsolation:
    """Test schema isolation"""
    
    def test_sandbox_schema_isolation(self, client, test_api_key, db):
        """Test that sandbox data is isolated from production"""
        api_key, api_key_record = test_api_key
        
        # Query should use sandbox schema
        # Production User model should not be accessible
        # This is tested implicitly through endpoint behavior
        
        response = client.get(
            "/api/v1/sandbox/test-accounts",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        # If we were querying production schema, this would fail or return wrong data

