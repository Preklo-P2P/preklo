"""
Transaction Limits and Controls Service for Story 2.6
Handles transaction limits, spending controls, approvals, and emergency blocking
"""

import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models import (
    User, Transaction, TransactionLimit, SpendingControl, 
    TransactionApproval, EmergencyBlock, SpendingAlert,
    FamilyAccount, BusinessAccount, Notification
)
from ..schemas import ApiResponse

logger = logging.getLogger("preklo.transaction_limits_service")


class TransactionLimitsService:
    """Service for managing transaction limits and controls"""
    
    def __init__(self):
        self._high_value_threshold = Decimal("1000.0")  # Default high-value threshold
        self._approval_timeout = timedelta(hours=24)  # 24 hours for approval timeout
    
    async def check_transaction_limits(
        self, 
        user: User, 
        amount: Decimal, 
        currency_type: str, 
        db: Session
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Check if transaction violates any limits
        Returns: (is_allowed, error_message, approval_required)
        """
        try:
            # Check daily limits
            daily_check = await self._check_daily_limit(user, amount, currency_type, db)
            if not daily_check[0]:
                return False, daily_check[1], None
            
            # Check weekly limits
            weekly_check = await self._check_weekly_limit(user, amount, currency_type, db)
            if not weekly_check[0]:
                return False, weekly_check[1], None
            
            # Check monthly limits
            monthly_check = await self._check_monthly_limit(user, amount, currency_type, db)
            if not monthly_check[0]:
                return False, monthly_check[1], None
            
            # Check spending controls
            spending_check = await self._check_spending_controls(user, amount, currency_type, db)
            if not spending_check[0]:
                return False, spending_check[1], None
            
            # Check emergency blocks
            emergency_check = await self._check_emergency_blocks(user, db)
            if not emergency_check[0]:
                return False, emergency_check[1], None
            
            # Check if approval is required for high-value transactions
            if amount >= self._high_value_threshold:
                approval_data = {
                    "approval_required": True,
                    "approval_type": "high_value",
                    "amount": str(amount),
                    "currency_type": currency_type
                }
                return True, None, approval_data
            
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error checking transaction limits: {e}")
            return False, "Error validating transaction limits", None
    
    async def _check_daily_limit(
        self, 
        user: User, 
        amount: Decimal, 
        currency_type: str, 
        db: Session
    ) -> Tuple[bool, Optional[str]]:
        """Check daily transaction limit"""
        try:
            today = datetime.now(timezone.utc).date()
            start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_day = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            # Get daily limit
            daily_limit = db.query(TransactionLimit).filter(
                and_(
                    TransactionLimit.user_id == user.id,
                    TransactionLimit.limit_type == "daily",
                    TransactionLimit.currency_type == currency_type.upper(),
                    TransactionLimit.is_active == True,
                    TransactionLimit.period_start <= start_of_day,
                    TransactionLimit.period_end >= end_of_day
                )
            ).first()
            
            if not daily_limit:
                return True, None  # No daily limit set
            
            # Calculate current usage for today
            current_usage = await self._calculate_period_usage(
                user, currency_type, start_of_day, end_of_day, db
            )
            
            if current_usage + amount > daily_limit.limit_amount:
                return False, f"Transaction would exceed daily limit of {daily_limit.limit_amount} {currency_type}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking daily limit: {e}")
            return False, "Error checking daily limit"
    
    async def _check_weekly_limit(
        self, 
        user: User, 
        amount: Decimal, 
        currency_type: str, 
        db: Session
    ) -> Tuple[bool, Optional[str]]:
        """Check weekly transaction limit"""
        try:
            today = datetime.now(timezone.utc).date()
            start_of_week = today - timedelta(days=today.weekday())
            start_of_week_dt = datetime.combine(start_of_week, datetime.min.time()).replace(tzinfo=timezone.utc)
            end_of_week = start_of_week + timedelta(days=6)
            end_of_week_dt = datetime.combine(end_of_week, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            # Get weekly limit
            weekly_limit = db.query(TransactionLimit).filter(
                and_(
                    TransactionLimit.user_id == user.id,
                    TransactionLimit.limit_type == "weekly",
                    TransactionLimit.currency_type == currency_type.upper(),
                    TransactionLimit.is_active == True,
                    TransactionLimit.period_start <= start_of_week_dt,
                    TransactionLimit.period_end >= end_of_week_dt
                )
            ).first()
            
            if not weekly_limit:
                return True, None  # No weekly limit set
            
            # Calculate current usage for this week
            current_usage = await self._calculate_period_usage(
                user, currency_type, start_of_week_dt, end_of_week_dt, db
            )
            
            if current_usage + amount > weekly_limit.limit_amount:
                return False, f"Transaction would exceed weekly limit of {weekly_limit.limit_amount} {currency_type}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking weekly limit: {e}")
            return False, "Error checking weekly limit"
    
    async def _check_monthly_limit(
        self, 
        user: User, 
        amount: Decimal, 
        currency_type: str, 
        db: Session
    ) -> Tuple[bool, Optional[str]]:
        """Check monthly transaction limit"""
        try:
            today = datetime.now(timezone.utc).date()
            start_of_month = today.replace(day=1)
            start_of_month_dt = datetime.combine(start_of_month, datetime.min.time()).replace(tzinfo=timezone.utc)
            
            # Calculate end of month
            if today.month == 12:
                end_of_month = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                end_of_month = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
            end_of_month_dt = datetime.combine(end_of_month, datetime.max.time()).replace(tzinfo=timezone.utc)
            
            # Get monthly limit
            monthly_limit = db.query(TransactionLimit).filter(
                and_(
                    TransactionLimit.user_id == user.id,
                    TransactionLimit.limit_type == "monthly",
                    TransactionLimit.currency_type == currency_type.upper(),
                    TransactionLimit.is_active == True,
                    TransactionLimit.period_start <= start_of_month_dt,
                    TransactionLimit.period_end >= end_of_month_dt
                )
            ).first()
            
            if not monthly_limit:
                return True, None  # No monthly limit set
            
            # Calculate current usage for this month
            current_usage = await self._calculate_period_usage(
                user, currency_type, start_of_month_dt, end_of_month_dt, db
            )
            
            if current_usage + amount > monthly_limit.limit_amount:
                return False, f"Transaction would exceed monthly limit of {monthly_limit.limit_amount} {currency_type}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking monthly limit: {e}")
            return False, "Error checking monthly limit"
    
    async def _calculate_period_usage(
        self, 
        user: User, 
        currency_type: str, 
        start_time: datetime, 
        end_time: datetime, 
        db: Session
    ) -> Decimal:
        """Calculate transaction usage for a specific period"""
        try:
            # Sum all sent transactions in the period
            usage = db.query(func.sum(Transaction.amount)).filter(
                and_(
                    Transaction.sender_id == user.id,
                    Transaction.currency_type == currency_type.upper(),
                    Transaction.status == "confirmed",
                    Transaction.created_at >= start_time,
                    Transaction.created_at <= end_time
                )
            ).scalar()
            
            return Decimal(str(usage or 0))
            
        except Exception as e:
            logger.error(f"Error calculating period usage: {e}")
            return Decimal("0")
    
    async def _check_spending_controls(
        self, 
        user: User, 
        amount: Decimal, 
        currency_type: str, 
        db: Session
    ) -> Tuple[bool, Optional[str]]:
        """Check spending controls"""
        try:
            # Get active spending controls
            controls = db.query(SpendingControl).filter(
                and_(
                    SpendingControl.user_id == user.id,
                    SpendingControl.currency_type == currency_type.upper(),
                    SpendingControl.is_active == True
                )
            ).all()
            
            for control in controls:
                if control.control_type == "max_amount" and control.max_amount:
                    if amount > control.max_amount:
                        return False, f"Transaction amount {amount} exceeds maximum allowed amount {control.max_amount}"
                
                # Add other control types as needed
                # - merchant_category
                # - geographic
                # - time_based
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking spending controls: {e}")
            return False, "Error checking spending controls"
    
    async def _check_emergency_blocks(
        self, 
        user: User, 
        db: Session
    ) -> Tuple[bool, Optional[str]]:
        """Check for active emergency blocks"""
        try:
            active_blocks = db.query(EmergencyBlock).filter(
                and_(
                    EmergencyBlock.user_id == user.id,
                    EmergencyBlock.is_active == True
                )
            ).all()
            
            if active_blocks:
                block_reasons = [block.reason for block in active_blocks]
                return False, f"Account is blocked: {', '.join(block_reasons)}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error checking emergency blocks: {e}")
            return False, "Error checking emergency blocks"
    
    async def create_transaction_approval(
        self,
        user: User,
        amount: Decimal,
        currency_type: str,
        approval_type: str,
        description: Optional[str],
        db: Session
    ) -> TransactionApproval:
        """Create a transaction approval request"""
        try:
            expires_at = datetime.now(timezone.utc) + self._approval_timeout
            
            approval = TransactionApproval(
                user_id=user.id,
                approval_type=approval_type,
                amount=amount,
                currency_type=currency_type.upper(),
                description=description,
                status="pending",
                expires_at=expires_at
            )
            
            db.add(approval)
            db.commit()
            db.refresh(approval)
            
            # Create notification
            await self._create_approval_notification(user, approval, db)
            
            logger.info(f"Created transaction approval {approval.id} for user {user.username}")
            return approval
            
        except Exception as e:
            logger.error(f"Error creating transaction approval: {e}")
            db.rollback()
            raise
    
    async def _create_approval_notification(
        self, 
        user: User, 
        approval: TransactionApproval, 
        db: Session
    ):
        """Create notification for transaction approval"""
        try:
            notification = Notification(
                user_id=user.id,
                type="transaction_approval",
                title="Transaction Approval Required",
                message=f"Transaction of {approval.amount} {approval.currency_type} requires approval",
                data={
                    "approval_id": str(approval.id),
                    "amount": str(approval.amount),
                    "currency_type": approval.currency_type,
                    "approval_type": approval.approval_type,
                    "expires_at": approval.expires_at.isoformat()
                }
            )
            
            db.add(notification)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error creating approval notification: {e}")
    
    async def approve_transaction(
        self,
        approval_id: str,
        approver_user: User,
        approval_method: str,
        db: Session
    ) -> ApiResponse:
        """Approve a pending transaction"""
        try:
            approval = db.query(TransactionApproval).filter(
                and_(
                    TransactionApproval.id == approval_id,
                    TransactionApproval.status == "pending"
                )
            ).first()
            
            if not approval:
                return ApiResponse(
                    success=False,
                    message="Approval not found or already processed"
                )
            
            if approval.expires_at < datetime.now(timezone.utc):
                approval.status = "expired"
                db.commit()
                return ApiResponse(
                    success=False,
                    message="Approval has expired"
                )
            
            # Update approval
            approval.status = "approved"
            approval.approved_by = approver_user.id
            approval.approved_at = datetime.now(timezone.utc)
            approval.approval_method = approval_method
            
            db.commit()
            
            # Create notification for original user
            await self._create_approval_result_notification(approval, "approved", db)
            
            logger.info(f"Transaction approval {approval_id} approved by {approver_user.username}")
            
            return ApiResponse(
                success=True,
                message="Transaction approved successfully"
            )
            
        except Exception as e:
            logger.error(f"Error approving transaction: {e}")
            db.rollback()
            return ApiResponse(
                success=False,
                message="Failed to approve transaction"
            )
    
    async def reject_transaction(
        self,
        approval_id: str,
        approver_user: User,
        reason: str,
        db: Session
    ) -> ApiResponse:
        """Reject a pending transaction"""
        try:
            approval = db.query(TransactionApproval).filter(
                and_(
                    TransactionApproval.id == approval_id,
                    TransactionApproval.status == "pending"
                )
            ).first()
            
            if not approval:
                return ApiResponse(
                    success=False,
                    message="Approval not found or already processed"
                )
            
            # Update approval
            approval.status = "rejected"
            approval.approved_by = approver_user.id
            approval.approved_at = datetime.now(timezone.utc)
            approval.description = f"{approval.description or ''} - Rejected: {reason}"
            
            db.commit()
            
            # Create notification for original user
            await self._create_approval_result_notification(approval, "rejected", db)
            
            logger.info(f"Transaction approval {approval_id} rejected by {approver_user.username}")
            
            return ApiResponse(
                success=True,
                message="Transaction rejected successfully"
            )
            
        except Exception as e:
            logger.error(f"Error rejecting transaction: {e}")
            db.rollback()
            return ApiResponse(
                success=False,
                message="Failed to reject transaction"
            )
    
    async def _create_approval_result_notification(
        self, 
        approval: TransactionApproval, 
        result: str, 
        db: Session
    ):
        """Create notification for approval result"""
        try:
            notification = Notification(
                user_id=approval.user_id,
                type="transaction_approval_result",
                title=f"Transaction {result.title()}",
                message=f"Your transaction of {approval.amount} {approval.currency_type} has been {result}",
                data={
                    "approval_id": str(approval.id),
                    "amount": str(approval.amount),
                    "currency_type": approval.currency_type,
                    "result": result,
                    "approved_at": approval.approved_at.isoformat() if approval.approved_at else None
                }
            )
            
            db.add(notification)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error creating approval result notification: {e}")
    
    async def create_emergency_block(
        self,
        user: User,
        block_type: str,
        reason: str,
        description: Optional[str],
        blocked_by: Optional[User],
        db: Session
    ) -> ApiResponse:
        """Create an emergency block"""
        try:
            emergency_block = EmergencyBlock(
                user_id=user.id,
                block_type=block_type,
                reason=reason,
                description=description,
                blocked_by=blocked_by.id if blocked_by else None
            )
            
            db.add(emergency_block)
            db.commit()
            
            # Create notification
            await self._create_emergency_block_notification(user, emergency_block, db)
            
            logger.info(f"Emergency block created for user {user.username}: {reason}")
            
            return ApiResponse(
                success=True,
                message="Emergency block created successfully"
            )
            
        except Exception as e:
            logger.error(f"Error creating emergency block: {e}")
            db.rollback()
            return ApiResponse(
                success=False,
                message="Failed to create emergency block"
            )
    
    async def _create_emergency_block_notification(
        self, 
        user: User, 
        emergency_block: EmergencyBlock, 
        db: Session
    ):
        """Create notification for emergency block"""
        try:
            notification = Notification(
                user_id=user.id,
                type="emergency_block",
                title="Account Blocked",
                message=f"Your account has been blocked: {emergency_block.reason}",
                data={
                    "block_id": str(emergency_block.id),
                    "block_type": emergency_block.block_type,
                    "reason": emergency_block.reason,
                    "blocked_at": emergency_block.created_at.isoformat()
                }
            )
            
            db.add(notification)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error creating emergency block notification: {e}")
    
    async def remove_emergency_block(
        self,
        block_id: str,
        unblocked_by: User,
        db: Session
    ) -> ApiResponse:
        """Remove an emergency block"""
        try:
            emergency_block = db.query(EmergencyBlock).filter(
                and_(
                    EmergencyBlock.id == block_id,
                    EmergencyBlock.is_active == True
                )
            ).first()
            
            if not emergency_block:
                return ApiResponse(
                    success=False,
                    message="Emergency block not found or already removed"
                )
            
            # Update block
            emergency_block.is_active = False
            emergency_block.unblocked_by = unblocked_by.id
            emergency_block.unblocked_at = datetime.now(timezone.utc)
            
            db.commit()
            
            # Create notification
            await self._create_emergency_unblock_notification(emergency_block, db)
            
            logger.info(f"Emergency block {block_id} removed by {unblocked_by.username}")
            
            return ApiResponse(
                success=True,
                message="Emergency block removed successfully"
            )
            
        except Exception as e:
            logger.error(f"Error removing emergency block: {e}")
            db.rollback()
            return ApiResponse(
                success=False,
                message="Failed to remove emergency block"
            )
    
    async def _create_emergency_unblock_notification(
        self, 
        emergency_block: EmergencyBlock, 
        db: Session
    ):
        """Create notification for emergency unblock"""
        try:
            notification = Notification(
                user_id=emergency_block.user_id,
                type="emergency_unblock",
                title="Account Unblocked",
                message="Your account has been unblocked and is now active",
                data={
                    "block_id": str(emergency_block.id),
                    "unblocked_at": emergency_block.unblocked_at.isoformat()
                }
            )
            
            db.add(notification)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error creating emergency unblock notification: {e}")


# Global service instance
transaction_limits_service = TransactionLimitsService()
