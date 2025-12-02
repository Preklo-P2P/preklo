"""
Unit Tests for Sandbox API Key Service
Tests API key generation, hashing, validation, and management.
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from app.services.sandbox_api_key_service import sandbox_api_key_service, SandboxAPIKeyService
from app.models.sandbox import SandboxAPIKey


class TestAPIKeyGeneration:
    """Test API key generation functionality"""
    
    def test_generate_api_key_format(self):
        """Test that generated API keys have correct format"""
        api_key = sandbox_api_key_service.generate_api_key()
        
        assert api_key.startswith("sb_"), "API key must start with 'sb_' prefix"
        assert len(api_key) > len("sb_"), "API key must have content after prefix"
    
    def test_generate_api_key_uniqueness(self):
        """Test that generated API keys are unique"""
        key1 = sandbox_api_key_service.generate_api_key()
        key2 = sandbox_api_key_service.generate_api_key()
        
        assert key1 != key2, "Generated API keys should be unique"
    
    def test_generate_api_key_length(self):
        """Test that generated API keys have reasonable length"""
        api_key = sandbox_api_key_service.generate_api_key()
        
        # Should be at least prefix + some characters
        assert len(api_key) >= len("sb_") + 32, "API key should have sufficient length"


class TestAPIKeyHashing:
    """Test API key hashing functionality"""
    
    def test_hash_api_key(self):
        """Test that API keys are hashed correctly"""
        api_key = "sb_test_key_123456"
        key_hash = sandbox_api_key_service.hash_api_key(api_key)
        
        assert key_hash != api_key, "Hash should be different from original key"
        assert len(key_hash) > 0, "Hash should not be empty"
        assert key_hash.startswith("$2b$") or key_hash.startswith("$2a$"), "Should use bcrypt hash"
    
    def test_verify_api_key_success(self):
        """Test successful API key verification"""
        api_key = "sb_test_key_123456"
        key_hash = sandbox_api_key_service.hash_api_key(api_key)
        
        result = sandbox_api_key_service.verify_api_key(api_key, key_hash)
        
        assert result is True, "Valid API key should verify successfully"
    
    def test_verify_api_key_failure(self):
        """Test failed API key verification with wrong key"""
        api_key = "sb_test_key_123456"
        wrong_key = "sb_wrong_key_789012"
        key_hash = sandbox_api_key_service.hash_api_key(api_key)
        
        result = sandbox_api_key_service.verify_api_key(wrong_key, key_hash)
        
        assert result is False, "Wrong API key should fail verification"


class TestAPIKeyValidation:
    """Test API key format validation"""
    
    def test_validate_api_key_format_valid(self):
        """Test validation of valid API key format"""
        valid_key = "sb_abc123def456ghi789jkl012mno345pq"
        result = sandbox_api_key_service.validate_api_key_format(valid_key)
        
        assert result is True, "Valid API key format should pass validation"
    
    def test_validate_api_key_format_invalid_prefix(self):
        """Test validation fails for wrong prefix"""
        invalid_key = "api_abc123def456ghi789jkl012mno345pq"
        result = sandbox_api_key_service.validate_api_key_format(invalid_key)
        
        assert result is False, "API key with wrong prefix should fail validation"
    
    def test_validate_api_key_format_empty(self):
        """Test validation fails for empty key"""
        result = sandbox_api_key_service.validate_api_key_format("")
        
        assert result is False, "Empty API key should fail validation"
    
    def test_validate_api_key_format_too_short(self):
        """Test validation fails for too short key"""
        short_key = "sb_abc"
        result = sandbox_api_key_service.validate_api_key_format(short_key)
        
        assert result is False, "Too short API key should fail validation"


class TestAPIKeyService:
    """Test API key service methods"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sandbox_user_id(self):
        """Create a test sandbox user ID"""
        return str(uuid.uuid4())
    
    def test_store_api_key(self, mock_db, sandbox_user_id):
        """Test storing an API key in the database"""
        api_key = sandbox_api_key_service.generate_api_key()
        
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = sandbox_api_key_service.store_api_key(
            db=mock_db,
            sandbox_user_id=sandbox_user_id,
            api_key=api_key,
            name="Test Key"
        )
        
        assert result is not None, "Should return API key record"
        assert mock_db.add.called, "Should add API key to database"
        assert mock_db.commit.called, "Should commit transaction"
    
    def test_store_api_key_invalid_format(self, mock_db, sandbox_user_id):
        """Test storing API key with invalid format raises error"""
        invalid_key = "invalid_key_format"
        
        with pytest.raises(ValueError, match="Invalid API key format"):
            sandbox_api_key_service.store_api_key(
                db=mock_db,
                sandbox_user_id=sandbox_user_id,
                api_key=invalid_key
            )
    
    def test_validate_api_key_not_found(self, mock_db):
        """Test validation when API key is not found"""
        api_key = "sb_test_key_not_in_db"
        
        # Mock query returning no results
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        result = sandbox_api_key_service.validate_api_key(mock_db, api_key)
        
        assert result is None, "Non-existent API key should return None"
    
    def test_revoke_api_key(self, mock_db, sandbox_user_id):
        """Test revoking an API key"""
        key_id = str(uuid.uuid4())
        
        # Create mock API key record
        mock_api_key = Mock(spec=SandboxAPIKey)
        mock_api_key.id = key_id
        mock_api_key.sandbox_user_id = sandbox_user_id
        mock_api_key.is_active = True
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_api_key
        mock_db.query.return_value = mock_query
        
        result = sandbox_api_key_service.revoke_api_key(
            db=mock_db,
            key_id=key_id,
            sandbox_user_id=sandbox_user_id
        )
        
        assert result is True, "Should successfully revoke API key"
        assert mock_api_key.is_active is False, "API key should be marked inactive"
        assert mock_api_key.revoked_at is not None, "Revoked timestamp should be set"
        assert mock_db.commit.called, "Should commit transaction"
    
    def test_revoke_api_key_not_found(self, mock_db, sandbox_user_id):
        """Test revoking non-existent API key"""
        key_id = str(uuid.uuid4())
        
        # Mock query returning None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = sandbox_api_key_service.revoke_api_key(
            db=mock_db,
            key_id=key_id,
            sandbox_user_id=sandbox_user_id
        )
        
        assert result is False, "Should return False for non-existent key"
    
    def test_get_api_keys_by_user(self, mock_db, sandbox_user_id):
        """Test retrieving all API keys for a user"""
        # Create mock API key records
        mock_key1 = Mock(spec=SandboxAPIKey)
        mock_key2 = Mock(spec=SandboxAPIKey)
        mock_keys = [mock_key1, mock_key2]
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = mock_keys
        mock_db.query.return_value = mock_query
        
        result = sandbox_api_key_service.get_api_keys_by_user(mock_db, sandbox_user_id)
        
        assert len(result) == 2, "Should return all API keys for user"
        assert result == mock_keys, "Should return the correct API keys"

