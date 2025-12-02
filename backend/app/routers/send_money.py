"""
Send Money Router for Story 2.3
Enhanced send money functionality with confirmation flow and real-time updates
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, Union
from decimal import Decimal
import uuid

from ..database import get_db
from ..models import User
from ..models.sandbox import SandboxAPIKey
from ..schemas import (
    SendMoneyRequest,
    SendMoneyResponse,
    SendMoneyConfirmation,
    TransactionStatusUpdate,
    ApiResponse
)
from ..services.send_money_service import send_money_service
from ..services.sandbox_transaction_service import sandbox_transaction_service
from ..services.test_account_service import test_account_service
from ..dependencies import require_authentication, rate_limit
from ..dependencies.unified_auth import require_unified_auth, is_sandbox_request
from ..dependencies.schema_aware_db import get_schema_aware_db
from ..dependencies.sandbox_rate_limit import sandbox_rate_limit

router = APIRouter()


@router.post("/initiate", response_model=SendMoneyResponse)
async def initiate_send_money(
    request: SendMoneyRequest,
    sender_account_id: Optional[str] = None,  # For sandbox mode
    recipient_account_id: Optional[str] = None,  # For sandbox mode
    auth_result: Union[User, SandboxAPIKey] = Depends(require_unified_auth),
    db: Session = Depends(get_schema_aware_db),
    is_sandbox: bool = Depends(is_sandbox_request)
):
    """
    Initiate send money process with validation and confirmation.
    Supports both production (JWT) and sandbox (API key) modes.
    Rate limiting is applied via unified_auth dependency.
    """
    # Validate auth type (rate limiting handled in unified_auth)
    if is_sandbox:
        if not isinstance(auth_result, SandboxAPIKey):
            raise HTTPException(status_code=403, detail="API key required for sandbox")
    else:
        if not isinstance(auth_result, User):
            raise HTTPException(status_code=403, detail="JWT token required for production")
    
    try:
        # Sandbox mode: use test accounts
        if is_sandbox:
            sandbox_user_id = str(auth_result.sandbox_user_id)
            
            if not sender_account_id or not recipient_account_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sandbox mode requires sender_account_id and recipient_account_id"
                )
            
            # Validate test accounts
            is_valid, error_msg = sandbox_transaction_service.validate_test_accounts_for_transaction(
                db=db,
                sender_id=sender_account_id,
                recipient_id=recipient_account_id,
                sandbox_user_id=sandbox_user_id
            )
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
            
            # Get accounts
            sender_account = test_account_service.get_test_account(
                db, sender_account_id, sandbox_user_id
            )
            recipient_account = test_account_service.get_test_account(
                db, recipient_account_id, sandbox_user_id
            )
            
            # Check balance
            currency_type = request.currency_type.upper()
            if currency_type == "USDC":
                if sender_account.usdc_balance < Decimal(request.amount):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient balance. Available: {sender_account.usdc_balance} USDC"
                    )
            elif currency_type == "APT":
                if sender_account.apt_balance < Decimal(request.amount):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Insufficient balance. Available: {sender_account.apt_balance} APT"
                    )
            
            # For sandbox, we can skip password verification and proceed directly
            # Create a simplified confirmation response
            return SendMoneyResponse(
                success=True,
                message="Transaction initiated. Use /confirm to execute.",
                transaction_id=str(uuid.uuid4()),
                estimated_gas_fee="0",  # No gas in sandbox
                total_cost=str(Decimal(request.amount)),
                requires_confirmation=True
            )
        
        # Production mode: use original service
        if not isinstance(auth_result, User):
            raise HTTPException(status_code=403, detail="JWT token required")
        
        current_user = auth_result
        result = await send_money_service.initiate_send_money(request, current_user, db)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate send money process"
        )


@router.get("/confirm/{transaction_id}", response_model=SendMoneyConfirmation)
async def get_confirmation_details(
    transaction_id: str,
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=20, window_seconds=60))
):
    """
    Get transaction confirmation details
    """
    try:
        confirmation = send_money_service.get_confirmation_details(transaction_id)
        
        if not confirmation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction confirmation not found or expired"
            )
        
        return confirmation
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get confirmation details"
        )


@router.post("/confirm/{transaction_id}", response_model=SendMoneyResponse)
async def confirm_send_money(
    transaction_id: str,
    sender_account_id: Optional[str] = None,  # For sandbox mode
    recipient_account_id: Optional[str] = None,  # For sandbox mode
    amount: Optional[Decimal] = None,  # For sandbox mode
    currency_type: Optional[str] = None,  # For sandbox mode
    auth_result: Union[User, SandboxAPIKey] = Depends(require_unified_auth),
    db: Session = Depends(get_schema_aware_db),
    is_sandbox: bool = Depends(is_sandbox_request)
):
    """
    Confirm and execute the send money transaction.
    Supports both production (JWT) and sandbox (API key) modes.
    Rate limiting is applied via unified_auth dependency.
    """
    # Validate auth type (rate limiting handled in unified_auth)
    if is_sandbox:
        if not isinstance(auth_result, SandboxAPIKey):
            raise HTTPException(status_code=403, detail="API key required for sandbox")
    else:
        if not isinstance(auth_result, User):
            raise HTTPException(status_code=403, detail="JWT token required")
    
    try:
        # Sandbox mode: process transaction directly
        if is_sandbox:
            if not sender_account_id or not recipient_account_id or not amount or not currency_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Sandbox mode requires sender_account_id, recipient_account_id, amount, and currency_type"
                )
            
            sandbox_user_id = str(auth_result.sandbox_user_id)
            
            # Process sandbox transaction
            transaction_data = sandbox_transaction_service.process_sandbox_transfer(
                db=db,
                sender_account_id=sender_account_id,
                recipient_account_id=recipient_account_id,
                amount=amount,
                currency_type=currency_type,
                sandbox_user_id=sandbox_user_id
            )
            
            return SendMoneyResponse(
                success=True,
                message="Transaction confirmed and processed",
                transaction_id=transaction_data["id"],
                transaction_hash=transaction_data["transaction_hash"],
                status="confirmed"
            )
        
        # Production mode: use original service
        if not isinstance(auth_result, User):
            raise HTTPException(status_code=403, detail="JWT token required")
        
        current_user = auth_result
        result = await send_money_service.confirm_send_money(transaction_id, db)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm transaction"
        )


@router.get("/status/{transaction_id}", response_model=TransactionStatusUpdate)
async def get_transaction_status(
    transaction_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=30, window_seconds=60))
):
    """
    Get real-time transaction status
    """
    try:
        status_update = await send_money_service.get_transaction_status(transaction_id, db)
        
        if not status_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return status_update
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transaction status"
        )


@router.post("/cleanup", response_model=ApiResponse)
async def cleanup_expired_confirmations(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=300))
):
    """
    Clean up expired transaction confirmations
    """
    try:
        # Run cleanup in background
        background_tasks.add_task(send_money_service.cleanup_expired_confirmations)
        
        return ApiResponse(
            success=True,
            message="Cleanup task scheduled"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule cleanup task"
        )


@router.get("/pending", response_model=Dict[str, Any])
async def get_pending_confirmations(
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=10, window_seconds=60))
):
    """
    Get pending confirmations for the current user
    """
    try:
        pending_count = len(send_money_service._pending_confirmations)
        
        return {
            "pending_confirmations": pending_count,
            "message": f"You have {pending_count} pending transaction confirmations"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending confirmations"
        )
