from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from datetime import datetime
import secrets

from ..database import get_db
from ..models import User, FiatTransaction, Balance
from ..schemas import (
    FiatTransactionCreate,
    FiatTransaction as FiatTransactionSchema,
    ApiResponse
)
from ..dependencies import require_authentication
from ..dependencies import require_authentication

router = APIRouter()

# Mock exchange rates (in production, these would come from a real API)
MOCK_EXCHANGE_RATES = {
    "USD": {
        "USDC": Decimal("1.00"),  # 1 USD = 1 USDC
        "APT": Decimal("0.125"),   # 1 USD = 0.125 APT (example rate)
    }
}

# Mock supported fiat currencies
SUPPORTED_FIAT_CURRENCIES = ["USD"]
SUPPORTED_CRYPTO_CURRENCIES = ["USDC", "APT"]


@router.post("/deposit", response_model=ApiResponse)
async def mock_fiat_deposit(
    deposit: FiatTransactionCreate,
    user_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Mock fiat deposit endpoint"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate transaction type
    if deposit.transaction_type != "deposit":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction type for deposit"
        )
    
    # Validate currencies
    if deposit.fiat_currency not in SUPPORTED_FIAT_CURRENCIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported fiat currency: {deposit.fiat_currency}"
        )
    
    if deposit.crypto_currency not in SUPPORTED_CRYPTO_CURRENCIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported crypto currency: {deposit.crypto_currency}"
        )
    
    # Validate amount
    if deposit.fiat_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deposit amount must be greater than 0"
        )
    
    # Minimum deposit amounts
    min_deposit = Decimal("10.00")  # $10 minimum
    if deposit.fiat_amount < min_deposit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum deposit amount is ${min_deposit}"
        )
    
    try:
        # Get exchange rate
        exchange_rate = MOCK_EXCHANGE_RATES[deposit.fiat_currency][deposit.crypto_currency]
        crypto_amount = deposit.fiat_amount * exchange_rate
        
        # Generate mock bank reference
        bank_reference = f"DEP-{secrets.token_hex(8).upper()}"
        
        # Create fiat transaction record
        fiat_transaction = FiatTransaction(
            user_id=user.id,
            transaction_type="deposit",
            fiat_amount=deposit.fiat_amount,
            fiat_currency=deposit.fiat_currency,
            crypto_amount=crypto_amount,
            crypto_currency=deposit.crypto_currency,
            exchange_rate=exchange_rate,
            status="completed",  # Mock deposits are instant
            bank_reference=bank_reference
        )
        
        db.add(fiat_transaction)
        
        # Update user balance
        user_balance = db.query(Balance).filter(
            Balance.user_id == user.id,
            Balance.currency_type == deposit.crypto_currency
        ).first()
        
        if user_balance:
            user_balance.balance += crypto_amount
        else:
            # Create new balance record
            user_balance = Balance(
                user_id=user.id,
                currency_type=deposit.crypto_currency,
                balance=crypto_amount
            )
            db.add(user_balance)
        
        db.commit()
        db.refresh(fiat_transaction)
        
        return ApiResponse(
            success=True,
            message=f"Mock deposit of ${deposit.fiat_amount} completed successfully",
            data={
                "transaction_id": str(fiat_transaction.id),
                "fiat_amount": str(deposit.fiat_amount),
                "fiat_currency": deposit.fiat_currency,
                "crypto_amount": str(crypto_amount),
                "crypto_currency": deposit.crypto_currency,
                "exchange_rate": str(exchange_rate),
                "bank_reference": bank_reference,
                "status": "completed"
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deposit failed: {str(e)}"
        )


@router.post("/withdraw", response_model=ApiResponse)
async def mock_fiat_withdrawal(
    withdrawal: FiatTransactionCreate,
    user_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Mock fiat withdrawal endpoint"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate transaction type
    if withdrawal.transaction_type != "withdraw":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid transaction type for withdrawal"
        )
    
    # Validate currencies
    if withdrawal.fiat_currency not in SUPPORTED_FIAT_CURRENCIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported fiat currency: {withdrawal.fiat_currency}"
        )
    
    if withdrawal.crypto_currency not in SUPPORTED_CRYPTO_CURRENCIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported crypto currency: {withdrawal.crypto_currency}"
        )
    
    # Validate amount
    if withdrawal.fiat_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Withdrawal amount must be greater than 0"
        )
    
    # Minimum withdrawal amounts
    min_withdrawal = Decimal("5.00")  # $5 minimum
    if withdrawal.fiat_amount < min_withdrawal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum withdrawal amount is ${min_withdrawal}"
        )
    
    try:
        # Get exchange rate
        exchange_rate = MOCK_EXCHANGE_RATES[withdrawal.fiat_currency][withdrawal.crypto_currency]
        crypto_amount = withdrawal.fiat_amount * exchange_rate
        
        # Check user balance
        user_balance = db.query(Balance).filter(
            Balance.user_id == user.id,
            Balance.currency_type == withdrawal.crypto_currency
        ).first()
        
        if not user_balance or user_balance.balance < crypto_amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance for withdrawal"
            )
        
        # Generate mock bank reference
        bank_reference = f"WTH-{secrets.token_hex(8).upper()}"
        
        # Create fiat transaction record
        fiat_transaction = FiatTransaction(
            user_id=user.id,
            transaction_type="withdraw",
            fiat_amount=withdrawal.fiat_amount,
            fiat_currency=withdrawal.fiat_currency,
            crypto_amount=crypto_amount,
            crypto_currency=withdrawal.crypto_currency,
            exchange_rate=exchange_rate,
            status="completed",  # Mock withdrawals are instant
            bank_reference=bank_reference
        )
        
        db.add(fiat_transaction)
        
        # Update user balance
        user_balance.balance -= crypto_amount
        
        db.commit()
        db.refresh(fiat_transaction)
        
        return ApiResponse(
            success=True,
            message=f"Mock withdrawal of ${withdrawal.fiat_amount} completed successfully",
            data={
                "transaction_id": str(fiat_transaction.id),
                "fiat_amount": str(withdrawal.fiat_amount),
                "fiat_currency": withdrawal.fiat_currency,
                "crypto_amount": str(crypto_amount),
                "crypto_currency": withdrawal.crypto_currency,
                "exchange_rate": str(exchange_rate),
                "bank_reference": bank_reference,
                "status": "completed"
            }
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Withdrawal failed: {str(e)}"
        )


