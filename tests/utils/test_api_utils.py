import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
import pytz
import pandas as pd
from sqlalchemy.orm import Session

# Replace 'app.utils.api_utils' with the actual path to your function
from app.utils.api_utils import get_antartida_data

# Create mock weather data with timestamps aligned to 10-minute intervals
def get_mock_weather_data():
    # Get the current time rounded down to the nearest 10 minutes
    now = datetime.now(pytz.UTC)
    now = now.replace(second=0, microsecond=0)
    minutes = (now.minute // 10) * 10
    now = now.replace(minute=minutes)

    # Generate timestamps for the past hour at 10-minute intervals
    timestamps = [now - timedelta(minutes=10 * i) for i in range(6)]
    timestamps = sorted(timestamps)

    data = []
    for i, ts in enumerate(timestamps):
        data.append(
            MagicMock(
                identificacion="12345",
                fhora=ts,
                data={
                    "identificacion": "12345",
                    "fhora": ts.isoformat(),
                    "temp": 20 + i,
                    "pres": 1013 - i,
                    "vel": 5 + i,
                },
            )
        )
    return data

def test_get_antartida_data_complete_cache_hit():
    # Create a mock database session
    db_session = MagicMock(spec=Session)

    # Get the mock weather data
    MOCK_WEATHER_DATA = get_mock_weather_data()

    # Mock the query to return our mock data
    db_session.query.return_value.filter.return_value.all.return_value = MOCK_WEATHER_DATA

    # Define test parameters using the timestamps from MOCK_WEATHER_DATA
    station_id = "12345"
    start_api_format = MOCK_WEATHER_DATA[0].fhora.isoformat()
    end_api_format = MOCK_WEATHER_DATA[-1].fhora.isoformat()
    location = "UTC"

    # Ensure start and end times are aligned to 10-minute intervals
    start_api_format = pd.to_datetime(start_api_format).floor("10T").isoformat()
    end_api_format = pd.to_datetime(end_api_format).ceil("10T").isoformat()

    # Call the function
    result = get_antartida_data(
        station_id, start_api_format, end_api_format, db_session, location
    )

    # Prepare expected result
    expected_result = []
    for row in MOCK_WEATHER_DATA:
        # Adjust the 'fhora' field to match the expected timezone
        row.data["fhora"] = (
            pd.to_datetime(row.data["fhora"])
            .tz_convert("UTC")
            .astimezone(pytz.timezone(location))
            .isoformat()
        )
        expected_result.append(row.data)

    # Sort results by 'fhora' to ensure consistent ordering
    result = sorted(result, key=lambda x: x["fhora"])
    expected_result = sorted(expected_result, key=lambda x: x["fhora"])

    # Assertions
    assert result == expected_result
    db_session.query.assert_called_once()
