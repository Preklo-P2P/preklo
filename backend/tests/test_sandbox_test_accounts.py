"""
Unit Tests for Sandbox Test Account Service
Tests test account creation, retrieval, reset, and funding.
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from decimal import Decimal
import uuid

from app.services.test_account_service import test_account_service, TestAccountService, TEST_ACCOUNTS
from app.models.sandbox import TestAccount


class TestTestAccountConfiguration:
    """Test test account configuration"""
    
    def test_test_accounts_configuration(self):
        """Test that TEST_ACCOUNTS has correct configuration"""
        assert len(TEST_ACCOUNTS) == 5, "Should have 5 test accounts configured"
        
        # Verify account structure
        for account in TEST_ACCOUNTS:
            assert "username" in account, "Account should have username"
            assert "usdc_balance" in account, "Account should have USDC balance"
            assert "apt_balance" in account, "Account should have APT balance"
            assert "currency_type" in account, "Account should have currency type"
    
    def test_test_accounts_balances(self):
        """Test that test accounts have expected balances"""
        # Account 1: Empty
        assert TEST_ACCOUNTS[0]["usdc_balance"] == Decimal("0.0")
        assert TEST_ACCOUNTS[0]["apt_balance"] == Decimal("0.0")
        
        # Account 2: Low balance
        assert TEST_ACCOUNTS[1]["usdc_balance"] == Decimal("10.0")
        assert TEST_ACCOUNTS[1]["apt_balance"] == Decimal("0.1")
        
        # Account 3: Medium balance
        assert TEST_ACCOUNTS[2]["usdc_balance"] == Decimal("100.0")
        assert TEST_ACCOUNTS[2]["apt_balance"] == Decimal("1.0")
        
        # Account 4: High balance
        assert TEST_ACCOUNTS[3]["usdc_balance"] == Decimal("1000.0")
        assert TEST_ACCOUNTS[3]["apt_balance"] == Decimal("10.0")
        
        # Account 5: Multi-currency
        assert TEST_ACCOUNTS[4]["usdc_balance"] == Decimal("50.0")
        assert TEST_ACCOUNTS[4]["apt_balance"] == Decimal("5.0")


class TestWalletGeneration:
    """Test wallet address generation"""
    
    def test_generate_wallet_address(self):
        """Test wallet address generation"""
        address = test_account_service._generate_wallet_address()
        
        assert address.startswith("0x"), "Wallet address should start with 0x"
        assert len(address) == 66, "Wallet address should be 66 characters (0x + 64 hex)"
    
    def test_generate_wallet_address_uniqueness(self):
        """Test that generated wallet addresses are unique"""
        address1 = test_account_service._generate_wallet_address()
        address2 = test_account_service._generate_wallet_address()
        
        assert address1 != address2, "Generated wallet addresses should be unique"


class TestTestAccountService:
    """Test test account service methods"""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sandbox_user_id(self):
        """Create a test sandbox user ID"""
        return str(uuid.uuid4())
    
    def test_create_default_accounts(self, mock_db, sandbox_user_id):
        """Test creating default test accounts"""
        # Mock database operations
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        result = test_account_service.create_default_accounts(
            db=mock_db,
            sandbox_user_id=sandbox_user_id
        )
        
        assert len(result) == 5, "Should create 5 test accounts"
        assert mock_db.add.call_count == 5, "Should add 5 accounts to database"
        assert mock_db.commit.called, "Should commit transaction"
        
        # Verify account properties
        for i, account in enumerate(result):
            assert account.sandbox_user_id == sandbox_user_id
            assert account.username == TEST_ACCOUNTS[i]["username"]
            assert account.usdc_balance == TEST_ACCOUNTS[i]["usdc_balance"]
            assert account.apt_balance == TEST_ACCOUNTS[i]["apt_balance"]
            assert account.original_usdc_balance == TEST_ACCOUNTS[i]["usdc_balance"]
            assert account.original_apt_balance == TEST_ACCOUNTS[i]["apt_balance"]
    
    def test_get_test_accounts_all(self, mock_db, sandbox_user_id):
        """Test retrieving all test accounts"""
        # Create mock accounts
        mock_accounts = [
            Mock(spec=TestAccount, sandbox_user_id=sandbox_user_id, currency_type="USDC")
            for _ in range(5)
        ]
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_accounts
        mock_db.query.return_value = mock_query
        
        result = test_account_service.get_test_accounts(
            db=mock_db,
            sandbox_user_id=sandbox_user_id
        )
        
        assert len(result) == 5, "Should return all test accounts"
    
    def test_get_test_accounts_filtered(self, mock_db, sandbox_user_id):
        """Test retrieving test accounts filtered by currency"""
        # Create mock accounts
        mock_accounts = [
            Mock(spec=TestAccount, sandbox_user_id=sandbox_user_id, currency_type="USDC")
            for _ in range(3)
        ]
        
        # Mock database query chain - need to chain filter() calls
        mock_query = Mock()
        mock_query.filter.return_value = mock_query  # First filter returns query
        mock_query.filter.return_value = mock_query  # Second filter (if any) returns query
        mock_query.all.return_value = mock_accounts  # all() returns accounts
        mock_db.query.return_value = mock_query
        
        result = test_account_service.get_test_accounts(
            db=mock_db,
            sandbox_user_id=sandbox_user_id,
            currency_type="USDC"
        )
        
        # The service chains filters, so we need to verify the call chain
        assert result == mock_accounts, "Should return filtered accounts"
        assert len(mock_accounts) == 3, "Should have 3 filtered accounts"
    
    def test_get_test_account_success(self, mock_db, sandbox_user_id):
        """Test retrieving a specific test account"""
        account_id = str(uuid.uuid4())
        mock_account = Mock(spec=TestAccount)
        mock_account.id = account_id
        mock_account.sandbox_user_id = sandbox_user_id
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        mock_db.query.return_value = mock_query
        
        result = test_account_service.get_test_account(
            db=mock_db,
            account_id=account_id,
            sandbox_user_id=sandbox_user_id
        )
        
        assert result == mock_account, "Should return the test account"
    
    def test_get_test_account_not_found(self, mock_db, sandbox_user_id):
        """Test retrieving non-existent test account"""
        account_id = str(uuid.uuid4())
        
        # Mock query returning None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = test_account_service.get_test_account(
            db=mock_db,
            account_id=account_id,
            sandbox_user_id=sandbox_user_id
        )
        
        assert result is None, "Should return None for non-existent account"
    
    def test_reset_balance(self, mock_db, sandbox_user_id):
        """Test resetting account balance"""
        account_id = str(uuid.uuid4())
        
        # Create mock account with modified balances
        mock_account = Mock(spec=TestAccount)
        mock_account.id = account_id
        mock_account.sandbox_user_id = sandbox_user_id
        mock_account.usdc_balance = Decimal("500.0")
        mock_account.apt_balance = Decimal("5.0")
        mock_account.original_usdc_balance = Decimal("100.0")
        mock_account.original_apt_balance = Decimal("1.0")
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        mock_db.query.return_value = mock_query
        
        result = test_account_service.reset_balance(
            db=mock_db,
            account_id=account_id,
            sandbox_user_id=sandbox_user_id
        )
        
        assert result == mock_account, "Should return the updated account"
        assert mock_account.usdc_balance == Decimal("100.0"), "USDC balance should be reset"
        assert mock_account.apt_balance == Decimal("1.0"), "APT balance should be reset"
        assert mock_db.commit.called, "Should commit transaction"
    
    def test_fund_account_usdc(self, mock_db, sandbox_user_id):
        """Test funding account with USDC"""
        account_id = str(uuid.uuid4())
        
        # Create mock account
        mock_account = Mock(spec=TestAccount)
        mock_account.id = account_id
        mock_account.sandbox_user_id = sandbox_user_id
        mock_account.usdc_balance = Decimal("100.0")
        mock_account.apt_balance = Decimal("1.0")
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        mock_db.query.return_value = mock_query
        
        result = test_account_service.fund_account(
            db=mock_db,
            account_id=account_id,
            sandbox_user_id=sandbox_user_id,
            usdc_amount=Decimal("50.0")
        )
        
        assert result == mock_account, "Should return the updated account"
        assert mock_account.usdc_balance == Decimal("150.0"), "USDC balance should be increased"
        assert mock_account.apt_balance == Decimal("1.0"), "APT balance should be unchanged"
        assert mock_db.commit.called, "Should commit transaction"
    
    def test_fund_account_apt(self, mock_db, sandbox_user_id):
        """Test funding account with APT"""
        account_id = str(uuid.uuid4())
        
        # Create mock account
        mock_account = Mock(spec=TestAccount)
        mock_account.id = account_id
        mock_account.sandbox_user_id = sandbox_user_id
        mock_account.usdc_balance = Decimal("100.0")
        mock_account.apt_balance = Decimal("1.0")
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        mock_db.query.return_value = mock_query
        
        result = test_account_service.fund_account(
            db=mock_db,
            account_id=account_id,
            sandbox_user_id=sandbox_user_id,
            apt_amount=Decimal("2.0")
        )
        
        assert result == mock_account, "Should return the updated account"
        assert mock_account.usdc_balance == Decimal("100.0"), "USDC balance should be unchanged"
        assert mock_account.apt_balance == Decimal("3.0"), "APT balance should be increased"
    
    def test_fund_account_both(self, mock_db, sandbox_user_id):
        """Test funding account with both USDC and APT"""
        account_id = str(uuid.uuid4())
        
        # Create mock account
        mock_account = Mock(spec=TestAccount)
        mock_account.id = account_id
        mock_account.sandbox_user_id = sandbox_user_id
        mock_account.usdc_balance = Decimal("100.0")
        mock_account.apt_balance = Decimal("1.0")
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        mock_db.query.return_value = mock_query
        
        result = test_account_service.fund_account(
            db=mock_db,
            account_id=account_id,
            sandbox_user_id=sandbox_user_id,
            usdc_amount=Decimal("50.0"),
            apt_amount=Decimal("2.0")
        )
        
        assert result == mock_account, "Should return the updated account"
        assert mock_account.usdc_balance == Decimal("150.0"), "USDC balance should be increased"
        assert mock_account.apt_balance == Decimal("3.0"), "APT balance should be increased"
    
    def test_validate_test_account_true(self, mock_db, sandbox_user_id):
        """Test validating existing test account"""
        account_id = str(uuid.uuid4())
        mock_account = Mock(spec=TestAccount)
        
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_account
        mock_db.query.return_value = mock_query
        
        result = test_account_service.validate_test_account(
            db=mock_db,
            account_id=account_id,
            sandbox_user_id=sandbox_user_id
        )
        
        assert result is True, "Should return True for existing account"
    
    def test_validate_test_account_false(self, mock_db, sandbox_user_id):
        """Test validating non-existent test account"""
        account_id = str(uuid.uuid4())
        
        # Mock query returning None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = test_account_service.validate_test_account(
            db=mock_db,
            account_id=account_id,
            sandbox_user_id=sandbox_user_id
        )
        
        assert result is False, "Should return False for non-existent account"

