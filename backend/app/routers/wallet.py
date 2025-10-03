from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from ..database import get_db
from ..models import User
from ..schemas import ApiResponse
from ..services.wallet_service import wallet_service
from ..services.aptos_service import aptos_service
from ..dependencies import require_authentication, rate_limit

router = APIRouter()


class WalletExportRequest(BaseModel):
    password: str


class WalletBackupRequest(BaseModel):
    password: str


@router.get("/status", response_model=ApiResponse)
async def get_wallet_status(
    current_user: User = Depends(require_authentication)
):
    """
    Get wallet status including security and backup information
    """
    try:
        # Get security status
        security_status = wallet_service.get_security_status(str(current_user.id))
        
        # Get backup status
        backup_status = wallet_service.get_backup_status(str(current_user.id))
        
        # Get wallet information
        wallet_info = {
            "wallet_address": current_user.wallet_address,
            "is_custodial": current_user.is_custodial,
            "wallet_exported": current_user.wallet_exported,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        }
        
        return ApiResponse(
            success=True,
            message="Wallet status retrieved",
            data={
                "wallet_info": wallet_info,
                "security_status": security_status,
                "backup_status": backup_status
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get wallet status: {str(e)}",
            data=None
        )


@router.get("/balance", response_model=ApiResponse)
async def get_wallet_balance(
    current_user: User = Depends(require_authentication)
):
    """
    Get current wallet balance for all supported tokens
    """
    try:
        # Get balances from blockchain
        apt_balance = await aptos_service.get_account_balance(current_user.wallet_address, "APT")
        usdc_balance = await aptos_service.get_account_balance(current_user.wallet_address, "USDC")
        
        return ApiResponse(
            success=True,
            message="Wallet balance retrieved",
            data={
                "wallet_address": current_user.wallet_address,
                "balances": {
                    "APT": str(apt_balance),
                    "USDC": str(usdc_balance)
                }
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get wallet balance: {str(e)}",
            data=None
        )


@router.post("/export", response_model=ApiResponse)
async def export_wallet(
    request: WalletExportRequest,
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=3, window_seconds=3600))  # 3 per hour
):
    """
    Export wallet data for self-custody migration
    """
    if not current_user.is_custodial or not current_user.encrypted_private_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only custodial wallets can be exported"
        )
    
    try:
        # Export wallet data
        wallet_data = wallet_service.export_wallet_data(
            current_user.encrypted_private_key,
            request.password,
            str(current_user.id)
        )
        
        if not wallet_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to export wallet. Check your password or try again later."
            )
        
        return ApiResponse(
            success=True,
            message="Wallet exported successfully",
            data=wallet_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to export wallet: {str(e)}",
            data=None
        )


@router.post("/backup", response_model=ApiResponse)
async def backup_wallet(
    request: WalletBackupRequest,
    current_user: User = Depends(require_authentication),
    _rate_limit: bool = Depends(rate_limit(max_requests=1, window_seconds=86400))  # 1 per day
):
    """
    Create wallet backup (same as export but with different rate limiting)
    """
    if not current_user.is_custodial or not current_user.encrypted_private_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only custodial wallets can be backed up"
        )
    
    try:
        # Check backup status
        backup_status = wallet_service.get_backup_status(str(current_user.id))
        if not backup_status["can_backup"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Backup cooldown active. Try again in {backup_status['cooldown_remaining']}"
            )
        
        # Export wallet data
        wallet_data = wallet_service.export_wallet_data(
            current_user.encrypted_private_key,
            request.password,
            str(current_user.id)
        )
        
        if not wallet_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to backup wallet. Check your password or try again later."
            )
        
        return ApiResponse(
            success=True,
            message="Wallet backed up successfully",
            data=wallet_data
        )
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to backup wallet: {str(e)}",
            data=None
        )


@router.get("/backup-status", response_model=ApiResponse)
async def get_backup_status(
    current_user: User = Depends(require_authentication)
):
    """
    Get wallet backup status and cooldown information
    """
    try:
        backup_status = wallet_service.get_backup_status(str(current_user.id))
        
        return ApiResponse(
            success=True,
            message="Backup status retrieved",
            data=backup_status
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get backup status: {str(e)}",
            data=None
        )


@router.get("/security-status", response_model=ApiResponse)
async def get_security_status(
    current_user: User = Depends(require_authentication)
):
    """
    Get wallet security status including failed attempts and lockout information
    """
    try:
        security_status = wallet_service.get_security_status(str(current_user.id))
        
        return ApiResponse(
            success=True,
            message="Security status retrieved",
            data=security_status
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get security status: {str(e)}",
            data=None
        )


@router.post("/validate-address", response_model=ApiResponse)
async def validate_wallet_address(
    address: str,
    current_user: User = Depends(require_authentication)
):
    """
    Validate Aptos wallet address format
    """
    try:
        is_valid = wallet_service.validate_wallet_address(address)
        
        return ApiResponse(
            success=True,
            message="Address validation completed",
            data={
                "address": address,
                "is_valid": is_valid
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to validate address: {str(e)}",
            data=None
        )


@router.get("/transactions", response_model=ApiResponse)
async def get_wallet_transactions(
    limit: int = 25,
    start: int = None,
    current_user: User = Depends(require_authentication)
):
    """
    Get wallet transaction history from blockchain
    """
    try:
        transactions = await aptos_service.get_account_transactions(
            current_user.wallet_address,
            limit=limit,
            start=start
        )
        
        return ApiResponse(
            success=True,
            message="Wallet transactions retrieved",
            data={
                "wallet_address": current_user.wallet_address,
                "transactions": transactions,
                "count": len(transactions)
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to get wallet transactions: {str(e)}",
            data=None
        )


@router.post("/sync-balance", response_model=ApiResponse)
async def sync_wallet_balance(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Sync wallet balance with blockchain
    """
    try:
        # Get balances from blockchain
        apt_balance = await aptos_service.get_account_balance(current_user.wallet_address, "APT")
        usdc_balance = await aptos_service.get_account_balance(current_user.wallet_address, "USDC")
        
        # Update database balances
        from ..models import Balance
        balances = db.query(Balance).filter(Balance.user_id == current_user.id).all()
        
        for balance in balances:
            if balance.currency_type == "APT":
                balance.balance = apt_balance
            elif balance.currency_type == "USDC":
                balance.balance = usdc_balance
        
        db.commit()
        
        return ApiResponse(
            success=True,
            message="Wallet balance synced successfully",
            data={
                "wallet_address": current_user.wallet_address,
                "balances": {
                    "APT": str(apt_balance),
                    "USDC": str(usdc_balance)
                }
            }
        )
    except Exception as e:
        return ApiResponse(
            success=False,
            message=f"Failed to sync wallet balance: {str(e)}",
            data=None
        )
