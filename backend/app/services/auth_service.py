"""
Authentication Service
Handles JWT token creation, validation, and user authentication
"""

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import secrets

from ..config import settings
from ..models import User


class AuthService:
    """
    Authentication service for JWT token management and user verification
    """
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against its hash
        bcrypt has a 72-byte limit, so we truncate if necessary
        """
        # Truncate password to 72 bytes to avoid bcrypt limitation
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            plain_password = password_bytes[:72].decode('utf-8', errors='ignore')
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """
        Hash a password for storage
        bcrypt has a 72-byte limit, so we truncate if necessary
        """
        # Truncate password to 72 bytes to avoid bcrypt limitation
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password = password_bytes[:72].decode('utf-8', errors='ignore')
        return self.pwd_context.hash(password)
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.secret_key, 
            algorithm=self.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token
        """
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return None
        except jwt.PyJWTError as e:
            print(f"JWT error: {e}")
            return None
    
    def authenticate_user(
        self, 
        db: Session, 
        username: str, 
        password: str
    ) -> Optional[User]:
        """
        Authenticate a user with username and password
        """
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user
    
    def create_user_tokens(self, user: User, remember_me: bool = False) -> Dict[str, str]:
        """
        Create access and refresh tokens for a user
        """
        # Access token (short-lived)
        access_token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "type": "access"
        }
        access_token = self.create_access_token(access_token_data)
        
        # Refresh token (long-lived) - longer if remember_me is True
        refresh_token_data = {
            "sub": str(user.id),
            "type": "refresh"
        }
        refresh_expiry = timedelta(days=90) if remember_me else timedelta(days=7)  # 90 days vs 7 days
        refresh_token = self.create_access_token(
            refresh_token_data,
            expires_delta=refresh_expiry
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    def refresh_access_token(self, refresh_token: str, db: Session) -> Optional[Dict[str, str]]:
        """
        Create a new access token using a refresh token
        """
        payload = self.verify_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None
        
        # Create new access token
        access_token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "type": "access"
        }
        access_token = self.create_access_token(access_token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    def generate_api_key(self, user_id: str) -> str:
        """
        Generate an API key for programmatic access
        """
        api_key_data = {
            "sub": user_id,
            "type": "api_key",
            "key_id": secrets.token_urlsafe(16)
        }
        
        # API keys don't expire (or have very long expiration)
        return self.create_access_token(
            api_key_data,
            expires_delta=timedelta(days=365)  # 1 year
        )
    
    def validate_api_key(self, api_key: str, db: Session) -> Optional[User]:
        """
        Validate an API key and return the associated user
        """
        payload = self.verify_token(api_key)
        
        if not payload or payload.get("type") != "api_key":
            return None
        
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return None
        
        return user
    
    def generate_reset_token(self, user_id: str) -> str:
        """
        Generate a password reset token
        """
        reset_data = {
            "sub": user_id,
            "type": "password_reset",
            "reset_id": secrets.token_urlsafe(16)
        }
        
        # Reset tokens expire in 1 hour
        return self.create_access_token(
            reset_data,
            expires_delta=timedelta(hours=1)
        )
    
    def validate_reset_token(self, reset_token: str) -> Optional[str]:
        """
        Validate a password reset token and return user_id
        """
        payload = self.verify_token(reset_token)
        
        if not payload or payload.get("type") != "password_reset":
            return None
        
        return payload.get("sub")
    
    def create_session_data(self, user: User) -> Dict[str, Any]:
        """
        Create session data for a user
        """
        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "wallet_address": user.wallet_address,
            "profile_picture_url": user.profile_picture_url,
            "is_active": user.is_active,
            "is_custodial": getattr(user, 'is_custodial', True),  # Default to True for new custodial system
            "wallet_exported": getattr(user, 'wallet_exported', False),
            "wallet_type": getattr(user, 'wallet_type', None),  # Include wallet type
            "created_at": user.created_at.isoformat() if user.created_at else None
        }


# Global service instance
auth_service = AuthService()
