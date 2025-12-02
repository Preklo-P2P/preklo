"""
Helper functions for auth tests
"""
from unittest.mock import MagicMock
from app.database import get_db


def override_get_db(mock_db):
    """Helper to override get_db dependency"""
    def _override():
        yield mock_db
    return _override

