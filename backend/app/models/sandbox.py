"""
Sandbox-specific models for API Sandbox infrastructure.

All models use the 'sandbox' schema to isolate sandbox data from production.
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

# Try relative import first, fall back to absolute import
try:
    from ..database import Base, GUID
except (ImportError, AttributeError):
    from app.database import Base, GUID


class TestAccount(Base):
    """Test account model for sandbox users."""
    __tablename__ = "test_accounts"
    __table_args__ = {'schema': 'sandbox'}
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    sandbox_user_id = Column(GUID, nullable=False, index=True)
    username = Column(String(32), nullable=False, index=True)
    wallet_address = Column(String(66), nullable=False, index=True)
    usdc_balance = Column(Numeric(20, 8), default=0.0, nullable=False)
    apt_balance = Column(Numeric(20, 8), default=0.0, nullable=False)
    original_usdc_balance = Column(Numeric(20, 8), nullable=False)  # For reset functionality
    original_apt_balance = Column(Numeric(20, 8), nullable=False)  # For reset functionality
    currency_type = Column(String(10), nullable=False)  # USDC, APT, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    # Note: sandbox_user relationship would reference sandbox.users if we create that model
    # For now, we'll use sandbox_user_id as a foreign key reference


class SandboxAPIKey(Base):
    """API key model for sandbox authentication."""
    __tablename__ = "api_keys"
    __table_args__ = {'schema': 'sandbox'}
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    sandbox_user_id = Column(GUID, nullable=False, index=True)
    key_hash = Column(String(255), nullable=False, unique=True, index=True)
    key_prefix = Column(String(16), nullable=False)  # First 8-12 chars for display (e.g., "sb_abc12345")
    name = Column(String(100), nullable=True)  # User-defined name for the key
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    # Note: sandbox_user relationship would reference sandbox.users if we create that model


class WebhookSubscription(Base):
    """Webhook subscription model for sandbox users."""
    __tablename__ = "webhook_subscriptions"
    __table_args__ = {'schema': 'sandbox'}
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    sandbox_user_id = Column(GUID, nullable=False, index=True)
    url = Column(String(512), nullable=False)
    events = Column(JSON, nullable=False)  # List of event types (e.g., ["transaction.created", "payment.completed"])
    secret = Column(String(255), nullable=False)  # HMAC signature secret
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    deliveries = relationship("WebhookDelivery", back_populates="subscription")


class WebhookDelivery(Base):
    """Webhook delivery log model for tracking webhook deliveries."""
    __tablename__ = "webhook_deliveries"
    __table_args__ = {'schema': 'sandbox'}
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    subscription_id = Column(GUID, ForeignKey('sandbox.webhook_subscriptions.id'), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False)  # pending, delivered, failed
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    subscription = relationship("WebhookSubscription", back_populates="deliveries")


class SandboxAnalytics(Base):
    """Analytics event model for tracking sandbox usage."""
    __tablename__ = "analytics"
    __table_args__ = {'schema': 'sandbox'}
    
    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    sandbox_user_id = Column(GUID, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # signup, api_call, transaction, etc.
    endpoint = Column(String(255), nullable=True)  # API endpoint called
    event_metadata = Column(JSON, nullable=True)  # Additional event data (renamed from 'metadata' to avoid SQLAlchemy conflict)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    # Note: sandbox_user relationship would reference sandbox.users if we create that model
