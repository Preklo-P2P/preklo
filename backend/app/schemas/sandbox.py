"""
Pydantic schemas for Sandbox API endpoints.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Sandbox Signup Schemas
class SandboxSignupRequest(BaseModel):
    """Request schema for sandbox signup."""
    email: EmailStr
    name: Optional[str] = Field(None, max_length=255, description="Optional developer name")


class TestAccountSummary(BaseModel):
    """Summary of test account for signup response."""
    id: UUID
    username: str
    usdc_balance: float
    apt_balance: float
    currency_type: str


class SandboxSignupResponse(BaseModel):
    """Response schema for sandbox signup."""
    success: bool
    message: str
    data: dict


# API Key Schemas
class CreateAPIKeyRequest(BaseModel):
    """Request schema for creating a new API key."""
    name: Optional[str] = Field(None, max_length=100, description="Optional name for the API key")


class APIKeyResponse(BaseModel):
    """Response schema for API key information."""
    id: UUID
    key_prefix: str = Field(..., description="First 8 characters of the API key for display")
    name: Optional[str]
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class APIKeyCreateResponse(BaseModel):
    """Response schema for API key creation (includes full key once)."""
    id: UUID
    api_key: str = Field(..., description="Full API key (shown only once)")
    key_prefix: str = Field(..., description="First 8 characters for future reference")
    name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ListAPIKeysResponse(BaseModel):
    """Response schema for listing API keys."""
    api_keys: List[APIKeyResponse]
    total: int


# Test Account Schemas
class TestAccountResponse(BaseModel):
    """Response schema for test account information."""
    id: UUID
    username: str
    wallet_address: str
    usdc_balance: float
    apt_balance: float
    currency_type: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ListTestAccountsResponse(BaseModel):
    """Response schema for listing test accounts."""
    accounts: List[TestAccountResponse]
    total: int


class ResetBalanceResponse(BaseModel):
    """Response schema for resetting account balance."""
    success: bool
    message: str
    account: TestAccountResponse


class FundAccountRequest(BaseModel):
    """Request schema for funding a test account."""
    usdc_amount: Optional[float] = Field(None, ge=0, description="Amount of USDC to add")
    apt_amount: Optional[float] = Field(None, ge=0, description="Amount of APT to add")
    
    class Config:
        json_schema_extra = {
            "example": {
                "usdc_amount": 100.0,
                "apt_amount": 1.0
            }
        }


class FundAccountResponse(BaseModel):
    """Response schema for funding a test account."""
    success: bool
    message: str
    account: TestAccountResponse


# Sandbox Account Info Schema
class SandboxAccountInfo(BaseModel):
    """Response schema for sandbox account information."""
    user_id: UUID
    email: Optional[str] = None  # Email not stored in current implementation
    name: Optional[str] = None  # Name not stored in current implementation
    api_keys_count: int
    test_accounts_count: int
    created_at: datetime
