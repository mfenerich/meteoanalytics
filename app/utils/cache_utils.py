from datetime import datetime, timedelta, timezone
import pandas as pd
from sqlalchemy import text
from app.core.logging_config import logger
from sqlalchemy.orm import Session

from app.db.models import WeatherData

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

def validate_cache_coverage(
    station_id: str,
    start_utc: datetime,
    end_utc: datetime,
    db: Session,
) -> bool:
    """
    Validate whether the cache fully covers the requested data range.

    Args:
        station_id (str): ID of the weather station.
        start_utc (datetime): Start datetime in UTC.
        end_utc (datetime): End datetime in UTC.
        db (Session): Database session.

    Returns:
        bool: True if the cache fully covers the requested range, False otherwise.
    """
    logger.info(f"Validating cache for station {station_id}: {start_utc} to {end_utc}")

    # Generate the range of timestamps expected for the requested interval
    requested_timestamps = pd.date_range(
        start=start_utc, end=end_utc, freq="10T", tz="UTC"
    )

    # Query the database for the existing timestamps in the range
    existing_data = (
        db.query(WeatherData.fhora)
        .filter(
            WeatherData.identificacion == station_id,
            WeatherData.fhora.between(start_utc, end_utc),
        )
        .all()
    )

    # Extract the timestamps from the query results
    cached_timestamps = {row[0] for row in existing_data}

    # Check for any missing timestamps
    missing_timestamps = set(requested_timestamps) - cached_timestamps

    if missing_timestamps:
        logger.warning(f"Cache miss for timestamps: {missing_timestamps}")
        return False

    logger.info("Cache fully covers the requested range.")
    return True
