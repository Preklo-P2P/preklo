"""
Authentication Routes
Handles user login, token refresh, password reset, and API key management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any
from decimal import Decimal
import logging

from ..database import get_db
from ..models import User
from ..schemas import (
    UserLogin, UserLoginResponse, TokenRefresh, TokenResponse,
    PasswordReset, PasswordResetRequest, APIKeyCreate, APIKeyResponse,
    UserCreate, UserCreateSimple, UserResponse, WalletExportData,
    WalletLoginRequest
)
from ..services.auth_service import auth_service
from ..services.wallet_service import wallet_service
from ..services.aptos_service import aptos_service
from ..services.email_service import email_service
from ..dependencies import require_authentication, get_current_user
from ..utils.validation import InputValidator

logger = logging.getLogger("preklo.auth")

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account
    """
    # Validate password strength
    is_valid_password, password_error = InputValidator.validate_password(user_data.password)
    if not is_valid_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_error
        )
    
    # Check if username, email, or wallet address already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | 
        (User.email == user_data.email) |
        (User.wallet_address == user_data.wallet_address)
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        elif existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        elif existing_user.wallet_address == user_data.wallet_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Wallet address already registered. Please use a different wallet or try logging in instead."
            )
    
    # Hash the password
    hashed_password = auth_service.get_password_hash(user_data.password)
    
    # Determine if user is providing their own wallet or wants a custodial wallet
    wallet_address = user_data.wallet_address
    encrypted_private_key = None
    is_custodial = False
    
    if user_data.wallet_address:
        # User provided their own wallet address - they're non-custodial
        is_custodial = False
        print(f"User {user_data.username} provided their own wallet: {wallet_address} (non-custodial)")
    else:
        # User didn't provide wallet - generate a custodial wallet
        try:
            generated_address, private_key = wallet_service.generate_wallet()
            encrypted_private_key = wallet_service.encrypt_private_key(private_key, user_data.password)
            wallet_address = generated_address
            is_custodial = True
            print(f"Generated custodial wallet for user {user_data.username}: {wallet_address}")
        except Exception as e:
            print(f"Warning: Could not generate custodial wallet: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create wallet. Please try again."
            )
    
    # Create new user
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        wallet_address=wallet_address,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        is_active=True,
        is_custodial=is_custodial,  # Set based on whether we generated the wallet or user provided their own
        encrypted_private_key=encrypted_private_key
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create initial balances for supported currencies
    from ..models import Balance
    currencies = ["APT", "USDC"]
    for currency in currencies:
        balance = Balance(
            user_id=db_user.id,
            currency_type=currency,
            balance=Decimal("0.0")
        )
        db.add(balance)
    
    db.commit()
    
    # Sync balances with blockchain after registration
    try:
        print(f"Syncing balances for new user {db_user.username} with wallet {db_user.wallet_address}")
        apt_balance = await aptos_service.get_account_balance(db_user.wallet_address, "APT")
        usdc_balance = await aptos_service.get_account_balance(db_user.wallet_address, "USDC")
        
        # Update database balances with actual blockchain balances
        balances = db.query(Balance).filter(Balance.user_id == db_user.id).all()
        for balance in balances:
            if balance.currency_type == "APT":
                balance.balance = apt_balance
            elif balance.currency_type == "USDC":
                balance.balance = usdc_balance
        
        db.commit()
        print(f"Balances synced: APT={apt_balance}, USDC={usdc_balance}")
    except Exception as e:
        print(f"Warning: Could not sync balances for new user: {e}")
        # Don't fail registration if balance sync fails
    
    return {
        "status": "success",
        "message": "User registered successfully",
        "data": {
            "id": str(db_user.id),
            "username": db_user.username,
            "email": db_user.email,
            "wallet_address": db_user.wallet_address,
            "full_name": db_user.full_name,
            "is_active": db_user.is_active,
            "created_at": db_user.created_at.isoformat() if db_user.created_at else None
        }
    }


