"""
Payment Request API Router

Handles payment request creation, management, and processing.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import User
from app.schemas import (
    PaymentRequestCreate, 
    PaymentRequestUpdate, 
    PaymentRequestResponse,
    PaymentRequestListResponse,
    PaymentRequestTemplate
)
from app.services.payment_request_service import PaymentRequestService
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/payment-requests", tags=["payment-requests"])


@router.post("/", response_model=PaymentRequestResponse)
async def create_payment_request(
    request_data: PaymentRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new payment request."""
    try:
        service = PaymentRequestService(db)
        payment_request = service.create_payment_request(
            sender_id=str(current_user.id),
            request_data=request_data
        )
        return payment_request
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create payment request")


@router.get("/", response_model=PaymentRequestListResponse)
async def get_payment_requests(
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment requests for the current user."""
    try:
        service = PaymentRequestService(db)
        offset = (page - 1) * page_size
        
        payment_requests = service.get_payment_requests(
            user_id=str(current_user.id),
            status=status,
            limit=page_size,
            offset=offset
        )
        
        # Get total count for pagination
        total_requests = service.get_payment_requests(
            user_id=str(current_user.id),
            status=status,
            limit=1000,  # Get all for count
            offset=0
        )
        
        return PaymentRequestListResponse(
            payment_requests=payment_requests,
            total=len(total_requests),
            page=page,
            page_size=page_size,
            has_more=len(payment_requests) == page_size
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get payment requests")


@router.get("/{request_id}", response_model=PaymentRequestResponse)
async def get_payment_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific payment request."""
    try:
        service = PaymentRequestService(db)
        payment_request = service.get_payment_request(request_id, str(current_user.id))
        
        if not payment_request:
            raise HTTPException(status_code=404, detail="Payment request not found")
        
        return payment_request
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get payment request")


@router.put("/{request_id}", response_model=PaymentRequestResponse)
async def update_payment_request(
    request_id: str,
    update_data: PaymentRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a payment request (only sender can update)."""
    try:
        service = PaymentRequestService(db)
        payment_request = service.update_payment_request(
            request_id=request_id,
            user_id=str(current_user.id),
            update_data=update_data
        )
        
        if not payment_request:
            raise HTTPException(status_code=404, detail="Payment request not found or cannot be updated")
        
        return payment_request
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update payment request")


@router.delete("/{request_id}")
async def cancel_payment_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a payment request."""
    try:
        service = PaymentRequestService(db)
        success = service.cancel_payment_request(request_id, str(current_user.id))
        
        if not success:
            raise HTTPException(status_code=404, detail="Payment request not found or cannot be cancelled")
        
        return {"message": "Payment request cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to cancel payment request")


@router.post("/{request_id}/pay", response_model=PaymentRequestResponse)
async def pay_payment_request(
    request_id: str,
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a payment request as paid."""
    try:
        service = PaymentRequestService(db)
        payment_request = service.pay_payment_request(
            request_id=request_id,
            payer_id=str(current_user.id),
            transaction_id=transaction_id
        )
        
        if not payment_request:
            raise HTTPException(
                status_code=404, 
                detail="Payment request not found, expired, or already paid"
            )
        
        return payment_request
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to pay payment request")


@router.get("/templates/list", response_model=List[PaymentRequestTemplate])
async def get_payment_request_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment request templates for the current user."""
    try:
        service = PaymentRequestService(db)
        templates = service.get_payment_request_templates(str(current_user.id))
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get payment request templates")


@router.post("/cleanup/expired")
async def cleanup_expired_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up expired payment requests (admin function)."""
    try:
        service = PaymentRequestService(db)
        count = service.cleanup_expired_requests()
        return {"message": f"Cleaned up {count} expired payment requests"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to cleanup expired requests")
