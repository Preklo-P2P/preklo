"""
Fee Management Router - Handles fee collection, withdrawal, and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta

from ..database import get_db
from ..models import User, FeeCollection, FeeWithdrawal, Transaction
from ..schemas import ApiResponse
from ..services.fee_service import fee_service
from ..dependencies import require_authentication

router = APIRouter()


@router.get("/statistics", response_model=ApiResponse)
async def get_fee_statistics(
    days: int = Query(30, description="Number of days to look back"),
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Get fee collection statistics
    Note: In production, this should be restricted to admin users
    """
    try:
        stats = fee_service.get_fee_statistics(db, days)
        
        return ApiResponse(
            success=True,
            message=f"Fee statistics for the last {days} days",
            data=stats
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fee statistics: {str(e)}"
        )


@router.get("/collections", response_model=ApiResponse)
async def get_fee_collections(
    limit: int = Query(50, description="Number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    currency_type: Optional[str] = Query(None, description="Filter by currency type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Get fee collection records
    Note: In production, this should be restricted to admin users
    """
    try:
        query = db.query(FeeCollection)
        
        if currency_type:
            query = query.filter(FeeCollection.currency_type == currency_type.upper())
        
        if status:
            query = query.filter(FeeCollection.status == status)
        
        collections = query.order_by(FeeCollection.created_at.desc()).offset(offset).limit(limit).all()
        
        collection_data = []
        for collection in collections:
            collection_data.append({
                "id": str(collection.id),
                "transaction_id": str(collection.transaction_id),
                "currency_type": collection.currency_type,
                "amount": str(collection.amount),
                "fee_percentage": str(collection.fee_percentage),
                "transaction_type": collection.transaction_type,
                "revenue_wallet_address": collection.revenue_wallet_address,
                "blockchain_tx_hash": collection.blockchain_tx_hash,
                "status": collection.status,
                "collected_at": collection.collected_at.isoformat() if collection.collected_at else None,
                "created_at": collection.created_at.isoformat()
            })
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(collection_data)} fee collections",
            data={
                "collections": collection_data,
                "total_count": query.count(),
                "limit": limit,
                "offset": offset
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fee collections: {str(e)}"
        )


@router.get("/withdrawals", response_model=ApiResponse)
async def get_fee_withdrawals(
    limit: int = Query(50, description="Number of records to return"),
    offset: int = Query(0, description="Number of records to skip"),
    currency_type: Optional[str] = Query(None, description="Filter by currency type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Get fee withdrawal records
    Note: In production, this should be restricted to admin users
    """
    try:
        query = db.query(FeeWithdrawal)
        
        if currency_type:
            query = query.filter(FeeWithdrawal.currency_type == currency_type.upper())
        
        if status:
            query = query.filter(FeeWithdrawal.status == status)
        
        withdrawals = query.order_by(FeeWithdrawal.created_at.desc()).offset(offset).limit(limit).all()
        
        withdrawal_data = []
        for withdrawal in withdrawals:
            withdrawal_data.append({
                "id": str(withdrawal.id),
                "currency_type": withdrawal.currency_type,
                "amount": str(withdrawal.amount),
                "destination_address": withdrawal.destination_address,
                "blockchain_tx_hash": withdrawal.blockchain_tx_hash,
                "status": withdrawal.status,
                "withdrawal_reason": withdrawal.withdrawal_reason,
                "processed_at": withdrawal.processed_at.isoformat() if withdrawal.processed_at else None,
                "created_at": withdrawal.created_at.isoformat()
            })
        
        return ApiResponse(
            success=True,
            message=f"Retrieved {len(withdrawal_data)} fee withdrawals",
            data={
                "withdrawals": withdrawal_data,
                "total_count": query.count(),
                "limit": limit,
                "offset": offset
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fee withdrawals: {str(e)}"
        )


@router.post("/withdraw", response_model=ApiResponse)
async def withdraw_fees(
    currency_type: str,
    amount: str,
    destination_address: str,
    withdrawal_reason: str = "revenue_withdrawal",
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Withdraw collected fees to a destination address
    Note: In production, this should be restricted to admin users with proper authorization
    """
    try:
        # Validate inputs
        if not currency_type or not amount or not destination_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="currency_type, amount, and destination_address are required"
            )
        
        try:
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                raise ValueError("Amount must be greater than 0")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid amount: {str(e)}"
            )
        
        # Validate currency type
        if currency_type.upper() not in ["APT", "USDC"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported currency type. Supported: APT, USDC"
            )
        
        # Execute withdrawal
        tx_hash = await fee_service.withdraw_collected_fees(
            db,
            currency_type.upper(),
            amount_decimal,
            destination_address,
            withdrawal_reason
        )
        
        if tx_hash:
            return ApiResponse(
                success=True,
                message=f"Successfully withdrew {amount} {currency_type.upper()} to {destination_address}",
                data={
                    "transaction_hash": tx_hash,
                    "currency_type": currency_type.upper(),
                    "amount": str(amount_decimal),
                    "destination_address": destination_address,
                    "withdrawal_reason": withdrawal_reason,
                    "status": "completed"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process fee withdrawal"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to withdraw fees: {str(e)}"
        )


@router.get("/config", response_model=ApiResponse)
async def get_fee_configuration(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Get current fee configuration
    """
    try:
        config = {
            "fee_percentages": {
                "p2p_domestic": fee_service.get_fee_percentage("p2p_domestic"),
                "p2p_cross_border": fee_service.get_fee_percentage("p2p_cross_border"),
                "card_present": fee_service.get_fee_percentage("card_present"),
                "card_not_present": fee_service.get_fee_percentage("card_not_present"),
                "merchant": fee_service.get_fee_percentage("merchant"),
            },
            "revenue_wallet": fee_service.revenue_wallet,
            "fee_collection_enabled": fee_service.enable_fee_collection,
            "supported_currencies": ["APT", "USDC"]
        }
        
        return ApiResponse(
            success=True,
            message="Fee configuration retrieved successfully",
            data=config
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fee configuration: {str(e)}"
        )


@router.get("/calculate", response_model=ApiResponse)
async def calculate_fee(
    amount: str,
    transaction_type: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Calculate fee for a given amount and transaction type
    """
    try:
        try:
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                raise ValueError("Amount must be greater than 0")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid amount: {str(e)}"
            )
        
        # Validate transaction type
        valid_types = ["p2p_domestic", "p2p_cross_border", "card_present", "card_not_present", "merchant"]
        if transaction_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid transaction type. Valid types: {', '.join(valid_types)}"
            )
        
        fee_amount, net_amount = fee_service.calculate_fee(amount_decimal, transaction_type)
        fee_percentage = fee_service.get_fee_percentage(transaction_type)
        
        return ApiResponse(
            success=True,
            message="Fee calculated successfully",
            data={
                "original_amount": str(amount_decimal),
                "fee_amount": str(fee_amount),
                "net_amount": str(net_amount),
                "fee_percentage": fee_percentage,
                "transaction_type": transaction_type,
                "fee_collection_enabled": fee_service.enable_fee_collection
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate fee: {str(e)}"
        )
