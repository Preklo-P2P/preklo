"""
Sandbox Transaction Service
Handles transaction processing in sandbox mode without blockchain calls.
"""
from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid

from ..models.sandbox import TestAccount
from ..services.test_account_service import test_account_service


class SandboxTransactionService:
    """
    Service for processing transactions in sandbox mode.
    
    Sandbox transactions:
    - Don't make blockchain calls
    - Update test account balances directly
    - Create transaction records in sandbox schema
    - Validate that all accounts are test accounts
    """
    
    def validate_test_accounts_for_transaction(
        self,
        db: Session,
        sender_id: str,
        recipient_id: str,
        sandbox_user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that both sender and recipient are test accounts.
        
        Args:
            db: Database session
            sender_id: UUID of sender account
            recipient_id: UUID of recipient account
            sandbox_user_id: UUID of sandbox user
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Validate sender is a test account
        sender_account = test_account_service.get_test_account(
            db=db,
            account_id=sender_id,
            sandbox_user_id=sandbox_user_id
        )
        
        if not sender_account:
            return False, "Sender must be a test account. Sandbox transactions can only use test accounts."
        
        # Validate recipient is a test account
        recipient_account = test_account_service.get_test_account(
            db=db,
            account_id=recipient_id,
            sandbox_user_id=sandbox_user_id
        )
        
        if not recipient_account:
            return False, "Recipient must be a test account. Sandbox transactions can only use test accounts."
        
        return True, None
    
    def process_sandbox_transfer(
        self,
        db: Session,
        sender_account_id: str,
        recipient_account_id: str,
        amount: Decimal,
        currency_type: str,
        sandbox_user_id: str,
        description: Optional[str] = None
    ) -> dict:
        """
        Process a transfer transaction in sandbox mode.
        
        This method:
        - Validates test accounts
        - Updates balances directly (no blockchain)
        - Creates transaction record in sandbox schema
        - Returns transaction details
        
        Args:
            db: Database session
            sender_account_id: UUID of sender test account
            recipient_account_id: UUID of recipient test account
            amount: Transfer amount
            currency_type: Currency type (USDC, APT)
            sandbox_user_id: UUID of sandbox user
            description: Optional transaction description
            
        Returns:
            dict: Transaction details including transaction_hash
        """
        # Validate test accounts
        is_valid, error_msg = self.validate_test_accounts_for_transaction(
            db=db,
            sender_id=sender_account_id,
            recipient_id=recipient_account_id,
            sandbox_user_id=sandbox_user_id
        )
        
        if not is_valid:
            raise ValueError(error_msg)
        
        # Get sender and recipient accounts
        sender_account = test_account_service.get_test_account(
            db=db,
            account_id=sender_account_id,
            sandbox_user_id=sandbox_user_id
        )
        recipient_account = test_account_service.get_test_account(
            db=db,
            account_id=recipient_account_id,
            sandbox_user_id=sandbox_user_id
        )
        
        if not sender_account or not recipient_account:
            raise ValueError("Test accounts not found")
        
        # Check sender balance
        if currency_type == "USDC":
            if sender_account.usdc_balance < amount:
                raise ValueError("Insufficient USDC balance")
        elif currency_type == "APT":
            if sender_account.apt_balance < amount:
                raise ValueError("Insufficient APT balance")
        else:
            raise ValueError(f"Unsupported currency type: {currency_type}")
        
        # Update balances
        if currency_type == "USDC":
            sender_account.usdc_balance -= amount
            recipient_account.usdc_balance += amount
        else:  # APT
            sender_account.apt_balance -= amount
            recipient_account.apt_balance += amount
        
        # Generate mock transaction hash for sandbox
        transaction_hash = f"0x{'sandbox_' + str(uuid.uuid4()).replace('-', '')[:56]}"
        
        # Create transaction record (would be in sandbox.transactions if we create that model)
        # For now, we'll return the transaction details
        transaction_data = {
            "id": str(uuid.uuid4()),
            "transaction_hash": transaction_hash,
            "sender_id": sender_account_id,
            "recipient_id": recipient_account_id,
            "sender_address": sender_account.wallet_address,
            "recipient_address": recipient_account.wallet_address,
            "amount": float(amount),
            "currency_type": currency_type,
            "status": "confirmed",  # Sandbox transactions are instant
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Commit balance changes
        db.commit()
        db.refresh(sender_account)
        db.refresh(recipient_account)
        
        return transaction_data
    
    def validate_sandbox_user_access(
        self,
        db: Session,
        account_id: str,
        sandbox_user_id: str
    ) -> bool:
        """
        Validate that a sandbox user has access to a test account.
        
        Args:
            db: Database session
            account_id: UUID of test account
            sandbox_user_id: UUID of sandbox user
            
        Returns:
            bool: True if user has access, False otherwise
        """
        return test_account_service.validate_test_account(
            db=db,
            account_id=account_id,
            sandbox_user_id=sandbox_user_id
        )


# Create singleton instance
sandbox_transaction_service = SandboxTransactionService()

