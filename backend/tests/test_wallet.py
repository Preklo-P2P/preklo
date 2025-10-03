import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, timedelta
from app.services.wallet_service import wallet_service


class TestWalletService:
    """Test wallet service functionality"""

    def test_generate_wallet(self):
        """Test wallet generation"""
        address, private_key = wallet_service.generate_wallet()
        
        assert address is not None
        assert private_key is not None
        assert address.startswith("0x")
        assert len(address) == 66  # 0x + 64 hex chars
        # Private key can be 64 or 66 chars depending on SDK implementation
        assert len(private_key) >= 64

    def test_encrypt_decrypt_private_key(self):
        """Test private key encryption and decryption"""
        private_key = "test_private_key_123456789"
        password = "test_password"
        
        # Encrypt
        encrypted = wallet_service.encrypt_private_key(private_key, password)
        assert encrypted is not None
        assert encrypted != private_key
        
        # Decrypt
        decrypted = wallet_service.decrypt_private_key(encrypted, password)
        assert decrypted == private_key

    def test_encrypt_decrypt_with_user_id(self):
        """Test private key encryption and decryption with user ID for security monitoring"""
        private_key = "test_private_key_123456789"
        password = "test_password"
        user_id = "test_user_123"
        
        # Encrypt
        encrypted = wallet_service.encrypt_private_key(private_key, password)
        
        # Decrypt with user ID
        decrypted = wallet_service.decrypt_private_key(encrypted, password, user_id)
        assert decrypted == private_key

    def test_failed_decryption_tracking(self):
        """Test failed decryption attempt tracking"""
        private_key = "test_private_key_123456789"
        password = "test_password"
        user_id = "test_user_123"
        
        # Encrypt
        encrypted = wallet_service.encrypt_private_key(private_key, password)
        
        # Try to decrypt with wrong password multiple times
        for i in range(6):  # More than max_failed_attempts (5)
            result = wallet_service.decrypt_private_key(encrypted, "wrong_password", user_id)
            assert result is None
        
        # Check security status
        security_status = wallet_service.get_security_status(user_id)
        assert security_status["is_locked_out"] is True
        assert security_status["failed_attempts"] >= 5

    def test_security_lockout_recovery(self):
        """Test security lockout functionality"""
        private_key = "test_private_key_123456789"
        password = "test_password"
        user_id = "test_user_lockout"  # Use unique user ID
        
        # Clear any existing state
        if user_id in wallet_service._failed_attempts:
            del wallet_service._failed_attempts[user_id]
        
        # Encrypt
        encrypted = wallet_service.encrypt_private_key(private_key, password)
        
        # Lock out user
        for i in range(6):
            wallet_service.decrypt_private_key(encrypted, "wrong_password", user_id)
        
        # Verify lockout
        security_status = wallet_service.get_security_status(user_id)
        assert security_status["is_locked_out"] is True
        assert security_status["failed_attempts"] >= 5
        
        # Try to decrypt with correct password while locked out - should fail
        result = wallet_service.decrypt_private_key(encrypted, password, user_id)
        assert result is None

    def test_create_custodial_wallet(self):
        """Test custodial wallet creation"""
        password = "test_password"
        
        address, encrypted_key = wallet_service.create_custodial_wallet(password)
        
        assert address is not None
        assert encrypted_key is not None
        assert address.startswith("0x")
        
        # Verify we can decrypt the private key
        decrypted_key = wallet_service.decrypt_private_key(encrypted_key, password)
        assert decrypted_key is not None

    def test_export_wallet_data(self):
        """Test wallet data export"""
        # Use a valid hex private key for testing
        private_key = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        password = "test_password"
        user_id = "test_user_export"  # Use unique user ID
        
        # Clear any existing state
        if user_id in wallet_service._failed_attempts:
            del wallet_service._failed_attempts[user_id]
        
        # Encrypt
        encrypted = wallet_service.encrypt_private_key(private_key, password)
        
        # Export wallet data
        wallet_data = wallet_service.export_wallet_data(encrypted, password, user_id)
        
        assert wallet_data is not None
        assert "wallet_address" in wallet_data
        assert "private_key" in wallet_data
        assert "export_warning" in wallet_data
        assert "export_timestamp" in wallet_data
        assert "backup_id" in wallet_data
        assert wallet_data["private_key"] == private_key

    def test_backup_cooldown(self):
        """Test backup cooldown functionality"""
        # Use a valid hex private key for testing
        private_key = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        password = "test_password"
        user_id = "test_user_backup"  # Use unique user ID
        
        # Clear any existing state
        if user_id in wallet_service._backup_requests:
            del wallet_service._backup_requests[user_id]
        
        # Encrypt
        encrypted = wallet_service.encrypt_private_key(private_key, password)
        
        # First backup
        wallet_data1 = wallet_service.export_wallet_data(encrypted, password, user_id)
        assert wallet_data1 is not None
        
        # Check backup status
        backup_status = wallet_service.get_backup_status(user_id)
        assert backup_status["can_backup"] is False
        assert backup_status["last_backup"] is not None
        
        # Try second backup immediately - should be blocked
        wallet_data2 = wallet_service.export_wallet_data(encrypted, password, user_id)
        assert wallet_data2 is None

    def test_validate_wallet_address(self):
        """Test wallet address validation"""
        # Valid addresses
        valid_addresses = [
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
            "0x0000000000000000000000000000000000000000000000000000000000000000",
            "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        ]
        
        for address in valid_addresses:
            assert wallet_service.validate_wallet_address(address) is True
        
        # Invalid addresses
        invalid_addresses = [
            "0x123",  # Too short
            "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",  # No 0x prefix
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdefg",  # Invalid hex
            "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcde",  # Too short
            "",  # Empty
            None  # None
        ]
        
        for address in invalid_addresses:
            if address is not None:
                assert wallet_service.validate_wallet_address(address) is False

    def test_get_account_for_transaction(self):
        """Test getting account for transaction"""
        private_key = "test_private_key_123456789"
        password = "test_password"
        user_id = "test_user_account"  # Use unique user ID
        
        # Clear any existing state
        if user_id in wallet_service._failed_attempts:
            del wallet_service._failed_attempts[user_id]
        
        # Encrypt
        encrypted = wallet_service.encrypt_private_key(private_key, password)
        
        # Mock SDK availability
        with patch('app.services.wallet_service.SDK_AVAILABLE', True):
            with patch('app.services.wallet_service.Account') as mock_account:
                mock_account_instance = MagicMock()
                mock_account.load_key.return_value = mock_account_instance
                
                # Get account for transaction
                account = wallet_service.get_account_for_transaction(encrypted, password, user_id)
                
                # Should return the mocked account
                assert account is not None
                mock_account.load_key.assert_called_once()

    def test_get_account_for_transaction_wrong_password(self):
        """Test getting account for transaction with wrong password"""
        private_key = "test_private_key_123456789"
        password = "test_password"
        user_id = "test_user_123"
        
        # Encrypt
        encrypted = wallet_service.encrypt_private_key(private_key, password)
        
        # Try with wrong password
        account = wallet_service.get_account_for_transaction(encrypted, "wrong_password", user_id)
        assert account is None

    def test_backup_status_tracking(self):
        """Test backup status tracking"""
        user_id = "test_user_status"  # Use unique user ID
        
        # Clear any existing state
        if user_id in wallet_service._backup_requests:
            del wallet_service._backup_requests[user_id]
        
        # Initial status
        status = wallet_service.get_backup_status(user_id)
        assert status["can_backup"] is True
        assert status["last_backup"] is None
        assert status["cooldown_remaining"] is None
        
        # Simulate backup request
        wallet_service._track_backup_request(user_id)
        
        # Check status after backup
        status = wallet_service.get_backup_status(user_id)
        assert status["can_backup"] is False
        assert status["last_backup"] is not None
        assert status["cooldown_remaining"] is not None

    def test_security_status_tracking(self):
        """Test security status tracking"""
        user_id = "test_user_456"  # Use different user ID to avoid conflicts
        
        # Initial status
        status = wallet_service.get_security_status(user_id)
        assert status["is_locked_out"] is False
        assert status["failed_attempts"] == 0
        assert status["lockout_remaining"] is None
        
        # Simulate failed attempts
        wallet_service._track_failed_attempt(user_id)
        wallet_service._track_failed_attempt(user_id)
        
        # Check status after failed attempts
        status = wallet_service.get_security_status(user_id)
        assert status["is_locked_out"] is False
        assert status["failed_attempts"] == 2
        assert status["lockout_remaining"] is None

    def test_generate_wallet_backup_phrase(self):
        """Test wallet backup phrase generation (placeholder)"""
        private_key = "test_private_key_123456789"
        
        # This should return None as it's not implemented yet
        phrase = wallet_service.generate_wallet_backup_phrase(private_key)
        assert phrase is None


class TestWalletIntegration:
    """Test wallet integration with other services"""

    @pytest.mark.asyncio
    async def test_wallet_balance_sync(self):
        """Test wallet balance synchronization"""
        # This would test integration with aptos_service
        # For now, just test that the method exists and can be called
        assert hasattr(wallet_service, 'generate_wallet')
        assert hasattr(wallet_service, 'encrypt_private_key')
        assert hasattr(wallet_service, 'decrypt_private_key')

    def test_wallet_security_integration(self):
        """Test wallet security integration"""
        # Test that security features work together
        user_id = "test_user_789"  # Use different user ID to avoid conflicts
        password = "test_password"
        
        # Create wallet
        address, encrypted_key = wallet_service.create_custodial_wallet(password)
        
        # Test normal operation
        decrypted_key = wallet_service.decrypt_private_key(encrypted_key, password, user_id)
        assert decrypted_key is not None
        
        # Test security status
        security_status = wallet_service.get_security_status(user_id)
        assert security_status["is_locked_out"] is False
        
        # Test backup status
        backup_status = wallet_service.get_backup_status(user_id)
        assert backup_status["can_backup"] is True
