"""
Circle Integration Routes
Handles Circle USDC operations, wallet management, and compliance features
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from decimal import Decimal

from ..database import get_db
from ..models import User, Transaction
from ..schemas import TransactionCreate
from ..services.circle_service import circle_service
from ..dependencies import require_authentication, rate_limit


router = APIRouter()


@router.post("/wallet/create")
async def create_circle_wallet(
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=3600))  # 5 per hour
):
    """
    Create a Circle Programmable Wallet for the current user
    """
    try:
        wallet_data = await circle_service.create_programmable_wallet(
            str(current_user.id),
            blockchain="MATIC-AMOY"  # Polygon testnet
        )
        
        if not wallet_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create Circle wallet"
            )
        
        return {
            "status": "success",
            "message": "Circle wallet created successfully",
            "data": {
                "wallet_id": wallet_data.get("walletId"),
                "address": wallet_data.get("address"),
                "blockchain": wallet_data.get("blockchain"),
                "state": wallet_data.get("state"),
                "account_type": wallet_data.get("accountType"),
                "created_at": wallet_data.get("createDate")
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating Circle wallet: {str(e)}"
        )


@router.get("/wallet/{wallet_id}/balance")
async def get_circle_wallet_balance(
    wallet_id: str,
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=100, window_seconds=3600))
):
    """
    Get Circle wallet balance for USDC and other tokens
    """
    try:
        balance_data = await circle_service.get_wallet_balance(wallet_id)
        
        return {
            "status": "success",
            "message": "Wallet balance retrieved successfully",
            "data": balance_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving wallet balance: {str(e)}"
        )


@router.post("/transfer/usdc")
async def transfer_circle_usdc(
    transfer_data: Dict[str, Any],
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db),
    _rate_limit: bool = Depends(rate_limit(max_requests=50, window_seconds=3600))
):
    """
    Transfer USDC using Circle Programmable Wallets
    """
    try:
        from_wallet_id = transfer_data.get("from_wallet_id")
        to_address = transfer_data.get("to_address")
        amount = Decimal(str(transfer_data.get("amount")))
        reference_id = transfer_data.get("reference_id")
        
        if not all([from_wallet_id, to_address, amount]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: from_wallet_id, to_address, amount"
            )
        
        # Validate address
        is_valid_address = await circle_service.validate_address(to_address)
        if not is_valid_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid recipient address"
            )
        
        # Initiate Circle transfer
        transfer_result = await circle_service.transfer_usdc(
            from_wallet_id=from_wallet_id,
            to_address=to_address,
            amount=amount,
            reference_id=reference_id
        )
        
        if not transfer_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate USDC transfer"
            )
        
        # Record transaction in database
        db_transaction = Transaction(
            sender_id=current_user.id,
            recipient_id=current_user.id,  # Will be updated when recipient is identified
            amount=amount,
            currency_type="USDC",
            status="pending",
            type="circle_transfer",
            transaction_hash=transfer_result.get("txHash")
        )
        
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        
        return {
            "status": "success",
            "message": "USDC transfer initiated successfully",
            "data": {
                "transfer_id": transfer_result.get("id"),
                "transaction_id": str(db_transaction.id),
                "amount": str(amount),
                "currency": "USDC",
                "status": transfer_result.get("state"),
                "tx_hash": transfer_result.get("txHash"),
                "created_at": transfer_result.get("createDate")
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid amount format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error transferring USDC: {str(e)}"
        )


@router.get("/transfer/{transfer_id}/status")
async def get_circle_transfer_status(
    transfer_id: str,
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=200, window_seconds=3600))
):
    """
    Get the status of a Circle transfer
    """
    try:
        transfer_status = await circle_service.get_transfer_status(transfer_id)
        
        if not transfer_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transfer not found"
            )
        
        return {
            "status": "success",
            "message": "Transfer status retrieved successfully",
            "data": {
                "transfer_id": transfer_status.get("id"),
                "state": transfer_status.get("state"),
                "tx_hash": transfer_status.get("txHash"),
                "updated_at": transfer_status.get("updateDate")
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving transfer status: {str(e)}"
        )


@router.get("/tokens/supported")
async def get_supported_tokens(
    blockchain: str = "MATIC-AMOY",
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=20, window_seconds=3600))
):
    """
    Get list of supported tokens for a blockchain
    """
    try:
        supported_tokens = await circle_service.get_supported_tokens(blockchain)
        
        return {
            "status": "success",
            "message": "Supported tokens retrieved successfully",
            "data": {
                "blockchain": blockchain,
                "tokens": supported_tokens
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving supported tokens: {str(e)}"
        )


@router.get("/wallet/{wallet_id}/history")
async def get_circle_wallet_history(
    wallet_id: str,
    limit: int = 50,
    page_token: Optional[str] = None,
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=100, window_seconds=3600))
):
    """
    Get transaction history for a Circle wallet
    """
    try:
        if limit > 100:
            limit = 100  # Cap at 100 for performance
        
        history_data = await circle_service.get_transaction_history(
            wallet_id=wallet_id,
            limit=limit,
            page_token=page_token
        )
        
        return {
            "status": "success",
            "message": "Wallet history retrieved successfully",
            "data": {
                "wallet_id": wallet_id,
                "transfers": history_data.get("transfers", []),
                "next_page_token": history_data.get("nextPageToken")
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving wallet history: {str(e)}"
        )


@router.post("/address/validate")
async def validate_blockchain_address(
    address_data: Dict[str, str],
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=100, window_seconds=3600))
):
    """
    Validate a blockchain address
    """
    try:
        address = address_data.get("address")
        blockchain = address_data.get("blockchain", "MATIC-AMOY")
        
        if not address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Address is required"
            )
        
        is_valid = await circle_service.validate_address(address, blockchain)
        
        return {
            "status": "success",
            "message": "Address validation completed",
            "data": {
                "address": address,
                "blockchain": blockchain,
                "is_valid": is_valid
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating address: {str(e)}"
        )


@router.post("/webhook/create")
async def create_circle_webhook(
    webhook_data: Dict[str, Any],
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=5, window_seconds=3600))  # 5 per hour
):
    """
    Create a webhook subscription for Circle events
    """
    try:
        endpoint_url = webhook_data.get("endpoint_url")
        subscription_details = webhook_data.get("subscription_details", {})
        
        if not endpoint_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Endpoint URL is required"
            )
        
        webhook_result = await circle_service.create_webhook_subscription(
            endpoint_url=endpoint_url,
            subscription_details=subscription_details
        )
        
        if not webhook_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create webhook subscription"
            )
        
        return {
            "status": "success",
            "message": "Webhook subscription created successfully",
            "data": webhook_result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating webhook: {str(e)}"
        )
