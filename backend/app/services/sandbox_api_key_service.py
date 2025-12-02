"""
Sandbox API Key Service
Handles API key generation, hashing, validation, and management for sandbox users.
"""
import secrets
from datetime import datetime, timezone
from typing import Optional
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.sandbox import SandboxAPIKey


class SandboxAPIKeyService:
    """
    Service for managing sandbox API keys.
    
    API keys are generated with 'sb_' prefix and hashed before storage.
    """
    
    # API key configuration
    KEY_PREFIX = "sb_"
    KEY_LENGTH = 32  # 32 random characters after prefix
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def generate_api_key(self) -> str:
        """
        Generate a new sandbox API key.
        
        Format: sb_{32_random_characters}
        Example: sb_abc123def456ghi789jkl012mno345pq
        
        Returns:
            str: The generated API key with 'sb_' prefix
        """
        # Generate random string
        random_string = secrets.token_urlsafe(self.KEY_LENGTH)
        # Remove any special characters that might cause issues (keep it alphanumeric + _)
        random_string = ''.join(c for c in random_string if c.isalnum() or c in ['_', '-'])
        # Ensure we have exactly KEY_LENGTH characters
        random_string = random_string[:self.KEY_LENGTH]
        
        return f"{self.KEY_PREFIX}{random_string}"
    
    def hash_api_key(self, api_key: str) -> str:
        """
        Hash an API key for secure storage.
        
        Args:
            api_key: The plain API key to hash
            
        Returns:
            str: The hashed API key
        """
        # Truncate to 72 bytes to avoid bcrypt limitation
        key_bytes = api_key.encode('utf-8')
        if len(key_bytes) > 72:
            api_key = key_bytes[:72].decode('utf-8', errors='ignore')
        return self.pwd_context.hash(api_key)
    
    def verify_api_key(self, api_key: str, key_hash: str) -> bool:
        """
        Verify an API key against its hash.
        
        Args:
            api_key: The plain API key to verify
            key_hash: The stored hash to verify against
            
        Returns:
            bool: True if the API key matches the hash
        """
        # Truncate to 72 bytes to avoid bcrypt limitation
        key_bytes = api_key.encode('utf-8')
        if len(key_bytes) > 72:
            api_key = key_bytes[:72].decode('utf-8', errors='ignore')
        return self.pwd_context.verify(api_key, key_hash)
    
    def validate_api_key_format(self, api_key: str) -> bool:
        """
        Validate that an API key has the correct format.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            bool: True if the format is valid
        """
        if not api_key:
            return False
        if not api_key.startswith(self.KEY_PREFIX):
            return False
        if len(api_key) < len(self.KEY_PREFIX) + self.KEY_LENGTH:
            return False
        return True
    
    def store_api_key(
        self,
        db: Session,
        sandbox_user_id: str,
        api_key: str,
        name: Optional[str] = None
    ) -> SandboxAPIKey:
        """
        Store a new API key in the database.
        
        Args:
            db: Database session
            sandbox_user_id: UUID of the sandbox user
            api_key: The plain API key to store
            name: Optional name for the API key
            
        Returns:
            SandboxAPIKey: The created API key record
        """
        # Validate format
        if not self.validate_api_key_format(api_key):
            raise ValueError(f"Invalid API key format. Must start with '{self.KEY_PREFIX}'")
        
        # Hash the API key
        key_hash = self.hash_api_key(api_key)
        
        # Get prefix for display (first 8 characters after 'sb_')
        key_prefix = api_key[:len(self.KEY_PREFIX) + 8]
        
        # Create API key record
        api_key_record = SandboxAPIKey(
            sandbox_user_id=sandbox_user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name or "Default API Key",
            is_active=True
        )
        
        db.add(api_key_record)
        db.commit()
        db.refresh(api_key_record)
        
        return api_key_record
    
    def validate_api_key(
        self,
        db: Session,
        api_key: str
    ) -> Optional[SandboxAPIKey]:
        """
        Validate an API key and return the associated record.
        
        Args:
            db: Database session
            api_key: The API key to validate
            
        Returns:
            Optional[SandboxAPIKey]: The API key record if valid, None otherwise
        """
        # Validate format first
        if not self.validate_api_key_format(api_key):
            return None
        
        # Query all active API keys for the sandbox user
        # We need to check each one because we can't query by hash directly
        # In production, consider caching this lookup
        api_keys = db.query(SandboxAPIKey).filter(
            and_(
                SandboxAPIKey.is_active == True,
                SandboxAPIKey.key_prefix == api_key[:len(self.KEY_PREFIX) + 8]
            )
        ).all()
        
        # Check each API key hash
        for key_record in api_keys:
            if self.verify_api_key(api_key, key_record.key_hash):
                # Update last_used_at timestamp
                key_record.last_used_at = datetime.now(timezone.utc)
                db.commit()
                return key_record
        
        return None
    
    def revoke_api_key(
        self,
        db: Session,
        key_id: str,
        sandbox_user_id: str
    ) -> bool:
        """
        Revoke an API key by deactivating it.
        
        Args:
            db: Database session
            key_id: UUID of the API key to revoke
            sandbox_user_id: UUID of the sandbox user (for security check)
            
        Returns:
            bool: True if the key was revoked, False if not found
        """
        api_key = db.query(SandboxAPIKey).filter(
            and_(
                SandboxAPIKey.id == key_id,
                SandboxAPIKey.sandbox_user_id == sandbox_user_id
            )
        ).first()
        
        if not api_key:
            return False
        
        api_key.is_active = False
        api_key.revoked_at = datetime.now(timezone.utc)
        db.commit()
        
        return True
    
    def get_api_keys_by_user(
        self,
        db: Session,
        sandbox_user_id: str
    ) -> list[SandboxAPIKey]:
        """
        Get all API keys for a sandbox user.
        
        Args:
            db: Database session
            sandbox_user_id: UUID of the sandbox user
            
        Returns:
            list[SandboxAPIKey]: List of API key records
        """
        return db.query(SandboxAPIKey).filter(
            SandboxAPIKey.sandbox_user_id == sandbox_user_id
        ).order_by(SandboxAPIKey.created_at.desc()).all()


# Create singleton instance
sandbox_api_key_service = SandboxAPIKeyService()

