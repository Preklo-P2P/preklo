import qrcode
import qrcode.image.svg
from io import BytesIO
import base64
from typing import Optional
import uuid
import secrets
from decimal import Decimal
from ..config import settings


class PaymentService:
    def __init__(self):
        self.base_url = "https://preklo.com"  # This would be your actual domain
        
    def generate_payment_id(self) -> str:
        """Generate a unique payment ID"""
        return secrets.token_urlsafe(32)
    
    def generate_payment_link(
        self,
        payment_id: str,
        recipient_username: str,
        amount: Decimal,
        currency_type: str,
        description: Optional[str] = None
    ) -> str:
        """Generate a payment link"""
        link = f"{self.base_url}/pay/{payment_id}"
        return link
    
    def generate_qr_code_data_url(
        self,
        payment_id: str,
        recipient_username: str,
        amount: Decimal,
        currency_type: str,
        description: Optional[str] = None
    ) -> str:
        """Generate QR code as base64 data URL"""
        # Create payment URL for QR code
        payment_url = self.generate_payment_link(
            payment_id, recipient_username, amount, currency_type, description
        )
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_url)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def generate_qr_code_svg(
        self,
        payment_id: str,
        recipient_username: str,
        amount: Decimal,
        currency_type: str,
        description: Optional[str] = None
    ) -> str:
        """Generate QR code as SVG string"""
        # Create payment URL for QR code
        payment_url = self.generate_payment_link(
            payment_id, recipient_username, amount, currency_type, description
        )
        
        # Generate QR code as SVG
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_url)
        qr.make(fit=True)
        
        factory = qrcode.image.svg.SvgPathImage
        img = qr.make_image(image_factory=factory)
        
        # Convert SVG to string
        buffer = BytesIO()
        img.save(buffer)
        return buffer.getvalue().decode('utf-8')
    
    def validate_payment_amount(self, amount: Decimal, currency_type: str) -> bool:
        """Validate payment amount based on currency type"""
        if amount <= 0:
            return False
            
        # Set minimum amounts based on currency
        min_amounts = {
            "USDC": Decimal("0.01"),  # $0.01 minimum
            "APT": Decimal("0.001"),   # 0.001 APT minimum
            "USDT": Decimal("0.01"),   # $0.01 minimum
        }
        
        min_amount = min_amounts.get(currency_type, Decimal("0.01"))
        return amount >= min_amount
    
    def calculate_fees(self, amount: Decimal, currency_type: str) -> Decimal:
        """Calculate transaction fees (mock implementation)"""
        # For testnet, we'll use minimal fees
        base_fees = {
            "USDC": Decimal("0.01"),  # $0.01 fee
            "APT": Decimal("0.001"),   # 0.001 APT fee
            "USDT": Decimal("0.01"),   # $0.01 fee
        }
        
        return base_fees.get(currency_type, Decimal("0.01"))
    
    def format_amount(self, amount: Decimal, currency_type: str) -> str:
        """Format amount for display"""
        if currency_type in ["USDC", "USDT"]:
            return f"${amount:.2f}"
        elif currency_type == "APT":
            return f"{amount:.4f} APT"
        else:
            return f"{amount} {currency_type}"


# Global service instance
payment_service = PaymentService()
