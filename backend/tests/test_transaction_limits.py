"""
Tests for Transaction Limits Service (Story 2.6)
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.transaction_limits_service import transaction_limits_service
from app.models import User, TransactionLimit, SpendingControl, TransactionApproval, EmergencyBlock


class TestTransactionLimitsService:
    """Test the transaction limits service"""
    
    def setup_method(self):
        """Setup test data"""
        self.mock_user = Mock(spec=User)
        self.mock_user.id = "test-user-id"
        self.mock_user.username = "testuser"
        self.mock_user.wallet_address = "0x1234567890abcdef"
        
        self.mock_db = Mock(spec=Session)
    
    @pytest.mark.asyncio
    async def test_check_transaction_limits_allowed(self):
        """Test transaction limits check when transaction is allowed"""
        # Mock no limits set
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        is_allowed, error_message, approval_data = await transaction_limits_service.check_transaction_limits(
            self.mock_user, Decimal("10.0"), "APT", self.mock_db
        )
        
        assert is_allowed is True
        assert error_message is None
        assert approval_data is None
    
    @pytest.mark.asyncio
    async def test_check_transaction_limits_high_value_approval(self):
        """Test transaction limits check when high-value approval is required"""
        # Mock no limits set
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        is_allowed, error_message, approval_data = await transaction_limits_service.check_transaction_limits(
            self.mock_user, Decimal("1500.0"), "APT", self.mock_db
        )
        
        assert is_allowed is True
        assert error_message is None
        assert approval_data is not None
        assert approval_data["approval_required"] is True
        assert approval_data["approval_type"] == "high_value"
    
    @pytest.mark.asyncio
    async def test_check_daily_limit_exceeded(self):
        """Test daily limit exceeded"""
        # Mock daily limit
        mock_limit = Mock(spec=TransactionLimit)
        mock_limit.limit_amount = Decimal("100.0")
        mock_limit.period_start = datetime.now(timezone.utc)
        mock_limit.period_end = datetime.now(timezone.utc) + timedelta(days=1)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_limit
        
        # Mock current usage calculation
        with patch.object(transaction_limits_service, '_calculate_period_usage') as mock_usage:
            mock_usage.return_value = Decimal("95.0")
            
            is_allowed, error_message = await transaction_limits_service._check_daily_limit(
                self.mock_user, Decimal("10.0"), "APT", self.mock_db
            )
            
            assert is_allowed is False
            assert "exceed daily limit" in error_message
    
    @pytest.mark.asyncio
    async def test_check_daily_limit_within_limit(self):
        """Test daily limit within allowed amount"""
        # Mock daily limit
        mock_limit = Mock(spec=TransactionLimit)
        mock_limit.limit_amount = Decimal("100.0")
        mock_limit.period_start = datetime.now(timezone.utc)
        mock_limit.period_end = datetime.now(timezone.utc) + timedelta(days=1)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_limit
        
        # Mock current usage calculation
        with patch.object(transaction_limits_service, '_calculate_period_usage') as mock_usage:
            mock_usage.return_value = Decimal("50.0")
            
            is_allowed, error_message = await transaction_limits_service._check_daily_limit(
                self.mock_user, Decimal("10.0"), "APT", self.mock_db
            )
            
            assert is_allowed is True
            assert error_message is None
    
    @pytest.mark.asyncio
    async def test_check_spending_controls_max_amount_exceeded(self):
        """Test spending controls with max amount exceeded"""
        # Mock spending control
        mock_control = Mock(spec=SpendingControl)
        mock_control.control_type = "max_amount"
        mock_control.max_amount = Decimal("50.0")
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_control]
        
        is_allowed, error_message = await transaction_limits_service._check_spending_controls(
            self.mock_user, Decimal("75.0"), "APT", self.mock_db
        )
        
        assert is_allowed is False
        assert "exceeds maximum allowed amount" in error_message
    
    @pytest.mark.asyncio
    async def test_check_spending_controls_within_limit(self):
        """Test spending controls within allowed amount"""
        # Mock spending control
        mock_control = Mock(spec=SpendingControl)
        mock_control.control_type = "max_amount"
        mock_control.max_amount = Decimal("100.0")
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_control]
        
        is_allowed, error_message = await transaction_limits_service._check_spending_controls(
            self.mock_user, Decimal("50.0"), "APT", self.mock_db
        )
        
        assert is_allowed is True
        assert error_message is None
    
    @pytest.mark.asyncio
    async def test_check_emergency_blocks_active_block(self):
        """Test emergency blocks with active block"""
        # Mock active emergency block
        mock_block = Mock(spec=EmergencyBlock)
        mock_block.reason = "Suspicious activity"
        
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_block]
        
        is_allowed, error_message = await transaction_limits_service._check_emergency_blocks(
            self.mock_user, self.mock_db
        )
        
        assert is_allowed is False
        assert "Account is blocked" in error_message
        assert "Suspicious activity" in error_message
    
    @pytest.mark.asyncio
    async def test_check_emergency_blocks_no_blocks(self):
        """Test emergency blocks with no active blocks"""
        # Mock no active blocks
        self.mock_db.query.return_value.filter.return_value.all.return_value = []
        
        is_allowed, error_message = await transaction_limits_service._check_emergency_blocks(
            self.mock_user, self.mock_db
        )
        
        assert is_allowed is True
        assert error_message is None
    
    @pytest.mark.asyncio
    async def test_calculate_period_usage(self):
        """Test period usage calculation"""
        # Mock database query result
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = Decimal("25.0")
        
        usage = await transaction_limits_service._calculate_period_usage(
            self.mock_user, "APT", 
            datetime.now(timezone.utc), 
            datetime.now(timezone.utc) + timedelta(days=1), 
            self.mock_db
        )
        
        assert usage == Decimal("25.0")
    
    @pytest.mark.asyncio
    async def test_calculate_period_usage_no_transactions(self):
        """Test period usage calculation with no transactions"""
        # Mock database query result
        self.mock_db.query.return_value.filter.return_value.scalar.return_value = None
        
        usage = await transaction_limits_service._calculate_period_usage(
            self.mock_user, "APT", 
            datetime.now(timezone.utc), 
            datetime.now(timezone.utc) + timedelta(days=1), 
            self.mock_db
        )
        
        assert usage == Decimal("0")
    
    @pytest.mark.asyncio
    async def test_create_transaction_approval(self):
        """Test creating transaction approval"""
        # Mock database operations
        self.mock_db.add.return_value = None
        self.mock_db.commit.return_value = None
        self.mock_db.refresh.return_value = None
        
        with patch.object(transaction_limits_service, '_create_approval_notification') as mock_notification:
            mock_notification.return_value = None
            
            approval = await transaction_limits_service.create_transaction_approval(
                self.mock_user, Decimal("1000.0"), "APT", "high_value", "Test approval", self.mock_db
            )
            
            assert approval is not None
            assert approval.amount == Decimal("1000.0")
            assert approval.currency_type == "APT"
            assert approval.approval_type == "high_value"
            assert approval.status == "pending"
    
    @pytest.mark.asyncio
    async def test_approve_transaction_success(self):
        """Test approving transaction successfully"""
        # Mock approval
        mock_approval = Mock(spec=TransactionApproval)
        mock_approval.id = "approval-id"
        mock_approval.status = "pending"
        mock_approval.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_approval.amount = Decimal("1000.0")
        mock_approval.currency_type = "APT"
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_approval
        self.mock_db.commit.return_value = None
        
        with patch.object(transaction_limits_service, '_create_approval_result_notification') as mock_notification:
            mock_notification.return_value = None
            
            result = await transaction_limits_service.approve_transaction(
                "approval-id", self.mock_user, "manual", self.mock_db
            )
            
            assert result.success is True
            assert "approved successfully" in result.message
            assert mock_approval.status == "approved"
    
    @pytest.mark.asyncio
    async def test_approve_transaction_not_found(self):
        """Test approving non-existent transaction"""
        # Mock no approval found
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await transaction_limits_service.approve_transaction(
            "non-existent-id", self.mock_user, "manual", self.mock_db
        )
        
        assert result.success is False
        assert "not found" in result.message
    
    @pytest.mark.asyncio
    async def test_approve_transaction_expired(self):
        """Test approving expired transaction"""
        # Mock expired approval
        mock_approval = Mock(spec=TransactionApproval)
        mock_approval.id = "approval-id"
        mock_approval.status = "pending"
        mock_approval.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_approval
        self.mock_db.commit.return_value = None
        
        result = await transaction_limits_service.approve_transaction(
            "approval-id", self.mock_user, "manual", self.mock_db
        )
        
        assert result.success is False
        assert "expired" in result.message
        assert mock_approval.status == "expired"
    
    @pytest.mark.asyncio
    async def test_reject_transaction_success(self):
        """Test rejecting transaction successfully"""
        # Mock approval
        mock_approval = Mock(spec=TransactionApproval)
        mock_approval.id = "approval-id"
        mock_approval.status = "pending"
        mock_approval.amount = Decimal("1000.0")
        mock_approval.currency_type = "APT"
        mock_approval.description = "Test transaction"
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_approval
        self.mock_db.commit.return_value = None
        
        with patch.object(transaction_limits_service, '_create_approval_result_notification') as mock_notification:
            mock_notification.return_value = None
            
            result = await transaction_limits_service.reject_transaction(
                "approval-id", self.mock_user, "Suspicious activity", self.mock_db
            )
            
            assert result.success is True
            assert "rejected successfully" in result.message
            assert mock_approval.status == "rejected"
    
    @pytest.mark.asyncio
    async def test_create_emergency_block(self):
        """Test creating emergency block"""
        # Mock database operations
        self.mock_db.add.return_value = None
        self.mock_db.commit.return_value = None
        
        with patch.object(transaction_limits_service, '_create_emergency_block_notification') as mock_notification:
            mock_notification.return_value = None
            
            result = await transaction_limits_service.create_emergency_block(
                self.mock_user, "account_freeze", "Suspicious activity", "Test block", self.mock_user, self.mock_db
            )
            
            assert result.success is True
            assert "block created successfully" in result.message
    
    @pytest.mark.asyncio
    async def test_remove_emergency_block_success(self):
        """Test removing emergency block successfully"""
        # Mock emergency block
        mock_block = Mock(spec=EmergencyBlock)
        mock_block.id = "block-id"
        mock_block.is_active = True
        mock_block.user_id = self.mock_user.id
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_block
        self.mock_db.commit.return_value = None
        
        with patch.object(transaction_limits_service, '_create_emergency_unblock_notification') as mock_notification:
            mock_notification.return_value = None
            
            result = await transaction_limits_service.remove_emergency_block(
                "block-id", self.mock_user, self.mock_db
            )
            
            assert result.success is True
            assert "block removed successfully" in result.message
            assert mock_block.is_active is False
    
    @pytest.mark.asyncio
    async def test_remove_emergency_block_not_found(self):
        """Test removing non-existent emergency block"""
        # Mock no block found
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = await transaction_limits_service.remove_emergency_block(
            "non-existent-id", self.mock_user, self.mock_db
        )
        
        assert result.success is False
        assert "not found" in result.message


class TestTransactionLimitsIntegration:
    """Integration tests for transaction limits functionality"""
    
    @pytest.mark.asyncio
    async def test_transaction_limits_flow_integration(self):
        """Test complete transaction limits flow"""
        # This would be an integration test that tests the entire flow
        # from limit checking to approval to emergency blocking
        pass
    
    @pytest.mark.asyncio
    async def test_transaction_limits_error_handling(self):
        """Test error handling in transaction limits flow"""
        # Test various error scenarios
        pass
