"""
Receive Money Service for Story 2.4
Handles automatic detection and processing of incoming transactions
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from ..models import User, Transaction, Balance, Notification
from ..services.aptos_service import aptos_service
from ..schemas import ApiResponse

logger = logging.getLogger("preklo.receive_money_service")


class ReceiveMoneyService:
    """Service for handling incoming money transactions"""
    
    def __init__(self):
        self._monitoring_active = False
        self._monitoring_interval = 30  # seconds
        self._last_processed_block = None
        self._processed_transactions = set()
    
    async def start_transaction_monitoring(self, db: Session):
        """
        Start monitoring for incoming transactions
        """
        if self._monitoring_active:
            logger.info("Transaction monitoring already active")
            return
        
        self._monitoring_active = True
        logger.info("Starting transaction monitoring for incoming payments")
        
        # Start monitoring in background
        asyncio.create_task(self._monitor_incoming_transactions(db))
    
    async def stop_transaction_monitoring(self):
        """
        Stop monitoring for incoming transactions
        """
        self._monitoring_active = False
        logger.info("Stopped transaction monitoring")
    
    async def _monitor_incoming_transactions(self, db: Session):
        """
        Background task to monitor for incoming transactions
        """
        while self._monitoring_active:
            try:
                await self._process_incoming_transactions(db)
                await asyncio.sleep(self._monitoring_interval)
            except Exception as e:
                logger.error(f"Error in transaction monitoring: {e}")
                await asyncio.sleep(self._monitoring_interval)
    
    async def _process_incoming_transactions(self, db: Session):
        """
        Process incoming transactions for all users
        """
        try:
            # Get all users with wallet addresses
            users = db.query(User).filter(
                User.wallet_address.isnot(None),
                User.is_active == True
            ).all()
            
            for user in users:
                await self._check_user_incoming_transactions(user, db)
                
        except Exception as e:
            logger.error(f"Error processing incoming transactions: {e}")
    
    async def _check_user_incoming_transactions(self, user: User, db: Session):
        """
        Check for incoming transactions for a specific user
        """
        try:
            # Get recent transactions for the user's wallet address
            recent_transactions = await aptos_service.get_account_transactions(
                user.wallet_address,
                limit=10
            )
            
            if not recent_transactions:
                return
            
            for tx_data in recent_transactions:
                await self._process_incoming_transaction(tx_data, user, db)
                
        except Exception as e:
            logger.error(f"Error checking transactions for user {user.username}: {e}")
    
    async def _process_incoming_transaction(self, tx_data: Dict[str, Any], user: User, db: Session):
        """
        Process a single incoming transaction
        """
        try:
            tx_hash = tx_data.get("hash")
            if not tx_hash or tx_hash in self._processed_transactions:
                return
            
            # Check if transaction is already in database
            existing_tx = db.query(Transaction).filter(
                Transaction.transaction_hash == tx_hash
            ).first()
            
            if existing_tx:
                self._processed_transactions.add(tx_hash)
                return
            
            # Check if this is an incoming transaction (user is recipient)
            if not self._is_incoming_transaction(tx_data, user.wallet_address):
                return
            
            # Extract transaction details
            sender_address = self._extract_sender_address(tx_data)
            amount = self._extract_amount(tx_data)
            currency_type = self._extract_currency_type(tx_data)
            
            if not sender_address or not amount or not currency_type:
                logger.warning(f"Could not extract transaction details for {tx_hash}")
                return
            
            # Find sender user if they exist in our system
            sender_user = db.query(User).filter(
                User.wallet_address == sender_address
            ).first()
            
            # Create transaction record
            db_transaction = Transaction(
                transaction_hash=tx_hash,
                sender_id=sender_user.id if sender_user else None,
                recipient_id=user.id,
                sender_address=sender_address,
                recipient_address=user.wallet_address,
                amount=amount,
                currency_type=currency_type,
                transaction_type="transfer",
                status="confirmed",  # Assume confirmed if we can see it
                description=f"Incoming payment from {sender_address[:8]}...{sender_address[-8:]}"
            )
            
            db.add(db_transaction)
            db.flush()  # Get the ID
            
            # Update user balance
            await self._update_user_balance(user, amount, currency_type, db)
            
            # Create notification
            await self._create_received_payment_notification(
                user, sender_user, amount, currency_type, db_transaction.id, db
            )
            
            db.commit()
            self._processed_transactions.add(tx_hash)
            
            logger.info(f"Processed incoming transaction {tx_hash} for user {user.username}")
            
        except Exception as e:
            logger.error(f"Error processing transaction {tx_data.get('hash', 'unknown')}: {e}")
            db.rollback()
    
    def _is_incoming_transaction(self, tx_data: Dict[str, Any], user_address: str) -> bool:
        """
        Check if transaction is incoming to the user
        """
        # Check if user's address appears in the transaction outputs
        changes = tx_data.get("changes", [])
        for change in changes:
            if change.get("address") == user_address:
                # Check if it's a positive change (incoming)
                data = change.get("data", {})
                if data.get("type") == "0x1::coin::CoinStore":
                    coin_data = data.get("data", {})
                    if coin_data.get("deposit") or coin_data.get("withdraw"):
                        return True
        
        return False
    
    def _extract_sender_address(self, tx_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract sender address from transaction data
        """
        # Look for the sender in transaction changes
        changes = tx_data.get("changes", [])
        for change in changes:
            data = change.get("data", {})
            if data.get("type") == "0x1::coin::CoinStore":
                coin_data = data.get("data", {})
                if coin_data.get("withdraw"):  # This indicates money leaving the account
                    return change.get("address")
        
        return None
    
    def _extract_amount(self, tx_data: Dict[str, Any]) -> Optional[Decimal]:
        """
        Extract transaction amount
        """
        changes = tx_data.get("changes", [])
        for change in changes:
            data = change.get("data", {})
            if data.get("type") == "0x1::coin::CoinStore":
                coin_data = data.get("data", {})
                deposit = coin_data.get("deposit")
                if deposit:
                    # Convert from smallest unit to main unit
                    return Decimal(deposit) / Decimal(10**8)  # APT has 8 decimals
        
        return None
    
    def _extract_currency_type(self, tx_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract currency type from transaction
        """
        changes = tx_data.get("changes", [])
        for change in changes:
            data = change.get("data", {})
            if data.get("type") == "0x1::coin::CoinStore":
                # Check the coin type
                coin_type = data.get("coin_type", "")
                if "aptos_coin::AptosCoin" in coin_type:
                    return "APT"
                elif "usdc" in coin_type.lower():
                    return "USDC"
        
        return "APT"  # Default to APT
    
    async def _update_user_balance(self, user: User, amount: Decimal, currency_type: str, db: Session):
        """
        Update user balance after receiving payment
        """
        try:
            # Get or create balance record
            balance = db.query(Balance).filter(
                Balance.user_id == user.id,
                Balance.currency_type == currency_type
            ).first()
            
            if balance:
                balance.balance += amount
            else:
                balance = Balance(
                    user_id=user.id,
                    currency_type=currency_type,
                    balance=amount
                )
                db.add(balance)
            
            logger.info(f"Updated balance for {user.username}: +{amount} {currency_type}")
            
        except Exception as e:
            logger.error(f"Error updating balance for {user.username}: {e}")
            raise
    
    async def _create_received_payment_notification(
        self, 
        recipient: User, 
        sender: Optional[User], 
        amount: Decimal, 
        currency_type: str, 
        transaction_id: str,
        db: Session
    ):
        """
        Create notification for received payment
        """
        try:
            sender_name = sender.username if sender else "Unknown User"
            sender_address = sender.wallet_address if sender else "Unknown Address"
            
            notification = Notification(
                user_id=recipient.id,
                type="payment_received",
                title="Payment Received",
                message=f"You received {amount} {currency_type} from {sender_name}",
                data={
                    "transaction_id": str(transaction_id),
                    "amount": str(amount),
                    "currency_type": currency_type,
                    "sender_username": sender_name,
                    "sender_address": sender_address
                }
            )
            
            db.add(notification)
            logger.info(f"Created notification for {recipient.username} about received payment")
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            # Don't raise - notification failure shouldn't break transaction processing
    
    async def get_received_transactions(
        self, 
        user: User, 
        limit: int = 25, 
        offset: int = 0,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Get received transactions for a user
        """
        try:
            # Query received transactions
            transactions = db.query(Transaction).filter(
                Transaction.recipient_id == user.id,
                Transaction.transaction_type == "transfer"
            ).order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
            
            # Format response
            result = []
            for tx in transactions:
                sender_user = db.query(User).filter(User.id == tx.sender_id).first()
                
                result.append({
                    "id": str(tx.id),
                    "transaction_hash": tx.transaction_hash,
                    "amount": str(tx.amount),
                    "currency_type": tx.currency_type,
                    "status": tx.status,
                    "description": tx.description,
                    "created_at": tx.created_at.isoformat(),
                    "sender": {
                        "username": sender_user.username if sender_user else None,
                        "address": tx.sender_address
                    } if sender_user else {
                        "address": tx.sender_address
                    }
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting received transactions for {user.username}: {e}")
            return []
    
    async def get_received_transaction_details(
        self, 
        transaction_id: str, 
        user: User, 
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Get details of a specific received transaction
        """
        try:
            transaction = db.query(Transaction).filter(
                Transaction.id == transaction_id,
                Transaction.recipient_id == user.id
            ).first()
            
            if not transaction:
                return None
            
            sender_user = db.query(User).filter(User.id == transaction.sender_id).first()
            
            return {
                "id": str(transaction.id),
                "transaction_hash": transaction.transaction_hash,
                "amount": str(transaction.amount),
                "currency_type": transaction.currency_type,
                "status": transaction.status,
                "description": transaction.description,
                "gas_fee": str(transaction.gas_fee) if transaction.gas_fee else None,
                "block_height": transaction.block_height,
                "created_at": transaction.created_at.isoformat(),
                "updated_at": transaction.updated_at.isoformat() if transaction.updated_at else None,
                "sender": {
                    "username": sender_user.username if sender_user else None,
                    "address": transaction.sender_address,
                    "full_name": sender_user.full_name if sender_user else None
                } if sender_user else {
                    "address": transaction.sender_address
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting transaction details: {e}")
            return None
    
    async def sync_user_transactions(self, user: User, db: Session) -> ApiResponse:
        """
        Manually sync transactions for a user
        """
        try:
            await self._check_user_incoming_transactions(user, db)
            
            return ApiResponse(
                success=True,
                message="Transactions synced successfully"
            )
            
        except Exception as e:
            logger.error(f"Error syncing transactions for {user.username}: {e}")
            return ApiResponse(
                success=False,
                message="Failed to sync transactions"
            )
    
    async def get_user_balance(self, user: User, currency_type: str = "APT", db: Session = None) -> Decimal:
        """
        Get user's current balance for a specific currency
        """
        try:
            balance = db.query(Balance).filter(
                Balance.user_id == user.id,
                Balance.currency_type == currency_type.upper()
            ).first()
            
            if balance:
                return balance.balance
            else:
                # Get balance from blockchain
                blockchain_balance = await aptos_service.get_account_balance(
                    user.wallet_address,
                    currency_type.upper()
                )
                
                # Create balance record
                new_balance = Balance(
                    user_id=user.id,
                    currency_type=currency_type.upper(),
                    balance=blockchain_balance
                )
                db.add(new_balance)
                db.commit()
                
                return blockchain_balance
                
        except Exception as e:
            logger.error(f"Error getting balance for {user.username}: {e}")
            return Decimal("0")


# Global service instance
receive_money_service = ReceiveMoneyService()
