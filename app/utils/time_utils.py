from typing import Tuple
import pytz
from fastapi import HTTPException
from app.core.logging_config import logger
from datetime import datetime, timedelta

def validate_and_localize_datetime(
    datetime_start: str, datetime_end: str, location: str
) -> Tuple[datetime, datetime]:
    """
    Validate and localize datetime strings to the given time zone or offset.

    Args:
        datetime_start (str): Start datetime string.
        datetime_end (str): End datetime string.
        location (str): Time zone (e.g., Europe/Berlin) or offset (e.g., +02:00).

    Returns:
        Tuple[datetime, datetime]: Localized start and end datetime objects.

    Raises:
        HTTPException: If the inputs are invalid, the time range exceeds one month, or the time zone is not recognized.
    """
    try:
        # Parse datetime strings
        start = datetime.fromisoformat(datetime_start)
        end = datetime.fromisoformat(datetime_end)

        # Validate time range
        if start >= end:
            raise ValueError("datetime_start must be before datetime_end")

        # Check if the range exceeds one month
        if (end - start) > timedelta(days=31):
            raise ValueError("The maximum allowed range is one month.")

        # Determine time zone or offset
        if location.startswith("+") or location.startswith("-"):
            # Handle offset-based time zone
            hours_offset = int(location[:3])
            minutes_offset = int(location[4:]) if len(location) > 3 else 0
            offset = timedelta(hours=hours_offset, minutes=minutes_offset)
            timezone = pytz.FixedOffset(int(offset.total_seconds() / 60))
        else:
            # Handle named time zone
            timezone = pytz.timezone(location)

        # Localize datetimes
        start_localized = timezone.localize(start)
        end_localized = timezone.localize(end)

        return start_localized, end_localized

    except Exception as e:
        logger.error(f"Error validating datetime: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid datetime or location: {str(e)}"
        )
