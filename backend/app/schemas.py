from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import uuid


# Base schemas
class UserBase(BaseModel):
    username: str
    wallet_address: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    profile_picture_url: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserCreateSimple(BaseModel):
    """Simple registration with just email, username, password - wallet auto-generated"""
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    terms_agreed: bool = False


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    profile_picture_url: Optional[str] = None


class User(UserBase):
    id: uuid.UUID
    is_active: bool
    is_custodial: bool = True
    wallet_exported: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WalletExportData(BaseModel):
    """Data for wallet export to self-custody"""
    wallet_address: str
    private_key: str
    export_warning: str


# Balance schemas
class BalanceBase(BaseModel):
    currency_type: str
    balance: Decimal


class Balance(BalanceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Transaction schemas
class TransactionBase(BaseModel):
    sender_address: str
    recipient_address: str
    amount: Decimal
    currency_type: str
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    recipient_username: Optional[str] = None  # Alternative to recipient_address


class Transaction(TransactionBase):
    id: uuid.UUID
    transaction_hash: str
    sender_id: uuid.UUID
    recipient_id: uuid.UUID
    transaction_type: str
    status: str
    gas_fee: Optional[Decimal] = None
    block_height: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserInfo(BaseModel):
    id: Optional[uuid.UUID] = None
    username: Optional[str] = None
    wallet_address: Optional[str] = None
    full_name: Optional[str] = None


class TransactionWithUsers(TransactionBase):
    id: uuid.UUID
    transaction_hash: str
    sender_id: uuid.UUID
    recipient_id: uuid.UUID
    transaction_type: str
    status: str
    gas_fee: Optional[Decimal] = None
    block_height: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    sender: Optional[UserInfo] = None
    recipient: Optional[UserInfo] = None
    
    class Config:
        from_attributes = True


# Payment Request schemas
class PaymentRequestBase(BaseModel):
    amount: Decimal
    currency_type: str
    description: Optional[str] = None
    expiry_hours: int = 24


class PaymentRequestCreate(PaymentRequestBase):
    recipient_id: uuid.UUID


class PaymentRequest(PaymentRequestBase):
    id: uuid.UUID
    payment_id: str
    recipient_id: uuid.UUID
    qr_code_url: Optional[str] = None
    payment_link: Optional[str] = None
    status: str
    expiry_timestamp: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Fiat Transaction schemas
class FiatTransactionBase(BaseModel):
    transaction_type: str  # deposit, withdraw
    fiat_amount: Decimal
    fiat_currency: str = "USD"
    crypto_currency: str = "USDC"


class FiatTransactionCreate(FiatTransactionBase):
    pass


class FiatTransaction(FiatTransactionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    crypto_amount: Decimal
    exchange_rate: Decimal
    status: str
    bank_reference: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Swap Transaction schemas
class SwapTransactionBase(BaseModel):
    from_currency: str
    to_currency: str
    from_amount: Decimal


class SwapTransactionCreate(SwapTransactionBase):
    pass


class SwapTransaction(SwapTransactionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    to_amount: Decimal
    exchange_rate: Decimal
    transaction_hash: Optional[str] = None
    status: str
    provider: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# API Response schemas
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class TransactionResponse(ApiResponse):
    data: Optional[Transaction] = None


class UserResponse(ApiResponse):
    data: Optional[User] = None


class PaymentRequestResponse(ApiResponse):
    data: Optional[PaymentRequest] = None


# Notification schemas
class NotificationBase(BaseModel):
    type: str
    title: str
    message: str
    data: Optional[dict] = None


class NotificationCreate(NotificationBase):
    user_id: uuid.UUID


class Notification(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    created_at: datetime


class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Username validation schemas
class UsernameCheck(BaseModel):
    username: str
    available: bool
    suggested_usernames: Optional[List[str]] = None


class UsernameResolve(BaseModel):
    username: str
    wallet_address: str
    user_id: uuid.UUID


# Transfer schemas
class TransferRequest(BaseModel):
    recipient: str  # Can be username or wallet address
    amount: Decimal
    currency_type: str = "USDC"
    description: Optional[str] = None


class PaymentLinkPayment(BaseModel):
    payment_id: str


# Authentication schemas
class UserLogin(BaseModel):
    username: str  # Can be username or email
    password: str
    remember_me: bool = False


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserLoginResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any]


class UserResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any]


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    reset_token: str
    new_password: str


class WalletLoginRequest(BaseModel):
    username: str
    wallet_address: str


class APIKeyCreate(BaseModel):
    name: str
    description: Optional[str] = None


class APIKeyResponse(BaseModel):
    status: str
    message: str
    data: Dict[str, Any]


class CustodialTransactionRequest(BaseModel):
    """Request to send money using custodial wallet (password-based signing)"""
    recipient_username: str
    amount: str
    currency_type: str = "APT"
    password: str
    description: Optional[str] = None


class PetraTransactionRequest(BaseModel):
    """Request to send money using Petra wallet (wallet-based signing)"""
    recipient_username: str
    amount: str
    currency_type: str = "APT"
    description: Optional[str] = None
    # Note: Petra wallet handles signing on the client side


class CustodialTransactionResponse(BaseModel):
    """Response from custodial transaction"""
    transaction_hash: str
    sender_address: str
    recipient_address: str
    amount: str
    currency_type: str
    status: str = "confirmed"


# Enhanced Send Money Schemas for Story 2.3
class SendMoneyRequest(BaseModel):
    """Request to send money with enhanced validation"""
    recipient_username: str
    amount: str
    currency_type: str = "APT"
    password: str
    description: Optional[str] = None


class SendMoneyConfirmation(BaseModel):
    """Transaction confirmation details"""
    transaction_id: str
    recipient_username: str
    recipient_address: str
    amount: str
    currency_type: str
    gas_fee: Optional[str] = None
    total_cost: Optional[str] = None
    description: Optional[str] = None
    expires_at: datetime


class SendMoneyResponse(BaseModel):
    """Response from send money operation"""
    success: bool
    message: str
    transaction_id: Optional[str] = None
    transaction_hash: Optional[str] = None
    status: Optional[str] = None
    data: Optional[dict] = None


class TransactionStatusUpdate(BaseModel):
    """Real-time transaction status update"""
    transaction_id: str
    transaction_hash: str
    status: str  # pending, confirmed, failed
    block_height: Optional[int] = None
    gas_fee: Optional[str] = None
    updated_at: datetime


# Unlimit Card Schemas
class UnlimitCardBase(BaseModel):
    card_type: str  # virtual, physical
    currency: str = "USD"
    region: str  # US, BR, ZA, etc.


class UnlimitCardCreate(UnlimitCardBase):
    user_id: str


class UnlimitCard(UnlimitCardBase):
    id: uuid.UUID
    user_id: uuid.UUID
    unlimit_card_id: str
    unlimit_user_id: str
    card_status: str
    last_four: Optional[str] = None
    expiry_month: Optional[int] = None
    expiry_year: Optional[int] = None
    card_program: Optional[str] = None
    spending_limits: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UnlimitTransactionBase(BaseModel):
    amount: Decimal
    currency: str
    merchant_name: Optional[str] = None


class UnlimitTransactionCreate(UnlimitTransactionBase):
    card_id: str
    transaction_type: str
    unlimit_transaction_id: str


class UnlimitTransaction(UnlimitTransactionBase):
    id: uuid.UUID
    card_id: uuid.UUID
    user_id: uuid.UUID
    unlimit_transaction_id: str
    transaction_type: str
    transaction_status: str
    decline_reason: Optional[str] = None
    auth_code: Optional[str] = None
    merchant_category: Optional[str] = None
    wallet_balance_before: Optional[Decimal] = None
    wallet_balance_after: Optional[Decimal] = None
    processing_fee: Optional[Decimal] = None
    exchange_rate: Optional[Decimal] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Unlimit API Request/Response Schemas
class CardCreationRequest(BaseModel):
    user_id: str
    card_type: str = "virtual"  # virtual or physical
    currency: str = "USD"
    region: str = "US"
    spending_limits: Optional[Dict[str, Any]] = None


class CardCreationResponse(BaseModel):
    success: bool
    message: str
    data: Optional[UnlimitCard] = None


class CardAuthorizationRequest(BaseModel):
    """Incoming authorization request from Unlimit webhook"""
    transaction_id: str
    card_id: str
    amount: Decimal
    currency: str
    merchant_name: Optional[str] = None
    merchant_category: Optional[str] = None


class CardAuthorizationResponse(BaseModel):
    """Response to Unlimit for authorization"""
    approved: bool
    decline_reason: Optional[str] = None
    auth_code: Optional[str] = None


class UnlimitWebhookPayload(BaseModel):
    """Webhook payload from Unlimit"""
    event_type: str
    webhook_id: str
    data: Dict[str, Any]
    timestamp: datetime


# Payment Request Schemas
class PaymentRequestCreate(BaseModel):
    """Schema for creating a payment request"""
    recipient_username: str
    amount: Decimal
    currency: str = "USDC"
    description: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

    @field_validator('recipient_username')
    @classmethod
    def validate_recipient_username(cls, v):
        if not v or not v.strip():
            raise ValueError('Recipient username is required')
        if not v.startswith('@'):
            v = '@' + v
        return v


class PaymentRequestUpdate(BaseModel):
    """Schema for updating a payment request"""
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v


class PaymentRequestResponse(BaseModel):
    """Schema for payment request response"""
    id: uuid.UUID
    sender_id: uuid.UUID
    recipient_id: uuid.UUID
    amount: Decimal
    currency: str
    description: Optional[str] = None
    status: str
    expires_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    transaction_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Additional fields for response
    sender_username: Optional[str] = None
    recipient_username: Optional[str] = None
    
    class Config:
        from_attributes = True


class PaymentRequestTemplate(BaseModel):
    """Schema for payment request template"""
    name: str
    amount: Decimal
    description: str
    currency: str = "USDC"


class PaymentRequestListResponse(BaseModel):
    """Schema for payment request list response"""
    payment_requests: List[PaymentRequestResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


# Voucher Schemas
class VoucherCreate(BaseModel):
    """Schema for creating a voucher"""
    amount: Decimal
    currency: str = "USDC"
    pin: Optional[str] = None
    expires_in_hours: int = 24  # Default 24 hours

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 10000:  # Max $10,000 per voucher
            raise ValueError('Amount cannot exceed $10,000')
        return v

    @field_validator('pin')
    @classmethod
    def validate_pin(cls, v):
        if v is not None:
            if len(v) < 4 or len(v) > 6:
                raise ValueError('PIN must be between 4 and 6 digits')
            if not v.isdigit():
                raise ValueError('PIN must contain only digits')
        return v

    @field_validator('expires_in_hours')
    @classmethod
    def validate_expires_in_hours(cls, v):
        if v < 1 or v > 168:  # Between 1 hour and 1 week
            raise ValueError('Expiration must be between 1 hour and 1 week')
        return v


class VoucherRedeem(BaseModel):
    """Schema for redeeming a voucher"""
    voucher_code: str
    pin: Optional[str] = None

    @field_validator('voucher_code')
    @classmethod
    def validate_voucher_code(cls, v):
        if not v or len(v) != 20:
            raise ValueError('Invalid voucher code format')
        return v.upper()


class VoucherResponse(BaseModel):
    """Schema for voucher response"""
    id: uuid.UUID
    voucher_code: str
    creator_id: uuid.UUID
    amount: Decimal
    currency: str
    status: str
    has_pin: bool
    expires_at: datetime
    redeemed_at: Optional[datetime] = None
    redeemed_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Additional fields for response
    creator_username: Optional[str] = None
    redeemer_username: Optional[str] = None
    time_remaining: Optional[str] = None
    
    class Config:
        from_attributes = True


class VoucherListResponse(BaseModel):
    """Schema for voucher list response"""
    vouchers: List[VoucherResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class VoucherAgent(BaseModel):
    """Schema for voucher agent"""
    id: uuid.UUID
    name: str
    address: str
    city: str
    country: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Security Schemas
class SecurityEventResponse(BaseModel):
    """Schema for security event response"""
    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    risk_score: int
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TrustedDeviceResponse(BaseModel):
    """Schema for trusted device response"""
    id: uuid.UUID
    user_id: uuid.UUID
    device_name: str
    device_fingerprint: str
    device_type: Optional[str] = None
    is_trusted: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TrustedDeviceCreate(BaseModel):
    """Schema for creating a trusted device"""
    device_name: str
    device_fingerprint: str
    device_type: Optional[str] = None

    @field_validator('device_name')
    @classmethod
    def validate_device_name(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('Device name must be at least 2 characters')
        return v.strip()

    @field_validator('device_fingerprint')
    @classmethod
    def validate_device_fingerprint(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Invalid device fingerprint')
        return v


class BiometricCredentialResponse(BaseModel):
    """Schema for biometric credential response"""
    id: uuid.UUID
    user_id: uuid.UUID
    credential_type: str
    credential_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class BiometricCredentialCreate(BaseModel):
    """Schema for creating a biometric credential"""
    credential_type: str
    credential_id: str
    public_key: Optional[str] = None

    @field_validator('credential_type')
    @classmethod
    def validate_credential_type(cls, v):
        allowed_types = ['fingerprint', 'face_id', 'voice', 'webauthn']
        if v not in allowed_types:
            raise ValueError(f'Credential type must be one of: {", ".join(allowed_types)}')
        return v

    @field_validator('credential_id')
    @classmethod
    def validate_credential_id(cls, v):
        if not v or len(v) < 10:
            raise ValueError('Invalid credential ID')
        return v


class SecurityStatusResponse(BaseModel):
    """Schema for security status response"""
    user_id: uuid.UUID
    has_biometric_auth: bool
    trusted_devices_count: int
    last_security_event: Optional[SecurityEventResponse] = None
    risk_score: int
    security_recommendations: List[str] = []
    mfa_enabled: bool
    session_timeout_minutes: int


class RiskAssessmentRequest(BaseModel):
    """Schema for risk assessment request"""
    transaction_amount: Optional[Decimal] = None
    transaction_type: Optional[str] = None
    recipient_username: Optional[str] = None
    device_fingerprint: Optional[str] = None
    location_data: Optional[Dict[str, Any]] = None

    @field_validator('transaction_amount')
    @classmethod
    def validate_transaction_amount(cls, v):
        if v is not None and v < 0:
            raise ValueError('Transaction amount cannot be negative')
        return v


class RiskAssessmentResponse(BaseModel):
    """Schema for risk assessment response"""
    risk_score: int  # 0-100
    risk_level: str  # low, medium, high, critical
    risk_factors: List[str] = []
    recommendations: List[str] = []
    requires_additional_auth: bool = False
    estimated_processing_time: Optional[int] = None  # seconds
