"""
Deposit Routes
Handles wallet address deposit functionality for crypto users
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import qrcode
import io
import base64

from ..database import get_db
from ..models import User
from ..dependencies import require_authentication
from ..config import settings

router = APIRouter()


def generate_qr_code_data_url(data: str) -> str:
    """Generate QR code as base64 data URL"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return ""


@router.get("/wallet-address")
async def get_wallet_address(
    current_user: User = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Get user's wallet address for deposits
    Returns wallet address, QR code, and instructions
    """
    try:
        wallet_address = current_user.wallet_address
        
        if not wallet_address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Wallet address not found for user"
            )
        
        # Generate QR code with wallet address
        # Format: aptos:0x... (Aptos URI scheme) or plain address
        qr_data = wallet_address  # Can also use: f"aptos:{wallet_address}"
        qr_code_data_url = generate_qr_code_data_url(qr_data)
        
        return {
            "status": "success",
            "data": {
                "wallet_address": wallet_address,
                "qr_code": qr_code_data_url,
                "network": "Aptos",
                "supported_currencies": ["USDC", "APT"],
                "instructions": {
                    "title": "How to deposit",
                    "steps": [
                        "Send USDC or APT to the address above",
                        "You can scan the QR code or copy the address",
                        "Your balance will update automatically when funds arrive",
                        "Make sure you're sending on Aptos network"
                    ],
                    "note": "Only send USDC or APT. Sending other tokens may result in loss of funds."
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving wallet address: {str(e)}"
        )

