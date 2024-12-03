"""
Database connection and session management for the FastAPI application.

This module configures the database engine and provides a dependency
for retrieving a synchronous database session.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Create the database engine
DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL, echo=True)

# Create a session factory
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    """
    Provide a database session for FastAPI routes.

    This function yields a synchronous SQLAlchemy session, ensuring that
    the session is properly closed after use.

    Yields:
        Session: The database session to be used within a route.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