@router.post("/register-simple", response_model=UserResponse)
async def register_user_simple(user_data: UserCreateSimple, db: Session = Depends(get_db)):
    """
    Register a new user with auto-generated custodial wallet
    Perfect for mass adoption - users just need email/username/password
    """
    # Validate password strength
    is_valid_password, password_error = InputValidator.validate_password(user_data.password)
    if not is_valid_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_error
        )
    
    # Validate terms agreement
    if not user_data.terms_agreed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must agree to the terms and conditions to register"
        )
    
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    try:
        # Generate custodial wallet
        wallet_address, encrypted_private_key = wallet_service.create_custodial_wallet(user_data.password)
        
        # Hash the password
        hashed_password = auth_service.get_password_hash(user_data.password)
        
        # Create new user with custodial wallet
        from datetime import datetime
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            wallet_address=wallet_address,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_custodial=True,
            encrypted_private_key=encrypted_private_key,
            wallet_exported=False,
            terms_agreed=user_data.terms_agreed,
            terms_agreed_at=datetime.utcnow() if user_data.terms_agreed else None
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Create initial balances for supported currencies
        from ..models import Balance
        currencies = ["APT", "USDC"]
        for currency in currencies:
            balance = Balance(
                user_id=db_user.id,
                currency_type=currency,
                balance=Decimal("0.0")
            )
            db.add(balance)
        
        db.commit()
        
        # Sync balances with blockchain after registration
        try:
            print(f"Syncing balances for new user {db_user.username} with wallet {db_user.wallet_address}")
            apt_balance = await aptos_service.get_account_balance(db_user.wallet_address, "APT")
            usdc_balance = await aptos_service.get_account_balance(db_user.wallet_address, "USDC")
            
            # Update database balances with actual blockchain balances
            balances = db.query(Balance).filter(Balance.user_id == db_user.id).all()
            for balance in balances:
                if balance.currency_type == "APT":
                    balance.balance = apt_balance
                elif balance.currency_type == "USDC":
                    balance.balance = usdc_balance
            
            db.commit()
            print(f"Balances synced: APT={apt_balance}, USDC={usdc_balance}")
        except Exception as e:
            print(f"Warning: Could not sync balances for new user: {e}")
            # Don't fail registration if balance sync fails
        
        # Try to register username on-chain (non-blocking)
        try:
            # Get decrypted private key for on-chain registration
            account = wallet_service.get_account_for_transaction(encrypted_private_key, user_data.password, str(current_user.id))
            if account:
                # Register username on-chain in background
                tx_hash = await aptos_service.register_username(account.private_key.hex(), user_data.username)
                print(f"Username {user_data.username} registered on-chain: {tx_hash}")
        except Exception as e:
            # Don't fail registration if on-chain registration fails
            print(f"Warning: Could not register username on-chain: {e}")
        
        return {
            "status": "success",
            "message": "User registered successfully with custodial wallet",
            "data": {
                "id": str(db_user.id),
                "username": db_user.username,
                "email": db_user.email,
                "wallet_address": db_user.wallet_address,
                "full_name": db_user.full_name,
                "is_active": db_user.is_active,
                "is_custodial": db_user.is_custodial,
                "wallet_exported": db_user.wallet_exported,
                "created_at": db_user.created_at.isoformat() if db_user.created_at else None,
                "onboarding_message": "Welcome! Your wallet has been created automatically. You can receive money immediately using your @username!"
            }
        }
        
    except Exception as e:
        db.rollback()
        print(f"Error creating custodial user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user account. Please try again."
        )


