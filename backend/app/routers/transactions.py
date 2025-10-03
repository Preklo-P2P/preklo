from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from ..database import get_db
from ..models import User, Transaction, Balance
from ..schemas import (
    TransferRequest, 
    Transaction as TransactionSchema, 
    TransactionWithUsers,
    TransactionResponse,
    ApiResponse,
    CustodialTransactionRequest,
    CustodialTransactionResponse,
    PetraTransactionRequest
)
from ..services.aptos_service import aptos_service
from ..services.wallet_service import wallet_service
from ..services.auth_service import auth_service
from ..services.fee_service import fee_service
from ..dependencies import require_authentication

router = APIRouter()


@router.post("/transfer", response_model=TransactionResponse)
async def create_transfer(
    transfer: TransferRequest,
    sender_private_key: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Create a new transfer transaction"""
    
    # Determine if recipient is username or address
    recipient_user = None
    recipient_address = transfer.recipient
    
    # Check if recipient is a username (starts with @)
    if transfer.recipient.startswith("@"):
        username = transfer.recipient[1:]  # Remove @ prefix
        recipient_user = db.query(User).filter(User.username == username).first()
        if not recipient_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipient username not found"
            )
        recipient_address = recipient_user.wallet_address
    else:
        # Try to find user by wallet address
        recipient_user = db.query(User).filter(User.wallet_address == transfer.recipient).first()
        if not recipient_user:
            # Create a temporary user record for unknown addresses
            # This allows transfers to any valid Aptos address
            pass
    
    # Get sender from private key (in a real app, this would come from authentication)
    # For now, we'll need to derive the address from the private key
    try:
        from aptos_sdk.account import Account
        sender_account = Account.load_key(sender_private_key)
        sender_address = str(sender_account.address())
        
        # Find sender user
        sender_user = db.query(User).filter(User.wallet_address == sender_address).first()
        if not sender_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Sender not found in database"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid sender private key"
        )
    
    # Validate amount
    if transfer.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount must be greater than 0"
        )
    
    # Check sender balance
    sender_balance = db.query(Balance).filter(
        and_(
            Balance.user_id == sender_user.id,
            Balance.currency_type == transfer.currency_type
        )
    ).first()
    
    if not sender_balance or sender_balance.balance < transfer.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    try:
        # Execute blockchain transaction
        if transfer.currency_type == "APT":
            tx_hash = await aptos_service.transfer_apt(
                sender_private_key,
                recipient_address,
                transfer.amount
            )
        elif transfer.currency_type == "USDC":
            tx_hash = await aptos_service.transfer_usdc(
                sender_private_key,
                recipient_address,
                transfer.amount
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported currency type"
            )
        
        if not tx_hash:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to execute blockchain transaction"
            )
        
        # Create transaction record
        db_transaction = Transaction(
            transaction_hash=tx_hash,
            sender_id=sender_user.id,
            recipient_id=recipient_user.id if recipient_user else None,
            sender_address=sender_address,
            recipient_address=recipient_address,
            amount=transfer.amount,
            currency_type=transfer.currency_type,
            transaction_type="transfer",
            status="confirmed",
            description=transfer.description
        )
        
        db.add(db_transaction)
        
        # Update balances
        sender_balance.balance -= transfer.amount
        
        if recipient_user:
            recipient_balance = db.query(Balance).filter(
                and_(
                    Balance.user_id == recipient_user.id,
                    Balance.currency_type == transfer.currency_type
                )
            ).first()
            
            if recipient_balance:
                recipient_balance.balance += transfer.amount
            else:
                # Create balance record for recipient
                recipient_balance = Balance(
                    user_id=recipient_user.id,
                    currency_type=transfer.currency_type,
                    balance=transfer.amount
                )
                db.add(recipient_balance)
        
        db.commit()
        db.refresh(db_transaction)
        
        return TransactionResponse(
            success=True,
            message="Transfer completed successfully",
            data=db_transaction
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transfer failed: {str(e)}"
        )


@router.get("/", response_model=List[TransactionSchema])
async def get_transactions(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    wallet_address: Optional[str] = Query(None, description="Filter by wallet address"),
    currency_type: Optional[str] = Query(None, description="Filter by currency type"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(25, description="Number of transactions to return"),
    offset: int = Query(0, description="Number of transactions to skip"),
    db: Session = Depends(get_db)
):
    """Get transactions with optional filters"""
    
    # Join with User table to get sender and recipient information
    from sqlalchemy.orm import aliased
    SenderUser = aliased(User)
    RecipientUser = aliased(User)
    
    query = db.query(Transaction, SenderUser, RecipientUser).outerjoin(
        SenderUser, Transaction.sender_id == SenderUser.id
    ).outerjoin(
        RecipientUser, Transaction.recipient_id == RecipientUser.id
    )
    
    # Apply filters
    if user_id:
        query = query.filter(
            or_(Transaction.sender_id == user_id, Transaction.recipient_id == user_id)
        )
    
    if wallet_address:
        query = query.filter(
            or_(
                Transaction.sender_address == wallet_address,
                Transaction.recipient_address == wallet_address
            )
        )
    
    if currency_type:
        query = query.filter(Transaction.currency_type == currency_type)
    
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    
    if status:
        query = query.filter(Transaction.status == status)
    
    # Order by creation date (newest first) and apply pagination
    results = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
    
    # Transform results to include user information
    transactions = []
    for result in results:
        transaction = result[0]  # Transaction object
        sender_user = result[1]  # Sender User object
        recipient_user = result[2]  # Recipient User object
        
        # Create transaction dict with user information
        transaction_dict = {
            "id": transaction.id,
            "transaction_hash": transaction.transaction_hash,
            "sender_id": transaction.sender_id,
            "recipient_id": transaction.recipient_id,
            "sender_address": transaction.sender_address,
            "recipient_address": transaction.recipient_address,
            "amount": transaction.amount,
            "currency_type": transaction.currency_type,
            "transaction_type": transaction.transaction_type,
            "status": transaction.status,
            "description": transaction.description,
            "gas_fee": transaction.gas_fee,
            "block_height": transaction.block_height,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
            "sender": {
                "id": sender_user.id if sender_user else None,
                "username": sender_user.username if sender_user else None,
                "wallet_address": sender_user.wallet_address if sender_user else None,
                "full_name": sender_user.full_name if sender_user else None,
            } if sender_user else None,
            "recipient": {
                "id": recipient_user.id if recipient_user else None,
                "username": recipient_user.username if recipient_user else None,
                "wallet_address": recipient_user.wallet_address if recipient_user else None,
                "full_name": recipient_user.full_name if recipient_user else None,
            } if recipient_user else None,
        }
        transactions.append(transaction_dict)
    
    return transactions


@router.post("/record", response_model=ApiResponse)
async def record_transaction(
    transaction_data: dict,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Record a completed wallet-signed transaction"""
    
    try:
        # Find recipient user if they exist
        recipient_user = db.query(User).filter(
            User.wallet_address == transaction_data.get('recipient_address')
        ).first()
        
        # Create transaction record
        db_transaction = Transaction(
            transaction_hash=transaction_data.get('transaction_hash'),
            sender_id=current_user.id,
            recipient_id=recipient_user.id if recipient_user else current_user.id,  # Fallback to sender if recipient not found
            sender_address=current_user.wallet_address,
            recipient_address=transaction_data.get('recipient_address'),
            amount=Decimal(str(transaction_data.get('amount', 0))),
            currency_type=transaction_data.get('currency_type', 'APT'),
            transaction_type=transaction_data.get('transaction_type', 'transfer'),
            status='confirmed',  # Wallet-signed transactions are confirmed
            description=transaction_data.get('description', '')
        )
        
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        
        return ApiResponse(
            success=True,
            message="Transaction recorded successfully",
            data={"transaction_id": str(db_transaction.id)}
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record transaction: {str(e)}"
        )


@router.get("/{transaction_id}", response_model=TransactionSchema)
async def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Get transaction by ID"""
    
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction


@router.get("/hash/{tx_hash}", response_model=TransactionSchema)
async def get_transaction_by_hash(tx_hash: str, db: Session = Depends(get_db)):
    """Get transaction by blockchain hash"""
    
    transaction = db.query(Transaction).filter(Transaction.transaction_hash == tx_hash).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    return transaction


@router.post("/{transaction_id}/sync", response_model=ApiResponse)
async def sync_transaction_status(transaction_id: str, db: Session = Depends(get_db)):
    """Sync transaction status with blockchain"""
    
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    try:
        # Get transaction details from blockchain
        blockchain_tx = await aptos_service.get_transaction_by_hash(transaction.transaction_hash)
        
        if blockchain_tx:
            # Update transaction status based on blockchain data
            if blockchain_tx.get("success"):
                transaction.status = "confirmed"
                if "gas_used" in blockchain_tx:
                    # Convert gas to proper units
                    gas_fee = Decimal(blockchain_tx["gas_used"]) / Decimal(10**8)
                    transaction.gas_fee = gas_fee
                
                if "version" in blockchain_tx:
                    transaction.block_height = int(blockchain_tx["version"])
            else:
                transaction.status = "failed"
            
            db.commit()
            db.refresh(transaction)
            
            return ApiResponse(
                success=True,
                message="Transaction status synced successfully",
                data={
                    "status": transaction.status,
                    "gas_fee": str(transaction.gas_fee) if transaction.gas_fee else None,
                    "block_height": transaction.block_height
                }
            )
        else:
            return ApiResponse(
                success=False,
                message="Transaction not found on blockchain",
                data=None
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync transaction: {str(e)}"
        )


@router.get("/user/{user_id}/history", response_model=List[TransactionWithUsers])
async def get_user_transaction_history(
    user_id: str,
    currency_type: Optional[str] = Query(None),
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get transaction history for a specific user"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Join with User table to get sender and recipient information
    from sqlalchemy.orm import aliased
    SenderUser = aliased(User)
    RecipientUser = aliased(User)
    
    query = db.query(Transaction, SenderUser, RecipientUser).outerjoin(
        SenderUser, Transaction.sender_id == SenderUser.id
    ).outerjoin(
        RecipientUser, Transaction.recipient_id == RecipientUser.id
    ).filter(
        or_(Transaction.sender_id == user_id, Transaction.recipient_id == user_id)
    )
    
    if currency_type:
        query = query.filter(Transaction.currency_type == currency_type)
    
    results = query.order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()
    
    # Transform results to include user information
    transactions = []
    for result in results:
        transaction = result[0]  # Transaction object
        sender_user = result[1]  # Sender User object
        recipient_user = result[2]  # Recipient User object
        
        # Create transaction dict with user information
        transaction_dict = {
            "id": transaction.id,
            "transaction_hash": transaction.transaction_hash,
            "sender_id": transaction.sender_id,
            "recipient_id": transaction.recipient_id,
            "sender_address": transaction.sender_address,
            "recipient_address": transaction.recipient_address,
            "amount": transaction.amount,
            "currency_type": transaction.currency_type,
            "transaction_type": transaction.transaction_type,
            "status": transaction.status,
            "description": transaction.description,
            "gas_fee": transaction.gas_fee,
            "block_height": transaction.block_height,
            "created_at": transaction.created_at,
            "updated_at": transaction.updated_at,
            "sender": {
                "id": sender_user.id if sender_user else None,
                "username": sender_user.username if sender_user else None,
                "wallet_address": sender_user.wallet_address if sender_user else None,
                "full_name": sender_user.full_name if sender_user else None,
            } if sender_user else None,
            "recipient": {
                "id": recipient_user.id if recipient_user else None,
                "username": recipient_user.username if recipient_user else None,
                "wallet_address": recipient_user.wallet_address if recipient_user else None,
                "full_name": recipient_user.full_name if recipient_user else None,
            } if recipient_user else None,
        }
        transactions.append(transaction_dict)
    
    return transactions


@router.post("/send-custodial", response_model=ApiResponse)
async def send_custodial_transaction(
    transaction_request: CustodialTransactionRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Send money using custodial wallet (password-based signing)
    This is the hackathon winning feature - no wallet connection needed!
    """
    
    # Verify this is a custodial user
    if not current_user.is_custodial:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is only for custodial wallet users"
        )
    
    if not current_user.encrypted_private_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No encrypted private key found for custodial account"
        )
    
    # Verify password
    if not auth_service.verify_password(transaction_request.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    try:
        # Resolve recipient username to wallet address
        recipient_user = db.query(User).filter(User.username == transaction_request.recipient_username).first()
        if not recipient_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User @{transaction_request.recipient_username} not found"
            )
        
        # Convert amount to decimal
        amount = Decimal(transaction_request.amount)
        if amount <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Amount must be greater than 0"
            )
        
        # Calculate fees
        transaction_type = fee_service.determine_transaction_type(
            "transfer",
            is_cross_border=False,  # Could be enhanced to detect cross-border
            is_card_transaction=False,
            is_merchant=False
        )
        
        fee_amount, net_amount = fee_service.calculate_fee(amount, transaction_type)
        
        # Check if user has enough balance for amount + fee
        if fee_amount > 0:
            total_required = amount + fee_amount
            # Note: In a real implementation, you'd check the user's actual balance
            print(f"Transaction requires {total_required} {transaction_request.currency_type.upper()} (amount: {amount}, fee: {fee_amount})")
        
        # Get account for signing transaction
        account = wallet_service.get_account_for_transaction(
            current_user.encrypted_private_key,
            transaction_request.password
        )
        
        if not account:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decrypt wallet for transaction signing"
            )
        
        # Sign and submit transaction based on currency type
        # For now, we'll send the full amount and collect fees separately
        # In a production system, you'd use the smart contract's fee collection mechanism
        if transaction_request.currency_type.upper() == "APT":
            tx_hash = await aptos_service.transfer_apt(
                account.private_key.hex(),
                recipient_user.wallet_address,
                amount  # Send full amount to recipient
            )
        elif transaction_request.currency_type.upper() == "USDC":
            tx_hash = await aptos_service.transfer_usdc(
                account.private_key.hex(),
                recipient_user.wallet_address,
                amount  # Send full amount to recipient
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported currency: {transaction_request.currency_type}"
            )
        
        if not tx_hash:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Transaction failed to submit to blockchain"
            )
        
        # Save transaction to database
        db_transaction = Transaction(
            transaction_hash=tx_hash,
            sender_id=current_user.id,
            recipient_id=recipient_user.id,
            sender_address=current_user.wallet_address,
            recipient_address=recipient_user.wallet_address,
            amount=amount,
            currency_type=transaction_request.currency_type.upper(),
            transaction_type="transfer",
            status="confirmed",
            description=transaction_request.description,
            fee_amount=fee_amount,
            fee_percentage=Decimal(fee_service.get_fee_percentage(transaction_type)),
            fee_collected=False,  # Will be updated after fee collection
            revenue_wallet_address=fee_service.revenue_wallet
        )
        
        db.add(db_transaction)
        db.flush()  # Get the ID for fee collection
        
        # Collect fees if applicable
        if fee_amount > 0:
            fee_tx_hash = await fee_service.collect_fee(
                db,
                db_transaction,
                fee_amount,
                transaction_type
            )
            if fee_tx_hash:
                print(f"Fee collected successfully: {fee_tx_hash}")
            else:
                print("Fee collection failed, but main transaction succeeded")
        
        db.commit()
        db.refresh(db_transaction)
        
        return ApiResponse(
            success=True,
            message=f"Successfully sent {amount} {transaction_request.currency_type.upper()} to @{transaction_request.recipient_username}",
            data={
                "transaction_hash": tx_hash,
                "sender_address": current_user.wallet_address,
                "recipient_address": recipient_user.wallet_address,
                "recipient_username": transaction_request.recipient_username,
                "amount": str(amount),
                "currency_type": transaction_request.currency_type.upper(),
                "status": "confirmed",
                "description": transaction_request.description,
                "fee_amount": str(fee_amount),
                "fee_percentage": str(fee_service.get_fee_percentage(transaction_type)),
                "fee_collected": db_transaction.fee_collected,
                "created_at": db_transaction.created_at.isoformat() if db_transaction.created_at else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in custodial transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process transaction. Please try again."
        )


@router.post("/send-petra", response_model=ApiResponse)
async def send_petra_transaction(
    transaction_request: PetraTransactionRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Send money using Petra wallet (wallet-based signing)
    This endpoint prepares the transaction for Petra wallet to sign
    """
    try:
        # Validate that user is using Petra wallet (non-custodial)
        if current_user.is_custodial:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This endpoint is only for Petra wallet users. Use /send-custodial for custodial wallets."
            )
        
        # Find recipient user
        recipient_user = db.query(User).filter(User.username == transaction_request.recipient_username).first()
        if not recipient_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient @{transaction_request.recipient_username} not found"
            )
        
        # Validate amount
        try:
            amount = Decimal(transaction_request.amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid amount format"
            )
        
        # Check sender balance
        sender_balance = await aptos_service.get_account_balance(current_user.wallet_address, transaction_request.currency_type)
        if sender_balance < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. You have {sender_balance} {transaction_request.currency_type}"
            )
        
        # Calculate fees
        transaction_type = "transfer"
        fee_amount, net_amount = fee_service.calculate_fee(amount, transaction_type)
        
        # Format addresses to ensure they're properly formatted for Aptos
        def format_aptos_address(address: str) -> str:
            """Format an Aptos address to ensure it's 64 hex characters (32 bytes)"""
            clean_address = address.replace('0x', '')
            formatted_address = clean_address.zfill(64)
            return f"0x{formatted_address}"

        # Return transaction details for Petra wallet to sign
        return ApiResponse(
            success=True,
            message="Transaction prepared for Petra wallet signing",
            data={
                "transaction_details": {
                    "sender_address": format_aptos_address(current_user.wallet_address),
                    "recipient_address": format_aptos_address(recipient_user.wallet_address),
                    "recipient_username": transaction_request.recipient_username,
                    "amount": str(amount),
                    "currency_type": transaction_request.currency_type.upper(),
                    "description": transaction_request.description,
                    "fee_amount": str(fee_amount),
                    "fee_percentage": str(fee_service.get_fee_percentage(transaction_type)),
                    "total_amount": str(amount + fee_amount)
                },
                "petra_wallet_required": True,
                "instructions": "Please sign this transaction with your Petra wallet to complete the transfer."
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in Petra transaction preparation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prepare transaction. Please try again."
        )


@router.post("/confirm-petra", response_model=ApiResponse)
async def confirm_petra_transaction(
    confirmation_data: dict,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Confirm and save a Petra wallet transaction after it's been signed
    """
    try:
        # Extract transaction details from confirmation data
        transaction_hash = confirmation_data.get("transaction_hash")
        recipient_username = confirmation_data.get("recipient_username")
        amount = confirmation_data.get("amount")
        currency_type = confirmation_data.get("currency_type", "APT")
        description = confirmation_data.get("description", "")
        
        if not all([transaction_hash, recipient_username, amount]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required transaction details"
            )
        
        # Find recipient user
        recipient_user = db.query(User).filter(User.username == recipient_username).first()
        if not recipient_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Recipient @{recipient_username} not found"
            )
        
        # Check if transaction already exists
        existing_transaction = db.query(Transaction).filter(
            Transaction.transaction_hash == transaction_hash
        ).first()
        
        if existing_transaction:
            return ApiResponse(
                success=True,
                message="Transaction already confirmed",
                data={"transaction_id": str(existing_transaction.id)}
            )
        
        # Create new transaction record
        new_transaction = Transaction(
            transaction_hash=transaction_hash,
            sender_id=current_user.id,
            recipient_id=recipient_user.id,
            sender_address=current_user.wallet_address,
            recipient_address=recipient_user.wallet_address,
            amount=Decimal(amount),
            currency_type=currency_type.upper(),
            transaction_type="transfer",
            status="confirmed",  # Petra transactions are confirmed after signing
            description=description,
            gas_fee=None,  # Will be updated later if needed
            block_height=None
        )
        
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
        
        return ApiResponse(
            success=True,
            message="Petra transaction confirmed and saved",
            data={
                "transaction_id": str(new_transaction.id),
                "transaction_hash": new_transaction.transaction_hash,
                "status": new_transaction.status
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error confirming Petra transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm transaction. Please try again."
        )
