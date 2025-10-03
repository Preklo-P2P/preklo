"""
Transaction Limits and Controls Router for Story 2.6
API endpoints for transaction limits, spending controls, approvals, and emergency blocking
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, timezone

from ..database import get_db
from ..models import User, TransactionLimit, SpendingControl, TransactionApproval, EmergencyBlock, SpendingAlert
from ..schemas import ApiResponse
from ..services.transaction_limits_service import transaction_limits_service
from ..dependencies import require_authentication, rate_limit

router = APIRouter()


@router.get("/limits", response_model=List[Dict[str, Any]])
async def get_transaction_limits(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    currency_type: Optional[str] = Query(None, description="Filter by currency type"),
    _rate_limit: bool = Depends(rate_limit(max_requests=30, window_seconds=60))
):
    """
    Get user's transaction limits
    """
    try:
        query = db.query(TransactionLimit).filter(
            TransactionLimit.user_id == current_user.id,
            TransactionLimit.is_active == True
        )
        
        if currency_type:
            query = query.filter(TransactionLimit.currency_type == currency_type.upper())
        
        limits = query.all()
        
        result = []
        for limit in limits:
            result.append({
                "id": str(limit.id),
                "limit_type": limit.limit_type,
                "currency_type": limit.currency_type,
                "limit_amount": str(limit.limit_amount),
                "current_usage": str(limit.current_usage),
                "period_start": limit.period_start.isoformat(),
                "period_end": limit.period_end.isoformat(),
                "usage_percentage": float(limit.current_usage / limit.limit_amount * 100) if limit.limit_amount > 0 else 0
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transaction limits"
        )


@router.put("/limits", response_model=ApiResponse)
async def update_transaction_limits(
    limits_data: Dict[str, Any],
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=300))
):
    """
    Update user's transaction limits
    """
    try:
        # Validate required fields
        required_fields = ["limit_type", "currency_type", "limit_amount"]
        for field in required_fields:
            if field not in limits_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        limit_type = limits_data["limit_type"]
        currency_type = limits_data["currency_type"].upper()
        limit_amount = Decimal(str(limits_data["limit_amount"]))
        
        if limit_type not in ["daily", "weekly", "monthly"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid limit type. Must be 'daily', 'weekly', or 'monthly'"
            )
        
        if limit_amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit amount must be greater than 0"
            )
        
        # Calculate period dates
        now = datetime.now(timezone.utc)
        if limit_type == "daily":
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            period_end = period_start + timedelta(days=1)
        elif limit_type == "weekly":
            days_since_monday = now.weekday()
            period_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday)
            period_end = period_start + timedelta(weeks=1)
        else:  # monthly
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                period_end = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                period_end = now.replace(month=now.month + 1, day=1) - timedelta(days=1)
            period_end = period_end.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Check if limit already exists
        existing_limit = db.query(TransactionLimit).filter(
            TransactionLimit.user_id == current_user.id,
            TransactionLimit.limit_type == limit_type,
            TransactionLimit.currency_type == currency_type,
            TransactionLimit.is_active == True
        ).first()
        
        if existing_limit:
            # Update existing limit
            existing_limit.limit_amount = limit_amount
            existing_limit.period_start = period_start
            existing_limit.period_end = period_end
            existing_limit.updated_at = now
        else:
            # Create new limit
            new_limit = TransactionLimit(
                user_id=current_user.id,
                limit_type=limit_type,
                currency_type=currency_type,
                limit_amount=limit_amount,
                current_usage=Decimal("0"),
                period_start=period_start,
                period_end=period_end
            )
            db.add(new_limit)
        
        db.commit()
        
        return ApiResponse(
            success=True,
            message=f"{limit_type.title()} limit updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update transaction limits"
        )


@router.get("/limits/usage", response_model=Dict[str, Any])
async def get_limit_usage(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    currency_type: Optional[str] = Query(None, description="Filter by currency type"),
    _rate_limit: bool = Depends(rate_limit(max_requests=60, window_seconds=60))
):
    """
    Get current limit usage for user
    """
    try:
        # Get all active limits
        query = db.query(TransactionLimit).filter(
            TransactionLimit.user_id == current_user.id,
            TransactionLimit.is_active == True
        )
        
        if currency_type:
            query = query.filter(TransactionLimit.currency_type == currency_type.upper())
        
        limits = query.all()
        
        usage_data = {}
        for limit in limits:
            # Calculate actual usage from transactions
            actual_usage = await transaction_limits_service._calculate_period_usage(
                current_user, limit.currency_type, limit.period_start, limit.period_end, db
            )
            
            # Update stored usage
            limit.current_usage = actual_usage
            db.commit()
            
            usage_data[f"{limit.limit_type}_{limit.currency_type}"] = {
                "limit_amount": str(limit.limit_amount),
                "current_usage": str(actual_usage),
                "remaining": str(limit.limit_amount - actual_usage),
                "usage_percentage": float(actual_usage / limit.limit_amount * 100) if limit.limit_amount > 0 else 0,
                "period_start": limit.period_start.isoformat(),
                "period_end": limit.period_end.isoformat()
            }
        
        return usage_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve limit usage"
        )


@router.get("/controls", response_model=List[Dict[str, Any]])
async def get_spending_controls(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=30, window_seconds=60))
):
    """
    Get user's spending controls
    """
    try:
        controls = db.query(SpendingControl).filter(
            SpendingControl.user_id == current_user.id,
            SpendingControl.is_active == True
        ).all()
        
        result = []
        for control in controls:
            result.append({
                "id": str(control.id),
                "control_type": control.control_type,
                "currency_type": control.currency_type,
                "max_amount": str(control.max_amount) if control.max_amount else None,
                "merchant_categories": control.merchant_categories,
                "allowed_countries": control.allowed_countries,
                "blocked_countries": control.blocked_countries,
                "allowed_hours": control.allowed_hours,
                "created_at": control.created_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve spending controls"
        )


@router.post("/controls", response_model=ApiResponse)
async def create_spending_control(
    control_data: Dict[str, Any],
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=300))
):
    """
    Create a new spending control
    """
    try:
        # Validate required fields
        required_fields = ["control_type", "currency_type"]
        for field in required_fields:
            if field not in control_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        control_type = control_data["control_type"]
        currency_type = control_data["currency_type"].upper()
        
        if control_type not in ["max_amount", "merchant_category", "geographic", "time_based"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid control type"
            )
        
        # Create spending control
        spending_control = SpendingControl(
            user_id=current_user.id,
            control_type=control_type,
            currency_type=currency_type,
            max_amount=Decimal(str(control_data.get("max_amount", 0))) if control_data.get("max_amount") else None,
            merchant_categories=control_data.get("merchant_categories"),
            allowed_countries=control_data.get("allowed_countries"),
            blocked_countries=control_data.get("blocked_countries"),
            allowed_hours=control_data.get("allowed_hours")
        )
        
        db.add(spending_control)
        db.commit()
        
        return ApiResponse(
            success=True,
            message="Spending control created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create spending control"
        )


@router.get("/approvals/pending", response_model=List[Dict[str, Any]])
async def get_pending_approvals(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=30, window_seconds=60))
):
    """
    Get pending transaction approvals
    """
    try:
        approvals = db.query(TransactionApproval).filter(
            TransactionApproval.user_id == current_user.id,
            TransactionApproval.status == "pending",
            TransactionApproval.expires_at > datetime.now(timezone.utc)
        ).all()
        
        result = []
        for approval in approvals:
            result.append({
                "id": str(approval.id),
                "approval_type": approval.approval_type,
                "amount": str(approval.amount),
                "currency_type": approval.currency_type,
                "description": approval.description,
                "expires_at": approval.expires_at.isoformat(),
                "created_at": approval.created_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending approvals"
        )


@router.post("/approvals/{approval_id}/approve", response_model=ApiResponse)
async def approve_transaction(
    approval_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=10, window_seconds=60))
):
    """
    Approve a pending transaction
    """
    try:
        result = await transaction_limits_service.approve_transaction(
            approval_id, current_user, "manual", db
        )
        
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
            detail="Failed to approve transaction"
        )


@router.post("/approvals/{approval_id}/reject", response_model=ApiResponse)
async def reject_transaction(
    approval_id: str,
    rejection_data: Dict[str, str],
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=10, window_seconds=60))
):
    """
    Reject a pending transaction
    """
    try:
        reason = rejection_data.get("reason", "No reason provided")
        
        result = await transaction_limits_service.reject_transaction(
            approval_id, current_user, reason, db
        )
        
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
            detail="Failed to reject transaction"
        )


@router.post("/emergency/block", response_model=ApiResponse)
async def create_emergency_block(
    block_data: Dict[str, str],
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=3, window_seconds=300))
):
    """
    Create an emergency block
    """
    try:
        required_fields = ["block_type", "reason"]
        for field in required_fields:
            if field not in block_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        block_type = block_data["block_type"]
        reason = block_data["reason"]
        description = block_data.get("description")
        
        if block_type not in ["account_freeze", "transaction_block", "card_block"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid block type"
            )
        
        result = await transaction_limits_service.create_emergency_block(
            current_user, block_type, reason, description, current_user, db
        )
        
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
            detail="Failed to create emergency block"
        )


@router.get("/emergency/blocks", response_model=List[Dict[str, Any]])
async def get_emergency_blocks(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=30, window_seconds=60))
):
    """
    Get user's emergency blocks
    """
    try:
        blocks = db.query(EmergencyBlock).filter(
            EmergencyBlock.user_id == current_user.id
        ).order_by(EmergencyBlock.created_at.desc()).all()
        
        result = []
        for block in blocks:
            result.append({
                "id": str(block.id),
                "block_type": block.block_type,
                "reason": block.reason,
                "description": block.description,
                "is_active": block.is_active,
                "created_at": block.created_at.isoformat(),
                "unblocked_at": block.unblocked_at.isoformat() if block.unblocked_at else None
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve emergency blocks"
        )


@router.post("/emergency/blocks/{block_id}/unblock", response_model=ApiResponse)
async def remove_emergency_block(
    block_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=300))
):
    """
    Remove an emergency block
    """
    try:
        result = await transaction_limits_service.remove_emergency_block(
            block_id, current_user, db
        )
        
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
            detail="Failed to remove emergency block"
        )


@router.get("/alerts", response_model=List[Dict[str, Any]])
async def get_spending_alerts(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=30, window_seconds=60))
):
    """
    Get user's spending alerts
    """
    try:
        alerts = db.query(SpendingAlert).filter(
            SpendingAlert.user_id == current_user.id,
            SpendingAlert.is_active == True
        ).all()
        
        result = []
        for alert in alerts:
            result.append({
                "id": str(alert.id),
                "alert_type": alert.alert_type,
                "limit_type": alert.limit_type,
                "threshold_percentage": float(alert.threshold_percentage) if alert.threshold_percentage else None,
                "currency_type": alert.currency_type,
                "amount_threshold": str(alert.amount_threshold) if alert.amount_threshold else None,
                "notification_methods": alert.notification_methods,
                "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None,
                "created_at": alert.created_at.isoformat()
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve spending alerts"
        )


@router.post("/alerts", response_model=ApiResponse)
async def create_spending_alert(
    alert_data: Dict[str, Any],
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=300))
):
    """
    Create a new spending alert
    """
    try:
        # Validate required fields
        required_fields = ["alert_type", "currency_type"]
        for field in required_fields:
            if field not in alert_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        alert_type = alert_data["alert_type"]
        currency_type = alert_data["currency_type"].upper()
        
        if alert_type not in ["limit_threshold", "unusual_spending", "large_transaction"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid alert type"
            )
        
        # Create spending alert
        spending_alert = SpendingAlert(
            user_id=current_user.id,
            alert_type=alert_type,
            limit_type=alert_data.get("limit_type"),
            threshold_percentage=Decimal(str(alert_data.get("threshold_percentage", 80))) if alert_data.get("threshold_percentage") else None,
            currency_type=currency_type,
            amount_threshold=Decimal(str(alert_data.get("amount_threshold", 0))) if alert_data.get("amount_threshold") else None,
            notification_methods=alert_data.get("notification_methods", ["email"])
        )
        
        db.add(spending_alert)
        db.commit()
        
        return ApiResponse(
            success=True,
            message="Spending alert created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create spending alert"
        )
