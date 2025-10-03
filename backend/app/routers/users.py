from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from decimal import Decimal

from ..database import get_db
from ..models import User, Balance
from ..schemas import UserCreate, UserUpdate, User as UserSchema, Balance as BalanceSchema, ApiResponse
from ..services.aptos_service import aptos_service
from ..dependencies import require_authentication, validate_user_access

router = APIRouter()


@router.get("/info/{username}")
async def get_user_info_by_username(username: str, db: Session = Depends(get_db)):
    """Get user info by username for login detection"""
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        return {
            "exists": False,
            "username": username
        }
    
    return {
        "exists": True,
        "username": user.username,
        "is_custodial": user.is_custodial,
        "is_active": user.is_active,
        "wallet_address": user.wallet_address
    }


@router.post("/", response_model=UserSchema)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    try:
        # Check if username or wallet address already exists
        existing_user = db.query(User).filter(
            (User.username == user.username) | (User.wallet_address == user.wallet_address)
        ).first()
        
        if existing_user:
            if existing_user.username == user.username:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Wallet address already registered"
                )
        
        # Create new user
        db_user = User(**user.dict())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create initial balances for supported currencies
        currencies = ["APT", "USDC"]
        for currency in currencies:
            balance = Balance(
                user_id=db_user.id,
                currency_type=currency,
                balance=Decimal("0.0")
            )
            db.add(balance)
        
        db.commit()
        
        return db_user
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username or wallet address already exists"
        )


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: str, 
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get user by ID"""
    # Validate user access (users can only access their own data)
    await validate_user_access(user_id, current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/username/{username}", response_model=UserSchema)
async def get_user_by_username(username: str, db: Session = Depends(get_db)):
    """Get user by username"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.get("/address/{wallet_address}", response_model=UserSchema)
async def get_user_by_address(wallet_address: str, db: Session = Depends(get_db)):
    """Get user by wallet address"""
    user = db.query(User).filter(User.wallet_address == wallet_address).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: str, 
    user_update: UserUpdate,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Update user information"""
    # Validate user access (users can only update their own data)
    await validate_user_access(user_id, current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update only provided fields
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )


@router.get("/{user_id}/balances", response_model=List[BalanceSchema])
async def get_user_balances(
    user_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Get user balances for all currencies"""
    # Validate user access
    await validate_user_access(user_id, current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get balances from database
    db_balances = db.query(Balance).filter(Balance.user_id == user_id).all()
    
    # Also fetch live balances from blockchain
    try:
        print(f"Fetching live balances for wallet: {user.wallet_address}")
        apt_balance = await aptos_service.get_account_balance(user.wallet_address, "APT")
        usdc_balance = await aptos_service.get_account_balance(user.wallet_address, "USDC")
        
        print(f"Blockchain balances - APT: {apt_balance}, USDC: {usdc_balance}")
        
        # Update database with live balances
        for balance in db_balances:
            if balance.currency_type == "APT":
                print(f"Updating APT balance from {balance.balance} to {apt_balance}")
                balance.balance = apt_balance
            elif balance.currency_type == "USDC":
                print(f"Updating USDC balance from {balance.balance} to {usdc_balance}")
                balance.balance = usdc_balance
        
        db.commit()
        print("Database balances updated successfully")
        
    except Exception as e:
        print(f"Error fetching live balances: {e}")
        # Continue with database balances if blockchain query fails
    
    return db_balances


@router.post("/{user_id}/sync-balances", response_model=ApiResponse)
async def sync_user_balances(
    user_id: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """Sync user balances with blockchain"""
    # Validate user access
    await validate_user_access(user_id, current_user)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Fetch balances from blockchain
        apt_balance = await aptos_service.get_account_balance(user.wallet_address, "APT")
        usdc_balance = await aptos_service.get_account_balance(user.wallet_address, "USDC")
        
        # Update database balances
        balances = db.query(Balance).filter(Balance.user_id == user_id).all()
        
        for balance in balances:
            if balance.currency_type == "APT":
                balance.balance = apt_balance
            elif balance.currency_type == "USDC":
                balance.balance = usdc_balance
        
        db.commit()
        
        return ApiResponse(
            success=True,
            message="Balances synced successfully",
            data={
                "apt_balance": str(apt_balance),
                "usdc_balance": str(usdc_balance)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync balances: {str(e)}"
        )
