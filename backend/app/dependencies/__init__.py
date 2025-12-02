"""
FastAPI Dependencies Package
Provides authentication, rate limiting, and other request dependencies
"""
# Import from the dependencies.py module (not this package)
import importlib.util
import sys
import os

# Load dependencies.py as a separate module
deps_py_path = os.path.join(os.path.dirname(__file__), '..', 'dependencies.py')
spec = importlib.util.spec_from_file_location("app.dependencies_module", deps_py_path)
deps_module = importlib.util.module_from_spec(spec)
sys.modules['app.dependencies_module'] = deps_module
spec.loader.exec_module(deps_module)

# Re-export for backwards compatibility
require_authentication = deps_module.require_authentication
get_current_user = deps_module.get_current_user
get_current_user_or_api_key = deps_module.get_current_user_or_api_key
validate_user_access = deps_module.validate_user_access
validate_payment_access = deps_module.validate_payment_access
rate_limit = deps_module.rate_limit
RateLimitMiddleware = deps_module.RateLimitMiddleware
security = deps_module.security

__all__ = [
    'require_authentication',
    'get_current_user',
    'get_current_user_or_api_key',
    'validate_user_access',
    'validate_payment_access',
    'rate_limit',
    'RateLimitMiddleware',
    'security',
]

