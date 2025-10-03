"""
Fee Service for Preklo - Handles transaction fee calculations and collections
"""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from ..config import settings
from ..models import Transaction, FeeCollection, FeeWithdrawal
from ..services.aptos_service import aptos_service
from ..utils.error_handlers import raise_bad_request


class FeeService:
    """Service for handling transaction fees and revenue collection"""
    
    def __init__(self):
        self.fee_config = {
            "p2p_domestic": settings.fee_p2p_domestic,
            "p2p_cross_border": settings.fee_p2p_cross_border,
            "card_present": settings.fee_card_present,
            "card_not_present": settings.fee_card_not_present,
            "merchant": settings.fee_merchant,
        }
        
        self.revenue_wallet = settings.revenue_wallet_address
        self.enable_fee_collection = settings.enable_fee_collection
    
    def calculate_fee(self, amount: Decimal, transaction_type: str) -> Tuple[Decimal, Decimal]:
        """
        Calculate fee amount and net amount for a transaction
        
        Args:
            amount: Transaction amount
            transaction_type: Type of transaction (p2p_domestic, card_present, etc.)
            
        Returns:
            Tuple of (fee_amount, net_amount)
        """
        if not self.enable_fee_collection:
            return Decimal("0"), amount
        
        # Get fee percentage in basis points
        fee_percentage = self.fee_config.get(transaction_type, 0)
        
        if fee_percentage == 0:
            return Decimal("0"), amount
        
        # Calculate fee (fee_percentage is in basis points, e.g., 25 = 0.25%)
        fee_amount = (amount * Decimal(fee_percentage)) / Decimal("10000")
        
        # Ensure minimum fee of 0.001 for very small transactions
        if fee_amount < Decimal("0.001") and amount > Decimal("0.001"):
            fee_amount = Decimal("0.001")
        
        net_amount = amount - fee_amount
        
        return fee_amount, net_amount
    
    def get_fee_percentage(self, transaction_type: str) -> int:
        """Get fee percentage for a transaction type"""
        return self.fee_config.get(transaction_type, 0)
    
    def determine_transaction_type(self, 
                                 transaction_type: str, 
                                 is_cross_border: bool = False,
                                 is_card_transaction: bool = False,
                                 is_merchant: bool = False) -> str:
        """
        Determine the appropriate fee category for a transaction
        
        Args:
            transaction_type: Original transaction type
            is_cross_border: Whether this is a cross-border transaction
            is_card_transaction: Whether this is a card transaction
            is_merchant: Whether this is a merchant transaction
            
        Returns:
            Fee category string
        """
        if is_merchant:
            return "merchant"
        elif is_card_transaction:
            # This would be determined by the card transaction context
            # For now, default to card_present
            return "card_present"
        elif transaction_type in ["transfer", "payment_request"]:
            return "p2p_cross_border" if is_cross_border else "p2p_domestic"
        else:
            return "p2p_domestic"
    
    async def collect_fee(self, 
                         db: Session,
                         transaction: Transaction,
                         fee_amount: Decimal,
                         transaction_type: str) -> Optional[str]:
        """
        Collect fee for a transaction
        
        Args:
            db: Database session
            transaction: Transaction object
            fee_amount: Amount of fee to collect
            transaction_type: Type of transaction for fee calculation
            
        Returns:
            Blockchain transaction hash if successful, None otherwise
        """
        if not self.enable_fee_collection or fee_amount <= 0:
            return None
        
        if not self.revenue_wallet:
            print("WARNING: Revenue wallet not configured, skipping fee collection")
            return None
        
        try:
            # Create fee collection record
            fee_collection = FeeCollection(
                transaction_id=transaction.id,
                currency_type=transaction.currency_type,
                amount=fee_amount,
                fee_percentage=Decimal(self.get_fee_percentage(transaction_type)),
                transaction_type=transaction_type,
                revenue_wallet_address=self.revenue_wallet,
                status="pending"
            )
            db.add(fee_collection)
            db.flush()  # Get the ID
            
            # Collect fee on blockchain
            if transaction.currency_type == "APT":
                tx_hash = await self._collect_apt_fee(
                    transaction.sender_address,
                    fee_amount
                )
            elif transaction.currency_type == "USDC":
                tx_hash = await self._collect_usdc_fee(
                    transaction.sender_address,
                    fee_amount
                )
            else:
                raise ValueError(f"Unsupported currency for fee collection: {transaction.currency_type}")
            
            if tx_hash:
                # Update fee collection record
                fee_collection.blockchain_tx_hash = tx_hash
                fee_collection.status = "collected"
                fee_collection.collected_at = datetime.utcnow()
                
                # Update transaction record
                transaction.fee_collected = True
                transaction.revenue_wallet_address = self.revenue_wallet
                
                db.commit()
                return tx_hash
            else:
                fee_collection.status = "failed"
                db.commit()
                return None
                
        except Exception as e:
            print(f"Error collecting fee: {e}")
            if 'fee_collection' in locals():
                fee_collection.status = "failed"
                db.commit()
            return None
    
    async def _collect_apt_fee(self, sender_address: str, fee_amount: Decimal) -> Optional[str]:
        """Collect APT fee from sender to revenue wallet"""
        try:
            # This would use the smart contract's fee collection mechanism
            # For now, we'll use a direct transfer approach
            if settings.revenue_wallet_private_key:
                tx_hash = await aptos_service.transfer_apt(
                    settings.revenue_wallet_private_key,
                    self.revenue_wallet,
                    fee_amount
                )
                return tx_hash
            else:
                print("WARNING: Revenue wallet private key not configured")
                return None
        except Exception as e:
            print(f"Error collecting APT fee: {e}")
            return None
    
    async def _collect_usdc_fee(self, sender_address: str, fee_amount: Decimal) -> Optional[str]:
        """Collect USDC fee from sender to revenue wallet"""
        try:
            # This would use the smart contract's fee collection mechanism
            # For now, we'll use a direct transfer approach
            if settings.revenue_wallet_private_key:
                tx_hash = await aptos_service.transfer_usdc(
                    settings.revenue_wallet_private_key,
                    self.revenue_wallet,
                    fee_amount
                )
                return tx_hash
            else:
                print("WARNING: Revenue wallet private key not configured")
                return None
        except Exception as e:
            print(f"Error collecting USDC fee: {e}")
            return None
    
    async def withdraw_collected_fees(self,
                                    db: Session,
                                    currency_type: str,
                                    amount: Decimal,
                                    destination_address: str,
                                    withdrawal_reason: str = "revenue_withdrawal") -> Optional[str]:
        """
        Withdraw collected fees to a destination address
        
        Args:
            db: Database session
            currency_type: Currency to withdraw (APT, USDC)
            amount: Amount to withdraw
            destination_address: Destination wallet address
            withdrawal_reason: Reason for withdrawal
            
        Returns:
            Blockchain transaction hash if successful, None otherwise
        """
        try:
            # Create withdrawal record
            withdrawal = FeeWithdrawal(
                currency_type=currency_type,
                amount=amount,
                destination_address=destination_address,
                withdrawal_reason=withdrawal_reason,
                status="pending"
            )
            db.add(withdrawal)
            db.flush()
            
            # Execute withdrawal on blockchain
            if currency_type == "APT":
                tx_hash = await aptos_service.transfer_apt(
                    settings.revenue_wallet_private_key,
                    destination_address,
                    amount
                )
            elif currency_type == "USDC":
                tx_hash = await aptos_service.transfer_usdc(
                    settings.revenue_wallet_private_key,
                    destination_address,
                    amount
                )
            else:
                raise ValueError(f"Unsupported currency for withdrawal: {currency_type}")
            
            if tx_hash:
                withdrawal.blockchain_tx_hash = tx_hash
                withdrawal.status = "completed"
                withdrawal.processed_at = datetime.utcnow()
                db.commit()
                return tx_hash
            else:
                withdrawal.status = "failed"
                db.commit()
                return None
                
        except Exception as e:
            print(f"Error withdrawing fees: {e}")
            if 'withdrawal' in locals():
                withdrawal.status = "failed"
                db.commit()
            return None
    
    def get_fee_statistics(self, db: Session, days: int = 30) -> Dict[str, Any]:
        """
        Get fee collection statistics
        
        Args:
            db: Database session
            days: Number of days to look back
            
        Returns:
            Dictionary with fee statistics
        """
        from datetime import datetime, timedelta
        from sqlalchemy import func, and_
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get total fees collected
        total_fees = db.query(
            func.sum(FeeCollection.amount).label('total_amount'),
            FeeCollection.currency_type
        ).filter(
            and_(
                FeeCollection.status == "collected",
                FeeCollection.created_at >= start_date
            )
        ).group_by(FeeCollection.currency_type).all()
        
        # Get fees by transaction type
        fees_by_type = db.query(
            func.sum(FeeCollection.amount).label('total_amount'),
            FeeCollection.transaction_type
        ).filter(
            and_(
                FeeCollection.status == "collected",
                FeeCollection.created_at >= start_date
            )
        ).group_by(FeeCollection.transaction_type).all()
        
        # Get daily fee collection
        daily_fees = db.query(
            func.date(FeeCollection.created_at).label('date'),
            func.sum(FeeCollection.amount).label('daily_amount'),
            FeeCollection.currency_type
        ).filter(
            and_(
                FeeCollection.status == "collected",
                FeeCollection.created_at >= start_date
            )
        ).group_by(
            func.date(FeeCollection.created_at),
            FeeCollection.currency_type
        ).all()
        
        return {
            "total_fees_by_currency": {row.currency_type: float(row.total_amount) for row in total_fees},
            "fees_by_transaction_type": {row.transaction_type: float(row.total_amount) for row in fees_by_type},
            "daily_fees": [
                {
                    "date": row.date.isoformat(),
                    "currency": row.currency_type,
                    "amount": float(row.daily_amount)
                }
                for row in daily_fees
            ],
            "period_days": days
        }


# Create global instance
fee_service = FeeService()
