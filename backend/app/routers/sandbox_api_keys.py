"""
Sandbox API Key Management Endpoints
Handles creation, listing, and revocation of sandbox API keys.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..database import get_db
from ..dependencies.sandbox_auth import get_sandbox_user_from_api_key
from ..models.sandbox import SandboxAPIKey
from ..schemas.sandbox import (
    CreateAPIKeyRequest,
    APIKeyResponse,
    APIKeyCreateResponse,
    ListAPIKeysResponse
)
from ..services.sandbox_api_key_service import sandbox_api_key_service

router = APIRouter(prefix="/api/v1/sandbox/api-keys", tags=["sandbox"])


@router.post("", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    request: CreateAPIKeyRequest,
    db: Session = Depends(get_db),
    current_api_key: SandboxAPIKey = Depends(get_sandbox_user_from_api_key)
):
    """
    Create a new API key for the authenticated sandbox user.
    
    The full API key is returned only once upon creation.
    Store it securely as it cannot be retrieved later.
    """
    # Generate new API key
    api_key = sandbox_api_key_service.generate_api_key()
    
    # Store API key
    api_key_record = sandbox_api_key_service.store_api_key(
        db=db,
        sandbox_user_id=str(current_api_key.sandbox_user_id),
        api_key=api_key,
        name=request.name
    )
    
    # Return response with full API key (only time it's shown)
    return APIKeyCreateResponse(
        id=api_key_record.id,
        api_key=api_key,  # Full key shown only once
        key_prefix=api_key_record.key_prefix,
        name=api_key_record.name,
        created_at=api_key_record.created_at
    )


@router.get("", response_model=ListAPIKeysResponse)
def list_api_keys(
    db: Session = Depends(get_db),
    current_api_key: SandboxAPIKey = Depends(get_sandbox_user_from_api_key)
):
    """
    List all API keys for the authenticated sandbox user.
    
    Only the key prefix is shown (not the full key) for security.
    """
    api_keys = sandbox_api_key_service.get_api_keys_by_user(
        db=db,
        sandbox_user_id=str(current_api_key.sandbox_user_id)
    )
    
    # Convert to response format (mask full keys)
    api_key_responses = [
        APIKeyResponse(
            id=key.id,
            key_prefix=key.key_prefix,
            name=key.name,
            is_active=key.is_active,
            last_used_at=key.last_used_at,
            created_at=key.created_at
        )
        for key in api_keys
    ]
    
    return ListAPIKeysResponse(
        api_keys=api_key_responses,
        total=len(api_key_responses)
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: UUID,
    db: Session = Depends(get_db),
    current_api_key: SandboxAPIKey = Depends(get_sandbox_user_from_api_key)
):
    """
    Revoke an API key by ID.
    
    Only the owner of the API key can revoke it.
    """
    success = sandbox_api_key_service.revoke_api_key(
        db=db,
        key_id=str(key_id),
        sandbox_user_id=str(current_api_key.sandbox_user_id)
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or you don't have permission to revoke it."
        )
    
    return None

