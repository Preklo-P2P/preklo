"""
Unified Authentication Dependencies
Supports both JWT (production) and API key (sandbox) authentication.
Automatically routes to appropriate schema based on authentication method.
"""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional, Union, Tuple
from enum import Enum

from ..database import get_db
from ..models import User
from ..models.sandbox import SandboxAPIKey
from ..services.auth_service import auth_service
from ..services.sandbox_api_key_service import sandbox_api_key_service
from ..utils.sandbox import is_sandbox_enabled
from .sandbox_auth import get_api_key_from_header


class AuthType(Enum):
    """Authentication type enum"""
    JWT = "jwt"
    API_KEY = "api_key"
    NONE = "none"

async def get_unified_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Tuple[Optional[Union[User, SandboxAPIKey]], AuthType]:
    """
    Unified authentication that supports both JWT and API key.
    
    Priority:
    1. If X-API-Key header present → Use API key auth → Return SandboxAPIKey
    2. If Authorization Bearer token present → Use JWT auth → Return User
    3. If neither → Return (None, AuthType.NONE)
    
    Returns:
        tuple: (authenticated_user_or_api_key, auth_type)
    """
    # Check for API key first (sandbox takes priority)
    if x_api_key:
        if not is_sandbox_enabled():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sandbox mode is not enabled"
            )
        
        # Validate API key
        if not sandbox_api_key_service.validate_api_key_format(x_api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format"
            )
        
        api_key_record = sandbox_api_key_service.validate_api_key(db, x_api_key)
        if not api_key_record or not api_key_record.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive API key"
            )
        
        return api_key_record, AuthType.API_KEY
    
    # Check for JWT token
    if credentials:
        token = credentials.credentials
        payload = auth_service.verify_token(token)
        
        if payload:
            user_id = payload.get("sub")
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user and user.is_active:
                    return user, AuthType.JWT
    
    # No authentication provided
    return None, AuthType.NONE


async def require_unified_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> Union[User, SandboxAPIKey]:
    """
    Require authentication (either JWT or API key).
    Applies rate limiting for API keys.
    
    Raises HTTPException if no valid authentication is provided.
    
    Returns:
        Union[User, SandboxAPIKey]: The authenticated user or API key record
    """
    auth_result, auth_type = await get_unified_auth(credentials, x_api_key, db)
    
    if auth_result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Provide either Bearer token or X-API-Key header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Apply rate limiting for API keys
    if isinstance(auth_result, SandboxAPIKey):
        from .sandbox_rate_limit import _check_rate_limit
        _check_rate_limit(auth_result, db)  # Raises HTTPException if limit exceeded
    
    return auth_result


def get_sandbox_user_from_auth(
    auth_result: Union[User, SandboxAPIKey] = Depends(require_unified_auth)
) -> Optional[str]:
    """
    Extract sandbox_user_id from authentication result.
    
    If API key auth → return sandbox_user_id
    If JWT auth → return None (production user)
    
    This is used to determine if we should route to sandbox schema.
    """
    if isinstance(auth_result, SandboxAPIKey):
        return str(auth_result.sandbox_user_id)
    return None


def is_sandbox_request(
    auth_result: Union[User, SandboxAPIKey] = Depends(require_unified_auth)
) -> bool:
    """
    Check if the current request is using sandbox authentication.
    
    Returns:
        bool: True if API key auth, False if JWT auth
    """
    return isinstance(auth_result, SandboxAPIKey)

