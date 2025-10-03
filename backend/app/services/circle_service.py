"""
Circle Web3 Services Integration
Handles Circle USDC operations, wallet creation, and compliance features
"""

import asyncio
from typing import Optional, Dict, Any, List
from decimal import Decimal
import httpx
import json
from datetime import datetime, timedelta, timezone

# Circle SDK is not available in pip, using direct HTTP API calls
# In production, you would use Circle's official SDK when available
CIRCLE_SDK_AVAILABLE = False
CircleClient = None
CircleAPIException = Exception

from ..config import settings


class CircleService:
    """
    Circle Web3 Services integration for USDC operations
    Provides wallet management, transfers, and compliance features
    """
    
    def __init__(self):
        if settings.circle_api_key and settings.circle_api_key != "your_circle_api_key_here":
            self.client = None  # Using HTTP API directly
            self.is_mock = False
            print("Circle API configured for HTTP requests")
        else:
            self.client = None
            self.is_mock = True
            print("WARNING: Circle API not configured, using mock service")
        
        self.base_url = "https://api.circle.com/v1"
        self.testnet_base_url = "https://api-sandbox.circle.com/v1"
        self.usdc_contract_address = settings.circle_usdc_contract_address
    
    async def create_programmable_wallet(
        self, 
        user_id: str, 
        blockchain: str = "MATIC-AMOY"  # Circle testnet
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Circle Programmable Wallet for a user
        """
        if self.is_mock:
            # Mock wallet creation for development
            mock_wallet = {
                "walletId": f"mock_wallet_{user_id}",
                "address": f"0x{user_id[:40].ljust(40, '0')}",
                "blockchain": blockchain,
                "accountType": "SCA",
                "state": "LIVE",
                "createDate": datetime.now(timezone.utc).isoformat(),
                "updateDate": datetime.now(timezone.utc).isoformat()
            }
            print(f"Mock: Created wallet for user {user_id}")
            return mock_wallet
        
        try:
            # Real Circle API call
            wallet_data = {
                "idempotencyKey": f"wallet_{user_id}_{int(datetime.now(timezone.utc).timestamp())}",
                "blockchains": [blockchain],
                "accountType": "SCA",
                "walletSetId": settings.circle_wallet_set_id  # From Circle console
            }
            
            response = await self._make_circle_request(
                "POST",
                "/w3s/wallets",
                data=wallet_data
            )
            
            if response and "data" in response:
                print(f"Circle: Created wallet for user {user_id}")
                return response["data"]["wallet"]
            
            return None
            
        except Exception as e:
            print(f"Error creating Circle wallet: {e}")
            return None
    
    async def get_wallet_balance(
        self, 
        wallet_id: str, 
        token_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get wallet balance for USDC or other tokens
        """
        if self.is_mock:
            # Mock balance for development
            return {
                "tokenBalances": [
                    {
                        "token": {
                            "id": self.usdc_contract_address,
                            "blockchain": "MATIC-AMOY",
                            "tokenAddress": self.usdc_contract_address,
                            "standard": "ERC20",
                            "name": "USD Coin",
                            "symbol": "USDC",
                            "decimals": 6,
                            "isNative": False
                        },
                        "amount": "1000.000000",  # Mock 1000 USDC
                        "updateDate": datetime.now(timezone.utc).isoformat()
                    }
                ]
            }
        
        try:
            # Real Circle API call
            response = await self._make_circle_request(
                "GET",
                f"/w3s/wallets/{wallet_id}/balances"
            )
            
            return response.get("data", {}) if response else {}
            
        except Exception as e:
            print(f"Error getting wallet balance: {e}")
            return {}
    
    async def transfer_usdc(
        self,
        from_wallet_id: str,
        to_address: str,
        amount: Decimal,
        reference_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Transfer USDC using Circle Programmable Wallets
        """
        if self.is_mock:
            # Mock transfer for development
            mock_transfer = {
                "id": f"mock_transfer_{int(datetime.now(timezone.utc).timestamp())}",
                "walletId": from_wallet_id,
                "sourceAddress": f"0x{from_wallet_id[:40].ljust(40, '0')}",
                "destinationAddress": to_address,
                "tokenId": self.usdc_contract_address,
                "amount": str(amount),
                "state": "COMPLETE",
                "txHash": f"0x{hash(f'{from_wallet_id}{to_address}{amount}')&0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff:064x}",
                "createDate": datetime.now(timezone.utc).isoformat(),
                "updateDate": datetime.now(timezone.utc).isoformat()
            }
            print(f"Mock: Transferred {amount} USDC from {from_wallet_id} to {to_address}")
            return mock_transfer
        
        try:
            # Real Circle API call
            transfer_data = {
                "idempotencyKey": reference_id or f"transfer_{int(datetime.now(timezone.utc).timestamp())}",
                "walletId": from_wallet_id,
                "destinationAddress": to_address,
                "tokenId": self.usdc_contract_address,
                "amount": str(amount),
                "fee": {
                    "type": "level",
                    "config": {
                        "feeLevel": "MEDIUM"
                    }
                }
            }
            
            response = await self._make_circle_request(
                "POST",
                "/w3s/user/transfers",
                data=transfer_data
            )
            
            if response and "data" in response:
                print(f"Circle: Initiated transfer of {amount} USDC")
                return response["data"]
            
            return None
            
        except Exception as e:
            print(f"Error transferring USDC: {e}")
            return None
    
    async def get_transfer_status(self, transfer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a transfer transaction
        """
        if self.is_mock:
            # Mock transfer status
            return {
                "id": transfer_id,
                "state": "COMPLETE",
                "txHash": f"0x{hash(transfer_id)&0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff:064x}",
                "updateDate": datetime.now(timezone.utc).isoformat()
            }
        
        try:
            response = await self._make_circle_request(
                "GET",
                f"/w3s/transfers/{transfer_id}"
            )
            
            return response.get("data", {}) if response else None
            
        except Exception as e:
            print(f"Error getting transfer status: {e}")
            return None
    
    async def validate_address(self, address: str, blockchain: str = "MATIC-AMOY") -> bool:
        """
        Validate a blockchain address using Circle's validation
        """
        if self.is_mock:
            # Basic validation for development
            return len(address) == 42 and address.startswith("0x")
        
        try:
            response = await self._make_circle_request(
                "POST",
                "/w3s/addressBook/validate",
                data={
                    "address": address,
                    "blockchain": blockchain
                }
            )
            
            return response.get("data", {}).get("isValid", False) if response else False
            
        except Exception as e:
            print(f"Error validating address: {e}")
            return False
    
    async def get_supported_tokens(self, blockchain: str = "MATIC-AMOY") -> List[Dict[str, Any]]:
        """
        Get list of supported tokens for a blockchain
        """
        if self.is_mock:
            # Mock supported tokens
            return [
                {
                    "id": self.usdc_contract_address,
                    "blockchain": blockchain,
                    "tokenAddress": self.usdc_contract_address,
                    "standard": "ERC20",
                    "name": "USD Coin",
                    "symbol": "USDC",
                    "decimals": 6,
                    "isNative": False
                }
            ]
        
        try:
            response = await self._make_circle_request(
                "GET",
                f"/w3s/tokens?blockchain={blockchain}"
            )
            
            return response.get("data", {}).get("tokens", []) if response else []
            
        except Exception as e:
            print(f"Error getting supported tokens: {e}")
            return []
    
    async def create_webhook_subscription(
        self, 
        endpoint_url: str, 
        subscription_details: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Create a webhook subscription for transaction notifications
        """
        if self.is_mock:
            # Mock webhook subscription
            return {
                "id": f"mock_webhook_{int(datetime.now(timezone.utc).timestamp())}",
                "url": endpoint_url,
                "subscriptionDetails": subscription_details,
                "status": "enabled",
                "createDate": datetime.now(timezone.utc).isoformat()
            }
        
        try:
            webhook_data = {
                "url": endpoint_url,
                "subscriptionDetails": subscription_details
            }
            
            response = await self._make_circle_request(
                "POST",
                "/w3s/webhooks",
                data=webhook_data
            )
            
            return response.get("data") if response else None
            
        except Exception as e:
            print(f"Error creating webhook subscription: {e}")
            return None
    
    async def _make_circle_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make authenticated request to Circle API
        """
        if self.is_mock:
            return None
        
        url = f"{self.testnet_base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {settings.circle_api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                if response.status_code == 200 or response.status_code == 201:
                    return response.json()
                else:
                    print(f"Circle API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Circle API request error: {e}")
            return None
    
    async def get_transaction_history(
        self, 
        wallet_id: str, 
        limit: int = 50,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get transaction history for a wallet
        """
        if self.is_mock:
            # Mock transaction history
            return {
                "transfers": [
                    {
                        "id": f"mock_tx_{i}",
                        "walletId": wallet_id,
                        "tokenId": self.usdc_contract_address,
                        "amount": f"{(i+1) * 10}.000000",
                        "state": "COMPLETE",
                        "txHash": f"0x{hash(f'{wallet_id}_{i}')&0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff:064x}",
                        "createDate": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat()
                    }
                    for i in range(min(limit, 10))
                ],
                "nextPageToken": None
            }
        
        try:
            params = {"walletId": wallet_id, "pageSize": str(limit)}
            if page_token:
                params["pageToken"] = page_token
            
            response = await self._make_circle_request(
                "GET",
                "/w3s/transfers",
                params=params
            )
            
            return response.get("data", {}) if response else {}
            
        except Exception as e:
            print(f"Error getting transaction history: {e}")
            return {}


# Global service instance
circle_service = CircleService()
