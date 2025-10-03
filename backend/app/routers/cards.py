"""
Card Management Routes
Handles Unlimit card creation, management, and transaction processing
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from ..database import get_db
from ..models import User, UnlimitCard, UnlimitTransaction
from ..schemas import (
    CardCreationRequest, CardCreationResponse,
    UnlimitCard as UnlimitCardSchema,
    UnlimitTransaction as UnlimitTransactionSchema,
    ApiResponse
)
from ..services.unlimit_service import unlimit_service
from ..dependencies import require_authentication

router = APIRouter()


@router.post("/create", response_model=CardCreationResponse)
async def create_card(
    card_request: CardCreationRequest,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Create a new Unlimit card for the authenticated user
    """
    try:
        # Validate card creation request
        if card_request.card_type not in ["virtual", "physical"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Card type must be 'virtual' or 'physical'"
            )
        
        # Check if user already has a card of this type in this region
        existing_card = db.query(UnlimitCard).filter(
            UnlimitCard.user_id == current_user.id,
            UnlimitCard.card_type == card_request.card_type,
            UnlimitCard.region == card_request.region,
            UnlimitCard.card_status == "active"
        ).first()
        
        if existing_card:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User already has an active {card_request.card_type} card in {card_request.region}"
            )
        
        # Create card through Unlimit service
        card = await unlimit_service.create_card(current_user, card_request, db)
        
        if not card:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create card with Unlimit"
            )
        
        return CardCreationResponse(
            success=True,
            message=f"{card_request.card_type.title()} card created successfully",
            data=card
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create card"
        )


@router.get("/", response_model=List[UnlimitCardSchema])
async def get_user_cards(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Get all cards for the authenticated user
    """
    cards = db.query(UnlimitCard).filter(
        UnlimitCard.user_id == current_user.id
    ).order_by(UnlimitCard.created_at.desc()).all()
    
    return cards


@router.get("/{card_id}", response_model=UnlimitCardSchema)
async def get_card(
    card_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Get specific card details
    """
    card = db.query(UnlimitCard).filter(
        UnlimitCard.id == card_id,
        UnlimitCard.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    return card


@router.put("/{card_id}/status", response_model=ApiResponse)
async def update_card_status(
    card_id: str,
    new_status: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Update card status (active, inactive, blocked)
    """
    if new_status not in ["active", "inactive", "blocked"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'active', 'inactive', or 'blocked'"
        )
    
    card = db.query(UnlimitCard).filter(
        UnlimitCard.id == card_id,
        UnlimitCard.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    try:
        # Update status through Unlimit service
        success = await unlimit_service.update_card_status(
            card.unlimit_card_id, new_status, db
        )
        
        if success:
            return ApiResponse(
                success=True,
                message=f"Card status updated to {new_status}",
                data={"card_id": card_id, "status": new_status}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update card status"
            )
            
    except Exception as e:
        print(f"Error updating card status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update card status"
        )


@router.get("/{card_id}/transactions", response_model=List[UnlimitTransactionSchema])
async def get_card_transactions(
    card_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Get transaction history for a specific card
    """
    # Verify card ownership
    card = db.query(UnlimitCard).filter(
        UnlimitCard.id == card_id,
        UnlimitCard.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Get transactions from database
    transactions = db.query(UnlimitTransaction).filter(
        UnlimitTransaction.card_id == card.id
    ).order_by(
        UnlimitTransaction.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return transactions


@router.get("/{card_id}/balance", response_model=ApiResponse)
async def get_card_spending_balance(
    card_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Get available spending balance for card (from wallet)
    """
    # Verify card ownership
    card = db.query(UnlimitCard).filter(
        UnlimitCard.id == card_id,
        UnlimitCard.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Get user's wallet balance (USDC is primary spending currency)
    from ..models import Balance
    wallet_balance = db.query(Balance).filter(
        Balance.user_id == current_user.id,
        Balance.currency_type == "USDC"
    ).first()
    
    available_balance = wallet_balance.balance if wallet_balance else Decimal("0")
    
    return ApiResponse(
        success=True,
        message="Card spending balance retrieved",
        data={
            "card_id": card_id,
            "available_balance": str(available_balance),
            "currency": "USDC",
            "card_currency": card.currency
        }
    )


@router.post("/{card_id}/limits", response_model=ApiResponse)
async def update_spending_limits(
    card_id: str,
    limits: dict,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Update card spending limits
    """
    # Verify card ownership
    card = db.query(UnlimitCard).filter(
        UnlimitCard.id == card_id,
        UnlimitCard.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Validate limits
    required_fields = ["daily_limit", "monthly_limit", "per_transaction_limit"]
    for field in required_fields:
        if field not in limits:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}"
            )
        
        if not isinstance(limits[field], (int, float)) or limits[field] < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value for {field}"
            )
    
    try:
        # Update limits through Unlimit API (mock implementation)
        # In real implementation, you'd call Unlimit API to update limits
        
        # Update local database
        import json
        card.spending_limits = json.dumps(limits)
        db.commit()
        
        return ApiResponse(
            success=True,
            message="Spending limits updated successfully",
            data={"card_id": card_id, "limits": limits}
        )
        
    except Exception as e:
        print(f"Error updating spending limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update spending limits"
        )


@router.delete("/{card_id}", response_model=ApiResponse)
async def deactivate_card(
    card_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Deactivate a card (soft delete)
    """
    card = db.query(UnlimitCard).filter(
        UnlimitCard.id == card_id,
        UnlimitCard.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    if card.card_status == "inactive":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Card is already inactive"
        )
    
    try:
        # Deactivate through Unlimit service
        success = await unlimit_service.update_card_status(
            card.unlimit_card_id, "inactive", db
        )
        
        if success:
            return ApiResponse(
                success=True,
                message="Card deactivated successfully",
                data={"card_id": card_id, "status": "inactive"}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to deactivate card"
            )
            
    except Exception as e:
        print(f"Error deactivating card: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate card"
        )


@router.post("/test-authorization", response_model=ApiResponse)
async def test_card_authorization(
    card_id: str,
    amount: Decimal,
    merchant_name: str = "Test Merchant",
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Test card authorization (for development/testing)
    """
    if not current_user or current_user.email != "david@rowellholdings.co.za":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test endpoint restricted to admin users"
        )
    
    # Verify card ownership
    card = db.query(UnlimitCard).filter(
        UnlimitCard.id == card_id,
        UnlimitCard.user_id == current_user.id
    ).first()
    
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    try:
        from ..schemas import CardAuthorizationRequest
        
        # Create test authorization request
        auth_request = CardAuthorizationRequest(
            transaction_id=f"test_txn_{card_id}_{int(amount * 100)}",
            card_id=card.unlimit_card_id,
            amount=amount,
            currency=card.currency,
            merchant_name=merchant_name
        )
        
        # Process authorization
        auth_response = await unlimit_service.authorize_transaction(auth_request, db)
        
        return ApiResponse(
            success=True,
            message="Test authorization completed",
            data={
                "approved": auth_response.approved,
                "auth_code": auth_response.auth_code,
                "decline_reason": auth_response.decline_reason
            }
        )
        
    except Exception as e:
        print(f"Error in test authorization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Test authorization failed"
        )
