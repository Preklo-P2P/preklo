"""
Sandbox Signup Endpoint
Handles free sandbox account creation with automatic API key generation.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid
import logging

from ..database import get_db
from ..dependencies.sandbox_auth import get_sandbox_user_from_api_key
from ..models.sandbox import SandboxAPIKey
from ..schemas.sandbox import (
    SandboxSignupRequest, SandboxSignupResponse, TestAccountSummary, SandboxAccountInfo
)
from ..services.sandbox_api_key_service import sandbox_api_key_service
from ..services.test_account_service import test_account_service
from ..services.email_service import email_service

logger = logging.getLogger("preklo.sandbox")

router = APIRouter(prefix="/api/v1/sandbox", tags=["sandbox"])


@router.post("/signup", response_model=SandboxSignupResponse, status_code=status.HTTP_201_CREATED)
async def sandbox_signup(
    request: SandboxSignupRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new sandbox account with instant API key generation.
    
    This is a public endpoint that requires no authentication.
    Upon signup, users receive:
    - An API key (generated automatically)
    - 5 pre-configured test accounts
    - A welcome email with their API key
    """
    try:
        # Generate sandbox user ID
        sandbox_user_id = str(uuid.uuid4())
        
        # Generate API key automatically
        api_key = sandbox_api_key_service.generate_api_key()
        api_key_record = sandbox_api_key_service.store_api_key(
            db=db,
            sandbox_user_id=sandbox_user_id,
            api_key=api_key,
            name="Default API Key"
        )
        
        # Create test accounts
        test_accounts = test_account_service.create_default_accounts(
            db=db,
            sandbox_user_id=sandbox_user_id
        )
        
        # Send welcome email
        try:
            email_service.send_sandbox_welcome_email(
                to_email=request.email,
                api_key=api_key,
                name=request.name or "Developer"
            )
        except Exception as e:
            logger.warning(f"Failed to send welcome email to {request.email}: {e}")
            # Don't fail signup if email fails
        
        # Prepare test accounts summary
        test_accounts_summary = [
            TestAccountSummary(
                id=account.id,
                username=account.username,
                usdc_balance=float(account.usdc_balance),
                apt_balance=float(account.apt_balance),
                currency_type=account.currency_type
            )
            for account in test_accounts
        ]
        
        # Return response
        return SandboxSignupResponse(
            success=True,
            message="Sandbox account created successfully",
            data={
                "user_id": sandbox_user_id,
                "api_key": api_key,  # Only shown once
                "api_key_id": str(api_key_record.id),
                "email": request.email,
                "name": request.name,
                "created_at": api_key_record.created_at.isoformat(),
                "test_accounts": [acc.dict() for acc in test_accounts_summary]
            }
        )
        
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating sandbox account: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create sandbox account. Please try again."
        )


@router.get("/account", response_model=SandboxAccountInfo)
def get_sandbox_account(
    db: Session = Depends(get_db),
    current_api_key: SandboxAPIKey = Depends(get_sandbox_user_from_api_key)
):
    """
    Get sandbox account information.
    
    Requires API key authentication.
    
    Returns account info including:
    - User ID
    - API keys count
    - Test accounts count
    - Created date
    """
    sandbox_user_id = str(current_api_key.sandbox_user_id)
    
    # Get API keys count
    api_keys = sandbox_api_key_service.get_api_keys_by_user(db, sandbox_user_id)
    api_keys_count = len(api_keys)
    
    # Get test accounts count
    test_accounts = test_account_service.get_test_accounts(db, sandbox_user_id)
    test_accounts_count = len(test_accounts)
    
    # Get creation date from first API key
    created_at = current_api_key.created_at
    
    return SandboxAccountInfo(
        user_id=current_api_key.sandbox_user_id,
        email="",  # Email not stored in current model - can be added later if needed
        name=None,  # Name not stored in current model
        api_keys_count=api_keys_count,
        test_accounts_count=test_accounts_count,
        created_at=created_at
    )

