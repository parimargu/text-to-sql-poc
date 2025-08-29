"""Pytest configuration and fixtures."""

import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base
from database.connection import DatabaseManager


@pytest.fixture(scope="session")
def test_database():
    """Create a test database for testing."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    
    # Create test database URL
    test_db_url = f"sqlite:///{db_path}"
    
    # Create engine and tables
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    
    yield test_db_url
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def test_db_manager(test_database):
    """Create a test database manager."""
    return DatabaseManager(database_url=test_database)


@pytest.fixture
def test_session(test_db_manager):
    """Create a test database session."""
    with test_db_manager.get_session() as session:
        yield session


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)
