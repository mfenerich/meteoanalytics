from fastapi import HTTPException
import pandas as pd
import pytest

from app.utils.data_processing import aggregate_data

@pytest.mark.parametrize(
    "aggregation, column, start_date, end_date, expected_average",
    [
        ("Monthly", "temp", "2020-12-01T14:00:00", "2020-12-31T14:00:00", 1.49),  # Expected average temperature for 1 Month
        ("Monthly", "pres", "2020-12-01T14:00:00", "2020-12-31T14:00:00", 982.52),  # Expected average pressure for 1 Month
        ("Monthly", "vel", "2020-12-01T14:00:00", "2020-12-31T14:00:00", 2.73),  # Expected average velocity for 1 Month
    ],
)
def test_aggregation_averages(mock_data, aggregation, column, start_date, end_date, expected_average):
    """
    Test that the aggregation logic correctly calculates averages for numeric fields.
    """
    import pandas as pd

    # Convert mock data to DataFrame
    df = pd.DataFrame(mock_data)
    df["fhora"] = pd.to_datetime(df["fhora"])

    # Aggregate data
    result = aggregate_data(df, aggregation, start_date, end_date)

    # Check the average value for the column
    calculated_average = result[column].mean()
    assert pytest.approx(calculated_average, rel=1e-2) == expected_average

def test_timezone_handling(mock_data):
    """Test that timezone-aware and naive datetime handling works correctly. """
    import pandas as pd

    # Create a timezone-naive DataFrame
    df_naive = pd.DataFrame(mock_data)
    df_naive["fhora"] = pd.to_datetime(df_naive["fhora"]).dt.tz_localize(None)

    # Create a timezone-aware DataFrame
    df_aware = pd.DataFrame(mock_data)
    df_aware["fhora"] = pd.to_datetime(df_aware["fhora"])

    # Ensure both pass through aggregation
    result_naive = aggregate_data(df_naive, "Daily", "2020-12-01T14:00:00", "2020-12-31T14:00:00")
    result_aware = aggregate_data(df_aware, "Daily", "2020-12-01T14:00:00", "2020-12-31T14:00:00")

    assert len(result_naive) == len(result_aware)

@pytest.mark.parametrize(
    "start, end, expected_count",
    [
        ("2020-12-01T00:00:00", "2020-12-01T01:00:00", 0),  # No data in range
        ("2020-02-28T00:00:00", "2020-02-28T00:00:00", None),  # Invalid range
        ("2020-02-28T00:00:00", "2020-03-01T00:00:00", 46),  # Leap year
    ],
)
def test_date_range_edge_cases(mock_data_leap_year, start, end, expected_count):
    """
    Test edge cases for date ranges.
    """
    # Convert mock data to DataFrame
    df = pd.DataFrame(mock_data_leap_year)
    df["fhora"] = pd.to_datetime(df["fhora"])

    if expected_count is None:
        # Expect an HTTPException for invalid ranges
        with pytest.raises(HTTPException) as exc_info:
            aggregate_data(df, "None", start, end)
        assert exc_info.value.status_code == 500
        assert "Start time must be before end time" in str(exc_info.value.detail)
    else:
        # Ensure correct result count for valid ranges
        result = aggregate_data(df, "Hourly", start, end)
        assert len(result) == expected_count

def test_invalid_aggregation_level(mock_data):
    """
    Test that invalid aggregation levels raise an HTTPException.
    """
    # Convert mock data to DataFrame
    df = pd.DataFrame(mock_data)
    df["fhora"] = pd.to_datetime(df["fhora"])

    with pytest.raises(HTTPException) as exc_info:
        aggregate_data(df, "InvalidLevel", "2020-12-01T14:00:00", "2020-12-31T14:00:00")
    
    assert exc_info.value.status_code == 500
    assert "Invalid aggregation level" in str(exc_info.value.detail)

def test_response_fields(mock_data):
    """Test that the response includes all required fields after aggregation."""

    # Convert mock data to DataFrame
    df = pd.DataFrame(mock_data)
    df["fhora"] = pd.to_datetime(df["fhora"])

    result = aggregate_data(df, "Hourly", "2020-12-01T14:00:00", "2020-12-31T14:00:00")
    required_fields = ["fhora", "temp", "pres", "vel"]
    for field in required_fields:
        assert field in result.columns

def test_missing_columns(mock_data):
    """
    Test that missing required columns are handled gracefully.
    Missing columns should be ignored, and the function should process the remaining data.
    """
    # Simulate missing 'temp' column
    df = pd.DataFrame(mock_data).drop(columns=["temp"])

    # Call the aggregation function
    try:
        result = aggregate_data(df, "Daily", "2020-12-01T00:00:00", "2020-12-31T00:00:00")
        assert "temp" not in result.columns, "The 'temp' column should not be in the result if it's missing in the input."
        assert len(result) > 0, "The result should not be empty when other columns are present."
    except Exception as e:
        pytest.fail(f"Test failed due to unexpected exception: {e}")


def test_overlapping_date_ranges(mock_data):
    """Test overlapping date ranges for aggregation."""
    df = pd.DataFrame(mock_data)
    df["fhora"] = pd.to_datetime(df["fhora"])

    # Aggregation with overlapping ranges
    result = aggregate_data(df, "Hourly", "2020-12-01T14:00:00", "2020-12-01T15:00:00")
    assert len(result) == 1  # Only one hour in range

def test_single_row_dataframe():
    """Test aggregation with a single-row DataFrame."""
    single_row = pd.DataFrame([{
        "fhora": "2020-12-01T14:00:00",
        "temp": 10.0,
        "pres": 1000.0,
        "vel": 5.0,
    }])
    single_row["fhora"] = pd.to_datetime(single_row["fhora"])
    result = aggregate_data(single_row, "Daily", "2020-12-01T00:00:00", "2020-12-31T00:00:00")
    assert len(result) == 1
    assert result["temp"].iloc[0] == 10.0

def test_nan_handling(mock_data):
    """Test aggregation with NaN values in optional columns."""
    df = pd.DataFrame(mock_data)
    df.loc[0, "temp"] = None  # Simulate NaN value in 'temp'
    df["fhora"] = pd.to_datetime(df["fhora"])

    result = aggregate_data(df, "Hourly", "2020-12-01T14:00:00", "2020-12-31T00:00:00")
    assert len(result) > 0
    assert result["temp"].notna().all()  # Ensure all remaining 'temp' values are non-NaN

def test_timezone_conversion(mock_data):
    """Test that the function handles timezone conversion correctly."""
    # Create a DataFrame from mock data
    df = pd.DataFrame(mock_data)

    # Make the datetime timezone-naive and then localize to UTC
    df["fhora"] = pd.to_datetime(df["fhora"], errors="coerce").dt.tz_localize(None)  # Ensure naive first
    df["fhora"] = df["fhora"].dt.tz_localize("UTC")  # Localize to UTC

    # Convert timezone to 'Europe/Berlin'
    df["fhora"] = df["fhora"].dt.tz_convert("Europe/Berlin")

    result = aggregate_data(df, "Daily", "2020-12-01T00:00:00", "2020-12-31T00:00:00")

    assert len(result) > 0
    assert result["fhora"].iloc[0].tz.zone == "Europe/Berlin"  # Ensure timezone is correctly converted