@router.post("/login", response_model=UserLoginResponse)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT tokens
    """
    user = auth_service.authenticate_user(
        db, user_credentials.username, user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens with appropriate expiration based on remember_me
    tokens = auth_service.create_user_tokens(user, remember_me=user_credentials.remember_me)
    
    # Create session data
    session_data = auth_service.create_session_data(user)
    
    # Sync balances with blockchain on login (non-blocking)
    try:
        print(f"Syncing balances for user {user.username} on login")
        apt_balance = await aptos_service.get_account_balance(user.wallet_address, "APT")
        usdc_balance = await aptos_service.get_account_balance(user.wallet_address, "USDC")
        
        # Update database balances with actual blockchain balances
        from ..models import Balance
        balances = db.query(Balance).filter(Balance.user_id == user.id).all()
        for balance in balances:
            if balance.currency_type == "APT":
                balance.balance = apt_balance
            elif balance.currency_type == "USDC":
                balance.balance = usdc_balance
        
        db.commit()
        print(f"Login balance sync completed: APT={apt_balance}, USDC={usdc_balance}")
    except Exception as e:
        print(f"Warning: Could not sync balances on login: {e}")
        # Don't fail login if balance sync fails
    
    return {
        "status": "success",
        "message": "Login successful",
        "data": {
            "user": session_data,
            "tokens": tokens
        }
    }


@router.post("/login-wallet", response_model=UserLoginResponse)
async def login_user_wallet(request: WalletLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user using wallet address (no password required)
    This is for Web3-style authentication where wallet connection = authentication
    """
    # Clean username (remove @ if present)
    clean_username = request.username.lstrip('@')
    
    # Find user by both username and wallet address to ensure they match
    user = db.query(User).filter(
        User.username == clean_username,
        User.wallet_address == request.wallet_address
    ).first()
    
    if not user:
        # Check if username exists but with different wallet
        existing_user = db.query(User).filter(User.username == clean_username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username @{clean_username} is associated with a different wallet address"
            )
        
        # Check if wallet exists but with different username
        existing_wallet = db.query(User).filter(User.wallet_address == request.wallet_address).first()
        if existing_wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This wallet address is already associated with username @{existing_wallet.username}"
            )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found for this username and wallet combination. Please sign up first."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated"
        )
    
    # Update user's custodial status based on whether they have an encrypted private key
    # If they don't have an encrypted private key, they're using their own wallet (non-custodial)
    if not user.encrypted_private_key and user.is_custodial:
        user.is_custodial = False
        db.commit()
        print(f"Updated user {user.username} to non-custodial (no encrypted private key)")
    
    # Auto-fix: If user has encrypted private key but is marked as non-custodial, fix it
    if user.encrypted_private_key and not user.is_custodial:
        user.is_custodial = True
        db.commit()
        print(f"Auto-fixed user {user.username}: set is_custodial=True (has encrypted private key)")
    
    # Create tokens
    tokens = auth_service.create_user_tokens(user)
    
    # Create session data
    session_data = auth_service.create_session_data(user)
    
    # Sync balances with blockchain on login (non-blocking)
    try:
        print(f"Syncing balances for user {user.username} on wallet login")
        apt_balance = await aptos_service.get_account_balance(request.wallet_address, "APT")
        usdc_balance = await aptos_service.get_account_balance(request.wallet_address, "USDC")
        
        # Update database balances with actual blockchain balances
        from ..models import Balance
        balances = db.query(Balance).filter(Balance.user_id == user.id).all()
        for balance in balances:
            if balance.currency_type == "APT":
                balance.balance = apt_balance
            elif balance.currency_type == "USDC":
                balance.balance = usdc_balance
        
        db.commit()
        print(f"Wallet login balance sync completed: APT={apt_balance}, USDC={usdc_balance}")
    except Exception as e:
        print(f"Warning: Could not sync balances on wallet login: {e}")
        # Don't fail login if balance sync fails
    
    return {
        "status": "success",
        "message": "Wallet authentication successful",
        "data": {
            "user": session_data,
            "tokens": tokens
        }
    }


@router.post("/login/oauth2", response_model=TokenResponse)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible login endpoint (for OpenAPI docs)
    """
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = auth_service.create_user_tokens(user)
    
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": tokens["token_type"]
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token
    """
    new_tokens = auth_service.refresh_access_token(token_data.refresh_token, db)
    
    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return new_tokens


