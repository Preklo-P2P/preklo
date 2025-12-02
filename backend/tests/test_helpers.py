"""
Helper utilities for tests
"""
from contextlib import contextmanager
from unittest.mock import MagicMock
from starlette.testclient import TestClient
import httpx

from app.main import app
from app.database import get_db


@contextmanager
def override_db_dependency(mock_db):
    """
    Context manager to override get_db dependency for testing.
    
    Usage:
        with override_db_dependency(mock_db):
            response = client.get("/endpoint")
    """
    def override_get_db():
        yield mock_db
    
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield
    finally:
        app.dependency_overrides.clear()


def create_mock_db(user_query_result=None):
    """
    Create a mock database session with common defaults.
    
    Args:
        user_query_result: What query().filter().first() should return (default: None)
    
    Returns:
        Mock database session
    """
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = user_query_result
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    return mock_db


@contextmanager
def create_test_client(app_instance=None, **client_kwargs):
    """Create a Starlette test client bound to the FastAPI app (httpx>=0.28 compatible)."""
    app_instance = app_instance or app
    
    # Patch httpx.Client.__init__ to handle the 'app' parameter for httpx>=0.28
    original_init = httpx.Client.__init__
    
    def patched_init(self, *args, **kwargs):
        kwargs.pop("app", None)
        return original_init(self, *args, **kwargs)
    
    httpx.Client.__init__ = patched_init
    try:
        test_client = TestClient(app_instance, **client_kwargs)
        yield test_client
        test_client.close()
    finally:
        httpx.Client.__init__ = original_init
