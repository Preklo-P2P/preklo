from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

# Try multiple import strategies to handle different loading contexts
try:
    from .database import GUID, Base
except (ImportError, AttributeError):
    try:
        from app.database import GUID, Base
    except (ImportError, AttributeError):
        # Last resort: import database module and get attributes directly
        import sys
        import os
        # Add parent directory to path if needed
        backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        from app.database import GUID, Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    username = Column(String(32), unique=True, nullable=False, index=True)
    wallet_address = Column(String(66), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=True)
    profile_picture_url = Column(String(512), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Custodial wallet fields
    is_custodial = Column(Boolean, default=True)  # True for auto-generated wallets
    encrypted_private_key = Column(Text, nullable=True)  # Encrypted private key for custodial wallets
    wallet_exported = Column(Boolean, default=False)  # Whether user has exported their wallet
    
    # Terms and legal
    terms_agreed = Column(Boolean, default=False)  # Whether user agreed to terms and conditions
    terms_agreed_at = Column(DateTime(timezone=True), nullable=True)  # When user agreed to terms
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sent_transactions = relationship("Transaction", foreign_keys="Transaction.sender_id", back_populates="sender")
    received_transactions = relationship("Transaction", foreign_keys="Transaction.recipient_id", back_populates="recipient")
    # sent_payment_requests removed - PaymentRequest model doesn't have sender_id field
    received_payment_requests = relationship("PaymentRequest", foreign_keys="PaymentRequest.recipient_id", back_populates="recipient")
    created_vouchers = relationship("Voucher", foreign_keys="Voucher.creator_id", back_populates="creator")
    redeemed_vouchers = relationship("Voucher", foreign_keys="Voucher.redeemed_by", back_populates="redeemer")
    security_events = relationship("SecurityEvent", back_populates="user")
    trusted_devices = relationship("TrustedDevice", back_populates="user")
    biometric_credentials = relationship("BiometricCredential", back_populates="user")
    balances = relationship("Balance", back_populates="user")
    unlimit_cards = relationship("UnlimitCard", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    transaction_limits = relationship("TransactionLimit", back_populates="user")
    spending_controls = relationship("SpendingControl", back_populates="user")
    transaction_approvals = relationship("TransactionApproval", back_populates="user")
    emergency_blocks = relationship("EmergencyBlock", back_populates="user")
    spending_alerts = relationship("SpendingAlert", back_populates="user")


class Balance(Base):
    __tablename__ = "balances"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    currency_type = Column(String(10), nullable=False)  # USDC, APT, etc.
    balance = Column(Numeric(20, 8), default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="balances")
    
    # Composite index for user and currency
    __table_args__ = (
        {'schema': None},
    )


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    transaction_hash = Column(String(66), unique=True, nullable=False, index=True)
    sender_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    sender_address = Column(String(66), nullable=False)
    recipient_address = Column(String(66), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    currency_type = Column(String(10), nullable=False)
    transaction_type = Column(String(20), default="transfer")  # transfer, payment_request, swap, card_present, card_not_present, merchant
    status = Column(String(20), default="pending")  # pending, confirmed, failed
    description = Column(Text, nullable=True)
    gas_fee = Column(Numeric(20, 8), nullable=True)
    block_height = Column(Integer, nullable=True)
    
    # Fee collection fields
    fee_amount = Column(Numeric(20, 8), nullable=True, default=0.0)
    fee_percentage = Column(Numeric(5, 2), nullable=True)  # Fee percentage in basis points
    fee_collected = Column(Boolean, default=False)
    revenue_wallet_address = Column(String(66), nullable=True)  # Where fees were sent
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_transactions")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_transactions")


class PaymentRequest(Base):
    __tablename__ = "payment_requests"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    payment_id = Column(String(64), nullable=False, unique=True)
    recipient_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    currency_type = Column(String(10), nullable=False)
    description = Column(Text, nullable=True)
    qr_code_url = Column(Text, nullable=True)
    payment_link = Column(String(512), nullable=True)
    status = Column(String(20), default="pending")  # pending, paid, expired, cancelled
    expiry_timestamp = Column(DateTime(timezone=True), nullable=False)
    transaction_id = Column(GUID, ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="received_payment_requests")
    transaction = relationship("Transaction")


class Voucher(Base):
    __tablename__ = "vouchers"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    voucher_code = Column(String(20), unique=True, nullable=False, index=True)
    creator_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    currency_type = Column(String(10), nullable=False, default="USDC")
    status = Column(String(20), default="active")  # active, redeemed, expired, cancelled
    pin_hash = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    redeemed_at = Column(DateTime(timezone=True), nullable=True)
    redeemed_by = Column(GUID, ForeignKey("users.id"), nullable=True)
    agent_id = Column(GUID, nullable=True)  # Voucher agent who processed redemption
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_vouchers")
    redeemer = relationship("User", foreign_keys=[redeemed_by], back_populates="redeemed_vouchers")


class SecurityEvent(Base):
    __tablename__ = "security_events"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(50), nullable=False)  # login, transaction, device_change, etc.
    event_data = Column(JSON, nullable=True)
    risk_score = Column(Integer, default=0)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    device_id = Column(String(255), nullable=True)
    location_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="security_events")


