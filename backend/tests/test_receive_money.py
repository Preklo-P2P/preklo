"""
Tests for Receive Money Service (Story 2.4)
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.receive_money_service import receive_money_service
from app.models import User, Transaction, Balance, Notification


class TestReceiveMoneyService:
    """Test the receive money service"""
    
    def setup_method(self):
        """Setup test data"""
        self.mock_user = Mock(spec=User)
        self.mock_user.id = "test-user-id"
        self.mock_user.username = "testuser"
        self.mock_user.wallet_address = "0x1234567890abcdef"
        self.mock_user.is_active = True
        
        self.mock_sender = Mock(spec=User)
        self.mock_sender.id = "sender-id"
        self.mock_sender.username = "sender"
        self.mock_sender.wallet_address = "0xabcdef1234567890"
        
        self.mock_db = Mock(spec=Session)
        
        # Clear processed transactions
        receive_money_service._processed_transactions.clear()
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self):
        """Test starting and stopping transaction monitoring"""
        # Test starting monitoring
        await receive_money_service.start_transaction_monitoring(self.mock_db)
        assert receive_money_service._monitoring_active is True
        
        # Test stopping monitoring
        await receive_money_service.stop_transaction_monitoring()
        assert receive_money_service._monitoring_active is False
    
    @pytest.mark.asyncio
    async def test_process_incoming_transactions(self):
        """Test processing incoming transactions"""
        # Mock users query
        self.mock_db.query.return_value.filter.return_value.all.return_value = [self.mock_user]
        
        # Mock aptos service
        with patch('app.services.receive_money_service.aptos_service') as mock_aptos:
            mock_aptos.get_account_transactions = AsyncMock(return_value=[
                {
                    "hash": "0x1234567890abcdef",
                    "changes": [
                        {
                            "address": "0x1234567890abcdef",
                            "data": {
                                "type": "0x1::coin::CoinStore",
                                "data": {
                                    "deposit": "100000000"  # 1 APT in smallest units
                                },
                                "coin_type": "0x1::aptos_coin::AptosCoin"
                            }
                        },
                        {
                            "address": "0xabcdef1234567890",  # Sender address
                            "data": {
                                "type": "0x1::coin::CoinStore",
                                "data": {
                                    "withdraw": "100000000"
                                }
                            }
                        }
                    ]
                }
            ])
            
            # Mock database queries
            self.mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing transaction
            self.mock_db.query.return_value.filter.return_value.all.return_value = [self.mock_user]
            
            # Mock database operations
            self.mock_db.add.return_value = None
            self.mock_db.flush.return_value = None
            self.mock_db.commit.return_value = None
            
            await receive_money_service._process_incoming_transactions(self.mock_db)
            
            # Verify transaction was processed
            assert "0x1234567890abcdef" in receive_money_service._processed_transactions
    
    @pytest.mark.asyncio
    async def test_check_user_incoming_transactions(self):
        """Test checking incoming transactions for a specific user"""
        # Mock aptos service
        with patch('app.services.receive_money_service.aptos_service') as mock_aptos:
            mock_aptos.get_account_transactions = AsyncMock(return_value=[
                {
                    "hash": "0x1234567890abcdef",
                    "changes": [
                        {
                            "address": "0x1234567890abcdef",
                            "data": {
                                "type": "0x1::coin::CoinStore",
                                "data": {
                                    "deposit": "100000000"  # 1 APT
                                },
                                "coin_type": "0x1::aptos_coin::AptosCoin"
                            }
                        },
                        {
                            "address": "0xabcdef1234567890",  # Sender address
                            "data": {
                                "type": "0x1::coin::CoinStore",
                                "data": {
                                    "withdraw": "100000000"
                                }
                            }
                        }
                    ]
                }
            ])
            
            # Mock database queries
            self.mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing transaction
            self.mock_db.query.return_value.filter.return_value.all.return_value = [self.mock_sender]
            
            # Mock database operations
            self.mock_db.add.return_value = None
            self.mock_db.flush.return_value = None
            self.mock_db.commit.return_value = None
            
            await receive_money_service._check_user_incoming_transactions(self.mock_user, self.mock_db)
            
            # Verify transaction was processed
            assert "0x1234567890abcdef" in receive_money_service._processed_transactions
    
    def test_is_incoming_transaction(self):
        """Test checking if transaction is incoming"""
        # Test incoming transaction
        tx_data = {
            "changes": [
                {
                    "address": "0x1234567890abcdef",
                    "data": {
                        "type": "0x1::coin::CoinStore",
                        "data": {
                            "deposit": "100000000"
                        }
                    }
                }
            ]
        }
        
        result = receive_money_service._is_incoming_transaction(tx_data, "0x1234567890abcdef")
        assert result is True
        
        # Test outgoing transaction (user's address not in changes)
        tx_data_outgoing = {
            "changes": [
                {
                    "address": "0xabcdef1234567890",  # Different address
                    "data": {
                        "type": "0x1::coin::CoinStore",
                        "data": {
                            "withdraw": "100000000"
                        }
                    }
                }
            ]
        }
        
        result = receive_money_service._is_incoming_transaction(tx_data_outgoing, "0x1234567890abcdef")
        assert result is False
    
    def test_extract_sender_address(self):
        """Test extracting sender address from transaction"""
        tx_data = {
            "changes": [
                {
                    "address": "0xabcdef1234567890",
                    "data": {
                        "type": "0x1::coin::CoinStore",
                        "data": {
                            "withdraw": "100000000"
                        }
                    }
                }
            ]
        }
        
        sender_address = receive_money_service._extract_sender_address(tx_data)
        assert sender_address == "0xabcdef1234567890"
    
    def test_extract_amount(self):
        """Test extracting amount from transaction"""
        tx_data = {
            "changes": [
                {
                    "data": {
                        "type": "0x1::coin::CoinStore",
                        "data": {
                            "deposit": "100000000"  # 1 APT
                        }
                    }
                }
            ]
        }
        
        amount = receive_money_service._extract_amount(tx_data)
        assert amount == Decimal("1.0")
    
    def test_extract_currency_type(self):
        """Test extracting currency type from transaction"""
        # Test APT
        tx_data_apt = {
            "changes": [
                {
                    "data": {
                        "type": "0x1::coin::CoinStore",
                        "coin_type": "0x1::aptos_coin::AptosCoin"
                    }
                }
            ]
        }
        
        currency = receive_money_service._extract_currency_type(tx_data_apt)
        assert currency == "APT"
        
        # Test USDC
        tx_data_usdc = {
            "changes": [
                {
                    "data": {
                        "type": "0x1::coin::CoinStore",
                        "coin_type": "0x1::usdc::USDC"
                    }
                }
            ]
        }
        
        currency = receive_money_service._extract_currency_type(tx_data_usdc)
        assert currency == "USDC"
    
    @pytest.mark.asyncio
    async def test_update_user_balance(self):
        """Test updating user balance"""
        # Mock existing balance
        mock_balance = Mock(spec=Balance)
        mock_balance.balance = Decimal("5.0")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_balance
        
        await receive_money_service._update_user_balance(
            self.mock_user, Decimal("1.0"), "APT", self.mock_db
        )
        
        # Verify balance was updated
        assert mock_balance.balance == Decimal("6.0")
    
    @pytest.mark.asyncio
    async def test_create_received_payment_notification(self):
        """Test creating notification for received payment"""
        # Mock database operations
        self.mock_db.add.return_value = None
        
        await receive_money_service._create_received_payment_notification(
            self.mock_user, self.mock_sender, Decimal("1.0"), "APT", "tx-id", self.mock_db
        )
        
        # Verify notification was created
        self.mock_db.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_received_transactions(self):
        """Test getting received transactions"""
        # Mock transaction
        mock_transaction = Mock(spec=Transaction)
        mock_transaction.id = "tx-id"
        mock_transaction.transaction_hash = "0x1234567890abcdef"
        mock_transaction.amount = Decimal("1.0")
        mock_transaction.currency_type = "APT"
        mock_transaction.status = "confirmed"
        mock_transaction.description = "Test payment"
        mock_transaction.created_at = datetime.now(timezone.utc)
        mock_transaction.sender_id = "sender-id"
        
        # Mock database queries
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_transaction]
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_sender
        
        transactions = await receive_money_service.get_received_transactions(
            self.mock_user, 25, 0, self.mock_db
        )
        
        assert len(transactions) == 1
        assert transactions[0]["amount"] == "1.0"
        assert transactions[0]["currency_type"] == "APT"
        assert transactions[0]["sender"]["username"] == "sender"
    
    @pytest.mark.asyncio
    async def test_get_received_transaction_details(self):
        """Test getting received transaction details"""
        # Mock transaction
        mock_transaction = Mock(spec=Transaction)
        mock_transaction.id = "tx-id"
        mock_transaction.transaction_hash = "0x1234567890abcdef"
        mock_transaction.amount = Decimal("1.0")
        mock_transaction.currency_type = "APT"
        mock_transaction.status = "confirmed"
        mock_transaction.description = "Test payment"
        mock_transaction.gas_fee = Decimal("0.01")
        mock_transaction.block_height = 12345
        mock_transaction.created_at = datetime.now(timezone.utc)
        mock_transaction.updated_at = datetime.now(timezone.utc)
        mock_transaction.sender_id = "sender-id"
        mock_transaction.sender_address = "0xabcdef1234567890"
        
        # Mock database queries - need to handle multiple calls
        query_mock = self.mock_db.query.return_value.filter.return_value
        query_mock.first.side_effect = [mock_transaction, self.mock_sender]
        
        transaction = await receive_money_service.get_received_transaction_details(
            "tx-id", self.mock_user, self.mock_db
        )
        
        assert transaction is not None
        assert transaction["amount"] == "1.0"
        assert transaction["currency_type"] == "APT"
        assert transaction["sender"]["username"] == "sender"
    
    @pytest.mark.asyncio
    async def test_sync_user_transactions(self):
        """Test syncing user transactions"""
        with patch.object(receive_money_service, '_check_user_incoming_transactions') as mock_check:
            mock_check.return_value = None
            
            result = await receive_money_service.sync_user_transactions(self.mock_user, self.mock_db)
            
            assert result.success is True
            assert "synced successfully" in result.message
    
    @pytest.mark.asyncio
    async def test_get_user_balance_existing(self):
        """Test getting user balance when balance record exists"""
        # Mock existing balance
        mock_balance = Mock(spec=Balance)
        mock_balance.balance = Decimal("10.0")
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_balance
        
        balance = await receive_money_service.get_user_balance(
            self.mock_user, "APT", self.mock_db
        )
        
        assert balance == Decimal("10.0")
    
    @pytest.mark.asyncio
    async def test_get_user_balance_new(self):
        """Test getting user balance when no balance record exists"""
        # Mock no existing balance
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Mock blockchain balance
        with patch('app.services.receive_money_service.aptos_service') as mock_aptos:
            mock_aptos.get_account_balance = AsyncMock(return_value=Decimal("5.0"))
            
            # Mock database operations
            self.mock_db.add.return_value = None
            self.mock_db.commit.return_value = None
            
            balance = await receive_money_service.get_user_balance(
                self.mock_user, "APT", self.mock_db
            )
            
            assert balance == Decimal("5.0")
            self.mock_db.add.assert_called_once()


class TestReceiveMoneyIntegration:
    """Integration tests for receive money functionality"""
    
    @pytest.mark.asyncio
    async def test_receive_money_flow_integration(self):
        """Test complete receive money flow"""
        # This would be an integration test that tests the entire flow
        # from transaction detection to notification delivery
        pass
    
    @pytest.mark.asyncio
    async def test_receive_money_error_handling(self):
        """Test error handling in receive money flow"""
        # Test various error scenarios
        pass
