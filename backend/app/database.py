from sqlalchemy import create_engine, text, TypeDecorator, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional
import uuid

# Import settings with fallback
try:
    from .config import settings
except (ImportError, AttributeError):
    # Fallback for when config isn't available (e.g., during migrations)
    class DummySettings:
        database_url = "postgresql://localhost/dummy"
        sandbox_enabled = False
    settings = DummySettings()


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL UUID when available, otherwise stores as String.
    """
    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


# Create database engine (lazy initialization to avoid import errors)
_engine = None

def get_engine():
    """Get or create the database engine"""
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url)
    return _engine

# Initialize engine immediately for normal use
try:
    engine = create_engine(settings.database_url)
except Exception:
    # If engine creation fails, we'll create it lazily
    engine = None

# Create SessionLocal class (lazy initialization)
SessionLocal = None

def get_session_local():
    """Get or create the SessionLocal class"""
    global SessionLocal
    if SessionLocal is None:
        engine_instance = engine if engine is not None else get_engine()
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_instance)
    return SessionLocal

# Initialize SessionLocal immediately for normal use
try:
    engine_instance = engine if engine is not None else get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_instance)
except Exception:
    # If initialization fails, we'll create it lazily
    SessionLocal = None

# Create Base class for models
Base = declarative_base()


# Dependency to get database session
def get_db():
    """
    Get database session with schema-aware routing.
    
    If SANDBOX_ENABLED is True, sets search_path to sandbox schema.
    Otherwise, uses default (public) schema.
    """
    session_local = SessionLocal if SessionLocal is not None else get_session_local()
    db = session_local()
    try:
        if settings.sandbox_enabled:
            # Set search_path to sandbox schema for this connection
            db.execute(text("SET search_path TO sandbox, public"))
        yield db
    finally:
        db.close()


def get_db_for_sandbox(sandbox_user_id: Optional[str] = None):
    """
    Get database session with sandbox schema routing.
    
    This is used when we know we're in sandbox mode (API key auth).
    
    Args:
        sandbox_user_id: Optional sandbox user ID (for future use)
    """
    session_local = SessionLocal if SessionLocal is not None else get_session_local()
    db = session_local()
    try:
        # Always use sandbox schema for sandbox requests
        db.execute(text("SET search_path TO sandbox, public"))
        yield db
    finally:
        db.close()
