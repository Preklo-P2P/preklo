"""
Send Money Router for Story 2.3
Enhanced send money functionality with confirmation flow and real-time updates
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..models import User
from ..schemas import (
    SendMoneyRequest,
    SendMoneyResponse,
    SendMoneyConfirmation,
    TransactionStatusUpdate,
    ApiResponse
)
from ..services.send_money_service import send_money_service
from ..dependencies import require_authentication, rate_limit

router = APIRouter()


@router.post("/initiate", response_model=SendMoneyResponse)
async def initiate_send_money(
    request: SendMoneyRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=10, window_seconds=60))
):
    """
    Initiate send money process with validation and confirmation
    """
    try:
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
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=60))
):
    """
    Confirm and execute the send money transaction
    """
    try:
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
