import datetime
from typing import Tuple
import pytz
from fastapi import HTTPException
from dateutil.parser import parse
from app.core.logging_config import logger

def validate_and_localize_datetime(
    datetime_start: str, datetime_end: str, location: str
) -> Tuple[datetime.datetime, datetime.datetime]:
    """Validate and localize datetime strings."""
    try:
        location_tz = pytz.timezone(location) if not location.startswith(("+", "-")) else pytz.FixedOffset(
            int(location[:3]) * 60 + int(location[4:])
        )
        start = parse(datetime_start).replace(tzinfo=None)
        end = parse(datetime_end).replace(tzinfo=None)
        start, end = location_tz.localize(start), location_tz.localize(end)

        if start >= end:
            raise ValueError("datetime_start must be before datetime_end")
        return start, end
    except Exception as e:
        logger.error(f"Error validating datetime: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid datetime or location: {str(e)}")
