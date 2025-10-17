import asyncio
import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal
import httpx
from datetime import datetime, timedelta
from ..config import settings

logger = logging.getLogger("preklo.aptos_service")

# Global variables for lazy loading
_SDK_AVAILABLE = None
_SDK_CLASSES = None

def _get_aptos_sdk():
    """Lazy load Aptos SDK classes"""
    global _SDK_AVAILABLE, _SDK_CLASSES
    
    if _SDK_AVAILABLE is None:
        try:
            from aptos_sdk.async_client import RestClient
            from aptos_sdk.account import Account
            from aptos_sdk.transactions import EntryFunction, TransactionPayload, TransactionArgument
            from aptos_sdk.type_tag import TypeTag, StructTag
            from aptos_sdk.account_address import AccountAddress
            from aptos_sdk.bcs import Serializer
            
            _SDK_AVAILABLE = True
            _SDK_CLASSES = {
                'RestClient': RestClient,
                'Account': Account,
                'EntryFunction': EntryFunction,
                'TransactionPayload': TransactionPayload,
                'TypeTag': TypeTag,
                'StructTag': StructTag,
                'TransactionArgument': TransactionArgument,
                'AccountAddress': AccountAddress,
                'Serializer': Serializer
            }
        except ImportError as e:
            print(f"WARNING: Failed to import Aptos SDK: {e}")
            
            _SDK_AVAILABLE = False
            _SDK_CLASSES = {
                'RestClient': None,
                'Account': None,
                'EntryFunction': None,
                'TransactionPayload': None,
                'TypeTag': None,
                'StructTag': None,
                'TransactionArgument': None,
                'AccountAddress': None,
                'Serializer': None
            }
        except Exception as e:
            print(f"WARNING: Unexpected error importing Aptos SDK: {e}")
            
            _SDK_AVAILABLE = False
            _SDK_CLASSES = {
                'RestClient': None,
                'Account': None,
                'EntryFunction': None,
                'TransactionPayload': None,
                'TypeTag': None,
                'StructTag': None,
                'TransactionArgument': None,
                'AccountAddress': None,
                'Serializer': None
            }
    
    return _SDK_AVAILABLE, _SDK_CLASSES


