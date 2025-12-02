"""
Shared fixtures and helpers for auth tests
"""
import pytest
from unittest.mock import MagicMock
from app.main import app
from app.database import get_db


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    mock_db = MagicMock()
    # Set up common mock behaviors
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    return mock_db


def override_get_db(mock_db):
    """Helper to override get_db dependency"""
    def _override():
        yield mock_db
    return _override


@pytest.fixture
def client_with_db(mock_db):
    """Create test client with database override"""
    app.dependency_overrides[get_db] = override_get_db(mock_db)
    from fastapi.testclient import TestClient
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()

