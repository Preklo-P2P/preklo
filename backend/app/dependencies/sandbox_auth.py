"""
Sandbox authentication dependencies.
Handles API key authentication for sandbox endpoints.
"""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..services.sandbox_api_key_service import sandbox_api_key_service
from ..models.sandbox import SandboxAPIKey


async def get_api_key_from_header(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[str]:
    """
    Extract API key from X-API-Key header.
    
    Args:
        x_api_key: The API key from the header
        
    Returns:
        Optional[str]: The API key if present, None otherwise
    """
    return x_api_key


def get_sandbox_user_from_api_key(
    api_key: Optional[str] = Depends(get_api_key_from_header),
    db: Session = Depends(get_db)
) -> SandboxAPIKey:
    """
    Validate API key and return the associated sandbox user.
    
    This dependency is used to authenticate sandbox endpoints.
    It extracts the API key from the X-API-Key header, validates it,
    and returns the SandboxAPIKey record if valid.
    
    Args:
        api_key: The API key from the header (extracted by get_api_key_from_header)
        db: Database session
        
    Returns:
        SandboxAPIKey: The API key record if valid
        
    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Please provide X-API-Key header."
        )
    
    # Validate API key format
    if not sandbox_api_key_service.validate_api_key_format(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format. API keys must start with 'sb_' prefix."
        )
    
    # Validate API key against database
    api_key_record = sandbox_api_key_service.validate_api_key(db, api_key)
    
    if not api_key_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key. Please check your API key and try again."
        )
    
    if not api_key_record.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has been revoked. Please use an active API key."
        )
    
    return api_key_record

