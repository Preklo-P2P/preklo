"""
Tests for Voucher Service
"""

import pytest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock, patch
from pydantic import ValidationError

from app.services.voucher_service import VoucherService
from app.models import Voucher, User
from app.schemas import VoucherCreate, VoucherRedeem


class TestVoucherService:
    @pytest.fixture
    def mock_db(self):
        return Mock()

    @pytest.fixture
    def voucher_service(self, mock_db):
        return VoucherService(mock_db)

    @pytest.fixture
    def mock_user(self):
        user = Mock(spec=User)
        user.id = "user-123"
        user.username = "test_user"
        return user

    @pytest.fixture
    def mock_voucher(self):
        voucher = Mock(spec=Voucher)
        voucher.id = "voucher-123"
        voucher.voucher_code = "ABC123DEF456GHI789"
        voucher.creator_id = "user-123"
        voucher.amount = Decimal("100.00")
        voucher.currency_type = "USDC"
        voucher.status = "active"
        voucher.pin_hash = None
        voucher.expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        voucher.redeemed_at = None
        voucher.redeemed_by = None
        voucher.created_at = datetime.now(timezone.utc)
        voucher.updated_at = datetime.now(timezone.utc)
        voucher.creator = None
        voucher.redeemer = None
        return voucher

    def test_create_voucher_success(self, voucher_service, mock_db, mock_user):
        """Test successful voucher creation"""
        # Arrange
        voucher_data = VoucherCreate(
            amount=Decimal("100.00"),
            currency="USDC",
            pin="1234",
            expires_in_hours=24
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        with patch.object(voucher_service, '_generate_voucher_code', return_value="ABC123DEF456GHI789"):
            with patch.object(voucher_service, '_hash_pin', return_value="hashed_pin"):
                with patch.object(voucher_service, '_format_voucher_response') as mock_format:
                    mock_format.return_value = {"id": "voucher-123"}
                    result = voucher_service.create_voucher("user-123", voucher_data)
        
        # Assert
        assert result is not None
        assert mock_db.add.call_count == 2  # Once for voucher, once for notification
        assert mock_db.commit.call_count == 2  # Once for voucher, once for notification
        assert mock_db.refresh.call_count == 2  # Once for voucher, once for notification

    def test_create_voucher_user_not_found(self, voucher_service, mock_db):
        """Test voucher creation with non-existent user"""
        # Arrange
        voucher_data = VoucherCreate(
            amount=Decimal("100.00"),
            currency="USDC"
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="User not found"):
            voucher_service.create_voucher("user-123", voucher_data)

    def test_create_voucher_invalid_amount(self, voucher_service, mock_db, mock_user):
        """Test voucher creation with invalid amount"""
        # Test that Pydantic validation rejects invalid amounts
        with pytest.raises(ValidationError) as exc_info:
            VoucherCreate(
                amount=Decimal("0.00"),
                currency="USDC"
            )
        
        # Verify the error message contains the expected validation error
        assert "Amount must be greater than 0" in str(exc_info.value)

    def test_redeem_voucher_success(self, voucher_service, mock_db, mock_voucher):
        """Test successful voucher redemption"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_voucher
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # Act
        with patch.object(voucher_service, '_format_voucher_response') as mock_format:
            mock_format.return_value = {"id": "voucher-123", "status": "redeemed"}
            result = voucher_service.redeem_voucher("ABC123DEF456GHI789", "user-456")
        
        # Assert
        assert result is not None
        assert mock_voucher.status == "redeemed"
        assert mock_voucher.redeemed_by == "user-456"
        assert mock_voucher.redeemed_at is not None
        assert mock_db.commit.call_count == 3  # Once for voucher, twice for notifications

    def test_redeem_voucher_not_found(self, voucher_service, mock_db):
        """Test voucher redemption with non-existent voucher"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match="Voucher not found"):
            voucher_service.redeem_voucher("INVALID123CODE456", "user-456")

    def test_redeem_voucher_expired(self, voucher_service, mock_db, mock_voucher):
        """Test redemption of expired voucher"""
        # Arrange
        mock_voucher.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_voucher
        mock_db.commit = Mock()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Voucher has expired"):
            voucher_service.redeem_voucher("ABC123DEF456GHI789", "user-456")

    def test_redeem_voucher_own_voucher(self, voucher_service, mock_db, mock_voucher):
        """Test redemption of own voucher"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_voucher
        
        # Act & Assert
        with pytest.raises(ValueError, match="Cannot redeem your own voucher"):
            voucher_service.redeem_voucher("ABC123DEF456GHI789", "user-123")

    def test_redeem_voucher_invalid_pin(self, voucher_service, mock_db, mock_voucher):
        """Test voucher redemption with invalid PIN"""
        # Arrange
        mock_voucher.pin_hash = "hashed_pin"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_voucher
        
        # Act & Assert
        with patch.object(voucher_service, '_verify_pin', return_value=False):
            with pytest.raises(ValueError, match="Invalid PIN"):
                voucher_service.redeem_voucher("ABC123DEF456GHI789", "user-456", "wrong_pin")

    def test_cancel_voucher_success(self, voucher_service, mock_db, mock_voucher):
        """Test successful voucher cancellation"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = mock_voucher
        mock_db.commit = Mock()
        
        # Act
        result = voucher_service.cancel_voucher("ABC123DEF456GHI789", "user-123")
        
        # Assert
        assert result is True
        assert mock_voucher.status == "cancelled"
        assert mock_db.commit.call_count == 2  # Once for voucher, once for notification

    def test_cancel_voucher_not_found(self, voucher_service, mock_db):
        """Test cancellation of non-existent voucher"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = voucher_service.cancel_voucher("INVALID123CODE456", "user-123")
        
        # Assert
        assert result is False

    def test_cleanup_expired_vouchers(self, voucher_service, mock_db, mock_voucher):
        """Test cleanup of expired vouchers"""
        # Arrange
        expired_voucher = Mock(spec=Voucher)
        expired_voucher.status = "active"
        expired_voucher.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        
        mock_db.query.return_value.filter.return_value.all.return_value = [expired_voucher]
        mock_db.commit = Mock()
        
        # Act
        count = voucher_service.cleanup_expired_vouchers()
        
        # Assert
        assert count == 1
        assert expired_voucher.status == "expired"
        mock_db.commit.assert_called_once()

    def test_get_voucher_analytics(self, voucher_service, mock_db):
        """Test voucher analytics calculation"""
        # Arrange
        created_vouchers = [
            Mock(amount=Decimal("100.00"), status="active"),
            Mock(amount=Decimal("200.00"), status="redeemed"),
            Mock(amount=Decimal("150.00"), status="expired")
        ]
        
        redeemed_vouchers = [
            Mock(amount=Decimal("200.00")),
            Mock(amount=Decimal("300.00"))
        ]
        
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            created_vouchers,  # First call for created vouchers
            redeemed_vouchers  # Second call for redeemed vouchers
        ]
        
        # Act
        analytics = voucher_service.get_voucher_analytics("user-123")
        
        # Assert
        assert analytics["total_created"] == 3
        assert analytics["total_redeemed"] == 2
        assert analytics["total_amount_created"] == 450.0
        assert analytics["total_amount_redeemed"] == 500.0
        assert analytics["status_breakdown"]["active"] == 1
        assert analytics["status_breakdown"]["redeemed"] == 1
        assert analytics["status_breakdown"]["expired"] == 1

    def test_generate_voucher_code(self, voucher_service, mock_db):
        """Test voucher code generation"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        code = voucher_service._generate_voucher_code()
        
        # Assert
        assert len(code) == 20
        assert code.isalnum()
        assert code.isupper()

    def test_hash_pin(self, voucher_service):
        """Test PIN hashing"""
        # Act
        hashed = voucher_service._hash_pin("1234")
        
        # Assert
        assert hashed is not None
        assert len(hashed) == 64  # SHA256 hex length
        assert hashed != "1234"

    def test_verify_pin(self, voucher_service):
        """Test PIN verification"""
        # Arrange
        pin = "1234"
        hashed = voucher_service._hash_pin(pin)
        
        # Act & Assert
        assert voucher_service._verify_pin(pin, hashed) is True
        assert voucher_service._verify_pin("wrong", hashed) is False
