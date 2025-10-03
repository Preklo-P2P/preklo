"""
Voucher Router

API endpoints for voucher management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import User
from app.schemas import (
    VoucherCreate, 
    VoucherRedeem, 
    VoucherResponse, 
    VoucherListResponse,
    VoucherAgent
)
from app.services.voucher_service import VoucherService

router = APIRouter()


@router.post("/", response_model=VoucherResponse)
async def create_voucher(
    voucher_data: VoucherCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new voucher."""
    
    try:
        voucher_service = VoucherService(db)
        voucher = voucher_service.create_voucher(
            creator_id=str(current_user.id),
            voucher_data=voucher_data
        )
        return voucher
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create voucher"
        )


@router.get("/", response_model=VoucherListResponse)
async def get_vouchers(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vouchers for the current user."""
    
    try:
        voucher_service = VoucherService(db)
        vouchers = voucher_service.get_vouchers(
            user_id=str(current_user.id),
            status=status,
            limit=limit,
            offset=offset
        )
        
        return VoucherListResponse(
            vouchers=vouchers,
            total=len(vouchers),
            page=offset // limit + 1,
            page_size=limit,
            has_more=len(vouchers) == limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vouchers"
        )


@router.get("/{voucher_code}", response_model=VoucherResponse)
async def get_voucher(
    voucher_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific voucher by code."""
    
    try:
        voucher_service = VoucherService(db)
        voucher = voucher_service.get_voucher(voucher_code)
        
        if not voucher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voucher not found"
            )
        
        return voucher
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voucher"
        )


@router.post("/{voucher_code}/redeem", response_model=VoucherResponse)
async def redeem_voucher(
    voucher_code: str,
    redeem_data: VoucherRedeem,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Redeem a voucher."""
    
    try:
        voucher_service = VoucherService(db)
        voucher = voucher_service.redeem_voucher(
            voucher_code=voucher_code,
            redeemer_id=str(current_user.id),
            pin=redeem_data.pin
        )
        return voucher
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to redeem voucher"
        )


@router.post("/{voucher_code}/cancel")
async def cancel_voucher(
    voucher_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a voucher (only creator can cancel)."""
    
    try:
        voucher_service = VoucherService(db)
        success = voucher_service.cancel_voucher(
            voucher_code=voucher_code,
            user_id=str(current_user.id)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voucher not found or cannot be cancelled"
            )
        
        return {"message": "Voucher cancelled successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel voucher"
        )


@router.get("/analytics/summary")
async def get_voucher_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get voucher analytics for the current user."""
    
    try:
        voucher_service = VoucherService(db)
        analytics = voucher_service.get_voucher_analytics(
            user_id=str(current_user.id)
        )
        return analytics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve voucher analytics"
        )


@router.post("/cleanup/expired")
async def cleanup_expired_vouchers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean up expired vouchers (admin only)."""
    
    # TODO: Add admin role check
    try:
        voucher_service = VoucherService(db)
        count = voucher_service.cleanup_expired_vouchers()
        return {"message": f"Cleaned up {count} expired vouchers"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup expired vouchers"
        )


@router.get("/agents/nearby", response_model=List[VoucherAgent])
async def get_nearby_agents(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: float = 10.0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get nearby voucher agents."""
    
    # TODO: Implement actual agent location search
    # For now, return mock data
    mock_agents = [
        VoucherAgent(
            id="agent-1",
            name="QuickCash Store",
            address="123 Main Street",
            city="New York",
            country="USA",
            phone="+1-555-0123",
            email="store@quickcash.com",
            is_active=True,
            created_at="2024-01-01T00:00:00Z"
        ),
        VoucherAgent(
            id="agent-2",
            name="MoneyMart",
            address="456 Oak Avenue",
            city="New York",
            country="USA",
            phone="+1-555-0456",
            email="info@moneymart.com",
            is_active=True,
            created_at="2024-01-01T00:00:00Z"
        )
    ]
    
    return mock_agents