class TrustedDevice(Base):
    __tablename__ = "trusted_devices"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    device_name = Column(String(255), nullable=False)
    device_fingerprint = Column(String(255), nullable=False, unique=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    is_trusted = Column(Boolean, default=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="trusted_devices")


class BiometricCredential(Base):
    __tablename__ = "biometric_credentials"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    credential_type = Column(String(50), nullable=False)  # fingerprint, face_id, voice, webauthn
    credential_id = Column(String(255), nullable=False, unique=True)
    public_key = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="biometric_credentials")


class FiatTransaction(Base):
    __tablename__ = "fiat_transactions"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    transaction_type = Column(String(20), nullable=False)  # deposit, withdraw
    fiat_amount = Column(Numeric(12, 2), nullable=False)
    fiat_currency = Column(String(3), default="USD")
    crypto_amount = Column(Numeric(20, 8), nullable=False)
    crypto_currency = Column(String(10), nullable=False)
    exchange_rate = Column(Numeric(12, 6), nullable=False)
    status = Column(String(20), default="pending")  # pending, completed, failed
    bank_reference = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")


class SwapTransaction(Base):
    __tablename__ = "swap_transactions"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    from_currency = Column(String(10), nullable=False)
    to_currency = Column(String(10), nullable=False)
    from_amount = Column(Numeric(20, 8), nullable=False)
    to_amount = Column(Numeric(20, 8), nullable=False)
    exchange_rate = Column(Numeric(12, 6), nullable=False)
    transaction_hash = Column(String(66), nullable=True)
    status = Column(String(20), default="pending")  # pending, completed, failed
    provider = Column(String(50), default="hyperion")  # hyperion, merkle_trade
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")


class UnlimitCard(Base):
    __tablename__ = "unlimit_cards"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    unlimit_card_id = Column(String(100), unique=True, nullable=False, index=True)
    unlimit_user_id = Column(String(100), nullable=False, index=True)
    card_type = Column(String(20), nullable=False)  # virtual, physical
    card_status = Column(String(20), default="active")  # active, inactive, blocked, expired
    last_four = Column(String(4), nullable=True)
    expiry_month = Column(Integer, nullable=True)
    expiry_year = Column(Integer, nullable=True)
    currency = Column(String(3), default="USD")
    region = Column(String(5), nullable=False)  # US, BR, ZA, etc.
    card_program = Column(String(50), nullable=True)
    spending_limits = Column(Text, nullable=True)  # JSON string for limits
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="unlimit_cards")
    transactions = relationship("UnlimitTransaction", back_populates="card")


