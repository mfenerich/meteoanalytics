from fastapi import HTTPException
import pandas as pd
import pytest

from app.utils.data_processing import aggregate_data

# Falta fazer as medias de outras granularidades
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


# # Error: precisa calcular as medias
# @pytest.mark.parametrize(
#     "aggregation, expected_count",
#     [
#         ("Hourly", 24),  # 24 records for 1 day
#         ("Daily", 1),    # 1 record for 1 day
#         ("Monthly", 1),  # 1 record for 1 month
#     ],
# )
# def test_aggregation_granularities(mock_data, aggregation, expected_count):
#     """
#     Test that aggregation produces the correct number of records for each granularity.
#     """
#     import pandas as pd

#     # Convert mock data to DataFrame
#     df = pd.DataFrame(mock_data)
#     df["fhora"] = pd.to_datetime(df["fhora"])

#     result = aggregate_data(df, aggregation, "2020-12-01T14:00:00", "2020-12-31T14:00:00")
#     assert len(result) == expected_count

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