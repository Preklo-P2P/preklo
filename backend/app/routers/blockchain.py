from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..services.aptos_service import aptos_service
from ..dependencies import require_authentication
from ..models import User
from ..schemas import ApiResponse

router = APIRouter()


@router.get("/health", response_model=ApiResponse)
async def get_blockchain_health():
    """
    Get blockchain connection health status
    """
    try:
        status_info = await aptos_service.get_connection_status()
        
        return ApiResponse(
            success=True,
            message="Blockchain health check completed",
            data=status_info
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Blockchain health check failed: {str(e)}",
            data=None
        )


@router.get("/network-info", response_model=ApiResponse)
async def get_network_info():
    """
    Get current blockchain network information
    """
    try:
        network_info = await aptos_service.get_network_info()
        
        return ApiResponse(
            success=True,
            message="Network information retrieved",
            data=network_info
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get network info: {str(e)}",
            data=None
        )


@router.get("/gas-estimate", response_model=ApiResponse)
async def estimate_gas_fee(transaction_type: str = "transfer"):
    """
    Estimate gas fee for a transaction
    """
    try:
        gas_fee = await aptos_service.estimate_gas_fee(transaction_type)
        
        return ApiResponse(
            success=True,
            message="Gas fee estimated",
            data={
                "gas_fee": str(gas_fee),
                "currency": "APT",
                "transaction_type": transaction_type
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to estimate gas fee: {str(e)}",
            data=None
        )


@router.get("/transaction/{tx_hash}/status", response_model=ApiResponse)
async def get_transaction_status(tx_hash: str):
    """
    Get transaction status by hash
    """
    try:
        status_info = await aptos_service.get_transaction_status(tx_hash)
        
        return ApiResponse(
            success=True,
            message="Transaction status retrieved",
            data=status_info
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get transaction status: {str(e)}",
            data=None
        )


@router.get("/transaction/{tx_hash}/monitor", response_model=ApiResponse)
async def monitor_transaction(tx_hash: str, timeout: int = 300):
    """
    Monitor a transaction until completion or timeout
    """
    try:
        status_info = await aptos_service.monitor_transaction(tx_hash, timeout)
        
        return ApiResponse(
            success=True,
            message="Transaction monitoring completed",
            data=status_info
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to monitor transaction: {str(e)}",
            data=None
        )


@router.get("/pending-transactions", response_model=ApiResponse)
async def get_pending_transactions(
    current_user: User = Depends(require_authentication)
):
    """
    Get all pending transactions being monitored
    """
    try:
        pending_info = await aptos_service.get_pending_transactions()
        
        return ApiResponse(
            success=True,
            message="Pending transactions retrieved",
            data=pending_info
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get pending transactions: {str(e)}",
            data=None
        )


@router.get("/balance/{address}", response_model=ApiResponse)
async def get_account_balance(address: str, currency: str = "APT"):
    """
    Get account balance for specified currency
    """
    try:
        balance = await aptos_service.get_account_balance(address, currency)
        
        return ApiResponse(
            success=True,
            message="Account balance retrieved",
            data={
                "address": address,
                "currency": currency,
                "balance": str(balance)
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get account balance: {str(e)}",
            data=None
        )


@router.get("/transactions/{address}", response_model=ApiResponse)
async def get_account_transactions(
    address: str,
    limit: int = 25,
    start: int = None
):
    """
    Get account transaction history
    """
    try:
        transactions = await aptos_service.get_account_transactions(
            address, limit, start
        )
        
        return ApiResponse(
            success=True,
            message="Account transactions retrieved",
            data={
                "address": address,
                "transactions": transactions,
                "count": len(transactions)
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get account transactions: {str(e)}",
            data=None
        )
