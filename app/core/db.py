"""
Database configuration and session management.
"""
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.engine import Engine
import os
from typing import Generator

# Database configuration
from app.core.config import settings
DB_PATH = settings.database_url

# Create engine with optimized settings for SQLite
engine = create_engine(
    DB_PATH,
    echo=False,  # Set to True for SQL debugging
    connect_args={
        "check_same_thread": False,  # Allow multiple threads for SQLite
        "timeout": 20,  # Connection timeout
    },
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
)


def create_db_and_tables() -> None:
    """
    Create database tables if they don't exist.
    This should be called during application startup.
    """
    from app.models.chat_models import Chat, Message  # Import here to avoid circular imports
    
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {str(e)}")
        raise


def get_session() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Use with FastAPI Depends() for automatic session management.
    """
    with Session(engine) as session:
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()


def get_engine() -> Engine:
    """Get the database engine instance."""
    return engine


def reset_database() -> None:
    """
    Reset the database by dropping and recreating all tables.
    WARNING: This will delete all data!
    """
    try:
        SQLModel.metadata.drop_all(engine)
        create_db_and_tables()
        print("✅ Database reset successfully")
    except Exception as e:
        print(f"❌ Error resetting database: {str(e)}")
        raise


def check_database_connection() -> bool:
    """
    Check if database connection is working.
    Returns True if connection is successful, False otherwise.
    """
    try:
        from sqlmodel import text
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False