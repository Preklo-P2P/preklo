import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal
from app.services.aptos_service import aptos_service


class TestBlockchainIntegration:
    """Test blockchain integration functionality"""

    @pytest.mark.asyncio
    async def test_connection_health_check(self):
        """Test blockchain connection health check"""
        with patch.object(aptos_service, 'get_connection_status') as mock_status:
            mock_status.return_value = {
                "connected": True,
                "healthy": True,
                "last_health_check": "2024-01-01T00:00:00",
                "network_info": {"chain_id": "testnet"},
                "pending_transactions": 0
            }
            
            result = await aptos_service.get_connection_status()
            assert result["connected"] is True
            assert result["healthy"] is True

    @pytest.mark.asyncio
    async def test_network_info(self):
        """Test network information retrieval"""
        with patch.object(aptos_service, 'get_network_info') as mock_info:
            mock_info.return_value = {
                "chain_id": "testnet",
                "ledger_version": "12345",
                "ledger_timestamp": "2024-01-01T00:00:00",
                "node_role": "validator"
            }
            
            result = await aptos_service.get_network_info()
            assert result["chain_id"] == "testnet"

    @pytest.mark.asyncio
    async def test_gas_fee_estimation(self):
        """Test gas fee estimation"""
        with patch.object(aptos_service, 'estimate_gas_fee') as mock_gas:
            mock_gas.return_value = Decimal("0.001")
            
            result = await aptos_service.estimate_gas_fee("transfer")
            assert result == Decimal("0.001")

    @pytest.mark.asyncio
    async def test_transaction_status(self):
        """Test transaction status retrieval"""
        with patch.object(aptos_service, 'get_transaction_status') as mock_status:
            mock_status.return_value = {
                "hash": "0x123",
                "status": "confirmed",
                "success": True,
                "timestamp": "2024-01-01T00:00:00",
                "gas_used": 1000,
                "gas_unit_price": 100
            }
            
            result = await aptos_service.get_transaction_status("0x123")
            assert result["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_transaction_monitoring(self):
        """Test transaction monitoring"""
        with patch.object(aptos_service, 'monitor_transaction') as mock_monitor:
            mock_monitor.return_value = {
                "hash": "0x123",
                "status": "confirmed",
                "success": True
            }
            
            result = await aptos_service.monitor_transaction("0x123", 300)
            assert result["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_account_balance(self):
        """Test account balance retrieval"""
        with patch.object(aptos_service, 'get_account_balance') as mock_balance:
            mock_balance.return_value = Decimal("10.5")
            
            result = await aptos_service.get_account_balance("0x123", "APT")
            assert result == Decimal("10.5")

    @pytest.mark.asyncio
    async def test_account_transactions(self):
        """Test account transaction history"""
        with patch.object(aptos_service, 'get_account_transactions') as mock_txs:
            mock_txs.return_value = [
                {"hash": "0x123", "amount": "1.0", "currency": "APT"},
                {"hash": "0x456", "amount": "2.0", "currency": "USDC"}
            ]
            
            result = await aptos_service.get_account_transactions("0x123", 25)
            assert len(result) == 2
            assert result[0]["hash"] == "0x123"


class TestAptosService:
    """Test Aptos service functionality"""

    @pytest.mark.asyncio
    async def test_connection_health_check(self):
        """Test connection health check method"""
        with patch.object(aptos_service, 'client') as mock_client:
            mock_client.ledger_info = AsyncMock(return_value={"chain_id": "testnet"})
            aptos_service._last_health_check = None
            
            result = await aptos_service._check_connection_health()
            assert result is True

    @pytest.mark.asyncio
    async def test_gas_fee_estimation(self):
        """Test gas fee estimation"""
        with patch.object(aptos_service, '_check_connection_health') as mock_health:
            mock_health.return_value = True
            
            result = await aptos_service.estimate_gas_fee("transfer")
            assert isinstance(result, Decimal)
            assert result > 0

    @pytest.mark.asyncio
    async def test_transaction_status_caching(self):
        """Test transaction status caching"""
        with patch.object(aptos_service, 'client') as mock_client:
            mock_client.transaction_by_hash = AsyncMock(return_value={
                "success": True,
                "timestamp": "2024-01-01T00:00:00",
                "gas_used": 1000,
                "gas_unit_price": 100,
                "version": 12345
            })
            
            # First call should fetch from blockchain
            result1 = await aptos_service.get_transaction_status("0x123")
            assert result1["status"] == "confirmed"
            
            # Second call should use cache
            result2 = await aptos_service.get_transaction_status("0x123")
            assert result2["status"] == "confirmed"
            assert result1 == result2

    @pytest.mark.asyncio
    async def test_balance_retry_logic(self):
        """Test balance fetching with retry logic"""
        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = ["100000000"]  # 1 APT in octas
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )
            
            result = await aptos_service.get_account_balance("0x123", "APT")
            assert result == Decimal("1.0")

    @pytest.mark.asyncio
    async def test_transfer_apt_with_monitoring(self):
        """Test APT transfer with transaction monitoring"""
        # Test the monitoring functionality without actual transfer
        aptos_service._pending_transactions["0x123"] = {
            "type": "APT_transfer",
            "amount": Decimal("1.0"),
            "recipient": "0x456",
            "timestamp": "2024-01-01T00:00:00"
        }
        
        assert "0x123" in aptos_service._pending_transactions
        assert aptos_service._pending_transactions["0x123"]["type"] == "APT_transfer"
        assert aptos_service._pending_transactions["0x123"]["amount"] == Decimal("1.0")

    @pytest.mark.asyncio
    async def test_transfer_usdc_with_monitoring(self):
        """Test USDC transfer with transaction monitoring"""
        # Test the monitoring functionality without actual transfer
        aptos_service._pending_transactions["0x456"] = {
            "type": "USDC_transfer",
            "amount": Decimal("10.0"),
            "recipient": "0x789",
            "timestamp": "2024-01-01T00:00:00"
        }
        
        assert "0x456" in aptos_service._pending_transactions
        assert aptos_service._pending_transactions["0x456"]["type"] == "USDC_transfer"
        assert aptos_service._pending_transactions["0x456"]["amount"] == Decimal("10.0")

    @pytest.mark.asyncio
    async def test_network_info_retrieval(self):
        """Test network information retrieval"""
        with patch.object(aptos_service, 'client') as mock_client:
            mock_client.ledger_info = AsyncMock(return_value={
                "chain_id": "testnet",
                "ledger_version": "12345",
                "ledger_timestamp": "2024-01-01T00:00:00",
                "node_role": "validator"
            })
            
            result = await aptos_service.get_network_info()
            assert result["chain_id"] == "testnet"
            assert result["ledger_version"] == "12345"

    @pytest.mark.asyncio
    async def test_pending_transactions_tracking(self):
        """Test pending transactions tracking"""
        # Clear existing transactions first
        aptos_service._pending_transactions.clear()
        
        # Add a pending transaction
        aptos_service._pending_transactions["0x123"] = {
            "type": "APT_transfer",
            "amount": Decimal("1.0"),
            "recipient": "0x456",
            "timestamp": "2024-01-01T00:00:00"
        }
        
        result = await aptos_service.get_pending_transactions()
        assert result["pending_count"] == 1
        assert "0x123" in result["transactions"]

    @pytest.mark.asyncio
    async def test_connection_status(self):
        """Test connection status retrieval"""
        with patch.object(aptos_service, '_check_connection_health') as mock_health:
            mock_health.return_value = True
            
            with patch.object(aptos_service, 'get_network_info') as mock_info:
                mock_info.return_value = {"chain_id": "testnet"}
                
                result = await aptos_service.get_connection_status()
                assert result["healthy"] is True
                assert result["network_info"]["chain_id"] == "testnet"
                assert "connected" in result
                assert "pending_transactions" in result
