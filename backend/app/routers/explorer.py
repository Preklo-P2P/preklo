from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from decimal import Decimal

from ..database import get_db
from ..models import User, Transaction
from ..schemas import ApiResponse
from ..services.nodit_service import nodit_service
from ..services.aptos_service import aptos_service

router = APIRouter()


@router.get("/transaction/{tx_hash}")
async def get_transaction_details(tx_hash: str, db: Session = Depends(get_db)):
    """Get detailed transaction information from blockchain"""
    
    try:
        # First try to get from Nodit (if API key is available)
        transaction_data = None
        if nodit_service.api_key:
            transaction_data = await nodit_service.get_transaction_by_hash(tx_hash)
        
        # Fallback to direct Aptos node
        if not transaction_data:
            transaction_data = await aptos_service.get_transaction_by_hash(tx_hash)
        
        if not transaction_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        # Check if we have this transaction in our database
        db_transaction = db.query(Transaction).filter(
            Transaction.transaction_hash == tx_hash
        ).first()
        
        # Parse transaction details
        parsed_data = {
            "hash": tx_hash,
            "success": transaction_data.get("success", False),
            "version": transaction_data.get("version"),
            "gas_used": transaction_data.get("gas_used"),
            "gas_unit_price": transaction_data.get("gas_unit_price"),
            "sender": transaction_data.get("sender"),
            "sequence_number": transaction_data.get("sequence_number"),
            "timestamp": transaction_data.get("timestamp"),
            "type": transaction_data.get("type"),
            "payload": transaction_data.get("payload"),
            "events": transaction_data.get("events", []),
            "vm_status": transaction_data.get("vm_status"),
            "state_change_hash": transaction_data.get("state_change_hash"),
            "event_root_hash": transaction_data.get("event_root_hash"),
            "accumulator_root_hash": transaction_data.get("accumulator_root_hash"),
        }
        
        # Add our database information if available
        if db_transaction:
            parsed_data["preklo_data"] = {
                "id": str(db_transaction.id),
                "sender_id": str(db_transaction.sender_id) if db_transaction.sender_id else None,
                "recipient_id": str(db_transaction.recipient_id) if db_transaction.recipient_id else None,
                "amount": str(db_transaction.amount),
                "currency_type": db_transaction.currency_type,
                "description": db_transaction.description,
                "transaction_type": db_transaction.transaction_type,
                "status": db_transaction.status,
                "created_at": db_transaction.created_at.isoformat() if db_transaction.created_at else None
            }
        
        return parsed_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch transaction details: {str(e)}"
        )


@router.get("/account/{address}/transactions")
async def get_account_transactions(
    address: str,
    limit: int = Query(25, description="Number of transactions to return"),
    start: Optional[int] = Query(None, description="Starting version number"),
    coin_type: Optional[str] = Query(None, description="Filter by coin type"),
    db: Session = Depends(get_db)
):
    """Get transaction history for an account from blockchain"""
    
    try:
        # Try to get from Nodit first
        transactions_data = []
        if nodit_service.api_key:
            if coin_type:
                # Get coin transfers specifically
                transactions_data = await nodit_service.get_coin_transfers(
                    address, coin_type, limit
                )
            else:
                # Get all account transactions
                transactions_data = await nodit_service.get_account_transactions(
                    address, limit, start
                )
        
        # Fallback to direct Aptos node
        if not transactions_data:
            transactions_data = await aptos_service.get_account_transactions(
                address, limit, start
            )
        
        # Enrich with our database information
        enriched_transactions = []
        for tx_data in transactions_data:
            tx_hash = tx_data.get("hash")
            
            # Look up in our database
            db_transaction = None
            if tx_hash:
                db_transaction = db.query(Transaction).filter(
                    Transaction.transaction_hash == tx_hash
                ).first()
            
            enriched_tx = {
                "hash": tx_hash,
                "version": tx_data.get("version"),
                "timestamp": tx_data.get("timestamp"),
                "success": tx_data.get("success", False),
                "sender": tx_data.get("sender"),
                "gas_used": tx_data.get("gas_used"),
                "type": tx_data.get("type"),
                "payload": tx_data.get("payload"),
                "events": tx_data.get("events", [])
            }
            
            # Add AptosSend-specific data if available
            if db_transaction:
                enriched_tx["preklo_data"] = {
                    "id": str(db_transaction.id),
                    "amount": str(db_transaction.amount),
                    "currency_type": db_transaction.currency_type,
                    "description": db_transaction.description,
                    "transaction_type": db_transaction.transaction_type,
                    "recipient_address": db_transaction.recipient_address,
                    "sender_address": db_transaction.sender_address
                }
            
            enriched_transactions.append(enriched_tx)
        
        return {
            "address": address,
            "transactions": enriched_transactions,
            "count": len(enriched_transactions),
            "limit": limit,
            "start": start
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch account transactions: {str(e)}"
        )