class UnlimitTransaction(Base):
    __tablename__ = "unlimit_transactions"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    card_id = Column(GUID, ForeignKey("unlimit_cards.id"), nullable=False)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    unlimit_transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    transaction_type = Column(String(30), nullable=False)  # authorization, settlement, refund
    amount = Column(Numeric(20, 8), nullable=False)
    currency = Column(String(3), nullable=False)
    merchant_name = Column(String(255), nullable=True)
    merchant_category = Column(String(10), nullable=True)  # MCC code
    transaction_status = Column(String(20), nullable=False)  # approved, declined, pending
    decline_reason = Column(String(100), nullable=True)
    auth_code = Column(String(20), nullable=True)
    wallet_balance_before = Column(Numeric(20, 8), nullable=True)
    wallet_balance_after = Column(Numeric(20, 8), nullable=True)
    processing_fee = Column(Numeric(10, 4), nullable=True)
    exchange_rate = Column(Numeric(12, 6), nullable=True)
    original_amount = Column(Numeric(20, 8), nullable=True)  # For currency conversion
    original_currency = Column(String(3), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    card = relationship("UnlimitCard", back_populates="transactions")
    user = relationship("User")


class UnlimitWebhook(Base):
    __tablename__ = "unlimit_webhooks"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    webhook_id = Column(String(100), unique=True, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # card.transaction.authorized, etc.
    status = Column(String(20), default="received")  # received, processed, failed
    payload = Column(Text, nullable=False)  # JSON payload from Unlimit
    signature = Column(String(255), nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class FeeCollection(Base):
    __tablename__ = "fee_collections"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    transaction_id = Column(GUID, ForeignKey("transactions.id"), nullable=False)
    currency_type = Column(String(10), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    fee_percentage = Column(Numeric(5, 2), nullable=False)  # Fee percentage in basis points
    transaction_type = Column(String(20), nullable=False)  # p2p_domestic, p2p_cross_border, card_present, etc.
    revenue_wallet_address = Column(String(66), nullable=False)
    blockchain_tx_hash = Column(String(66), nullable=True)  # Transaction hash for fee collection
    status = Column(String(20), default="pending")  # pending, collected, failed
    collected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    transaction = relationship("Transaction")


class FeeWithdrawal(Base):
    __tablename__ = "fee_withdrawals"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    currency_type = Column(String(10), nullable=False)
    amount = Column(Numeric(20, 8), nullable=False)
    destination_address = Column(String(66), nullable=False)
    blockchain_tx_hash = Column(String(66), nullable=True)
    status = Column(String(20), default="pending")  # pending, completed, failed
    withdrawal_reason = Column(String(255), nullable=True)  # e.g., "monthly_revenue_withdrawal"
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    type = Column(String(50), nullable=False)  # payment_request, payment_received, payment_sent, system
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    data = Column(JSON, nullable=True)  # Additional data like payment_id, amount, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notifications")


# Transaction Limits and Controls Models for Story 2.6

class TransactionLimit(Base):
    __tablename__ = "transaction_limits"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    limit_type = Column(String(20), nullable=False)  # daily, weekly, monthly
    currency_type = Column(String(10), nullable=False)  # APT, USDC, etc.
    limit_amount = Column(Numeric(20, 8), nullable=False)
    current_usage = Column(Numeric(20, 8), default=0.0)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transaction_limits")


class SpendingControl(Base):
    __tablename__ = "spending_controls"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    control_type = Column(String(30), nullable=False)  # max_amount, merchant_category, geographic, time_based
    currency_type = Column(String(10), nullable=False)
    max_amount = Column(Numeric(20, 8), nullable=True)
    merchant_categories = Column(JSON, nullable=True)  # List of restricted categories
    allowed_countries = Column(JSON, nullable=True)  # List of allowed countries
    blocked_countries = Column(JSON, nullable=True)  # List of blocked countries
    allowed_hours = Column(JSON, nullable=True)  # Allowed time ranges
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="spending_controls")


class TransactionApproval(Base):
    __tablename__ = "transaction_approvals"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    transaction_id = Column(GUID, ForeignKey("transactions.id"), nullable=True)
    approval_type = Column(String(30), nullable=False)  # high_value, suspicious, manual_review
    amount = Column(Numeric(20, 8), nullable=False)
    currency_type = Column(String(10), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, approved, rejected, expired
    approval_method = Column(String(30), nullable=True)  # mfa, email, sms, manual
    approved_by = Column(GUID, nullable=True)  # User ID who approved
    approved_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transaction_approvals")
    transaction = relationship("Transaction")


class EmergencyBlock(Base):
    __tablename__ = "emergency_blocks"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    block_type = Column(String(30), nullable=False)  # account_freeze, transaction_block, card_block
    reason = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    blocked_by = Column(GUID, nullable=True)  # User ID who initiated block
    unblocked_by = Column(GUID, nullable=True)  # User ID who unblocked
    unblocked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="emergency_blocks")


class SpendingAlert(Base):
    __tablename__ = "spending_alerts"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    alert_type = Column(String(30), nullable=False)  # limit_threshold, unusual_spending, large_transaction
    limit_type = Column(String(20), nullable=True)  # daily, weekly, monthly
    threshold_percentage = Column(Numeric(5, 2), nullable=True)  # 80% of limit
    currency_type = Column(String(10), nullable=False)
    amount_threshold = Column(Numeric(20, 8), nullable=True)
    is_active = Column(Boolean, default=True)
    notification_methods = Column(JSON, nullable=True)  # email, sms, push
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="spending_alerts")


class FamilyAccount(Base):
    __tablename__ = "family_accounts"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    parent_user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    child_user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    relationship_type = Column(String(20), nullable=False)  # parent, guardian, family_member
    spending_limit = Column(Numeric(20, 8), nullable=True)
    currency_type = Column(String(10), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent_user = relationship("User", foreign_keys=[parent_user_id])
    child_user = relationship("User", foreign_keys=[child_user_id])


class BusinessAccount(Base):
    __tablename__ = "business_accounts"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    organization_id = Column(GUID, nullable=False)
    admin_user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    employee_user_id = Column(GUID, ForeignKey("users.id"), nullable=False)
    role = Column(String(30), nullable=False)  # admin, manager, employee
    spending_limit = Column(Numeric(20, 8), nullable=True)
    currency_type = Column(String(10), nullable=False)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    admin_user = relationship("User", foreign_keys=[admin_user_id])
    employee_user = relationship("User", foreign_keys=[employee_user_id])


class Waitlist(Base):
    __tablename__ = "waitlist"
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    country = Column(String(100), nullable=False)  # Selected country from dropdown
    custom_country = Column(String(100), nullable=True)  # Custom country if "Other" is selected
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
