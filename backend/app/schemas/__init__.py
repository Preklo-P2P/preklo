"""
Schemas Package
Provides Pydantic schemas for API requests and responses
"""
# Import from schemas.py module (not this package)
import importlib.util
import sys
import os

# Load schemas.py as a separate module
schemas_py_path = os.path.join(os.path.dirname(__file__), '..', 'schemas.py')
spec = importlib.util.spec_from_file_location("app.schemas_module", schemas_py_path)
schemas_module = importlib.util.module_from_spec(spec)
sys.modules['app.schemas_module'] = schemas_module
spec.loader.exec_module(schemas_module)

# Re-export all schemas from schemas.py
# This allows imports like: from app.schemas import User, Transaction, etc.
for name in dir(schemas_module):
    if not name.startswith('_') and isinstance(getattr(schemas_module, name), type):
        # Only export classes (Pydantic models)
        globals()[name] = getattr(schemas_module, name)

# Import sandbox schemas with explicit names to avoid collisions
from .sandbox import (  # noqa: F401
    CreateAPIKeyRequest as SandboxCreateAPIKeyRequest,
    APIKeyResponse as SandboxAPIKeyResponse,
    ListAPIKeysResponse as SandboxListAPIKeysResponse,
    TestAccountResponse,
    ListTestAccountsResponse,
    ResetBalanceResponse,
    FundAccountRequest,
    FundAccountResponse,
    SandboxSignupRequest,
    SandboxSignupResponse,
    TestAccountSummary,
    SandboxAccountInfo,
)

__all__ = [
    # Export all from schemas.py dynamically
    # Plus sandbox schemas
    'SandboxCreateAPIKeyRequest',
    'SandboxAPIKeyResponse',
    'SandboxListAPIKeysResponse',
    'TestAccountResponse',
    'ListTestAccountsResponse',
    'ResetBalanceResponse',
    'FundAccountRequest',
    'FundAccountResponse',
    'SandboxSignupRequest',
    'SandboxSignupResponse',
    'TestAccountSummary',
    'SandboxAccountInfo',
]

