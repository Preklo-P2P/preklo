"""
Sandbox Transaction Endpoints
Example implementation showing how existing endpoints work in sandbox mode.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Union

from ..database import get_db
from ..dependencies.unified_auth import require_unified_auth, is_sandbox_request
from ..dependencies.schema_aware_db import get_schema_aware_db
from ..models import User
from ..models.sandbox import SandboxAPIKey, TestAccount
from ..services.sandbox_transaction_service import sandbox_transaction_service
from ..services.test_account_service import test_account_service

router = APIRouter(prefix="/api/v1", tags=["sandbox-transactions"])


@router.post("/sandbox/transactions/transfer")
async def sandbox_transfer(
    sender_account_id: str,
    recipient_account_id: str,
    amount: Decimal,
    currency_type: str,
    auth_result: Union[User, SandboxAPIKey] = Depends(require_unified_auth),
    db: Session = Depends(get_schema_aware_db),
    is_sandbox: bool = Depends(is_sandbox_request)
):
    """
    Example sandbox transaction endpoint.
    
    This endpoint demonstrates how to:
    1. Support both JWT and API key authentication
    2. Route to sandbox schema when API key is used
    3. Process transactions without blockchain calls in sandbox mode
    4. Validate test accounts
    
    Args:
        sender_account_id: UUID of sender test account
        recipient_account_id: UUID of recipient test account
        amount: Transfer amount
        currency_type: Currency type (USDC, APT)
        auth_result: Authenticated user or API key (from unified_auth)
        db: Schema-aware database session
        is_sandbox: Whether this is a sandbox request
    """
    # Only allow sandbox requests for this endpoint
    if not is_sandbox:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in sandbox mode. Use API key authentication."
        )
    
    # Get sandbox user ID from API key
    if not isinstance(auth_result, SandboxAPIKey):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key authentication required for sandbox transactions"
        )
    
    sandbox_user_id = str(auth_result.sandbox_user_id)
    
    try:
        # Process sandbox transaction (no blockchain calls)
        transaction_data = sandbox_transaction_service.process_sandbox_transfer(
            db=db,
            sender_account_id=sender_account_id,
            recipient_account_id=recipient_account_id,
            amount=amount,
            currency_type=currency_type,
            sandbox_user_id=sandbox_user_id
        )
        
        return {
            "success": True,
            "message": "Transaction processed successfully",
            "data": transaction_data
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process transaction"
        )


@router.get("/sandbox/balance/{account_id}")
async def get_sandbox_balance(
    account_id: str,
    auth_result: Union[User, SandboxAPIKey] = Depends(require_unified_auth),
    db: Session = Depends(get_schema_aware_db),
    is_sandbox: bool = Depends(is_sandbox_request)
):
    """
    Get test account balance (sandbox mode only).
    
    Example endpoint showing how to retrieve test account data.
    """
    if not is_sandbox:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in sandbox mode"
        )
    
    if not isinstance(auth_result, SandboxAPIKey):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key authentication required"
        )
    
    sandbox_user_id = str(auth_result.sandbox_user_id)
    
    # Get test account
    account = test_account_service.get_test_account(
        db=db,
        account_id=account_id,
        sandbox_user_id=sandbox_user_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test account not found"
        )
    
    return {
        "account_id": str(account.id),
        "username": account.username,
        "usdc_balance": float(account.usdc_balance),
        "apt_balance": float(account.apt_balance),
        "wallet_address": account.wallet_address
    }

