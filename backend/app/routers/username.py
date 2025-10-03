from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User
from ..schemas import UsernameCheck, UsernameResolve, ApiResponse
from ..services.aptos_service import aptos_service
import re

router = APIRouter()


@router.post("/initialize", response_model=ApiResponse)
async def initialize_username_registry():
    """Initialize the username registry on-chain (admin only)"""
    try:
        # Initialize the username registry
        tx_hash = await aptos_service.initialize_username_registry()
        
        if tx_hash:
            return ApiResponse(
                success=True,
                message="Username registry initialized successfully",
                data={"transaction_hash": tx_hash}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize username registry"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize username registry: {str(e)}"
        )


def validate_username(username: str) -> bool:
    """Validate username format"""
    # Username rules: 3-32 characters, alphanumeric + underscore, start with letter
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]{2,31}$'
    return bool(re.match(pattern, username))


def generate_username_suggestions(base_username: str, db: Session) -> List[str]:
    """Generate alternative username suggestions"""
    suggestions = []
    
    # Add numbers to the end
    for i in range(1, 6):
        suggestion = f"{base_username}{i}"
        if len(suggestion) <= 32:
            existing = db.query(User).filter(User.username == suggestion).first()
            if not existing:
                suggestions.append(suggestion)
    
    # Add underscore and numbers
    for i in range(1, 4):
        suggestion = f"{base_username}_{i}"
        if len(suggestion) <= 32:
            existing = db.query(User).filter(User.username == suggestion).first()
            if not existing:
                suggestions.append(suggestion)
    
    # Truncate base and add numbers if too long
    if len(base_username) > 28:
        truncated = base_username[:28]
        for i in range(1, 4):
            suggestion = f"{truncated}{i}"
            existing = db.query(User).filter(User.username == suggestion).first()
            if not existing:
                suggestions.append(suggestion)
    
    return suggestions[:5]  # Return max 5 suggestions


@router.get("/check/{username}", response_model=UsernameCheck)
async def check_username_availability(username: str, db: Session = Depends(get_db)):
    """Check if username is available"""
    
    # Validate username format
    if not validate_username(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username format. Username must be 3-32 characters, start with a letter, and contain only letters, numbers, and underscores."
        )
    
    # Check if username exists in database
    existing_user = db.query(User).filter(User.username == username).first()
    available = existing_user is None
    
    # Generate suggestions if username is taken
    suggestions = []
    if not available:
        suggestions = generate_username_suggestions(username, db)
    
    return UsernameCheck(
        username=username,
        available=available,
        suggested_usernames=suggestions if suggestions else None
    )


@router.get("/resolve/{username}", response_model=UsernameResolve)
async def resolve_username(username: str, db: Session = Depends(get_db)):
    """Resolve username to wallet address and user ID"""
    
    # First check database
    user = db.query(User).filter(User.username == username).first()
    if not user:
        # Also check on-chain (in case database is out of sync)
        try:
            on_chain_address = await aptos_service.resolve_username(username)
            if on_chain_address:
                # Try to find user by address
                user = db.query(User).filter(User.wallet_address == on_chain_address).first()
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Username found on-chain but user not in database"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Username not found"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Username not found"
            )
    
    return UsernameResolve(
        username=user.username,
        wallet_address=user.wallet_address,
        user_id=user.id
    )


@router.post("/register", response_model=ApiResponse)
async def register_username_on_chain(
    username: str,
    user_private_key: str,
    db: Session = Depends(get_db)
):
    """Register username on-chain (for testing purposes)"""
    
    # Validate username format
    if not validate_username(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username format"
        )
    
    # Check if username is available
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    try:
        # Register username on-chain
        tx_hash = await aptos_service.register_username(user_private_key, username)
        
        if tx_hash:
            return ApiResponse(
                success=True,
                message="Username registered on-chain successfully",
                data={"transaction_hash": tx_hash}
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register username on-chain"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register username: {str(e)}"
        )


@router.get("/validate/{username}")
async def validate_username_format(username: str):
    """Validate username format without checking availability"""
    
    valid = validate_username(username)
    
    errors = []
    if len(username) < 3:
        errors.append("Username must be at least 3 characters long")
    if len(username) > 32:
        errors.append("Username must be no more than 32 characters long")
    if not username[0].isalpha():
        errors.append("Username must start with a letter")
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        errors.append("Username can only contain letters, numbers, and underscores")
    
    return {
        "username": username,
        "valid": valid,
        "errors": errors if errors else None
    }


@router.get("/search")
async def search_usernames(query: str, limit: int = 10, db: Session = Depends(get_db)):
    """Search usernames (for autocomplete/suggestions)"""
    
    if len(query) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query must be at least 2 characters long"
        )
    
    # Search for usernames that start with the query
    users = db.query(User).filter(
        User.username.ilike(f"{query}%")
    ).filter(
        User.is_active == True
    ).limit(limit).all()
    
    results = []
    for user in users:
        results.append({
            "username": user.username,
            "full_name": user.full_name,
            "profile_picture_url": user.profile_picture_url
        })
    
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }
