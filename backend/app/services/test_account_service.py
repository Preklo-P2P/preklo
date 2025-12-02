"""
Test Account Service
Handles creation and management of test accounts for sandbox users.
"""
import secrets
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.sandbox import TestAccount
from ..services.wallet_service import WalletService


# Test account configuration - 5 fixed accounts per sandbox user
TEST_ACCOUNTS = [
    {
        "username": "@alice_test",
        "usdc_balance": Decimal("0.0"),
        "apt_balance": Decimal("0.0"),
        "currency_type": "USDC"
    },
    {
        "username": "@bob_test",
        "usdc_balance": Decimal("10.0"),
        "apt_balance": Decimal("0.1"),
        "currency_type": "USDC"
    },
    {
        "username": "@charlie_test",
        "usdc_balance": Decimal("100.0"),
        "apt_balance": Decimal("1.0"),
        "currency_type": "USDC"
    },
    {
        "username": "@diana_test",
        "usdc_balance": Decimal("1000.0"),
        "apt_balance": Decimal("10.0"),
        "currency_type": "USDC"
    },
    {
        "username": "@eve_test",
        "usdc_balance": Decimal("50.0"),
        "apt_balance": Decimal("5.0"),
        "currency_type": "USDC"
    },
]


class TestAccountService:
    """
    Service for managing test accounts in the sandbox.
    
    Each sandbox user gets 5 pre-configured test accounts with different balances.
    """
    
    def __init__(self):
        self.wallet_service = WalletService()
    
    def _generate_wallet_address(self) -> str:
        """
        Generate a mock wallet address for test accounts.
        
        Returns:
            str: A formatted wallet address
        """
        # Generate a mock address for testing
        return f"0x{secrets.token_hex(32)}"
    
    def create_default_accounts(
        self,
        db: Session,
        sandbox_user_id: str
    ) -> List[TestAccount]:
        """
        Create the 5 default test accounts for a sandbox user.
        
        Args:
            db: Database session
            sandbox_user_id: UUID of the sandbox user
            
        Returns:
            List[TestAccount]: List of created test accounts
        """
        accounts = []
        
        for account_config in TEST_ACCOUNTS:
            # Generate wallet address for this test account
            wallet_address = self._generate_wallet_address()
            
            # Create test account
            test_account = TestAccount(
                sandbox_user_id=sandbox_user_id,
                username=account_config["username"],
                wallet_address=wallet_address,
                usdc_balance=account_config["usdc_balance"],
                apt_balance=account_config["apt_balance"],
                original_usdc_balance=account_config["usdc_balance"],
                original_apt_balance=account_config["apt_balance"],
                currency_type=account_config["currency_type"]
            )
            
            db.add(test_account)
            accounts.append(test_account)
        
        db.commit()
        
        # Refresh all accounts
        for account in accounts:
            db.refresh(account)
        
        return accounts
    
    def get_test_accounts(
        self,
        db: Session,
        sandbox_user_id: str,
        currency_type: Optional[str] = None
    ) -> List[TestAccount]:
        """
        Get all test accounts for a sandbox user.
        
        Args:
            db: Database session
            sandbox_user_id: UUID of the sandbox user
            currency_type: Optional filter by currency type
            
        Returns:
            List[TestAccount]: List of test accounts
        """
        query = db.query(TestAccount).filter(
            TestAccount.sandbox_user_id == sandbox_user_id
        )
        
        if currency_type:
            query = query.filter(TestAccount.currency_type == currency_type)
        
        return query.all()
    
    def get_test_account(
        self,
        db: Session,
        account_id: str,
        sandbox_user_id: str
    ) -> Optional[TestAccount]:
        """
        Get a specific test account by ID.
        
        Args:
            db: Database session
            account_id: UUID of the test account
            sandbox_user_id: UUID of the sandbox user (for security check)
            
        Returns:
            Optional[TestAccount]: The test account if found and owned by user
        """
        return db.query(TestAccount).filter(
            and_(
                TestAccount.id == account_id,
                TestAccount.sandbox_user_id == sandbox_user_id
            )
        ).first()
    
    def reset_balance(
        self,
        db: Session,
        account_id: str,
        sandbox_user_id: str
    ) -> Optional[TestAccount]:
        """
        Reset a test account balance to its original values.
        
        Args:
            db: Database session
            account_id: UUID of the test account
            sandbox_user_id: UUID of the sandbox user (for security check)
            
        Returns:
            Optional[TestAccount]: The updated test account if found
        """
        account = self.get_test_account(db, account_id, sandbox_user_id)
        
        if not account:
            return None
        
        # Reset to original balances
        account.usdc_balance = account.original_usdc_balance
        account.apt_balance = account.original_apt_balance
        
        db.commit()
        db.refresh(account)
        
        return account
    
    def fund_account(
        self,
        db: Session,
        account_id: str,
        sandbox_user_id: str,
        usdc_amount: Optional[Decimal] = None,
        apt_amount: Optional[Decimal] = None
    ) -> Optional[TestAccount]:
        """
        Add test funds to a test account.
        
        Args:
            db: Database session
            account_id: UUID of the test account
            sandbox_user_id: UUID of the sandbox user (for security check)
            usdc_amount: Optional USDC amount to add
            apt_amount: Optional APT amount to add
            
        Returns:
            Optional[TestAccount]: The updated test account if found
        """
        account = self.get_test_account(db, account_id, sandbox_user_id)
        
        if not account:
            return None
        
        # Add funds
        if usdc_amount is not None:
            account.usdc_balance += usdc_amount
        
        if apt_amount is not None:
            account.apt_balance += apt_amount
        
        db.commit()
        db.refresh(account)
        
        return account
    
    def validate_test_account(
        self,
        db: Session,
        account_id: str,
        sandbox_user_id: str
    ) -> bool:
        """
        Validate that a test account exists and belongs to the sandbox user.
        
        Args:
            db: Database session
            account_id: UUID of the test account
            sandbox_user_id: UUID of the sandbox user
            
        Returns:
            bool: True if the account exists and belongs to the user
        """
        account = self.get_test_account(db, account_id, sandbox_user_id)
        return account is not None


# Create singleton instance
test_account_service = TestAccountService()