@router.get("/account/{address}/balance-history")
async def get_balance_history(
    address: str,
    coin_type: str = Query(..., description="Coin type (e.g., 0x1::aptos_coin::AptosCoin)"),
    from_timestamp: Optional[int] = Query(None, description="Start timestamp"),
    to_timestamp: Optional[int] = Query(None, description="End timestamp"),
    limit: int = Query(100, description="Number of records to return")
):
    """Get balance history for an account"""
    
    try:
        if nodit_service.api_key:
            balance_history = await nodit_service.get_account_balance_history(
                address, coin_type, from_timestamp, to_timestamp, limit
            )
            
            return {
                "address": address,
                "coin_type": coin_type,
                "balance_history": balance_history,
                "count": len(balance_history)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Balance history requires Nodit API access"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch balance history: {str(e)}"
        )


@router.post("/sync/transaction/{tx_hash}", response_model=ApiResponse)
async def sync_transaction_with_blockchain(tx_hash: str, db: Session = Depends(get_db)):
    """Sync a specific transaction with blockchain data"""
    
    try:
        # Get transaction from database
        db_transaction = db.query(Transaction).filter(
            Transaction.transaction_hash == tx_hash
        ).first()
        
        if not db_transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found in database"
            )
        
        # Get latest data from blockchain
        blockchain_data = None
        if nodit_service.api_key:
            blockchain_data = await nodit_service.get_transaction_by_hash(tx_hash)
        
        if not blockchain_data:
            blockchain_data = await aptos_service.get_transaction_by_hash(tx_hash)
        
        if not blockchain_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found on blockchain"
            )
        
        # Update database with blockchain data
        updates_made = []
        
        if blockchain_data.get("success") is not None:
            new_status = "confirmed" if blockchain_data["success"] else "failed"
            if db_transaction.status != new_status:
                db_transaction.status = new_status
                updates_made.append(f"status: {new_status}")
        
        if blockchain_data.get("gas_used"):
            gas_fee = Decimal(blockchain_data["gas_used"]) / Decimal(10**8)  # Convert to APT
            if db_transaction.gas_fee != gas_fee:
                db_transaction.gas_fee = gas_fee
                updates_made.append(f"gas_fee: {gas_fee}")
        
        if blockchain_data.get("version"):
            block_height = int(blockchain_data["version"])
            if db_transaction.block_height != block_height:
                db_transaction.block_height = block_height
                updates_made.append(f"block_height: {block_height}")
        
        if updates_made:
            db.commit()
            db.refresh(db_transaction)
        
        return ApiResponse(
            success=True,
            message=f"Transaction synced successfully. Updates: {', '.join(updates_made) if updates_made else 'No updates needed'}",
            data={
                "transaction_id": str(db_transaction.id),
                "hash": tx_hash,
                "status": db_transaction.status,
                "gas_fee": str(db_transaction.gas_fee) if db_transaction.gas_fee else None,
                "block_height": db_transaction.block_height,
                "updates_made": updates_made
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync transaction: {str(e)}"
        )


@router.get("/stats/network")
async def get_network_stats():
    """Get network statistics"""
    
    try:
        # Get ledger info from Aptos node
        ledger_info = await aptos_service.client.ledger_info()
        
        stats = {
            "chain_id": ledger_info.get("chain_id"),
            "ledger_version": ledger_info.get("ledger_version"),
            "ledger_timestamp": ledger_info.get("ledger_timestamp"),
            "epoch": ledger_info.get("epoch"),
            "block_height": ledger_info.get("block_height"),
            "oldest_ledger_version": ledger_info.get("oldest_ledger_version"),
            "oldest_block_height": ledger_info.get("oldest_block_height"),
            "node_role": ledger_info.get("node_role"),
            "git_hash": ledger_info.get("git_hash")
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch network stats: {str(e)}"
        )
