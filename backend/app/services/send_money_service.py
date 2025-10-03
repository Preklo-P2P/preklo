"""
Send Money Service for Story 2.3
Handles enhanced send money functionality with confirmation flow and real-time updates
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models import User, Transaction, Balance
from ..services.aptos_service import aptos_service
from ..services.wallet_service import wallet_service
from ..services.auth_service import auth_service
from ..services.fee_service import fee_service
from ..schemas import SendMoneyRequest, SendMoneyConfirmation, SendMoneyResponse, TransactionStatusUpdate

logger = logging.getLogger("preklo.send_money_service")


class SendMoneyService:
    """Enhanced send money service with confirmation flow and real-time updates"""
    
    def __init__(self):
        self._pending_confirmations: Dict[str, Dict[str, Any]] = {}
        self._confirmation_timeout = timedelta(minutes=5)  # 5 minute timeout
    
    async def initiate_send_money(
        self,
        request: SendMoneyRequest,
        current_user: User,
        db: Session
    ) -> SendMoneyResponse:
        """
        Initiate send money process with validation and confirmation
        """
        try:
            # Validate recipient
            recipient_user = db.query(User).filter(
                User.username == request.recipient_username
            ).first()
            
            if not recipient_user:
                return SendMoneyResponse(
                    success=False,
                    message=f"User @{request.recipient_username} not found"
                )
            
            # Validate amount
            try:
                amount = Decimal(request.amount)
                if amount <= 0:
                    return SendMoneyResponse(
                        success=False,
                        message="Amount must be greater than 0"
                    )
            except (ValueError, TypeError):
                return SendMoneyResponse(
                    success=False,
                    message="Invalid amount format"
                )
            
            # Verify password
            if not auth_service.verify_password(request.password, current_user.hashed_password):
                return SendMoneyResponse(
                    success=False,
                    message="Invalid password"
                )
            
            # Check if user is custodial
            if not current_user.is_custodial or not current_user.encrypted_private_key:
                return SendMoneyResponse(
                    success=False,
                    message="This feature is only available for custodial wallet users"
                )
            
            # Get user balance
            user_balance = await aptos_service.get_account_balance(
                current_user.wallet_address,
                request.currency_type.upper()
            )
            
            if user_balance < amount:
                return SendMoneyResponse(
                    success=False,
                    message=f"Insufficient balance. Available: {user_balance} {request.currency_type.upper()}"
                )
            
            # Estimate gas fee
            gas_fee = await aptos_service.estimate_gas_fee(
                current_user.wallet_address,
                recipient_user.wallet_address,
                amount,
                request.currency_type.upper()
            )
            
            total_cost = amount + gas_fee
            
            # Check if user has enough for total cost
            if user_balance < total_cost:
                return SendMoneyResponse(
                    success=False,
                    message=f"Insufficient balance for amount + gas fee. Required: {total_cost} {request.currency_type.upper()}"
                )
            
            # Create confirmation
            transaction_id = str(uuid.uuid4())
            confirmation = SendMoneyConfirmation(
                transaction_id=transaction_id,
                recipient_username=request.recipient_username,
                recipient_address=recipient_user.wallet_address,
                amount=str(amount),
                currency_type=request.currency_type.upper(),
                gas_fee=str(gas_fee),
                total_cost=str(total_cost),
                description=request.description,
                expires_at=datetime.now(timezone.utc) + self._confirmation_timeout
            )
            
            # Store confirmation for later processing
            self._pending_confirmations[transaction_id] = {
                "confirmation": confirmation,
                "request": request,
                "current_user": current_user,
                "recipient_user": recipient_user,
                "created_at": datetime.now(timezone.utc)
            }
            
            logger.info(f"Send money confirmation created for transaction {transaction_id}")
            
            return SendMoneyResponse(
                success=True,
                message="Transaction confirmation created. Please confirm to proceed.",
                transaction_id=transaction_id,
                data=confirmation.model_dump()
            )
            
        except Exception as e:
            logger.error(f"Error initiating send money: {e}")
            return SendMoneyResponse(
                success=False,
                message="Failed to initiate transaction. Please try again."
            )
    
    async def confirm_send_money(
        self,
        transaction_id: str,
        db: Session
    ) -> SendMoneyResponse:
        """
        Confirm and execute the send money transaction
        """
        try:
            # Check if confirmation exists and is not expired
            if transaction_id not in self._pending_confirmations:
                return SendMoneyResponse(
                    success=False,
                    message="Transaction confirmation not found or expired"
                )
            
            confirmation_data = self._pending_confirmations[transaction_id]
            confirmation = confirmation_data["confirmation"]
            request = confirmation_data["request"]
            current_user = confirmation_data["current_user"]
            recipient_user = confirmation_data["recipient_user"]
            
            # Check if confirmation is expired
            if datetime.now(timezone.utc) > confirmation.expires_at:
                del self._pending_confirmations[transaction_id]
                return SendMoneyResponse(
                    success=False,
                    message="Transaction confirmation has expired"
                )
            
            # Get account for signing
            account = wallet_service.get_account_for_transaction(
                current_user.encrypted_private_key,
                request.password,
                str(current_user.id)
            )
            
            if not account:
                return SendMoneyResponse(
                    success=False,
                    message="Failed to decrypt wallet for transaction signing"
                )
            
            # Execute blockchain transaction
            amount = Decimal(confirmation.amount)
            
            if confirmation.currency_type == "APT":
                tx_hash = await aptos_service.transfer_apt(
                    account.private_key.hex(),
                    confirmation.recipient_address,
                    amount
                )
            elif confirmation.currency_type == "USDC":
                tx_hash = await aptos_service.transfer_usdc(
                    account.private_key.hex(),
                    confirmation.recipient_address,
                    amount
                )
            else:
                return SendMoneyResponse(
                    success=False,
                    message=f"Unsupported currency: {confirmation.currency_type}"
                )
            
            if not tx_hash:
                return SendMoneyResponse(
                    success=False,
                    message="Transaction failed to submit to blockchain"
                )
            
            # Create transaction record
            db_transaction = Transaction(
                transaction_hash=tx_hash,
                sender_id=current_user.id,
                recipient_id=recipient_user.id,
                sender_address=current_user.wallet_address,
                recipient_address=confirmation.recipient_address,
                amount=amount,
                currency_type=confirmation.currency_type,
                transaction_type="transfer",
                status="pending",  # Will be updated by monitoring
                description=confirmation.description,
                gas_fee=Decimal(confirmation.gas_fee) if confirmation.gas_fee else None
            )
            
            db.add(db_transaction)
            db.commit()
            db.refresh(db_transaction)
            
            # Start monitoring the transaction
            await aptos_service.monitor_transaction(tx_hash)
            
            # Clean up confirmation
            del self._pending_confirmations[transaction_id]
            
            logger.info(f"Send money transaction confirmed: {tx_hash}")
            
            return SendMoneyResponse(
                success=True,
                message=f"Successfully sent {amount} {confirmation.currency_type} to @{confirmation.recipient_username}",
                transaction_id=str(db_transaction.id),
                transaction_hash=tx_hash,
                status="pending",
                data={
                    "transaction_id": str(db_transaction.id),
                    "transaction_hash": tx_hash,
                    "amount": str(amount),
                    "currency_type": confirmation.currency_type,
                    "recipient_username": confirmation.recipient_username,
                    "status": "pending"
                }
            )
            
        except Exception as e:
            logger.error(f"Error confirming send money: {e}")
            return SendMoneyResponse(
                success=False,
                message="Failed to confirm transaction. Please try again."
            )
    
    async def get_transaction_status(
        self,
        transaction_id: str,
        db: Session
    ) -> Optional[TransactionStatusUpdate]:
        """
        Get real-time transaction status
        """
        try:
            transaction = db.query(Transaction).filter(
                Transaction.id == transaction_id
            ).first()
            
            if not transaction:
                return None
            
            # Get latest status from blockchain
            blockchain_status = await aptos_service.get_transaction_status(transaction.transaction_hash)
            
            if blockchain_status:
                # Update database if status changed
                if transaction.status != blockchain_status.get("status", transaction.status):
                    transaction.status = blockchain_status.get("status", transaction.status)
                    if blockchain_status.get("block_height"):
                        transaction.block_height = blockchain_status["block_height"]
                    if blockchain_status.get("gas_fee"):
                        transaction.gas_fee = Decimal(blockchain_status["gas_fee"])
                    
                    db.commit()
                    db.refresh(transaction)
            
            return TransactionStatusUpdate(
                transaction_id=str(transaction.id),
                transaction_hash=transaction.transaction_hash,
                status=transaction.status,
                block_height=transaction.block_height,
                gas_fee=str(transaction.gas_fee) if transaction.gas_fee else None,
                updated_at=transaction.updated_at or transaction.created_at
            )
            
        except Exception as e:
            logger.error(f"Error getting transaction status: {e}")
            return None
    
    def get_confirmation_details(self, transaction_id: str) -> Optional[SendMoneyConfirmation]:
        """
        Get confirmation details for a pending transaction
        """
        if transaction_id in self._pending_confirmations:
            confirmation_data = self._pending_confirmations[transaction_id]
            confirmation = confirmation_data["confirmation"]
            
            # Check if expired
            if datetime.now(timezone.utc) > confirmation.expires_at:
                del self._pending_confirmations[transaction_id]
                return None
            
            return confirmation
        
        return None
    
    def cleanup_expired_confirmations(self):
        """
        Clean up expired confirmations
        """
        current_time = datetime.now(timezone.utc)
        expired_ids = []
        
        for transaction_id, confirmation_data in self._pending_confirmations.items():
            if current_time > confirmation_data["confirmation"].expires_at:
                expired_ids.append(transaction_id)
        
        for transaction_id in expired_ids:
            del self._pending_confirmations[transaction_id]
            logger.info(f"Cleaned up expired confirmation: {transaction_id}")


# Global service instance
send_money_service = SendMoneyService()
