"""
Voucher Service

Handles voucher creation, redemption, and management.
"""

import uuid
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import Voucher, User
from app.schemas import VoucherCreate, VoucherRedeem, VoucherResponse
from app.config import settings
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService


class VoucherService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.email_service = EmailService()

    def create_voucher(
        self, 
        creator_id: str, 
        voucher_data: VoucherCreate
    ) -> VoucherResponse:
        """Create a new voucher."""
        
        # Check user balance
        user = self.db.query(User).filter(User.id == creator_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Generate unique voucher code
        voucher_code = self._generate_voucher_code()
        
        # Hash PIN if provided
        pin_hash = None
        if voucher_data.pin:
            pin_hash = self._hash_pin(voucher_data.pin)
        
        # Calculate expiration time
        expires_at = datetime.now(timezone.utc) + timedelta(hours=voucher_data.expires_in_hours)
        
        # Create voucher
        voucher = Voucher(
            id=str(uuid.uuid4()),
            voucher_code=voucher_code,
            creator_id=creator_id,
            amount=voucher_data.amount,
            currency_type=voucher_data.currency,
            status="active",
            pin_hash=pin_hash,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.db.add(voucher)
        self.db.commit()
        self.db.refresh(voucher)
        
        # Send notification to creator
        self._send_voucher_created_notification(voucher)
        
        return self._format_voucher_response(voucher)
    
    def get_vouchers(
        self, 
        user_id: str, 
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[VoucherResponse]:
        """Get vouchers for a user (created or redeemed)."""
        
        query = self.db.query(Voucher).filter(
            or_(
                Voucher.creator_id == user_id,
                Voucher.redeemed_by == user_id
            )
        )
        
        if status:
            query = query.filter(Voucher.status == status)
        
        vouchers = query.order_by(
            Voucher.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [self._format_voucher_response(voucher) for voucher in vouchers]
    
    def get_voucher(self, voucher_code: str) -> Optional[VoucherResponse]:
        """Get a specific voucher by code."""
        
        voucher = self.db.query(Voucher).filter(
            Voucher.voucher_code == voucher_code.upper()
        ).first()
        
        if not voucher:
            return None
        
        return self._format_voucher_response(voucher)
    
    def redeem_voucher(
        self, 
        voucher_code: str, 
        redeemer_id: str,
        pin: Optional[str] = None
    ) -> VoucherResponse:
        """Redeem a voucher."""
        
        voucher = self.db.query(Voucher).filter(
            Voucher.voucher_code == voucher_code.upper()
        ).first()
        
        if not voucher:
            raise ValueError("Voucher not found")
        
        if voucher.status != "active":
            raise ValueError(f"Voucher is {voucher.status}")
        
        if voucher.expires_at < datetime.now(timezone.utc):
            voucher.status = "expired"
            voucher.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            raise ValueError("Voucher has expired")
        
        if voucher.creator_id == redeemer_id:
            raise ValueError("Cannot redeem your own voucher")
        
        # Verify PIN if required
        if voucher.pin_hash:
            if not pin:
                raise ValueError("PIN is required for this voucher")
            if not self._verify_pin(pin, voucher.pin_hash):
                raise ValueError("Invalid PIN")
        
        # Mark voucher as redeemed
        voucher.status = "redeemed"
        voucher.redeemed_at = datetime.now(timezone.utc)
        voucher.redeemed_by = redeemer_id
        voucher.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        self.db.refresh(voucher)
        
        # Send notifications
        self._send_voucher_redeemed_notifications(voucher)
        
        return self._format_voucher_response(voucher)
    
    def cancel_voucher(self, voucher_code: str, user_id: str) -> bool:
        """Cancel a voucher (only creator can cancel)."""
        
        voucher = self.db.query(Voucher).filter(
            and_(
                Voucher.voucher_code == voucher_code.upper(),
                Voucher.creator_id == user_id,
                Voucher.status == "active"
            )
        ).first()
        
        if not voucher:
            return False
        
        voucher.status = "cancelled"
        voucher.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        # Send cancellation notification
        self._send_voucher_cancelled_notification(voucher)
        
        return True
    
    def cleanup_expired_vouchers(self) -> int:
        """Clean up expired vouchers."""
        
        expired_vouchers = self.db.query(Voucher).filter(
            and_(
                Voucher.status == "active",
                Voucher.expires_at < datetime.now(timezone.utc)
            )
        ).all()
        
        count = 0
        for voucher in expired_vouchers:
            voucher.status = "expired"
            voucher.updated_at = datetime.now(timezone.utc)
            count += 1
        
        self.db.commit()
        return count
    
    def get_voucher_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get voucher analytics for a user."""
        
        created_vouchers = self.db.query(Voucher).filter(
            Voucher.creator_id == user_id
        ).all()
        
        redeemed_vouchers = self.db.query(Voucher).filter(
            Voucher.redeemed_by == user_id
        ).all()
        
        total_created = len(created_vouchers)
        total_redeemed = len(redeemed_vouchers)
        total_amount_created = sum(float(v.amount) for v in created_vouchers)
        total_amount_redeemed = sum(float(v.amount) for v in redeemed_vouchers)
        
        status_counts = {}
        for voucher in created_vouchers:
            status_counts[voucher.status] = status_counts.get(voucher.status, 0) + 1
        
        return {
            "total_created": total_created,
            "total_redeemed": total_redeemed,
            "total_amount_created": total_amount_created,
            "total_amount_redeemed": total_amount_redeemed,
            "status_breakdown": status_counts,
            "success_rate": (status_counts.get("redeemed", 0) / total_created * 100) if total_created > 0 else 0
        }
    
    def _generate_voucher_code(self) -> str:
        """Generate a unique 20-character voucher code."""
        while True:
            # Generate 20-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(20))
            
            # Check if code already exists
            existing = self.db.query(Voucher).filter(Voucher.voucher_code == code).first()
            if not existing:
                return code
    
    def _hash_pin(self, pin: str) -> str:
        """Hash a PIN for secure storage."""
        return hashlib.sha256(pin.encode()).hexdigest()
    
    def _verify_pin(self, pin: str, pin_hash: str) -> bool:
        """Verify a PIN against its hash."""
        return self._hash_pin(pin) == pin_hash
    
    def _format_voucher_response(self, voucher: Voucher) -> VoucherResponse:
        """Format voucher for response."""
        
        # Calculate time remaining
        time_remaining = None
        if voucher.status == "active" and voucher.expires_at:
            remaining = voucher.expires_at - datetime.now(timezone.utc)
            if remaining.total_seconds() > 0:
                hours = int(remaining.total_seconds() // 3600)
                minutes = int((remaining.total_seconds() % 3600) // 60)
                if hours > 0:
                    time_remaining = f"{hours}h {minutes}m"
                else:
                    time_remaining = f"{minutes}m"
            else:
                time_remaining = "Expired"
        
        # Get usernames
        creator_username = None
        redeemer_username = None
        
        if voucher.creator:
            creator_username = voucher.creator.username
        
        if voucher.redeemer:
            redeemer_username = voucher.redeemer.username
        
        return VoucherResponse(
            id=voucher.id,
            voucher_code=voucher.voucher_code,
            creator_id=voucher.creator_id,
            amount=voucher.amount,
            currency=voucher.currency_type,
            status=voucher.status,
            has_pin=voucher.pin_hash is not None,
            expires_at=voucher.expires_at,
            redeemed_at=voucher.redeemed_at,
            redeemed_by=voucher.redeemed_by,
            created_at=voucher.created_at,
            updated_at=voucher.updated_at,
            creator_username=creator_username,
            redeemer_username=redeemer_username,
            time_remaining=time_remaining
        )
    
    def _send_voucher_created_notification(self, voucher: Voucher):
        """Send notification when voucher is created."""
        
        self.notification_service.create_notification(
            user_id=voucher.creator_id,
            title="Voucher Created",
            message=f"Voucher {voucher.voucher_code} created for ${voucher.amount} {voucher.currency_type}",
            notification_type="voucher_created"
        )
    
    def _send_voucher_redeemed_notifications(self, voucher: Voucher):
        """Send notifications when voucher is redeemed."""
        
        # Notify creator
        self.notification_service.create_notification(
            user_id=voucher.creator_id,
            title="Voucher Redeemed",
            message=f"Your voucher {voucher.voucher_code} has been redeemed",
            notification_type="voucher_redeemed"
        )
        
        # Notify redeemer
        if voucher.redeemed_by:
            self.notification_service.create_notification(
                user_id=voucher.redeemed_by,
                title="Voucher Redeemed Successfully",
                message=f"You redeemed voucher {voucher.voucher_code} for ${voucher.amount} {voucher.currency_type}",
                notification_type="voucher_redeemed_success"
            )
    
    def _send_voucher_cancelled_notification(self, voucher: Voucher):
        """Send notification when voucher is cancelled."""
        
        self.notification_service.create_notification(
            user_id=voucher.creator_id,
            title="Voucher Cancelled",
            message=f"Voucher {voucher.voucher_code} has been cancelled",
            notification_type="voucher_cancelled"
        )