class AptosService:
    def __init__(self):
        self._client = None
        self.contract_address = settings.aptos_contract_address
        self.usdc_contract_address = settings.circle_usdc_contract_address
        
        # Initialize client lazily when first needed
        self._client_initialized = False
        self._connection_healthy = False
        self._last_health_check = None
        self._health_check_interval = 300  # 5 minutes
        
        # Transaction monitoring
        self._pending_transactions = {}
        self._transaction_status_cache = {}
        self._cache_ttl = 60  # 1 minute cache TTL
    
    def _ensure_client(self):
        """Ensure the Aptos client is initialized"""
        if not self._client_initialized:
            SDK_AVAILABLE, SDK_CLASSES = _get_aptos_sdk()
            if SDK_AVAILABLE and SDK_CLASSES['RestClient']:
                try:
                    self._client = SDK_CLASSES['RestClient'](settings.aptos_node_url)
                    logger.info("Aptos SDK connected to testnet")
                    self._connection_healthy = True
                except Exception as e:
                    logger.error(f"Failed to initialize Aptos client: {e}")
                    self._client = None
                    self._connection_healthy = False
            else:
                self._client = None
                self._connection_healthy = False
                logger.warning("Aptos SDK not available, using mock service")
            self._client_initialized = True
    
    @property
    def client(self):
        """Get the Aptos client, initializing it if needed"""
        if not self._client_initialized:
            self._ensure_client()
        return self._client
    
    async def _check_connection_health(self) -> bool:
        """Check if the blockchain connection is healthy"""
        if not self._last_health_check or \
           (datetime.now() - self._last_health_check).seconds > self._health_check_interval:
            
            try:
                if self.client:
                    # Try to get the latest ledger info using the correct method
                    await self.client.info()
                    self._connection_healthy = True
                    logger.debug("Blockchain connection health check passed")
                else:
                    self._connection_healthy = False
                    logger.warning("Blockchain connection health check failed: no client")
            except Exception as e:
                self._connection_healthy = False
                logger.error(f"Blockchain connection health check failed: {e}")
            
            self._last_health_check = datetime.now()
        
        return self._connection_healthy
    
    async def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """Retry a function with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return await func()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Function failed after {max_retries} attempts: {e}")
                    raise
                
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                await asyncio.sleep(delay)
    
    async def estimate_gas_fee(self, transaction_type: str = "transfer") -> Decimal:
        """Estimate gas fee for a transaction"""
        try:
            # Check connection health first
            if not await self._check_connection_health():
                logger.warning("Connection unhealthy, using default gas fee")
                return Decimal("0.001")  # Default 0.001 APT
            
            if self.client:
                # Get current gas price from the network
                try:
                    # Try to get gas price from the latest transaction
                    ledger_info = await self.client.ledger_info()
                    # For now, return a reasonable estimate
                    # In a real implementation, you'd calculate based on network conditions
                    return Decimal("0.001")  # 0.001 APT base fee
                except Exception as e:
                    logger.warning(f"Could not get gas price: {e}")
                    return Decimal("0.001")
            else:
                return Decimal("0.001")
                
        except Exception as e:
            logger.error(f"Error estimating gas fee: {e}")
            return Decimal("0.001")  # Fallback to default
    
    async def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction status with caching"""
        # Check cache first
        if tx_hash in self._transaction_status_cache:
            cached_data = self._transaction_status_cache[tx_hash]
            if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self._cache_ttl):
                return cached_data['status']
        
        try:
            if not await self._check_connection_health():
                return {"status": "unknown", "error": "Connection unhealthy"}
            
            if self.client:
                transaction = await self.client.transaction_by_hash(tx_hash)
                
                status = {
                    "hash": tx_hash,
                    "status": "confirmed" if transaction.get("success", False) else "failed",
                    "success": transaction.get("success", False),
                    "timestamp": transaction.get("timestamp", None),
                    "gas_used": transaction.get("gas_used", 0),
                    "gas_unit_price": transaction.get("gas_unit_price", 0),
                    "version": transaction.get("version", None)
                }
                
                # Cache the result
                self._transaction_status_cache[tx_hash] = {
                    "status": status,
                    "timestamp": datetime.now()
                }
                
                return status
            else:
                return {"status": "unknown", "error": "No client available"}
                
        except Exception as e:
            logger.error(f"Error getting transaction status for {tx_hash}: {e}")
            return {"status": "unknown", "error": str(e)}
    
    async def monitor_transaction(self, tx_hash: str, timeout: int = 300) -> Dict[str, Any]:
        """Monitor a transaction until completion or timeout"""
        start_time = datetime.now()
        
        while (datetime.now() - start_time).seconds < timeout:
            status = await self.get_transaction_status(tx_hash)
            
            if status["status"] in ["confirmed", "failed"]:
                return status
            
            # Wait before checking again
            await asyncio.sleep(5)
        
        return {"status": "timeout", "error": "Transaction monitoring timed out"}
    
    async def get_network_info(self) -> Dict[str, Any]:
        """Get current network information"""
        try:
            if not await self._check_connection_health():
                return {"error": "Connection unhealthy"}
            
            if self.client:
                ledger_info = await self.client.ledger_info()
                return {
                    "chain_id": ledger_info.get("chain_id", None),
                    "ledger_version": ledger_info.get("ledger_version", None),
                    "ledger_timestamp": ledger_info.get("ledger_timestamp", None),
                    "node_role": ledger_info.get("node_role", None)
                }
            else:
                return {"error": "No client available"}
                
        except Exception as e:
            logger.error(f"Error getting network info: {e}")
            return {"error": str(e)}
        
    async def get_account_balance(self, address: str, currency_type: str = "APT") -> Decimal:
        """Get account balance for specified currency with enhanced error handling"""
        try:
            # Ensure client is initialized first
            self._ensure_client()
            
            # Check connection health
            if not await self._check_connection_health():
                logger.warning(f"Connection unhealthy, using cached balance for {address}")
                # Return cached balance if available, otherwise 0
                return Decimal("0")
            
            if currency_type == "APT":
                # Use view function to get real APT balance with retry logic
                async def fetch_apt_balance():
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            f"{settings.aptos_node_url.rstrip('/v1')}/v1/view",
                            json={
                                "function": "0x1::coin::balance",
                                "type_arguments": ["0x1::aptos_coin::AptosCoin"],
                                "arguments": [address]
                            },
                            headers={"Content-Type": "application/json"}
                        )
                        
                        if response.status_code == 200:
                            balance_data = response.json()
                            if balance_data and len(balance_data) > 0:
                                balance = int(balance_data[0])
                                return Decimal(balance) / Decimal(10**8)
                        
                        return Decimal("0")
                
                # Use retry logic for balance fetching
                balance = await self._retry_with_backoff(fetch_apt_balance)
                logger.debug(f"APT balance for {address}: {balance}")
                return balance
            
            elif currency_type == "USDC":
                # Use view function to get real USDC balance
                async def fetch_usdc_balance():
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            f"{settings.aptos_node_url.rstrip('/v1')}/v1/view",
                            json={
                                "function": "0x1::coin::balance",
                                "type_arguments": [self.usdc_contract_address],
                                "arguments": [address]
                            },
                            headers={"Content-Type": "application/json"}
                        )
                        
                        if response.status_code == 200:
                            balance_data = response.json()
                            if balance_data and len(balance_data) > 0:
                                balance = int(balance_data[0])
                                return Decimal(balance) / Decimal(10**6)  # USDC has 6 decimals
                        
                        return Decimal("0")
                
                # Use retry logic for USDC balance fetching
                balance = await self._retry_with_backoff(fetch_usdc_balance)
                logger.debug(f"USDC balance for {address}: {balance}")
                return balance
                
        except Exception as e:
            logger.error(f"Error fetching balance for {address} ({currency_type}): {e}")
            return Decimal("0")
    
    async def transfer_apt(
        self, 
        sender_private_key: str,
        recipient_address: str,
        amount: Decimal
    ) -> Optional[str]:
        """Transfer APT to another account with enhanced error handling and monitoring"""
        self._ensure_client()
        
        # Check connection health first
        if not await self._check_connection_health():
            logger.error("Cannot transfer APT: blockchain connection unhealthy")
            return None
        
        SDK_AVAILABLE, SDK_CLASSES = _get_aptos_sdk()
        if not SDK_AVAILABLE or SDK_CLASSES['Account'] is None:
            logger.error("Aptos SDK not available, cannot transfer APT")
            return None
            
        try:
            Account = SDK_CLASSES['Account']
            sender_account = Account.load_key(sender_private_key)
            
            # Convert amount to octas (APT's smallest unit)
            amount_octas = int(Decimal(str(amount)) * Decimal(10**8))
            
            # Validate amount is positive and reasonable
            if amount_octas <= 0:
                raise ValueError("Transfer amount must be positive")
            
            if amount_octas > 10**15:  # More than 10 million APT
                raise ValueError("Transfer amount is too large")
            
            # Estimate gas fee before transaction
            estimated_gas = await self.estimate_gas_fee("transfer")
            logger.info(f"Estimated gas fee for APT transfer: {estimated_gas} APT")
            
            # Use the proper SDK classes for transaction creation
            try:
                logger.info("Attempting APT transfer using proper SDK classes...")
                EntryFunction = SDK_CLASSES['EntryFunction']
                TypeTag = SDK_CLASSES['TypeTag']
                StructTag = SDK_CLASSES['StructTag']
                TransactionArgument = SDK_CLASSES['TransactionArgument']
                AccountAddress = SDK_CLASSES['AccountAddress']
                TransactionPayload = SDK_CLASSES['TransactionPayload']
                
                # Create transaction payload using proper SDK patterns
                payload = EntryFunction.natural(
                    "0x1::coin",
                    "transfer",
                    [TypeTag(StructTag.from_str("0x1::aptos_coin::AptosCoin"))],
                    [recipient_address, str(amount_octas)]
                )
                
                # Create signed transaction and submit it
                try:
                    signed_transaction = await self.client.create_bcs_signed_transaction(
                        sender_account,
                        TransactionPayload(payload)
                    )
                    txn_hash = await self.client.submit_bcs_transaction(signed_transaction)
                except Exception as submit_error:
                    logger.error(f"Failed to submit APT transaction to blockchain: {submit_error}")
                    # Check if it's a specific blockchain rejection
                    error_str = str(submit_error).lower()
                    if "insufficient" in error_str:
                        raise ValueError(f"Insufficient balance: {submit_error}")
                    elif "sequence" in error_str:
                        raise ValueError(f"Transaction sequence error: {submit_error}")
                    elif "gas" in error_str:
                        raise ValueError(f"Gas error: {submit_error}")
                    else:
                        raise ValueError(f"Blockchain transaction failed: {submit_error}")
                logger.info(f"APT transfer transaction submitted: {txn_hash}")
                
                # Start monitoring the transaction
                self._pending_transactions[txn_hash] = {
                    "type": "APT_transfer",
                    "amount": amount,
                    "recipient": recipient_address,
                    "timestamp": datetime.now()
                }
                
                # Wait for transaction to complete
                await self.client.wait_for_transaction(txn_hash)
                
                # Remove from pending transactions
                if txn_hash in self._pending_transactions:
                    del self._pending_transactions[txn_hash]
                
                logger.info(f"APT transfer completed successfully: {txn_hash}")
                return txn_hash
                
            except Exception as e:
                logger.error(f"create_bcs_signed_transaction failed: {e}")
                # Provide more specific error information
                error_str = str(e).lower()
                if "insufficient" in error_str:
                    logger.error(f"Insufficient balance for APT transfer: {e}")
                elif "gas" in error_str:
                    logger.error(f"Gas-related error for APT transfer: {e}")
                elif "network" in error_str or "connection" in error_str:
                    logger.error(f"Network error for APT transfer: {e}")
                elif "400" in error_str or "bad request" in error_str:
                    logger.error(f"Bad request to Aptos blockchain for APT transfer: {e}")
                    logger.error(f"Transaction details - Sender: {sender_private_key[:10]}..., Recipient: {recipient_address}, Amount: {amount_octas}")
                raise e
            
        except Exception as e:
            logger.error(f"Error transferring APT: {e}")
            # Log more details for debugging
            logger.error(f"Sender: {sender_private_key[:10]}..., Recipient: {recipient_address}, Amount: {amount}")
            return None
    
    async def transfer_usdc(
        self,
        sender_private_key: str,
        recipient_address: str,
        amount: Decimal
    ) -> Optional[str]:
        """Transfer USDC to another account with enhanced error handling and monitoring"""
        self._ensure_client()
        
        # Check connection health first
        if not await self._check_connection_health():
            logger.error("Cannot transfer USDC: blockchain connection unhealthy")
            return None
        
        SDK_AVAILABLE, SDK_CLASSES = _get_aptos_sdk()
        if not SDK_AVAILABLE or SDK_CLASSES['Account'] is None:
            logger.error("Aptos SDK not available, cannot transfer USDC")
            return None
            
        try:
            Account = SDK_CLASSES['Account']
            sender_account = Account.load_key(sender_private_key)
            
            # Convert amount to USDC's smallest unit (6 decimals)
            amount_units = int(amount * Decimal(10**6))
            
            # Estimate gas fee before transaction
            estimated_gas = await self.estimate_gas_fee("transfer")
            logger.info(f"Estimated gas fee for USDC transfer: {estimated_gas} APT")
            
            # Create USDC transfer transaction
            EntryFunction = SDK_CLASSES['EntryFunction']
            TypeTag = SDK_CLASSES['TypeTag']
            StructTag = SDK_CLASSES['StructTag']
            TransactionArgument = SDK_CLASSES['TransactionArgument']
            AccountAddress = SDK_CLASSES['AccountAddress']
            TransactionPayload = SDK_CLASSES['TransactionPayload']
            
            payload = EntryFunction.natural(
                "0x1::coin",
                "transfer",
                [TypeTag(StructTag.from_str(self.usdc_contract_address))],
                [recipient_address, str(amount_units)]
            )
            
            # Create signed transaction and submit it
            signed_transaction = await self.client.create_bcs_signed_transaction(
                sender_account,
                TransactionPayload(payload)
            )
            txn_hash = await self.client.submit_bcs_transaction(signed_transaction)
            logger.info(f"USDC transfer transaction submitted: {txn_hash}")
            
            # Start monitoring the transaction
            self._pending_transactions[txn_hash] = {
                "type": "USDC_transfer",
                "amount": amount,
                "recipient": recipient_address,
                "timestamp": datetime.now()
            }
            
            # Wait for transaction to be processed
            await self.client.wait_for_transaction(txn_hash)
            
            # Remove from pending transactions
            if txn_hash in self._pending_transactions:
                del self._pending_transactions[txn_hash]
            
            logger.info(f"USDC transfer completed successfully: {txn_hash}")
            return txn_hash
            
        except Exception as e:
            logger.error(f"Error transferring USDC: {e}")
            # Log more details for debugging
            logger.error(f"Sender: {sender_private_key[:10]}..., Recipient: {recipient_address}, Amount: {amount}")
            # Provide more specific error information
            if "insufficient" in str(e).lower():
                logger.error(f"Insufficient balance for USDC transfer: {e}")
            elif "gas" in str(e).lower():
                logger.error(f"Gas-related error for USDC transfer: {e}")
            elif "network" in str(e).lower() or "connection" in str(e).lower():
                logger.error(f"Network error for USDC transfer: {e}")
            return None
    
    async def initialize_username_registry(self) -> Optional[str]:
        """Initialize the username registry on-chain"""
        self._ensure_client()
        
        SDK_AVAILABLE, SDK_CLASSES = _get_aptos_sdk()
        if not SDK_AVAILABLE or SDK_CLASSES['Account'] is None:
            print("WARNING: Aptos SDK not available, cannot initialize username registry")
            return None
            
        try:
            # Use the admin account (contract deployer)
            admin_private_key = settings.admin_private_key
            if not admin_private_key:
                print("ERROR: admin_private_key not set in settings")
                return None
                
            Account = SDK_CLASSES['Account']
            admin_account = Account.load_key(admin_private_key)
            
            TransactionPayload = SDK_CLASSES['TransactionPayload']
            EntryFunction = SDK_CLASSES['EntryFunction']
            
            # Use the proper SDK classes for transaction creation
            try:
                print("Trying create_bcs_transaction method...")
                # Create proper transaction payload using SDK classes
                payload = EntryFunction.natural(
                    f"{self.contract_address}::username_registry",
                    "initialize",
                    [],
                    []
                )
                
                transaction = await self.client.create_bcs_transaction(
                    admin_account,
                    TransactionPayload(payload)
                )
                
                txn_hash = await self.client.submit_bcs_transaction(transaction)
                print("create_bcs_signed_transaction successful")
                
                # Wait for transaction to complete
                await self.client.wait_for_transaction(txn_hash)
                return txn_hash
                
            except Exception as e:
                print(f"create_bcs_signed_transaction failed: {e}, trying manual approach")
                
                # Try manual approach with EntryFunction
                payload = EntryFunction.natural(
                    f"{self.contract_address}::username_registry",
                    "initialize",
                    [],
                    []
                )
                
                # Submit transaction using modern API
                transaction = await self.client.create_bcs_transaction(
                    admin_account,
                    TransactionPayload(payload)
                )
                
                txn_hash = await self.client.submit_bcs_transaction(transaction)
                
                # Wait for transaction to complete
                await self.client.wait_for_transaction(txn_hash)
                print(f"Username registry initialized with transaction: {txn_hash}")
                return txn_hash
            
        except Exception as e:
            print(f"Error initializing username registry: {e}")
            return None
    
    async def register_username(
        self,
        user_private_key: str,
        username: str
    ) -> Optional[str]:
        """Register username on-chain"""
        self._ensure_client()
        
        SDK_AVAILABLE, SDK_CLASSES = _get_aptos_sdk()
        if not SDK_AVAILABLE or SDK_CLASSES['Account'] is None:
            print("WARNING: Aptos SDK not available, cannot register username")
            return None
            
        try:
            Account = SDK_CLASSES['Account']
            user_account = Account.load_key(user_private_key)
            
            EntryFunction = SDK_CLASSES['EntryFunction']
            TransactionArgument = SDK_CLASSES['TransactionArgument']
            TransactionPayload = SDK_CLASSES['TransactionPayload']
            
            payload = EntryFunction.natural(
                f"{self.contract_address}::username_registry",
                "register_username",
                [],
                [username]
            )
            
            # Create signed transaction and submit it
            signed_transaction = await self.client.create_bcs_signed_transaction(
                user_account,
                TransactionPayload(payload)
            )
            txn_hash = await self.client.submit_bcs_transaction(signed_transaction)
            
            await self.client.wait_for_transaction(txn_hash)
            
            return txn_hash
            
        except Exception as e:
            print(f"Error registering username: {e}")
            return None
    
    async def resolve_username(self, username: str) -> Optional[str]:
        """Resolve username to wallet address"""
        try:
            # Call view function to get address by username
            result = await self.client.view(
                f"{self.contract_address}::username_registry::get_address_by_username",
                [],
                [username]
            )
            
            if result and len(result) > 0:
                return result[0]
            return None
            
        except Exception as e:
            print(f"Error resolving username: {e}")
            return None
    
    async def create_payment_request(
        self,
        recipient_private_key: str,
        payment_id: str,
        amount: Decimal,
        currency_type: str,
        description: str,
        expiry_hours: int
    ) -> Optional[str]:
        """Create payment request on-chain"""
        self._ensure_client()
        
        SDK_AVAILABLE, SDK_CLASSES = _get_aptos_sdk()
        if not SDK_AVAILABLE or SDK_CLASSES['Account'] is None:
            print("WARNING: Aptos SDK not available, cannot create payment request")
            return None
            
        try:
            Account = SDK_CLASSES['Account']
            recipient_account = Account.load_key(recipient_private_key)
            
            # Convert amount based on currency
            if currency_type == "USDC":
                amount_units = int(amount * Decimal(10**6))
            else:  # APT
                amount_units = int(amount * Decimal(10**8))
            
            EntryFunction = SDK_CLASSES['EntryFunction']
            TransactionArgument = SDK_CLASSES['TransactionArgument']
            TransactionPayload = SDK_CLASSES['TransactionPayload']
            
            payload = EntryFunction.natural(
                f"{self.contract_address}::payment_forwarding",
                "create_payment_request",
                [],
                [
                    payment_id,
                    str(amount_units),
                    currency_type,
                    description,
                    str(expiry_hours)
                ]
            )
            
            # Create signed transaction and submit it
            signed_transaction = await self.client.create_bcs_signed_transaction(
                recipient_account,
                TransactionPayload(payload)
            )
            txn_hash = await self.client.submit_bcs_transaction(signed_transaction)
            
            await self.client.wait_for_transaction(txn_hash)
            
            return txn_hash
            
        except Exception as e:
            print(f"Error creating payment request: {e}")
            return None
    
    async def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict[Any, Any]]:
        """Get transaction details by hash"""
        try:
            transaction = await self.client.transaction_by_hash(tx_hash)
            return transaction
        except Exception as e:
            print(f"Error getting transaction: {e}")
            return None
    
    async def get_account_transactions(
        self,
        address: str,
        limit: int = 25,
        start: Optional[int] = None
    ) -> List[Dict[Any, Any]]:
        """Get account transactions"""
        try:
            if not await self._check_connection_health():
                logger.warning("Connection unhealthy, cannot fetch account transactions")
                return []
            
            if self.client:
                transactions = await self.client.account_transactions(
                    address,
                    limit=limit,
                    start=start
                )
                return transactions
            else:
                logger.error("No client available for fetching account transactions")
                return []
        except Exception as e:
            logger.error(f"Error getting account transactions: {e}")
            return []
    
    async def get_pending_transactions(self) -> Dict[str, Any]:
        """Get all pending transactions being monitored"""
        return {
            "pending_count": len(self._pending_transactions),
            "transactions": self._pending_transactions
        }
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """Get blockchain connection status"""
        is_healthy = await self._check_connection_health()
        network_info = await self.get_network_info()
        
        return {
            "connected": self._client_initialized,
            "healthy": is_healthy,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "network_info": network_info,
            "pending_transactions": len(self._pending_transactions)
        }


# Global service instance
aptos_service = AptosService()
