"""
Payment Request Service

Handles payment request creation, management, and processing.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import PaymentRequest, User, Transaction
from app.schemas import PaymentRequestCreate, PaymentRequestUpdate, PaymentRequestResponse
from app.config import settings
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService


class PaymentRequestService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.email_service = EmailService()

    def create_payment_request(
        self, 
        sender_id: str, 
        request_data: PaymentRequestCreate
    ) -> PaymentRequestResponse:
        """Create a new payment request."""
        
        # Validate recipient exists
        recipient = self.db.query(User).filter(
            User.username == request_data.recipient_username
        ).first()
        
        if not recipient:
            raise ValueError("Recipient not found")
        
        if recipient.id == sender_id:
            raise ValueError("Cannot send payment request to yourself")
        
        # Set expiration date if not provided
        expires_at = request_data.expires_at
        if not expires_at:
            expires_at = datetime.now(timezone.utc) + timedelta(days=7)  # Default 7 days
        
        # Create payment request
        payment_request = PaymentRequest(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            recipient_id=recipient.id,
            amount=request_data.amount,
            currency=request_data.currency,
            description=request_data.description,
            status="pending",
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(payment_request)
        self.db.commit()
        self.db.refresh(payment_request)
        
        # Send notifications
        self._send_payment_request_notifications(payment_request)
        
        return PaymentRequestResponse.from_orm(payment_request)
    
    def get_payment_requests(
        self, 
        user_id: str, 
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[PaymentRequestResponse]:
        """Get payment requests for a user (sent or received)."""
        
        query = self.db.query(PaymentRequest).filter(
            or_(
                PaymentRequest.sender_id == user_id,
                PaymentRequest.recipient_id == user_id
            )
        )
        
        if status:
            query = query.filter(PaymentRequest.status == status)
        
        payment_requests = query.order_by(
            PaymentRequest.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [PaymentRequestResponse.from_orm(req) for req in payment_requests]
    
    def get_payment_request(self, request_id: str, user_id: str) -> Optional[PaymentRequestResponse]:
        """Get a specific payment request."""
        
        payment_request = self.db.query(PaymentRequest).filter(
            and_(
                PaymentRequest.id == request_id,
                or_(
                    PaymentRequest.sender_id == user_id,
                    PaymentRequest.recipient_id == user_id
                )
            )
        ).first()
        
        if not payment_request:
            return None
        
        return PaymentRequestResponse.from_orm(payment_request)
    
    def update_payment_request(
        self, 
        request_id: str, 
        user_id: str, 
        update_data: PaymentRequestUpdate
    ) -> Optional[PaymentRequestResponse]:
        """Update a payment request (only sender can update)."""
        
        payment_request = self.db.query(PaymentRequest).filter(
            and_(
                PaymentRequest.id == request_id,
                PaymentRequest.sender_id == user_id,
                PaymentRequest.status == "pending"
            )
        ).first()
        
        if not payment_request:
            return None
        
        # Update fields
        if update_data.amount is not None:
            payment_request.amount = update_data.amount
        if update_data.currency is not None:
            payment_request.currency = update_data.currency
        if update_data.description is not None:
            payment_request.description = update_data.description
        if update_data.expires_at is not None:
            payment_request.expires_at = update_data.expires_at
        
        payment_request.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(payment_request)
        
        return PaymentRequestResponse.from_orm(payment_request)
    
    def cancel_payment_request(self, request_id: str, user_id: str) -> bool:
        """Cancel a payment request."""
        
        payment_request = self.db.query(PaymentRequest).filter(
            and_(
                PaymentRequest.id == request_id,
                PaymentRequest.sender_id == user_id,
                PaymentRequest.status == "pending"
            )
        ).first()
        
        if not payment_request:
            return False
        
        payment_request.status = "cancelled"
        payment_request.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        # Send cancellation notification
        self._send_cancellation_notification(payment_request)
        
        return True
    
    def pay_payment_request(
        self, 
        request_id: str, 
        payer_id: str,
        transaction_id: str
    ) -> Optional[PaymentRequestResponse]:
        """Mark a payment request as paid."""
        
        payment_request = self.db.query(PaymentRequest).filter(
            and_(
                PaymentRequest.id == request_id,
                PaymentRequest.recipient_id == payer_id,
                PaymentRequest.status == "pending"
            )
        ).first()
        
        if not payment_request:
            return None
        
        # Check if request has expired
        if payment_request.expires_at and payment_request.expires_at < datetime.now(timezone.utc):
            payment_request.status = "expired"
            payment_request.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            return None
        
        # Mark as paid
        payment_request.status = "paid"
        payment_request.paid_at = datetime.now(timezone.utc)
        payment_request.transaction_id = transaction_id
        payment_request.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(payment_request)
        
        # Send payment confirmation notifications
        self._send_payment_confirmation_notifications(payment_request)
        
        return PaymentRequestResponse.from_orm(payment_request)
    
    def get_payment_request_templates(self, user_id: str) -> List[Dict[str, Any]]:
        """Get payment request templates for a user."""
        
        # Get user's transaction history to suggest templates
        recent_transactions = self.db.query(Transaction).filter(
            or_(
                Transaction.sender_id == user_id,
                Transaction.recipient_id == user_id
            )
        ).order_by(Transaction.created_at.desc()).limit(20).all()
        
        # Generate templates based on common descriptions and amounts
        templates = []
        
        # Common templates
        common_templates = [
            {"name": "Lunch", "amount": 15.00, "description": "Lunch payment"},
            {"name": "Rent", "amount": 500.00, "description": "Monthly rent"},
            {"name": "Utilities", "amount": 75.00, "description": "Utility bill split"},
            {"name": "Groceries", "amount": 50.00, "description": "Grocery shopping"},
            {"name": "Gas", "amount": 30.00, "description": "Gas money"},
        ]
        
        # Add user-specific templates based on history
        user_templates = {}
        for transaction in recent_transactions:
            if transaction.description:
                desc = transaction.description.lower()
                amount = float(transaction.amount)
                
                # Group similar descriptions
                if "lunch" in desc or "food" in desc:
                    user_templates["lunch"] = {"amount": amount, "description": transaction.description}
                elif "rent" in desc:
                    user_templates["rent"] = {"amount": amount, "description": transaction.description}
                elif "utility" in desc or "bill" in desc:
                    user_templates["utilities"] = {"amount": amount, "description": transaction.description}
        
        # Combine common and user templates
        for template in common_templates:
            if template["name"].lower() not in user_templates:
                templates.append(template)
        
        for name, data in user_templates.items():
            templates.append({
                "name": name.title(),
                "amount": data["amount"],
                "description": data["description"]
            })
        
        return templates[:10]  # Limit to 10 templates
    
    def cleanup_expired_requests(self) -> int:
        """Clean up expired payment requests."""
        
        expired_requests = self.db.query(PaymentRequest).filter(
            and_(
                PaymentRequest.status == "pending",
                PaymentRequest.expires_at < datetime.now(timezone.utc)
            )
        ).all()
        
        count = 0
        for request in expired_requests:
            request.status = "expired"
            request.updated_at = datetime.now(timezone.utc)
            count += 1
        
        self.db.commit()
        return count
    
    def _send_payment_request_notifications(self, payment_request: PaymentRequest):
        """Send notifications for new payment request."""
        
        # Get sender and recipient info
        sender = self.db.query(User).filter(User.id == payment_request.sender_id).first()
        recipient = self.db.query(User).filter(User.id == payment_request.recipient_id).first()
        
        if not sender or not recipient:
            return
        
        # Send in-app notification to recipient
        self.notification_service.create_notification(
            user_id=recipient.id,
            title="New Payment Request",
            message=f"{sender.username} requested ${payment_request.amount} {payment_request.currency}",
            type="payment_request",
            data={
                "payment_request_id": payment_request.id,
                "sender_username": sender.username,
                "amount": float(payment_request.amount),
                "currency": payment_request.currency
            }
        )
        
        # Send email notification to recipient
        if recipient.email:
            self.email_service.send_payment_request_email(
                recipient_email=recipient.email,
                recipient_name=recipient.username,
                sender_name=sender.username,
                amount=payment_request.amount,
                currency=payment_request.currency,
                description=payment_request.description,
                request_id=payment_request.id
            )
    
    def _send_cancellation_notification(self, payment_request: PaymentRequest):
        """Send notification for cancelled payment request."""
        
        sender = self.db.query(User).filter(User.id == payment_request.sender_id).first()
        recipient = self.db.query(User).filter(User.id == payment_request.recipient_id).first()
        
        if not sender or not recipient:
            return
        
        self.notification_service.create_notification(
            user_id=recipient.id,
            title="Payment Request Cancelled",
            message=f"{sender.username} cancelled their payment request",
            type="payment_request_cancelled",
            data={
                "payment_request_id": payment_request.id,
                "sender_username": sender.username
            }
        )
    
    def _send_payment_confirmation_notifications(self, payment_request: PaymentRequest):
        """Send notifications for paid payment request."""
        
        sender = self.db.query(User).filter(User.id == payment_request.sender_id).first()
        recipient = self.db.query(User).filter(User.id == payment_request.recipient_id).first()
        
        if not sender or not recipient:
            return
        
        # Notify sender that request was paid
        self.notification_service.create_notification(
            user_id=sender.id,
            title="Payment Request Paid",
            message=f"{recipient.username} paid your request for ${payment_request.amount} {payment_request.currency}",
            type="payment_request_paid",
            data={
                "payment_request_id": payment_request.id,
                "recipient_username": recipient.username,
                "amount": float(payment_request.amount),
                "currency": payment_request.currency
            }
        )
        
        # Send email confirmation to sender
        if sender.email:
            self.email_service.send_payment_confirmation_email(
                sender_email=sender.email,
                sender_name=sender.username,
                recipient_name=recipient.username,
                amount=payment_request.amount,
                currency=payment_request.currency,
                transaction_id=payment_request.transaction_id
            )
