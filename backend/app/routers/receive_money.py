"""
Receive Money Router for Story 2.4
Handles incoming transaction detection and management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from decimal import Decimal

from ..database import get_db
from ..models import User
from ..schemas import ApiResponse
from ..services.receive_money_service import receive_money_service
from ..dependencies import require_authentication, rate_limit

router = APIRouter()


@router.get("/transactions", response_model=List[Dict[str, Any]])
async def get_received_transactions(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    limit: int = Query(25, description="Number of transactions to return"),
    offset: int = Query(0, description="Number of transactions to skip"),
    _rate_limit: bool = Depends(rate_limit(max_requests=30, window_seconds=60))
):
    """
    Get received transactions for the current user
    """
    try:
        transactions = await receive_money_service.get_received_transactions(
            current_user, limit, offset, db
        )
        
        return transactions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve received transactions"
        )


@router.get("/transactions/{transaction_id}", response_model=Dict[str, Any])
async def get_received_transaction_details(
    transaction_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=20, window_seconds=60))
):
    """
    Get details of a specific received transaction
    """
    try:
        transaction = await receive_money_service.get_received_transaction_details(
            transaction_id, current_user, db
        )
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction details"
        )


@router.get("/balance", response_model=Dict[str, Any])
async def get_user_balance(
    currency_type: str = Query("APT", description="Currency type (APT, USDC)"),
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=60, window_seconds=60))
):
    """
    Get current balance for the user
    """
    try:
        balance = await receive_money_service.get_user_balance(
            current_user, currency_type.upper(), db
        )
        
        return {
            "balance": str(balance),
            "currency_type": currency_type.upper(),
            "wallet_address": current_user.wallet_address
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve balance"
        )


@router.post("/sync", response_model=ApiResponse)
async def sync_transactions(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=300))
):
    """
    Manually sync transactions for the current user
    """
    try:
        result = await receive_money_service.sync_user_transactions(current_user, db)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.message
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync transactions"
        )


@router.get("/notifications", response_model=List[Dict[str, Any]])
async def get_receive_notifications(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    limit: int = Query(25, description="Number of notifications to return"),
    offset: int = Query(0, description="Number of notifications to skip"),
    _rate_limit: bool = Depends(rate_limit(max_requests=30, window_seconds=60))
):
    """
    Get receive money notifications for the current user
    """
    try:
        from ..models import Notification
        
        notifications = db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.type == "payment_received"
        ).order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
        
        result = []
        for notification in notifications:
            result.append({
                "id": str(notification.id),
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "data": notification.data,
                "created_at": notification.created_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )


@router.post("/notifications/mark-read", response_model=ApiResponse)
async def mark_notifications_as_read(
    notification_ids: List[str],
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=10, window_seconds=60))
):
    """
    Mark receive money notifications as read
    """
    try:
        from ..models import Notification
        
        # Mark specified notifications as read
        updated_count = db.query(Notification).filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == current_user.id,
            Notification.type == "payment_received"
        ).update({"is_read": True})
        
        db.commit()
        
        return ApiResponse(
            success=True,
            message=f"Marked {updated_count} notifications as read"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )


@router.post("/start-monitoring", response_model=ApiResponse)
async def start_transaction_monitoring(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=300))
):
    """
    Start transaction monitoring for incoming payments
    """
    try:
        # Start monitoring in background
        background_tasks.add_task(
            receive_money_service.start_transaction_monitoring,
            db
        )
        
        return ApiResponse(
            success=True,
            message="Transaction monitoring started"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start transaction monitoring"
        )


@router.post("/stop-monitoring", response_model=ApiResponse)
async def stop_transaction_monitoring(
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=300))
):
    """
    Stop transaction monitoring
    """
    try:
        await receive_money_service.stop_transaction_monitoring()
        
        return ApiResponse(
            success=True,
            message="Transaction monitoring stopped"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop transaction monitoring"
        )


@router.get("/status", response_model=Dict[str, Any])
async def get_monitoring_status(
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=10, window_seconds=60))
):
    """
    Get transaction monitoring status
    """
    try:
        return {
            "monitoring_active": receive_money_service._monitoring_active,
            "monitoring_interval": receive_money_service._monitoring_interval,
            "last_processed_block": receive_money_service._last_processed_block,
            "processed_transactions_count": len(receive_money_service._processed_transactions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get monitoring status"
        )
