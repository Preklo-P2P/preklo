"""
Unlimit Card Issuing Service
Handles card creation, authorization, and transaction processing with Unlimit APIs
"""

import asyncio
import hashlib
import hmac
import json
import secrets
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, timezone
import httpx
from sqlalchemy.orm import Session

from ..config import settings
from ..models import User, UnlimitCard, UnlimitTransaction, Balance
from ..schemas import (
    CardCreationRequest, CardCreationResponse, 
    CardAuthorizationRequest, CardAuthorizationResponse,
    UnlimitCard as UnlimitCardSchema
)


class UnlimitService:
    """
    Unlimit Card Issuing API integration service
    Based on Unlimit sandbox integration documentation
    """
    
    def __init__(self):
        self.api_key = settings.unlimit_api_key
        self.secret_key = settings.unlimit_secret_key
        self.base_url = settings.unlimit_base_url
        self.webhook_secret = settings.unlimit_webhook_secret
        self.environment = settings.unlimit_environment
        
        # Default headers for API requests
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-API-Version": "2024-01"
        }
        
        # Mock mode if credentials not set
        self.is_mock = not (self.api_key and self.secret_key)
        if self.is_mock:
            print("WARNING: Unlimit credentials not set, using mock mode")
    
    def _generate_signature(self, payload: str, timestamp: str) -> str:
        """
        Generate HMAC signature for API requests
        """
        if not self.secret_key:
            return "mock_signature"
        
        message = f"{timestamp}{payload}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def _verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature from Unlimit
        """
        if self.is_mock:
            return True
        
        if not self.webhook_secret:
            print("WARNING: Webhook secret not configured")
            return False
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def _make_api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Make authenticated request to Unlimit API
        """
        if self.is_mock:
            return await self._mock_api_response(method, endpoint, data)
        
        url = f"{self.base_url}{endpoint}"
        timestamp = str(int(datetime.now(timezone.utc).timestamp()))
        
        # Add timestamp and signature to headers
        headers = self.headers.copy()
        headers["X-Timestamp"] = timestamp
        
        if data:
            payload = json.dumps(data, sort_keys=True)
            headers["X-Signature"] = self._generate_signature(payload, timestamp)
        else:
            payload = ""
            headers["X-Signature"] = self._generate_signature("", timestamp)
        
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
                
                if response.status_code in [200, 201]:
                    return response.json()
                else:
                    print(f"Unlimit API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Unlimit API request error: {e}")
            return None
    
    async def _mock_api_response(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Mock API responses for development/testing
        """
        if "users" in endpoint and method == "POST":
            return {
                "success": True,
                "data": {
                    "user_id": f"unlimit_user_{secrets.token_hex(8)}",
                    "status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            }
        
        elif "cards" in endpoint and method == "POST":
            return {
                "success": True,
                "data": {
                    "card_id": f"unlimit_card_{secrets.token_hex(8)}",
                    "card_type": data.get("card_type", "virtual"),
                    "status": "active",
                    "last_four": "1234",
                    "expiry_month": 12,
                    "expiry_year": 2027,
                    "currency": data.get("currency", "USD"),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            }
        
        elif "authorize" in endpoint:
            # Mock authorization - approve if amount < $1000
            amount = data.get("amount", 0)
            return {
                "success": True,
                "approved": float(amount) < 1000,
                "auth_code": f"AUTH{secrets.token_hex(4).upper()}" if float(amount) < 1000 else None,
                "decline_reason": "Insufficient funds" if float(amount) >= 1000 else None
            }
        
        return {"success": True, "data": {}}
    
    async def create_user(self, user: User) -> Optional[str]:
        """
        Create a user in Unlimit system
        Returns Unlimit user ID
        """
        user_data = {
            "external_user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name or user.username,
            "username": user.username,
            "phone": None,  # Add phone field to User model if needed
            "address": {
                "country": "US",  # Default, should be configurable
                "city": None,
                "state": None,
                "postal_code": None,
                "address_line_1": None
            },
            "kyc_status": "pending"
        }
        
        response = await self._make_api_request("POST", "/users", user_data)
        
        if response and response.get("success"):
            return response["data"]["user_id"]
        
        return None
    
    async def create_card(
        self,
        user: User,
        card_request: CardCreationRequest,
        db: Session
    ) -> Optional[UnlimitCardSchema]:
        """
        Create a new card for a user
        """
        # First ensure user exists in Unlimit system
        unlimit_user_id = await self.create_user(user)
        if not unlimit_user_id:
            print(f"Failed to create Unlimit user for {user.id}")
            return None
        
        # Create card request
        card_data = {
            "user_id": unlimit_user_id,
            "card_type": card_request.card_type,
            "currency": card_request.currency,
            "program": "default",  # Card program from Unlimit
            "spending_limits": card_request.spending_limits or {
                "daily_limit": 1000,
                "monthly_limit": 5000,
                "per_transaction_limit": 500
            },
            "metadata": {
                "preklo_user_id": str(user.id),
                "region": card_request.region
            }
        }
        
        response = await self._make_api_request("POST", "/cards", card_data)
        
        if response and response.get("success"):
            card_data = response["data"]
            
            # Save card to database
            db_card = UnlimitCard(
                user_id=user.id,
                unlimit_card_id=card_data["card_id"],
                unlimit_user_id=unlimit_user_id,
                card_type=card_request.card_type,
                card_status="active",
                last_four=card_data.get("last_four"),
                expiry_month=card_data.get("expiry_month"),
                expiry_year=card_data.get("expiry_year"),
                currency=card_request.currency,
                region=card_request.region,
                spending_limits=json.dumps(card_data.get("spending_limits", {}))
            )
            
            db.add(db_card)
            db.commit()
            db.refresh(db_card)
            
            return UnlimitCardSchema.from_orm(db_card)
        
        return None
    
    async def authorize_transaction(
        self,
        auth_request: CardAuthorizationRequest,
        db: Session
    ) -> CardAuthorizationResponse:
        """
        Process card authorization request from Unlimit webhook
        """
        # Find the card and user
        card = db.query(UnlimitCard).filter(
            UnlimitCard.unlimit_card_id == auth_request.card_id
        ).first()
        
        if not card:
            return CardAuthorizationResponse(
                approved=False,
                decline_reason="Card not found"
            )
        
        user = db.query(User).filter(User.id == card.user_id).first()
        if not user:
            return CardAuthorizationResponse(
                approved=False,
                decline_reason="User not found"
            )
        
        # Check user's wallet balance
        user_balance = db.query(Balance).filter(
            Balance.user_id == user.id,
            Balance.currency_type == "USDC"  # Primary spending currency
        ).first()
        
        if not user_balance or user_balance.balance < auth_request.amount:
            return CardAuthorizationResponse(
                approved=False,
                decline_reason="Insufficient funds"
            )
        
        # Approve transaction and reserve balance
        auth_code = f"AUTH{secrets.token_hex(4).upper()}"
        
        # Create transaction record
        db_transaction = UnlimitTransaction(
            card_id=card.id,
            user_id=user.id,
            unlimit_transaction_id=auth_request.transaction_id,
            transaction_type="authorization",
            amount=auth_request.amount,
            currency=auth_request.currency,
            merchant_name=auth_request.merchant_name,
            merchant_category=auth_request.merchant_category,
            transaction_status="approved",
            auth_code=auth_code,
            wallet_balance_before=user_balance.balance
        )
        
        # Reserve balance (don't deduct yet, wait for settlement)
        # In production, you might want a separate "reserved" balance field
        user_balance.balance -= auth_request.amount
        db_transaction.wallet_balance_after = user_balance.balance
        
        db.add(db_transaction)
        db.commit()
        
        return CardAuthorizationResponse(
            approved=True,
            auth_code=auth_code
        )
    
    async def process_settlement(
        self,
        transaction_id: str,
        settlement_amount: Decimal,
        db: Session
    ) -> bool:
        """
        Process transaction settlement
        """
        transaction = db.query(UnlimitTransaction).filter(
            UnlimitTransaction.unlimit_transaction_id == transaction_id
        ).first()
        
        if not transaction:
            print(f"Transaction {transaction_id} not found for settlement")
            return False
        
        # Update transaction status
        transaction.transaction_status = "settled"
        transaction.amount = settlement_amount  # Final settled amount
        
        # The balance was already deducted during authorization
        # If settlement amount differs, adjust the balance
        if settlement_amount != transaction.amount:
            user_balance = db.query(Balance).filter(
                Balance.user_id == transaction.user_id,
                Balance.currency_type == "USDC"
            ).first()
            
            if user_balance:
                difference = transaction.amount - settlement_amount
                user_balance.balance += difference  # Refund or additional charge
        
        db.commit()
        return True
    
    async def get_card_transactions(
        self,
        card_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get transaction history for a card
        """
        response = await self._make_api_request(
            "GET", 
            f"/cards/{card_id}/transactions",
            params={"limit": str(limit)}
        )
        
        if response and response.get("success"):
            return response.get("data", {}).get("transactions", [])
        
        return []
    
    async def update_card_status(
        self,
        card_id: str,
        status: str,
        db: Session
    ) -> bool:
        """
        Update card status (active, inactive, blocked)
        """
        # Update in Unlimit
        response = await self._make_api_request(
            "PUT",
            f"/cards/{card_id}/status",
            {"status": status}
        )
        
        if response and response.get("success"):
            # Update local database
            card = db.query(UnlimitCard).filter(
                UnlimitCard.unlimit_card_id == card_id
            ).first()
            
            if card:
                card.card_status = status
                db.commit()
                return True
        
        return False
    
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """
        Verify incoming webhook signature
        """
        return self._verify_webhook_signature(payload, signature)


# Global service instance
unlimit_service = UnlimitService()
