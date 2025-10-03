import httpx
from typing import Dict, List, Optional, Any
from decimal import Decimal
from datetime import datetime
from ..config import settings


class NoditService:
    def __init__(self):
        self.api_key = settings.nodit_api_key
        self.rpc_url = settings.nodit_rpc_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}" if self.api_key else None,
            "Content-Type": "application/json"
        }
    
    async def get_transaction_by_hash(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Get transaction details by hash using Nodit RPC"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "get_transaction_by_hash",
                "params": [tx_hash],
                "id": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.rpc_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        return data["result"]
                    elif "error" in data:
                        print(f"Nodit API error: {data['error']}")
                        return None
                else:
                    print(f"Nodit API request failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Error fetching transaction from Nodit: {e}")
            # Fallback to direct Aptos node
            return None
    
    async def get_account_transactions(
        self, 
        address: str, 
        limit: int = 25,
        start: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get account transactions using Nodit indexing"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "get_account_transactions",
                "params": {
                    "address": address,
                    "limit": limit,
                    "start": start
                },
                "id": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.rpc_url,
                    json=payload,
                    headers=self.headers,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        return data["result"]
                    elif "error" in data:
                        print(f"Nodit API error: {data['error']}")
                        return []
                else:
                    print(f"Nodit API request failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Error fetching account transactions from Nodit: {e}")
            return []
    
    async def get_transaction_events(self, tx_hash: str) -> List[Dict[str, Any]]:
        """Get events for a specific transaction"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "get_transaction_events",
                "params": [tx_hash],
                "id": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.rpc_url,
                    json=payload,
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        return data["result"]
                    elif "error" in data:
                        print(f"Nodit API error: {data['error']}")
                        return []
                else:
                    print(f"Nodit API request failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Error fetching transaction events from Nodit: {e}")
            return []
    
    async def get_coin_transfers(
        self,
        address: str,
        coin_type: Optional[str] = None,
        limit: int = 25,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get coin transfer events for an address"""
        try:
            params = {
                "address": address,
                "limit": limit,
                "offset": offset
            }
            
            if coin_type:
                params["coin_type"] = coin_type
            
            payload = {
                "jsonrpc": "2.0",
                "method": "get_coin_transfers",
                "params": params,
                "id": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.rpc_url,
                    json=payload,
                    headers=self.headers,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        return data["result"]
                    elif "error" in data:
                        print(f"Nodit API error: {data['error']}")
                        return []
                else:
                    print(f"Nodit API request failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Error fetching coin transfers from Nodit: {e}")
            return []
    
    async def get_account_balance_history(
        self,
        address: str,
        coin_type: str,
        from_timestamp: Optional[int] = None,
        to_timestamp: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get balance history for an account"""
        try:
            params = {
                "address": address,
                "coin_type": coin_type,
                "limit": limit
            }
            
            if from_timestamp:
                params["from_timestamp"] = from_timestamp
            if to_timestamp:
                params["to_timestamp"] = to_timestamp
            
            payload = {
                "jsonrpc": "2.0",
                "method": "get_account_balance_history",
                "params": params,
                "id": 1
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.rpc_url,
                    json=payload,
                    headers=self.headers,
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        return data["result"]
                    elif "error" in data:
                        print(f"Nodit API error: {data['error']}")
                        return []
                else:
                    print(f"Nodit API request failed: {response.status_code}")
                    return []
                    
        except Exception as e:
            print(f"Error fetching balance history from Nodit: {e}")
            return []
    
    def parse_transaction_amount(self, transaction: Dict[str, Any]) -> Optional[Decimal]:
        """Parse transaction amount from Nodit transaction data"""
        try:
            # Look for coin transfer events
            if "events" in transaction:
                for event in transaction["events"]:
                    if event.get("type") == "0x1::coin::WithdrawEvent" or event.get("type") == "0x1::coin::DepositEvent":
                        if "data" in event and "amount" in event["data"]:
                            amount_str = event["data"]["amount"]
                            # Convert from smallest unit based on coin type
                            if "0x1::aptos_coin::AptosCoin" in event.get("type", ""):
                                return Decimal(amount_str) / Decimal(10**8)  # APT has 8 decimals
                            elif "usdc" in event.get("type", "").lower():
                                return Decimal(amount_str) / Decimal(10**6)  # USDC has 6 decimals
                            else:
                                return Decimal(amount_str) / Decimal(10**8)  # Default to 8 decimals
            
            return None
        except Exception as e:
            print(f"Error parsing transaction amount: {e}")
            return None
    
    def extract_addresses_from_transaction(self, transaction: Dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
        """Extract sender and recipient addresses from transaction"""
        try:
            sender = transaction.get("sender")
            
            # Look for recipient in events or payload
            recipient = None
            if "payload" in transaction and "arguments" in transaction["payload"]:
                args = transaction["payload"]["arguments"]
                if len(args) > 0:
                    # First argument is usually the recipient address
                    recipient = args[0]
            
            # Also check events for more accurate recipient info
            if "events" in transaction:
                for event in transaction["events"]:
                    if event.get("type") == "0x1::coin::DepositEvent":
                        recipient = event.get("account")
                        break
            
            return sender, recipient
        except Exception as e:
            print(f"Error extracting addresses from transaction: {e}")
            return None, None


# Global service instance
nodit_service = NoditService()