@router.get("/transactions/{user_id}", response_model=List[FiatTransactionSchema])
async def get_fiat_transactions(
    user_id: str,
    transaction_type: str = None,
    limit: int = 25,
    offset: int = 0,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get fiat transaction history for a user"""
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    query = db.query(FiatTransaction).filter(FiatTransaction.user_id == user_id)
    
    if transaction_type:
        if transaction_type not in ["deposit", "withdraw"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid transaction type. Must be 'deposit' or 'withdraw'"
            )
        query = query.filter(FiatTransaction.transaction_type == transaction_type)
    
    transactions = query.order_by(
        FiatTransaction.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return transactions


@router.get("/rates", response_model=dict)
async def get_exchange_rates():
    """Get current mock exchange rates"""
    
    return {
        "rates": MOCK_EXCHANGE_RATES,
        "supported_fiat": SUPPORTED_FIAT_CURRENCIES,
        "supported_crypto": SUPPORTED_CRYPTO_CURRENCIES,
        "last_updated": datetime.utcnow().isoformat(),
        "note": "These are mock exchange rates for testing purposes only"
    }


@router.get("/limits", response_model=dict)
async def get_transaction_limits():
    """Get fiat transaction limits"""
    
    return {
        "deposit": {
            "min_amount": "10.00",
            "max_amount": "10000.00",
            "daily_limit": "25000.00",
            "currency": "USD"
        },
        "withdraw": {
            "min_amount": "5.00",
            "max_amount": "5000.00",
            "daily_limit": "15000.00",
            "currency": "USD"
        },
        "note": "These are mock limits for testing purposes only"
    }
