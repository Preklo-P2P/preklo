"""
Models package
Provides access to both production models (models.py) and sandbox models (sandbox.py)
"""
# Import Base from database for compatibility
from ..database import Base

# Import all sandbox models for easy access
from .sandbox import (  # noqa: F401
    TestAccount,
    SandboxAPIKey,
    WebhookSubscription,
    WebhookDelivery,
    SandboxAnalytics
)

# For production models, import directly from models.py module (not this package)
# This avoids circular imports. Code should use: from app.models import User
# or import app.models; app.models.User
import importlib.util
import sys
import os

# Load models.py as a separate module
models_py_path = os.path.join(os.path.dirname(__file__), '..', 'models.py')
spec = importlib.util.spec_from_file_location("app.models_production", models_py_path)
models_production = importlib.util.module_from_spec(spec)
sys.modules['app.models_production'] = models_production
spec.loader.exec_module(models_production)

# Re-export production models for backwards compatibility
User = models_production.User  # noqa: F401
Transaction = models_production.Transaction  # noqa: F401
Balance = models_production.Balance  # noqa: F401
PaymentRequest = models_production.PaymentRequest  # noqa: F401
Voucher = models_production.Voucher  # noqa: F401
SecurityEvent = models_production.SecurityEvent  # noqa: F401
TrustedDevice = models_production.TrustedDevice  # noqa: F401
BiometricCredential = models_production.BiometricCredential  # noqa: F401
UnlimitCard = models_production.UnlimitCard  # noqa: F401
Notification = models_production.Notification  # noqa: F401
TransactionLimit = models_production.TransactionLimit  # noqa: F401
SpendingControl = models_production.SpendingControl  # noqa: F401
TransactionApproval = models_production.TransactionApproval  # noqa: F401
EmergencyBlock = models_production.EmergencyBlock  # noqa: F401
SpendingAlert = models_production.SpendingAlert  # noqa: F401
FeeCollection = models_production.FeeCollection  # noqa: F401
FeeWithdrawal = models_production.FeeWithdrawal  # noqa: F401
FamilyAccount = models_production.FamilyAccount  # noqa: F401
BusinessAccount = models_production.BusinessAccount  # noqa: F401
FiatTransaction = models_production.FiatTransaction  # noqa: F401
SwapTransaction = models_production.SwapTransaction  # noqa: F401
UnlimitTransaction = models_production.UnlimitTransaction  # noqa: F401
UnlimitWebhook = models_production.UnlimitWebhook  # noqa: F401
Waitlist = models_production.Waitlist  # noqa: F401

__all__ = [
    'Base',
    'User', 'Transaction', 'Balance', 'PaymentRequest', 'Voucher',
    'SecurityEvent', 'TrustedDevice', 'BiometricCredential',
    'UnlimitCard', 'Notification', 'TransactionLimit', 'SpendingControl',
    'TransactionApproval', 'EmergencyBlock', 'SpendingAlert',
    'FeeCollection', 'FeeWithdrawal', 'FamilyAccount', 'BusinessAccount',
    'FiatTransaction', 'SwapTransaction', 'UnlimitTransaction', 'UnlimitWebhook',
    'Waitlist',
    'TestAccount',
    'SandboxAPIKey',
    'WebhookSubscription',
    'WebhookDelivery',
    'SandboxAnalytics',
]

