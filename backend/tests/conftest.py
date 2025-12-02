"""
Pytest configuration and fixtures for sandbox tests.
"""
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base

# Create in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# SQLite doesn't support schemas, so we need to remove schema from table args
# This event listener removes schema from table definitions for SQLite
@event.listens_for(Base.metadata, "before_create")
def remove_schema_for_sqlite(target, connection, **kw):
    """Remove schema from table args for SQLite compatibility"""
    if connection.dialect.name == 'sqlite':
        for table in target.tables.values():
            # Remove schema from table kwargs for SQLite
            if hasattr(table, 'schema') and table.schema:
                table.schema = None

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database session"""
    # For SQLite, create tables without schema
    # The event listener will remove schema automatically
    Base.metadata.create_all(bind=test_engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables
        Base.metadata.drop_all(bind=test_engine)
