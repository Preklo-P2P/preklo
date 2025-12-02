"""
USDC Integration Tests
Comprehensive test suite for USDC functionality on Aptos
"""

import pytest
import httpx
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock, AsyncMock
from decimal import Decimal
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.models import User, Transaction, Balance
from app.services.aptos_service import aptos_service
from app.services.circle_service import circle_service
from app.config import settings
from fastapi.testclient import TestClient
from .test_helpers import override_db_dependency, create_mock_db


@pytest.fixture
def client():
    """Test client fixture compatible with httpx>=0.28."""
    original_init = httpx.Client.__init__

    def patched_init(self, *args, **kwargs):
        kwargs.pop("app", None)
        return original_init(self, *args, **kwargs)

    httpx.Client.__init__ = patched_init
    test_client = TestClient(app)
    try:
        yield test_client
    finally:
        test_client.close()
        httpx.Client.__init__ = original_init


@pytest.fixture
def db_session():
    """Create a mock database session for testing"""
    return create_mock_db()


@pytest.fixture
def test_user(db_session):
    """Create a test user with USDC balance"""
    from app.services.wallet_service import wallet_service
    
    user = User(
        username="testuser_usdc",
        wallet_address="0x1234567890123456789012345678901234567890123456789012345678901234",
        email="testusdc@example.com",
        full_name="Test USDC User",
        hashed_password="hashed_password_here",
        is_custodial=True,
        encrypted_private_key=wallet_service.encrypt_private_key("0x" + "1" * 64, "testpassword123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    # Add USDC balance
    balance = Balance(
        user_id=user.id,
        currency_type="USDC",
        balance=Decimal("100.0")
    )
    db_session.add(balance)
    db_session.commit()
    
    return user


@pytest.fixture
def authenticated_client(client, test_user):
    """Create an authenticated test client"""
    from app.services.auth_service import auth_service
    
    # Create token with proper format (dict with 'sub' key)
    token_data = {"sub": str(test_user.id)}
    token = auth_service.create_access_token(token_data)
    
    # Set auth header
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


class TestUSDCBalance:
    """Test USDC balance retrieval"""
    
    @patch('app.services.aptos_service.aptos_service.get_account_balance')
    def test_get_usdc_balance_success(self, mock_get_balance, authenticated_client, test_user):
        """Test successful USDC balance retrieval"""
        mock_get_balance.return_value = Decimal("100.5")
        
        response = authenticated_client.get(f"/api/v1/users/{test_user.id}/balances")
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        
        # Check if USDC balance is in the response
        balances = data["data"]
        usdc_balance = next((b for b in balances if b["currency_type"] == "USDC"), None)
        assert usdc_balance is not None
        assert Decimal(usdc_balance["balance"]) == Decimal("100.5")
    
    @patch('app.services.aptos_service.aptos_service.get_account_balance')
    def test_get_usdc_balance_zero(self, mock_get_balance, authenticated_client, test_user):
        """Test USDC balance when account has zero USDC"""
        mock_get_balance.return_value = Decimal("0")
        
        response = authenticated_client.get(f"/api/v1/users/{test_user.id}/balances")
        
        assert response.status_code == 200
        data = response.json()
        balances = data["data"]
        usdc_balance = next((b for b in balances if b["currency_type"] == "USDC"), None)
        assert usdc_balance is not None
        assert Decimal(usdc_balance["balance"]) == Decimal("0")


class TestUSDCTransfer:
    """Test USDC transfer functionality"""
    
    @patch('app.services.aptos_service.aptos_service.transfer_usdc')
    @patch('app.services.aptos_service.aptos_service.get_account_balance')
    def test_transfer_usdc_success(
        self, 
        mock_get_balance, 
        mock_transfer_usdc,
        authenticated_client, 
        test_user,
        db_session
    ):
        """Test successful USDC transfer"""
        # Mock balance check
        mock_get_balance.return_value = Decimal("100.0")
        
        # Mock successful transfer
        mock_transfer_usdc.return_value = "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        
        # Create recipient user
        recipient = User(
            username="recipient_usdc",
            wallet_address="0x9876543210987654321098765432109876543210987654321098765432109876",
            email="recipient@example.com",
            full_name="Recipient User",
            hashed_password="hashed_password",
            is_custodial=True
        )
        db_session.add(recipient)
        db_session.commit()
        db_session.refresh(recipient)
        
        # Create transfer request
        transfer_data = {
            "recipient": f"@{recipient.username}",
            "amount": "10.5",
            "currency_type": "USDC",
            "description": "Test USDC transfer"
        }
        
        response = authenticated_client.post(
            "/api/v1/transactions/transfer",
            json=transfer_data,
            params={"sender_private_key": "0x" + "1" * 64}
        )
        
        assert response.status_code == 200 or response.status_code == 201
        data = response.json()
        assert "data" in data or "transaction_hash" in data.get("data", {})
        
        # Verify transfer_usdc was called
        mock_transfer_usdc.assert_called_once()
        call_args = mock_transfer_usdc.call_args
        assert call_args[1]["amount"] == Decimal("10.5")
        assert call_args[1]["recipient_address"] == recipient.wallet_address
    
    @patch('app.services.aptos_service.aptos_service.get_account_balance')
    def test_transfer_usdc_insufficient_balance(
        self,
        mock_get_balance,
        authenticated_client,
        test_user,
        db_session
    ):
        """Test USDC transfer with insufficient balance"""
        # Mock insufficient balance
        mock_get_balance.return_value = Decimal("5.0")
        
        # Create recipient user
        recipient = User(
            username="recipient_usdc2",
            wallet_address="0x9876543210987654321098765432109876543210987654321098765432109876",
            email="recipient2@example.com",
            full_name="Recipient User 2",
            hashed_password="hashed_password",
            is_custodial=True
        )
        db_session.add(recipient)
        db_session.commit()
        
        transfer_data = {
            "recipient": f"@{recipient.username}",
            "amount": "10.5",
            "currency_type": "USDC",
            "description": "Test USDC transfer"
        }
        
        response = authenticated_client.post(
            "/api/v1/transactions/transfer",
            json=transfer_data,
            params={"sender_private_key": "0x" + "1" * 64}
        )
        
        # Should fail with insufficient balance
        assert response.status_code in [400, 500]
        assert "insufficient" in response.json().get("detail", "").lower() or \
               "balance" in response.json().get("detail", "").lower()
    
    @patch('app.services.aptos_service.aptos_service.transfer_usdc')
    @patch('app.services.aptos_service.aptos_service.get_account_balance')
    def test_transfer_usdc_invalid_recipient(
        self,
        mock_get_balance,
        mock_transfer_usdc,
        authenticated_client,
        test_user
    ):
        """Test USDC transfer to invalid recipient"""
        mock_get_balance.return_value = Decimal("100.0")
        
        transfer_data = {
            "recipient": "@nonexistent_user",
            "amount": "10.5",
            "currency_type": "USDC",
            "description": "Test USDC transfer"
        }
        
        response = authenticated_client.post(
            "/api/v1/transactions/transfer",
            json=transfer_data,
            params={"sender_private_key": "0x" + "1" * 64}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json().get("detail", "").lower()
        mock_transfer_usdc.assert_not_called()


class TestCustodialUSDCTransfer:
    """Test USDC transfers using custodial wallets"""
    
    @patch('app.services.aptos_service.aptos_service.transfer_usdc')
    @patch('app.services.aptos_service.aptos_service.get_account_balance')
    def test_custodial_transfer_usdc_success(
        self,
        mock_get_balance,
        mock_transfer_usdc,
        authenticated_client,
        test_user,
        db_session
    ):
        """Test successful custodial USDC transfer"""
        mock_get_balance.return_value = Decimal("100.0")
        mock_transfer_usdc.return_value = "0xtest_hash_1234567890"
        
        # Create recipient
        recipient = User(
            username="recipient_custodial",
            wallet_address="0x9876543210987654321098765432109876543210987654321098765432109876",
            email="recipient_custodial@example.com",
            full_name="Recipient",
            hashed_password="hashed",
            is_custodial=True
        )
        db_session.add(recipient)
        db_session.commit()
        db_session.refresh(recipient)
        
        transfer_data = {
            "recipient_username": recipient.username,
            "amount": "25.0",
            "currency_type": "USDC",
            "password": "testpassword123",
            "description": "Custodial USDC transfer"
        }
        
        response = authenticated_client.post(
            "/api/v1/transactions/send-custodial",
            json=transfer_data
        )
        
        # Should succeed
        assert response.status_code in [200, 201]
        mock_transfer_usdc.assert_called_once()


class TestCircleService:
    """Test Circle service integration (if configured)"""
    
    def test_circle_service_initialization(self):
        """Test Circle service initializes correctly"""
        assert circle_service is not None
        # If API key is not set, should be in mock mode
        if not settings.circle_api_key or settings.circle_api_key == "your_circle_api_key_here":
            assert circle_service.is_mock == True
    
    @pytest.mark.asyncio
    async def test_circle_service_mock_wallet_creation(self):
        """Test Circle service mock wallet creation"""
        # Force mock mode for testing
        original_is_mock = circle_service.is_mock
        circle_service.is_mock = True
        
        try:
            wallet = await circle_service.create_programmable_wallet(
                user_id="test_user_123",
                blockchain="APTOS-TESTNET"
            )
            
            assert wallet is not None
            assert "walletId" in wallet or "address" in wallet
        finally:
            # Restore original state
            circle_service.is_mock = original_is_mock
    
    @pytest.mark.asyncio
    async def test_circle_service_mock_balance(self):
        """Test Circle service mock balance retrieval"""
        balance = await circle_service.get_wallet_balance("mock_wallet_123")
        
        assert balance is not None
        if "tokenBalances" in balance:
            assert len(balance["tokenBalances"]) > 0


class TestUSDCContractAddress:
    """Test USDC contract address configuration"""
    
    def test_usdc_contract_address_configured(self):
        """Test that USDC contract address is configured"""
        assert settings.circle_usdc_contract_address is not None
        assert len(settings.circle_usdc_contract_address) > 0
        # Should be in format: address::module::struct
        assert "::" in settings.circle_usdc_contract_address
    
    def test_aptos_service_has_usdc_address(self):
        """Test that AptosService has USDC contract address"""
        assert aptos_service.usdc_contract_address is not None
        assert aptos_service.usdc_contract_address == settings.circle_usdc_contract_address


class TestUSDCIntegration:
    """Integration tests for USDC functionality"""
    
    @patch('app.services.aptos_service.aptos_service.get_account_balance')
    def test_usdc_balance_sync(
        self,
        mock_get_balance,
        authenticated_client,
        test_user
    ):
        """Test USDC balance synchronization"""
        mock_get_balance.return_value = Decimal("150.75")
        
        response = authenticated_client.post(
            f"/api/v1/users/{test_user.id}/sync-balances"
        )
        
        assert response.status_code == 200
        # Balance should be synced
        mock_get_balance.assert_called()
    
    @patch('app.services.aptos_service.aptos_service.transfer_usdc')
    @patch('app.services.aptos_service.aptos_service.get_account_balance')
    def test_usdc_payment_request(
        self,
        mock_get_balance,
        mock_transfer_usdc,
        authenticated_client,
        test_user,
        db_session
    ):
        """Test USDC payment request creation and payment"""
        mock_get_balance.return_value = Decimal("100.0")
        mock_transfer_usdc.return_value = "0xpayment_hash_123"
        
        # Create payment request
        payment_request = {
            "amount": "50.0",
            "currency_type": "USDC",
            "description": "USDC payment request",
            "expiry_hours": 24
        }
        
        create_response = authenticated_client.post(
            "/api/v1/payments/request",
            json=payment_request
        )
        
        assert create_response.status_code in [200, 201]
        payment_data = create_response.json()
        payment_id = payment_data.get("data", {}).get("payment_id")
        
        assert payment_id is not None
        
        # Pay the request
        pay_data = {
            "payment_id": payment_id,
            "password": "testpassword123"
        }
        
        pay_response = authenticated_client.post(
            "/api/v1/payments/pay",
            json=pay_data
        )
        
        # Payment should be initiated
        assert pay_response.status_code in [200, 201, 202]

