from datetime import timedelta

import pytest
import pytz
from fastapi import HTTPException

from app.utils.time_utils import validate_and_localize_datetime


def test_valid_named_timezone():
    """Test with valid datetime strings and a named time zone."""
    start = "2023-12-01T10:00:00"
    end = "2023-12-02T10:00:00"
    timezone = "Europe/Berlin"
    result = validate_and_localize_datetime(start, end, timezone)
    assert result[0].tzinfo.zone == pytz.timezone(timezone).zone
    assert result[1].tzinfo.zone == pytz.timezone(timezone).zone


def test_valid_offset_timezone():
    """Test with valid datetime strings and an offset time zone."""
    start = "2023-12-01T10:00:00"
    end = "2023-12-02T10:00:00"
    offset = "+02:00"
    result = validate_and_localize_datetime(start, end, offset)
    assert result[0].tzinfo.utcoffset(result[0]) == timedelta(hours=2)
    assert result[1].tzinfo.utcoffset(result[1]) == timedelta(hours=2)


def test_invalid_timezone():
    """Test with an invalid time zone."""
    start = "2023-12-01T10:00:00"
    end = "2023-12-02T10:00:00"
    timezone = "Invalid/Timezone"
    with pytest.raises(HTTPException) as exc_info:
        validate_and_localize_datetime(start, end, timezone)
    assert exc_info.value.status_code == 400
    assert "Invalid datetime or location" in exc_info.value.detail


def test_start_after_end():
    """Test with datetime_start after datetime_end."""
    start = "2023-12-02T10:00:00"
    end = "2023-12-01T10:00:00"
    timezone = "Europe/Berlin"
    with pytest.raises(HTTPException) as exc_info:
        validate_and_localize_datetime(start, end, timezone)
    assert exc_info.value.status_code == 400
    assert "datetime_start must be before datetime_end" in exc_info.value.detail


def test_range_exceeds_one_month():
    """Test with a range that exceeds one month."""
    start = "2023-12-01T10:00:00"
    end = "2024-01-15T10:00:00"
    timezone = "Europe/Berlin"
    with pytest.raises(HTTPException) as exc_info:
        validate_and_localize_datetime(start, end, timezone)
    assert exc_info.value.status_code == 400
    assert "The maximum allowed range is one month." in exc_info.value.detail


def test_missing_offset_minutes():
    """Test with an offset time zone missing minutes."""
    start = "2023-12-01T10:00:00"
    end = "2023-12-02T10:00:00"
    offset = "+02"
    result = validate_and_localize_datetime(start, end, offset)
    assert result[0].tzinfo.utcoffset(result[0]) == timedelta(hours=2)
    assert result[1].tzinfo.utcoffset(result[1]) == timedelta(hours=2)


def test_invalid_datetime_format():
    """Test with invalid datetime format."""
    start = "InvalidDate"
    end = "2023-12-02T10:00:00"
    timezone = "Europe/Berlin"
    with pytest.raises(HTTPException) as exc_info:
        validate_and_localize_datetime(start, end, timezone)
    assert exc_info.value.status_code == 400
    assert "Invalid datetime or location" in exc_info.value.detail


def test_timezone_with_utc_offset():
    """Test with valid UTC offset time zone."""
    start = "2023-12-01T10:00:00"
    end = "2023-12-02T10:00:00"
    offset = "-03:30"
    result = validate_and_localize_datetime(start, end, offset)
    assert result[0].tzinfo.utcoffset(result[0]) == timedelta(hours=-3, minutes=-30)
    assert result[1].tzinfo.utcoffset(result[1]) == timedelta(hours=-3, minutes=-30)


def test_dst_transition_named_timezone():
    """Test with a named time zone during a DST transition."""
    # Test date in standard time (e.g., UTC+1 for Europe/Berlin)
    start_std = "2023-01-15T10:00:00"  # Winter, standard time
    end_std = "2023-01-15T11:00:00"
    timezone = "Europe/Berlin"
    result_std = validate_and_localize_datetime(start_std, end_std, timezone)
    assert result_std[0].tzinfo.utcoffset(result_std[0]) == timedelta(hours=1)
    assert result_std[1].tzinfo.utcoffset(result_std[1]) == timedelta(hours=1)

    # Test date in DST (e.g., UTC+2 for Europe/Berlin)
    start_dst = "2023-07-15T10:00:00"  # Summer, DST
    end_dst = "2023-07-15T11:00:00"
    result_dst = validate_and_localize_datetime(start_dst, end_dst, timezone)
    assert result_dst[0].tzinfo.utcoffset(result_dst[0]) == timedelta(hours=2)
    assert result_dst[1].tzinfo.utcoffset(result_dst[1]) == timedelta(hours=2)


def test_dst_transition_fixed_offset():
    """Test with a fixed offset time zone, which should not change."""
    # Fixed offset of +02:00
    start = "2023-01-15T10:00:00"
    end = "2023-01-15T11:00:00"
    offset = "+02:00"
    result = validate_and_localize_datetime(start, end, offset)
    assert result[0].tzinfo.utcoffset(result[0]) == timedelta(hours=2)
    assert result[1].tzinfo.utcoffset(result[1]) == timedelta(hours=2)

    # Same test for a DST period
    start_dst = "2023-07-15T10:00:00"
    end_dst = "2023-07-15T11:00:00"
    result_dst = validate_and_localize_datetime(start_dst, end_dst, offset)
    assert result_dst[0].tzinfo.utcoffset(result_dst[0]) == timedelta(hours=2)
    assert result_dst[1].tzinfo.utcoffset(result_dst[1]) == timedelta(hours=2)
