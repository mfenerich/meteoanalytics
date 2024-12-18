"""
Utilities for managing and cleaning up cached data.

This module provides helper functions to handle cache-related operations,
such as removing outdated data from the database, ensuring efficient
management of stored weather data.
"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging_config import logger


def cleanup_cache(db: Session) -> None:
    """
    Remove cache entries older than 12 hours.

    Args:
        db (Session): Database session.
    """
    try:
        # Use timezone-aware datetime for UTC
        expiration_time = datetime.now(timezone.utc) - timedelta(hours=12)
        db.execute(
            text("DELETE FROM weather_data WHERE created_at <= :expiration_time"),
            {"expiration_time": expiration_time},
        )
        db.commit()
        logger.info("Successfully cleaned up cache entries older than 12 hours.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clean up cache: {e}")