@router.post("/logout")
async def logout_user(current_user: User = Depends(require_authentication)):
    """
    Logout user (token invalidation would be handled by client)
    """
    # In a production system, you might want to maintain a blacklist of tokens
    # For now, we'll just return success as token invalidation is client-side
    return {
        "status": "success",
        "message": "Logged out successfully",
        "data": {
            "user_id": str(current_user.id),
            "username": current_user.username
        }
    }


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(require_authentication)):
    """
    Get current authenticated user information
    """
    session_data = auth_service.create_session_data(current_user)
    
    return {
        "status": "success",
        "message": "User information retrieved",
        "data": session_data
    }


@router.post("/password/reset-request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset (sends reset token)
    """
    user = db.query(User).filter(User.email == reset_request.email).first()
    
    if not user:
        # Don't reveal if email exists or not
        return {
            "status": "success",
            "message": "If the email exists, a reset link has been sent",
            "data": None
        }
    
    # Generate reset token
    reset_token = auth_service.generate_reset_token(str(user.id))
    
    # Send reset email
    email_sent = email_service.send_password_reset_email(
        to_email=user.email,
        reset_token=reset_token,
        username=user.username
    )
    
    if not email_sent:
        logger.warning(f"Failed to send password reset email to {user.email}")
        # Still return success to avoid revealing if email exists
    
    return {
        "status": "success",
        "message": "If the email exists, a reset link has been sent",
        "data": {
            "expires_in": "1 hour",
            "email_sent": email_sent
        }
    }


@router.post("/password/reset")
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token
    """
    # Validate new password strength
    is_valid_password, password_error = InputValidator.validate_password(reset_data.new_password)
    if not is_valid_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_error
        )
    
    user_id = auth_service.validate_reset_token(reset_data.reset_token)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash new password and update
    hashed_password = auth_service.get_password_hash(reset_data.new_password)
    user.hashed_password = hashed_password
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Password reset successfully",
        "data": {
            "user_id": str(user.id),
            "username": user.username
        }
    }


@router.post("/api-key", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: User = Depends(require_authentication)
):
    """
    Create an API key for programmatic access
    """
    api_key = auth_service.generate_api_key(str(current_user.id))
    
    return {
        "status": "success",
        "message": "API key created successfully",
        "data": {
            "api_key": api_key,
            "name": api_key_data.name,
            "expires_in": "1 year",
            "usage": "Include in Authorization header as 'Bearer <api_key>'"
        }
    }


@router.get("/api-key/validate")
async def validate_api_key(current_user: User = Depends(get_current_user)):
    """
    Validate current API key or token
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication"
        )
    
    return {
        "status": "success",
        "message": "Authentication valid",
        "data": {
            "user_id": str(current_user.id),
            "username": current_user.username,
            "is_active": current_user.is_active
        }
    }


@router.post("/export-wallet", response_model=Dict[str, Any])
async def export_wallet(
    password: str,
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Export custodial wallet data for migration to self-custody
    Users can take control of their private keys
    """
    if not current_user.is_custodial:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account is not using a custodial wallet"
        )
    
    if not current_user.encrypted_private_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No encrypted private key found for custodial account"
        )
    
    # Verify password
    if not auth_service.verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    try:
        # Export wallet data
        wallet_data = wallet_service.export_wallet_data(
            current_user.encrypted_private_key, 
            password,
            str(current_user.id)
        )
        
        if not wallet_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to decrypt wallet data"
            )
        
        # Mark wallet as exported
        current_user.wallet_exported = True
        db.commit()
        
        return {
            "status": "success",
            "message": "Wallet exported successfully. Keep this data secure!",
            "data": wallet_data,
            "security_notice": {
                "warning": "CRITICAL SECURITY WARNING",
                "instructions": [
                    "Save your private key in a secure location",
                    "Never share your private key with anyone",
                    "Anyone with this private key can control your wallet",
                    "Consider importing into Petra wallet",
                    "You can continue using Preklo or switch to self-custody"
                ]
            }
        }
        
    except Exception as e:
        print(f"Error exporting wallet: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export wallet data"
        )
