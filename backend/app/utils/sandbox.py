"""
Sandbox utility functions for feature flag management and schema handling.
"""
from ..config import settings


def is_sandbox_enabled() -> bool:
    """
    Check if sandbox mode is enabled.
    
    Returns:
        bool: True if sandbox is enabled, False otherwise
    """
    return settings.sandbox_enabled


def get_current_schema() -> str:
    """
    Get the current schema name based on sandbox mode.
    
    Returns:
        str: 'sandbox' if sandbox is enabled, 'public' otherwise
    """
    return settings.sandbox_schema if settings.sandbox_enabled else settings.production_schema


def require_sandbox(func):
    """
    Decorator to require sandbox mode to be enabled.
    
    Raises:
        RuntimeError: If sandbox mode is not enabled
    
    Usage:
        @require_sandbox
        def my_sandbox_function():
            ...
    """
    def wrapper(*args, **kwargs):
        if not is_sandbox_enabled():
            raise RuntimeError("Sandbox mode must be enabled to use this function")
        return func(*args, **kwargs)
    return wrapper

