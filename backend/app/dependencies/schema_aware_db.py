"""
Schema-aware database dependency.
Automatically routes to sandbox schema when API key authentication is used.
"""
from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from ..database import SessionLocal, get_session_local
from ..dependencies.unified_auth import require_unified_auth, is_sandbox_request
from ..models import User
from ..models.sandbox import SandboxAPIKey


def get_schema_aware_db(
    auth_result = Depends(require_unified_auth),
    is_sandbox: bool = Depends(is_sandbox_request)
) -> Session:
    """
    Get database session with automatic schema routing.
    
    - If API key auth → routes to sandbox schema
    - If JWT auth → routes to production (public) schema
    
    Args:
        auth_result: The authenticated user or API key (from unified_auth)
        is_sandbox: Whether this is a sandbox request
        
    Yields:
        Session: Database session with appropriate schema
    """
    session_local = SessionLocal if SessionLocal is not None else get_session_local()
    db = session_local()
    try:
        if is_sandbox:
            # Set search_path to sandbox schema for API key requests
            db.execute(text("SET search_path TO sandbox, public"))
        else:
            # Use default (public) schema for JWT requests
            db.execute(text("SET search_path TO public"))
        yield db
    finally:
        db.close()


def get_db_for_context(
    auth_result = Depends(require_unified_auth)
) -> Session:
    """
    Get database session with context-aware schema routing.
    
    This is an alternative dependency that routes based on auth type.
    
    Args:
        auth_result: The authenticated user or API key
        
    Yields:
        Session: Database session with appropriate schema
    """
    session_local = SessionLocal if SessionLocal is not None else get_session_local()
    db = session_local()
    try:
        if isinstance(auth_result, SandboxAPIKey):
            # API key auth → sandbox schema
            db.execute(text("SET search_path TO sandbox, public"))
        else:
            # JWT auth → production schema
            db.execute(text("SET search_path TO public"))
        yield db
    finally:
        db.close()

