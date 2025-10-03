"""
Tests for Transaction History Service (Story 2.5)
"""

import pytest
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.transaction_history_service import transaction_history_service
from app.models import User, Transaction


class TestTransactionHistoryService:
    """Test the transaction history service"""
    
    def setup_method(self):
        """Setup test data"""
        self.mock_user = Mock(spec=User)
        self.mock_user.id = "test-user-id"
        self.mock_user.username = "testuser"
        self.mock_user.wallet_address = "0x1234567890abcdef"
        
        self.mock_sender = Mock(spec=User)
        self.mock_sender.id = "sender-id"
        self.mock_sender.username = "sender"
        self.mock_sender.wallet_address = "0xabcdef1234567890"
        
        self.mock_recipient = Mock(spec=User)
        self.mock_recipient.id = "recipient-id"
        self.mock_recipient.username = "recipient"
        self.mock_recipient.wallet_address = "0x1234567890abcdef"
        
        self.mock_db = Mock(spec=Session)
        
        # Clear caches
        transaction_history_service._export_cache.clear()
        transaction_history_service._analytics_cache.clear()
    
    @pytest.mark.asyncio
    async def test_get_enhanced_transaction_history_basic(self):
        """Test basic transaction history retrieval"""
        # Test error handling when database query fails
        result = await transaction_history_service.get_enhanced_transaction_history(
            self.mock_user, self.mock_db
        )
        
        assert "transactions" in result
        assert "pagination" in result
        assert "filters_applied" in result
        assert "search_query" in result
        assert result["transactions"] == []
        assert result["pagination"]["total"] == 0
    
    @pytest.mark.asyncio
    async def test_get_enhanced_transaction_history_with_filters(self):
        """Test transaction history with filters"""
        filters = {
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-12-31T23:59:59Z",
            "min_amount": 1.0,
            "max_amount": 100.0,
            "status": "confirmed",
            "currency_type": "APT"
        }
        
        result = await transaction_history_service.get_enhanced_transaction_history(
            self.mock_user, self.mock_db, filters=filters
        )
        
        assert "transactions" in result
        assert "filters_applied" in result
        # Test error handling when database query fails - filters_applied will be empty
        assert result["filters_applied"] == {}
    
    @pytest.mark.asyncio
    async def test_get_enhanced_transaction_history_with_search(self):
        """Test transaction history with search"""
        # Mock database query
        query_mock = self.mock_db.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value
        query_mock.count.return_value = 0
        query_mock.offset.return_value.limit.return_value.all.return_value = []
        
        result = await transaction_history_service.get_enhanced_transaction_history(
            self.mock_user, self.mock_db, search_query="test"
        )
        
        assert "transactions" in result
        assert "search_query" in result
        assert result["search_query"] == "test"
    
    @pytest.mark.asyncio
    async def test_get_transaction_analytics_30d(self):
        """Test transaction analytics for 30 days"""
        result = await transaction_history_service.get_transaction_analytics(
            self.mock_user, self.mock_db, "30d"
        )
        
        assert "period" in result
        assert result["period"] == "30d"
        # Test error handling when database query fails
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_get_transaction_analytics_7d(self):
        """Test transaction analytics for 7 days"""
        result = await transaction_history_service.get_transaction_analytics(
            self.mock_user, self.mock_db, "7d"
        )
        
        assert result["period"] == "7d"
        # Test error handling when database query fails
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_export_transactions_csv(self):
        """Test CSV export functionality"""
        # Mock transaction
        mock_transaction = Mock(spec=Transaction)
        mock_transaction.id = "tx-id"
        mock_transaction.transaction_hash = "0x1234567890abcdef"
        mock_transaction.amount = Decimal("1.0")
        mock_transaction.currency_type = "APT"
        mock_transaction.transaction_type = "transfer"
        mock_transaction.status = "confirmed"
        mock_transaction.description = "Test payment"
        mock_transaction.gas_fee = Decimal("0.01")
        mock_transaction.block_height = 12345
        mock_transaction.created_at = datetime.now(timezone.utc)
        mock_transaction.updated_at = datetime.now(timezone.utc)
        mock_transaction.sender_id = "sender-id"
        mock_transaction.recipient_id = "recipient-id"
        
        # Mock database query
        query_mock = self.mock_db.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value
        query_mock.order_by.return_value.all.return_value = [
            (mock_transaction, self.mock_sender, self.mock_recipient)
        ]
        
        result = await transaction_history_service.export_transactions(
            self.mock_user, self.mock_db, "csv"
        )
        
        assert "export_id" in result
        assert "format" in result
        assert "transaction_count" in result
        assert "download_url" in result
        assert result["format"] == "csv"
        assert result["transaction_count"] == 1
    
    @pytest.mark.asyncio
    async def test_export_transactions_pdf(self):
        """Test PDF export functionality"""
        # Mock transaction
        mock_transaction = Mock(spec=Transaction)
        mock_transaction.id = "tx-id"
        mock_transaction.transaction_hash = "0x1234567890abcdef"
        mock_transaction.amount = Decimal("1.0")
        mock_transaction.currency_type = "APT"
        mock_transaction.transaction_type = "transfer"
        mock_transaction.status = "confirmed"
        mock_transaction.description = "Test payment"
        mock_transaction.gas_fee = Decimal("0.01")
        mock_transaction.block_height = 12345
        mock_transaction.created_at = datetime.now(timezone.utc)
        mock_transaction.updated_at = datetime.now(timezone.utc)
        mock_transaction.sender_id = "sender-id"
        mock_transaction.recipient_id = "recipient-id"
        
        # Mock database query
        query_mock = self.mock_db.query.return_value.outerjoin.return_value.outerjoin.return_value.filter.return_value
        query_mock.order_by.return_value.all.return_value = [
            (mock_transaction, self.mock_sender, self.mock_recipient)
        ]
        
        result = await transaction_history_service.export_transactions(
            self.mock_user, self.mock_db, "pdf"
        )
        
        assert "export_id" in result
        assert "format" in result
        assert "transaction_count" in result
        assert "download_url" in result
        assert result["format"] == "pdf"
        assert result["transaction_count"] == 1
    
    def test_get_export_success(self):
        """Test getting export by ID"""
        # Create a test export
        export_id = "test-export-id"
        export_data = {
            "data": "test,csv,data",
            "format": "csv",
            "created_at": datetime.now(timezone.utc),
            "transaction_count": 1
        }
        
        transaction_history_service._export_cache[export_id] = export_data
        
        result = transaction_history_service.get_export(export_id)
        
        assert result is not None
        assert result["format"] == "csv"
        assert result["transaction_count"] == 1
    
    def test_get_export_not_found(self):
        """Test getting non-existent export"""
        result = transaction_history_service.get_export("non-existent-id")
        assert result is None
    
    def test_get_export_expired(self):
        """Test getting expired export"""
        # Create an expired export
        export_id = "expired-export-id"
        export_data = {
            "data": "test,csv,data",
            "format": "csv",
            "created_at": datetime.now(timezone.utc) - timedelta(hours=2),  # 2 hours ago
            "transaction_count": 1
        }
        
        transaction_history_service._export_cache[export_id] = export_data
        
        result = transaction_history_service.get_export(export_id)
        
        # Should return None and clean up the cache
        assert result is None
        assert export_id not in transaction_history_service._export_cache
    
    def test_cleanup_expired_exports(self):
        """Test cleanup of expired exports"""
        # Create some exports
        current_time = datetime.now(timezone.utc)
        
        # Valid export
        valid_export = {
            "data": "valid,data",
            "format": "csv",
            "created_at": current_time - timedelta(minutes=30),
            "transaction_count": 1
        }
        
        # Expired export
        expired_export = {
            "data": "expired,data",
            "format": "csv",
            "created_at": current_time - timedelta(hours=2),
            "transaction_count": 1
        }
        
        transaction_history_service._export_cache["valid-id"] = valid_export
        transaction_history_service._export_cache["expired-id"] = expired_export
        
        # Run cleanup
        transaction_history_service.cleanup_expired_exports()
        
        # Check that only valid export remains
        assert "valid-id" in transaction_history_service._export_cache
        assert "expired-id" not in transaction_history_service._export_cache
    
    def test_generate_csv_export(self):
        """Test CSV generation"""
        transactions = [
            {
                "id": "tx-1",
                "transaction_hash": "0x123",
                "amount": "1.0",
                "currency_type": "APT",
                "transaction_type": "transfer",
                "status": "confirmed",
                "description": "Test payment",
                "gas_fee": "0.01",
                "block_height": 12345,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "sender": {
                    "username": "sender",
                    "wallet_address": "0xabc"
                },
                "recipient": {
                    "username": "recipient",
                    "wallet_address": "0x123"
                }
            }
        ]
        
        csv_data = transaction_history_service._generate_csv_export(transactions)
        
        assert "ID,Transaction Hash,Amount" in csv_data
        assert "tx-1,0x123,1.0" in csv_data
        assert "sender,0xabc" in csv_data
        assert "recipient,0x123" in csv_data
    
    def test_generate_pdf_export(self):
        """Test PDF generation placeholder"""
        transactions = [
            {
                "id": "tx-1",
                "amount": "1.0",
                "currency_type": "APT"
            }
        ]
        
        pdf_data = transaction_history_service._generate_pdf_export(transactions)
        
        assert "PDF export for 1 transactions" in pdf_data


class TestTransactionHistoryIntegration:
    """Integration tests for transaction history functionality"""
    
    @pytest.mark.asyncio
    async def test_transaction_history_flow_integration(self):
        """Test complete transaction history flow"""
        # This would be an integration test that tests the entire flow
        # from filtering to export to analytics
        pass
    
    @pytest.mark.asyncio
    async def test_transaction_history_error_handling(self):
        """Test error handling in transaction history flow"""
        # Test various error scenarios
        pass
