from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from ..database import get_db
from ..models import User, PaymentRequest, Transaction
from ..schemas import (
    PaymentRequestCreate,
    PaymentRequest as PaymentRequestSchema,
    PaymentRequestResponse,
    PaymentLinkPayment,
    ApiResponse
)
from ..services.payment_service import payment_service
from ..services.aptos_service import aptos_service
from ..dependencies import require_authentication
from .notifications import create_notification

router = APIRouter()


@router.post("/request", response_model=PaymentRequestResponse)
async def create_payment_request(
    payment_req: PaymentRequestCreate,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Create a new payment request"""
    
    # Verify recipient exists
    recipient = db.query(User).filter(User.id == payment_req.recipient_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    # Validate amount
    if not payment_service.validate_payment_amount(payment_req.amount, payment_req.currency_type):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payment amount for {payment_req.currency_type}"
        )
    
    try:
        # Generate payment ID
        payment_id = payment_service.generate_payment_id()
        
        # Calculate expiry timestamp
        expiry_timestamp = datetime.now(timezone.utc) + timedelta(hours=payment_req.expiry_hours)
        
        # Generate payment link and QR code
        payment_link = payment_service.generate_payment_link(
            payment_id,
            recipient.username,
            payment_req.amount,
            payment_req.currency_type,
            payment_req.description
        )
        
        qr_code_data_url = payment_service.generate_qr_code_data_url(
            payment_id,
            recipient.username,
            payment_req.amount,
            payment_req.currency_type,
            payment_req.description
        )
        
        # Create payment request in database
        db_payment_request = PaymentRequest(
            payment_id=payment_id,
            recipient_id=recipient.id,
            amount=payment_req.amount,
            currency_type=payment_req.currency_type,
            description=payment_req.description,
            qr_code_url=qr_code_data_url,
            payment_link=payment_link,
            status="pending",
            expiry_timestamp=expiry_timestamp
        )
        
        db.add(db_payment_request)
        db.commit()
        db.refresh(db_payment_request)
        
        # Create notification for recipient
        await create_notification(
            db=db,
            user_id=str(recipient.id),
            notification_type="payment_request",
            title="New Payment Request",
            message=f"{current_user.username} requested {payment_req.amount} {payment_req.currency_type}",
            data={
                "payment_id": payment_id,
                "amount": str(payment_req.amount),
                "currency_type": payment_req.currency_type,
                "requester_username": current_user.username,
                "description": payment_req.description
            }
        )
        
        return PaymentRequestResponse(
            success=True,
            message="Payment request created successfully",
            data=db_payment_request
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment request: {str(e)}"
        )


@router.get("/request/{payment_id}", response_model=PaymentRequestSchema)
async def get_payment_request(payment_id: str, db: Session = Depends(get_db)):
    """Get payment request by payment ID"""
    
    payment_request = db.query(PaymentRequest).filter(
        PaymentRequest.payment_id == payment_id
    ).first()
    
    if not payment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment request not found"
        )
    
    # Check if payment request has expired
    if payment_request.expiry_timestamp < datetime.now(timezone.utc) and payment_request.status == "pending":
        payment_request.status = "expired"
        db.commit()
    
    return payment_request


@router.post("/pay", response_model=ApiResponse)
async def pay_payment_request(
    payment: PaymentLinkPayment,
    payer_private_key: str,
    db: Session = Depends(get_db)
):
    """Pay a payment request"""
    
    # Get payment request
    payment_request = db.query(PaymentRequest).filter(
        PaymentRequest.payment_id == payment.payment_id
    ).first()
    
    if not payment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment request not found"
        )
    
    # Check if payment request is still valid
    if payment_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment request is {payment_request.status}"
        )
    
    if payment_request.expiry_timestamp < datetime.now(timezone.utc):
        payment_request.status = "expired"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment request has expired"
        )
    
    # Get payer information
    try:
        from aptos_sdk.account import Account
        payer_account = Account.load_key(payer_private_key)
        payer_address = str(payer_account.address())
        
        payer_user = db.query(User).filter(User.wallet_address == payer_address).first()
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid payer private key"
        )
    
    # Get recipient
    recipient = db.query(User).filter(User.id == payment_request.recipient_id).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    try:
        # Execute blockchain transaction
        if payment_request.currency_type == "APT":
            tx_hash = await aptos_service.transfer_apt(
                payer_private_key,
                recipient.wallet_address,
                payment_request.amount
            )
        elif payment_request.currency_type == "USDC":
            tx_hash = await aptos_service.transfer_usdc(
                payer_private_key,
                recipient.wallet_address,
                payment_request.amount
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported currency type"
            )
        
        if not tx_hash:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to execute payment transaction"
            )
        
        # Create transaction record
        db_transaction = Transaction(
            transaction_hash=tx_hash,
            sender_id=payer_user.id if payer_user else None,
            recipient_id=recipient.id,
            sender_address=payer_address,
            recipient_address=recipient.wallet_address,
            amount=payment_request.amount,
            currency_type=payment_request.currency_type,
            transaction_type="payment_request",
            status="confirmed",
            description=f"Payment for request: {payment_request.description or payment_request.payment_id}"
        )
        
        db.add(db_transaction)
        
        # Update payment request status
        payment_request.status = "paid"
        payment_request.transaction_id = db_transaction.id
        
        db.commit()
        db.refresh(db_transaction)
        
        return ApiResponse(
            success=True,
            message="Payment completed successfully",
            data={
                "transaction_hash": tx_hash,
                "transaction_id": str(db_transaction.id),
                "amount": str(payment_request.amount),
                "currency_type": payment_request.currency_type
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment failed: {str(e)}"
        )


@router.get("/user/{user_id}/requests", response_model=List[PaymentRequestSchema])
async def get_user_payment_requests(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get payment requests for a user"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    query = db.query(PaymentRequest).filter(PaymentRequest.recipient_id == user_id)
    
    if status:
        query = query.filter(PaymentRequest.status == status)
    
    payment_requests = query.order_by(
        PaymentRequest.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    # Update expired payment requests
    current_time = datetime.now(timezone.utc)
    for pr in payment_requests:
        if pr.status == "pending" and pr.expiry_timestamp < current_time:
            pr.status = "expired"
    
    db.commit()
    
    return payment_requests


@router.put("/request/{payment_id}/cancel", response_model=ApiResponse)
async def cancel_payment_request(
    payment_id: str,
    recipient_id: str,
    db: Session = Depends(get_db)
):
    """Cancel a payment request"""
    
    payment_request = db.query(PaymentRequest).filter(
        PaymentRequest.payment_id == payment_id
    ).first()
    
    if not payment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment request not found"
        )
    
    # Verify the recipient is canceling their own request
    if str(payment_request.recipient_id) != recipient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own payment requests"
        )
    
    if payment_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel payment request with status: {payment_request.status}"
        )
    
    payment_request.status = "cancelled"
    db.commit()
    
    return ApiResponse(
        success=True,
        message="Payment request cancelled successfully",
        data={"payment_id": payment_id, "status": "cancelled"}
    )


@router.get("/qr/{payment_id}")
async def get_payment_qr_code(payment_id: str, db: Session = Depends(get_db)):
    """Get QR code for payment request"""
    
    payment_request = db.query(PaymentRequest).filter(
        PaymentRequest.payment_id == payment_id
    ).first()
    
    if not payment_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment request not found"
        )
    
    if payment_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment request is not active"
        )
    
    return {
        "payment_id": payment_id,
        "qr_code_url": payment_request.qr_code_url,
        "payment_link": payment_request.payment_link,
        "amount": str(payment_request.amount),
        "currency_type": payment_request.currency_type,
        "description": payment_request.description,
        "expires_at": payment_request.expiry_timestamp.isoformat()
    }
