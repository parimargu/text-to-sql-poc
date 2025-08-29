"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from config.settings import settings
from database.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize database engine and session factory."""
        try:
            if "sqlite" in self.database_url:
                self.engine = create_engine(
                    self.database_url,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False}
                )
            else:
                self.engine = create_engine(self.database_url)
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_schema_info(self) -> str:
        """Get database schema information for LLM context."""
        schema_info = """
        Database Schema:
        
        1. stores table:
           - id (INTEGER, PRIMARY KEY)
           - name (VARCHAR(100))
           - location (VARCHAR(200))
           - manager (VARCHAR(100))
           - phone (VARCHAR(20))
           - email (VARCHAR(100))
           - created_at (DATETIME)
        
        2. customers table:
           - id (INTEGER, PRIMARY KEY)
           - first_name (VARCHAR(50))
           - last_name (VARCHAR(50))
           - email (VARCHAR(100), UNIQUE)
           - phone (VARCHAR(20))
           - address (TEXT)
           - created_at (DATETIME)
        
        3. products table:
           - id (INTEGER, PRIMARY KEY)
           - name (VARCHAR(100))
           - category (VARCHAR(50))
           - price (FLOAT)
           - description (TEXT)
           - in_stock (BOOLEAN)
           - created_at (DATETIME)
        
        4. orders table:
           - id (INTEGER, PRIMARY KEY)
           - customer_id (INTEGER, FOREIGN KEY to customers.id)
           - store_id (INTEGER, FOREIGN KEY to stores.id)
           - order_date (DATETIME)
           - total_amount (FLOAT)
           - status (VARCHAR(20))
        
        5. order_items table:
           - id (INTEGER, PRIMARY KEY)
           - order_id (INTEGER, FOREIGN KEY to orders.id)
           - product_id (INTEGER, FOREIGN KEY to products.id)
           - quantity (INTEGER)
           - unit_price (FLOAT)
        """
        return schema_info


# Global database manager instance
db_manager = DatabaseManager()
