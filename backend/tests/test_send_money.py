"""
Tests for Send Money Service (Story 2.3)
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.send_money_service import send_money_service
from app.schemas import SendMoneyRequest, SendMoneyResponse
from app.models import User


class TestSendMoneyService:
    """Test the enhanced send money service"""
    
    def setup_method(self):
        """Setup test data"""
        self.mock_user = Mock(spec=User)
        self.mock_user.id = "test-user-id"
        self.mock_user.username = "testuser"
        self.mock_user.wallet_address = "0x1234567890abcdef"
        self.mock_user.is_custodial = True
        self.mock_user.encrypted_private_key = "encrypted_key"
        self.mock_user.hashed_password = "hashed_password"
        
        self.mock_recipient = Mock(spec=User)
        self.mock_recipient.id = "recipient-id"
        self.mock_recipient.username = "recipient"
        self.mock_recipient.wallet_address = "0xabcdef1234567890"
        
        self.mock_db = Mock(spec=Session)
        
        # Clear any existing confirmations
        send_money_service._pending_confirmations.clear()
    
    @pytest.mark.asyncio
    async def test_initiate_send_money_success(self):
        """Test successful send money initiation"""
        request = SendMoneyRequest(
            recipient_username="recipient",
            amount="10.0",
            currency_type="APT",
            password="test_password",
            description="Test payment"
        )
        
        with patch('app.services.send_money_service.auth_service') as mock_auth, \
             patch('app.services.send_money_service.aptos_service') as mock_aptos, \
             patch('app.services.send_money_service.wallet_service') as mock_wallet:
            
            # Mock successful authentication
            mock_auth.verify_password.return_value = True
            
            # Mock balance check
            mock_aptos.get_account_balance = AsyncMock(return_value=Decimal("100.0"))
            
            # Mock gas fee estimation
            mock_aptos.estimate_gas_fee = AsyncMock(return_value=Decimal("0.01"))
            
            # Mock database query
            self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_recipient
            
            result = await send_money_service.initiate_send_money(
                request, self.mock_user, self.mock_db
            )
            
            assert result.success is True
            assert result.transaction_id is not None
            assert "confirmation created" in result.message.lower()
            assert result.data is not None
    
    @pytest.mark.asyncio
    async def test_initiate_send_money_recipient_not_found(self):
        """Test send money initiation with non-existent recipient"""
        request = SendMoneyRequest(
            recipient_username="nonexistent",
            amount="10.0",
            currency_type="APT",
            password="test_password"
        )
        
        with patch('app.services.send_money_service.auth_service') as mock_auth:
            mock_auth.verify_password.return_value = True
            
            # Mock database query to return None (recipient not found)
            self.mock_db.query.return_value.filter.return_value.first.return_value = None
            
            result = await send_money_service.initiate_send_money(
                request, self.mock_user, self.mock_db
            )
            
            assert result.success is False
            assert "not found" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_initiate_send_money_insufficient_balance(self):
        """Test send money initiation with insufficient balance"""
        request = SendMoneyRequest(
            recipient_username="recipient",
            amount="1000.0",  # Large amount
            currency_type="APT",
            password="test_password"
        )
        
        with patch('app.services.send_money_service.auth_service') as mock_auth, \
             patch('app.services.send_money_service.aptos_service') as mock_aptos:
            
            mock_auth.verify_password.return_value = True
            
            # Mock low balance
            mock_aptos.get_account_balance = AsyncMock(return_value=Decimal("10.0"))
            mock_aptos.estimate_gas_fee = AsyncMock(return_value=Decimal("0.01"))
            
            self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_recipient
            
            result = await send_money_service.initiate_send_money(
                request, self.mock_user, self.mock_db
            )
            
            assert result.success is False
            assert "insufficient balance" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_initiate_send_money_invalid_password(self):
        """Test send money initiation with invalid password"""
        request = SendMoneyRequest(
            recipient_username="recipient",
            amount="10.0",
            currency_type="APT",
            password="wrong_password"
        )
        
        with patch('app.services.send_money_service.auth_service') as mock_auth:
            mock_auth.verify_password.return_value = False
            
            result = await send_money_service.initiate_send_money(
                request, self.mock_user, self.mock_db
            )
            
            assert result.success is False
            assert "invalid password" in result.message.lower()
    
    @pytest.mark.asyncio
    async def test_confirm_send_money_success(self):
        """Test successful send money confirmation"""
        # First create a confirmation
        request = SendMoneyRequest(
            recipient_username="recipient",
            amount="10.0",
            currency_type="APT",
            password="test_password"
        )
        
        with patch('app.services.send_money_service.auth_service') as mock_auth, \
             patch('app.services.send_money_service.aptos_service') as mock_aptos, \
             patch('app.services.send_money_service.wallet_service') as mock_wallet:
            
            mock_auth.verify_password.return_value = True
            mock_aptos.get_account_balance = AsyncMock(return_value=Decimal("100.0"))
            mock_aptos.estimate_gas_fee = AsyncMock(return_value=Decimal("0.01"))
            self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_recipient
            
            # Create confirmation
            initiate_result = await send_money_service.initiate_send_money(
                request, self.mock_user, self.mock_db
            )
            
            assert initiate_result.success is True
            transaction_id = initiate_result.transaction_id
            
            # Mock wallet service and blockchain transaction
            mock_account = Mock()
            mock_account.private_key.hex.return_value = "private_key_hex"
            mock_wallet.get_account_for_transaction.return_value = mock_account
            
            mock_aptos.transfer_apt = AsyncMock(return_value="0x1234567890abcdef")
            mock_aptos.monitor_transaction = AsyncMock(return_value=None)
            
            # Mock database transaction creation
            mock_transaction = Mock()
            mock_transaction.id = "transaction-id"
            self.mock_db.add.return_value = None
            self.mock_db.commit.return_value = None
            self.mock_db.refresh.return_value = None
            
            # Confirm transaction
            confirm_result = await send_money_service.confirm_send_money(
                transaction_id, self.mock_db
            )
            
            assert confirm_result.success is True
            assert confirm_result.transaction_hash == "0x1234567890abcdef"
            assert "successfully sent" in confirm_result.message.lower()
    
    @pytest.mark.asyncio
    async def test_confirm_send_money_expired(self):
        """Test confirmation of expired transaction"""
        # Create a confirmation and manually expire it
        request = SendMoneyRequest(
            recipient_username="recipient",
            amount="10.0",
            currency_type="APT",
            password="test_password"
        )
        
        with patch('app.services.send_money_service.auth_service') as mock_auth, \
             patch('app.services.send_money_service.aptos_service') as mock_aptos:
            
            mock_auth.verify_password.return_value = True
            mock_aptos.get_account_balance = AsyncMock(return_value=Decimal("100.0"))
            mock_aptos.estimate_gas_fee = AsyncMock(return_value=Decimal("0.01"))
            self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_recipient
            
            # Create confirmation
            initiate_result = await send_money_service.initiate_send_money(
                request, self.mock_user, self.mock_db
            )
            
            transaction_id = initiate_result.transaction_id
            
            # Manually expire the confirmation
            send_money_service._pending_confirmations[transaction_id]["confirmation"].expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
            
            # Try to confirm expired transaction
            confirm_result = await send_money_service.confirm_send_money(
                transaction_id, self.mock_db
            )
            
            assert confirm_result.success is False
            assert "expired" in confirm_result.message.lower()
    
    @pytest.mark.asyncio
    async def test_get_transaction_status(self):
        """Test getting transaction status"""
        # Mock database transaction
        mock_transaction = Mock()
        mock_transaction.id = "transaction-id"
        mock_transaction.transaction_hash = "0x1234567890abcdef"
        mock_transaction.status = "confirmed"
        mock_transaction.block_height = 12345
        mock_transaction.gas_fee = Decimal("0.01")
        mock_transaction.updated_at = datetime.now(timezone.utc)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_transaction
        
        with patch('app.services.send_money_service.aptos_service') as mock_aptos:
            mock_aptos.get_transaction_status = AsyncMock(return_value={
                "status": "confirmed",
                "block_height": 12345,
                "gas_fee": "0.01"
            })
            
            status = await send_money_service.get_transaction_status(
                "transaction-id", self.mock_db
            )
            
            assert status is not None
            assert status.transaction_id == "transaction-id"
            assert status.status == "confirmed"
            assert status.block_height == 12345
    
    def test_get_confirmation_details(self):
        """Test getting confirmation details"""
        # Create a confirmation manually
        from app.schemas import SendMoneyConfirmation
        
        confirmation = SendMoneyConfirmation(
            transaction_id="test-id",
            recipient_username="recipient",
            recipient_address="0x123",
            amount="10.0",
            currency_type="APT",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
        )
        
        send_money_service._pending_confirmations["test-id"] = {
            "confirmation": confirmation,
            "request": None,
            "current_user": None,
            "recipient_user": None,
            "created_at": datetime.now(timezone.utc)
        }
        
        result = send_money_service.get_confirmation_details("test-id")
        
        assert result is not None
        assert result.transaction_id == "test-id"
        assert result.recipient_username == "recipient"
    
    def test_get_confirmation_details_not_found(self):
        """Test getting confirmation details for non-existent transaction"""
        result = send_money_service.get_confirmation_details("nonexistent-id")
        assert result is None
    
    def test_cleanup_expired_confirmations(self):
        """Test cleanup of expired confirmations"""
        # Create an expired confirmation
        from app.schemas import SendMoneyConfirmation
        
        expired_confirmation = SendMoneyConfirmation(
            transaction_id="expired-id",
            recipient_username="recipient",
            recipient_address="0x123",
            amount="10.0",
            currency_type="APT",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)  # Expired
        )
        
        send_money_service._pending_confirmations["expired-id"] = {
            "confirmation": expired_confirmation,
            "request": None,
            "current_user": None,
            "recipient_user": None,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Create a valid confirmation
        valid_confirmation = SendMoneyConfirmation(
            transaction_id="valid-id",
            recipient_username="recipient",
            recipient_address="0x123",
            amount="10.0",
            currency_type="APT",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)  # Valid
        )
        
        send_money_service._pending_confirmations["valid-id"] = {
            "confirmation": valid_confirmation,
            "request": None,
            "current_user": None,
            "recipient_user": None,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Run cleanup
        send_money_service.cleanup_expired_confirmations()
        
        # Check that expired confirmation was removed
        assert "expired-id" not in send_money_service._pending_confirmations
        assert "valid-id" in send_money_service._pending_confirmations


class TestSendMoneyIntegration:
    """Integration tests for send money functionality"""
    
    @pytest.mark.asyncio
    async def test_send_money_flow_integration(self):
        """Test complete send money flow"""
        # This would be an integration test that tests the entire flow
        # from initiation to confirmation to status checking
        pass
    
    @pytest.mark.asyncio
    async def test_send_money_error_handling(self):
        """Test error handling in send money flow"""
        # Test various error scenarios
        pass
