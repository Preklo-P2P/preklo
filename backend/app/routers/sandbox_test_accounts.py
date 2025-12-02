"""
Sandbox Test Account Endpoints
Handles listing, retrieving, resetting, and funding test accounts.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from decimal import Decimal

from ..database import get_db
from ..dependencies.sandbox_auth import get_sandbox_user_from_api_key
from ..models.sandbox import SandboxAPIKey
from ..schemas.sandbox import (
    TestAccountResponse,
    ListTestAccountsResponse,
    ResetBalanceResponse,
    FundAccountRequest,
    FundAccountResponse
)
from ..services.test_account_service import test_account_service

router = APIRouter(prefix="/api/v1/sandbox/test-accounts", tags=["sandbox"])


@router.get("/balances", response_model=dict)
def get_test_account_balances(
    current_api_key: SandboxAPIKey = Depends(get_sandbox_user_from_api_key),
    db: Session = Depends(get_db)
):
    """
    Get balances for all test accounts (sandbox mode).
    
    Returns a summary of all test account balances.
    This endpoint provides balance information similar to /users/{user_id}/balances
    but for sandbox test accounts.
    """
    sandbox_user_id = str(current_api_key.sandbox_user_id)
    accounts = test_account_service.get_test_accounts(db, sandbox_user_id)
    
    balances_summary = []
    total_usdc = Decimal("0")
    total_apt = Decimal("0")
    
    for account in accounts:
        balances_summary.append({
            "account_id": str(account.id),
            "username": account.username,
            "usdc_balance": float(account.usdc_balance),
            "apt_balance": float(account.apt_balance),
            "wallet_address": account.wallet_address,
            "currency_type": account.currency_type
        })
        total_usdc += account.usdc_balance
        total_apt += account.apt_balance
    
    return {
        "accounts": balances_summary,
        "total_usdc": float(total_usdc),
        "total_apt": float(total_apt),
        "account_count": len(accounts)
    }


@router.get("", response_model=ListTestAccountsResponse)
def list_test_accounts(
    currency_type: Optional[str] = Query(None, description="Filter by currency type (USDC, APT)"),
    db: Session = Depends(get_db),
    current_api_key: SandboxAPIKey = Depends(get_sandbox_user_from_api_key)
):
    """
    List all test accounts for the authenticated sandbox user.
    
    Optionally filter by currency type.
    """
    accounts = test_account_service.get_test_accounts(
        db=db,
        sandbox_user_id=str(current_api_key.sandbox_user_id),
        currency_type=currency_type
    )
    
    # Convert to response format
    account_responses = [
        TestAccountResponse(
            id=account.id,
            username=account.username,
            wallet_address=account.wallet_address,
            usdc_balance=float(account.usdc_balance),
            apt_balance=float(account.apt_balance),
            currency_type=account.currency_type,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
        for account in accounts
    ]
    
    return ListTestAccountsResponse(
        accounts=account_responses,
        total=len(account_responses)
    )


@router.get("/{account_id}", response_model=TestAccountResponse)
def get_test_account(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_api_key: SandboxAPIKey = Depends(get_sandbox_user_from_api_key)
):
    """
    Get a specific test account by ID.
    
    Only accounts owned by the authenticated sandbox user are accessible.
    """
    account = test_account_service.get_test_account(
        db=db,
        account_id=str(account_id),
        sandbox_user_id=str(current_api_key.sandbox_user_id)
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test account not found or you don't have permission to access it."
        )
    
    return TestAccountResponse(
        id=account.id,
        username=account.username,
        wallet_address=account.wallet_address,
        usdc_balance=float(account.usdc_balance),
        apt_balance=float(account.apt_balance),
        currency_type=account.currency_type,
        created_at=account.created_at,
        updated_at=account.updated_at
    )


@router.post("/{account_id}/reset", response_model=ResetBalanceResponse)
def reset_account_balance(
    account_id: UUID,
    db: Session = Depends(get_db),
    current_api_key: SandboxAPIKey = Depends(get_sandbox_user_from_api_key)
):
    """
    Reset a test account balance to its original values.
    
    This is useful for resetting accounts after testing transactions.
    """
    account = test_account_service.reset_balance(
        db=db,
        account_id=str(account_id),
        sandbox_user_id=str(current_api_key.sandbox_user_id)
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test account not found or you don't have permission to reset it."
        )
    
    return ResetBalanceResponse(
        success=True,
        message="Account balance reset successfully",
        account=TestAccountResponse(
            id=account.id,
            username=account.username,
            wallet_address=account.wallet_address,
            usdc_balance=float(account.usdc_balance),
            apt_balance=float(account.apt_balance),
            currency_type=account.currency_type,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
    )


@router.post("/{account_id}/fund", response_model=FundAccountResponse)
def fund_account(
    account_id: UUID,
    request: FundAccountRequest,
    db: Session = Depends(get_db),
    current_api_key: SandboxAPIKey = Depends(get_sandbox_user_from_api_key)
):
    """
    Add test funds to a test account.
    
    You can add USDC, APT, or both. Amounts must be non-negative.
    """
    # Validate that at least one amount is provided
    if request.usdc_amount is None and request.apt_amount is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of usdc_amount or apt_amount must be provided."
        )
    
    # Convert to Decimal for database operations
    usdc_decimal = Decimal(str(request.usdc_amount)) if request.usdc_amount is not None else None
    apt_decimal = Decimal(str(request.apt_amount)) if request.apt_amount is not None else None
    
    account = test_account_service.fund_account(
        db=db,
        account_id=str(account_id),
        sandbox_user_id=str(current_api_key.sandbox_user_id),
        usdc_amount=usdc_decimal,
        apt_amount=apt_decimal
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test account not found or you don't have permission to fund it."
        )
    
    return FundAccountResponse(
        success=True,
        message="Account funded successfully",
        account=TestAccountResponse(
            id=account.id,
            username=account.username,
            wallet_address=account.wallet_address,
            usdc_balance=float(account.usdc_balance),
            apt_balance=float(account.apt_balance),
            currency_type=account.currency_type,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
    )

