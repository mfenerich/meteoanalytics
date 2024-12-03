from datetime import datetime, timedelta
from typing import Tuple

import pytz
from fastapi import HTTPException

from app.core.logging_config import logger


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
            if ":" in location:
                hours_offset, minutes_offset = map(int, location.split(":"))
                total_minutes = (
                    hours_offset * 60 + minutes_offset
                    if hours_offset >= 0
                    else hours_offset * 60 - minutes_offset
                )
            else:
                total_minutes = int(location) * 60
            timezone = pytz.FixedOffset(total_minutes)
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
            status_code=400, detail=f"Invalid datetime or location: {e!s}"
        )
