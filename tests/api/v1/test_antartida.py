"""
Tests for the temperature-related API endpoints.

Includes tests for adding temperature data and fetching average temperature data.
"""

from fastapi import HTTPException
import pandas as pd
import pytest

from app.enums.enums import Station, TimeAggregation, DataType
from app.utils.data_processing import aggregate_data

@pytest.mark.parametrize(
    "query_params, expected_status, expected_detail",
    [
        ("/v1/antartida/timeseries/?datetime_end=2020-12-02T14%3A00%3A00&station=89064", 422, "detail"), # Missing datetime_start
        ("/v1/antartida/timeseries/?datetime_start=2020-12-01T14%3A00%3A00&station=89064", 422, "detail"), # Missing datetime_end
        ("/v1/antartida/timeseries/?datetime_start=2020-12-01T14%3A00%3A00&datetime_end=2020-12-02T14%3A00%3A00", 422, "detail"), # Missing station
    ],
)
def test_add_temperature_missing_fields(test_client, query_params, expected_status, expected_detail):
    """
    Test the `add_temperature` endpoint with various missing fields.

    Ensures:
    - HTTP status code is 422 for missing required parameters.
    - Validation error details are returned.
    """
    response = test_client.get(query_params)
    assert response.status_code == expected_status
    assert expected_detail in response.json()

@pytest.mark.parametrize(
    "query_params, expected_status",
    [
        ("/v1/antartida/timeseries/?datetime_start=2020-12-01T00:00:00&datetime_end=2020-12-31T23:59:59&station=89064", 200),
        ("/v1/antartida/timeseries/?datetime_start=2020-12-01T00:00:00&datetime_end=2021-01-31T23:59:59&station=89064", 400),  # > 1 month
    ],
)
def test_time_range_validation(test_client, query_params, expected_status):
    """Test the time range validation."""
    response = test_client.get(query_params)
    assert response.status_code == expected_status

@pytest.mark.parametrize(
    "query_params, expected_fields",
    [
        (
            {
                "datetime_start": "2020-12-01T00:00:00",
                "datetime_end": "2020-12-30T00:00:00",
                "station": Station.JUAN_CARLOS_I.value,
                "data_types": [DataType.TEMPERATURE.value],
            },
            ["nombre", "fhora", "temp"],
        ),
        (
            {
                "datetime_start": "2020-12-01T00:00:00",
                "datetime_end": "2020-12-30T00:00:00",
                "station": Station.JUAN_CARLOS_I.value,
                "data_types": [DataType.TEMPERATURE.value, DataType.PRESSURE.value],
            },
            ["nombre", "fhora", "temp", "pres"],
        ),
    ],
)
def test_data_type_filters(test_client, query_params, expected_fields):
    """Test filtering by data types (temperature, pressure, speed)."""
    response = test_client.get("/v1/antartida/timeseries/", params=query_params)
    assert response.status_code == 200
    for record in response.json():
        print(record)
        assert all(field in record for field in expected_fields)


def test_timezone_adjustment(test_client):
    """Test that the timezone adjustment works as expected."""
    query_params = (
        f"/v1/antartida/timeseries/?datetime_start=2020-12-01T00:00:00&datetime_end=2020-12-31T23:59:59&station={Station.JUAN_CARLOS_I.value}&location=Europe/Berlin"
    )
    response = test_client.get(query_params)
    assert response.status_code == 200

    # Verify the timezone in the datetime field
    for record in response.json():
        assert record["fhora"].endswith("+01:00") or record["fhora"].endswith("+02:00")

@pytest.mark.parametrize(
    "time_aggregation, start, end, expected_count",
    [
        (TimeAggregation.HOURLY.value, "2020-12-01T00:00:00", "2020-12-02T00:00:00", 24),  # One day = 24 hours
        (TimeAggregation.DAILY.value, "2020-12-01T00:00:00", "2020-12-01T01:00:00", 1),    # One day = 1 record
        (TimeAggregation.DAILY.value, "2020-12-01T00:00:00", "2020-12-02T00:00:00", 2),    # Two days = 2 record
        (TimeAggregation.MONTHLY.value, "2020-12-01T00:00:00", "2020-12-02T00:00:00", 1),  # One month = 1 record
    ],
)
def test_time_aggregation(test_client, time_aggregation, start, end, expected_count):
    """Test different time aggregation levels."""
    query_params = {
        "datetime_start": start,
        "datetime_end": end,
        "station": Station.JUAN_CARLOS_I.value,
        "time_aggregation": time_aggregation,
    }
    response = test_client.get("/v1/antartida/timeseries/", params=query_params)
    assert response.status_code == 200

    response_data = response.json()
    assert len(response_data) == expected_count

# Falta fazer as medias de outras granularidades
# @pytest.mark.parametrize(
#     "aggregation, column, start_date, end_date, expected_average",
#     [
#         ("Monthly", "temp", "2020-12-01T14:00:00", "2020-12-31T14:00:00", 1.49),  # Expected average temperature for 1 Month
#         ("Monthly", "pres", "2020-12-01T14:00:00", "2020-12-31T14:00:00", 982.52),  # Expected average pressure for 1 Month
#         ("Monthly", "vel", "2020-12-01T14:00:00", "2020-12-31T14:00:00", 2.73),  # Expected average velocity for 1 Month
#     ],
# )
# def test_aggregation_averages(mock_data, aggregation, column, start_date, end_date, expected_average):
#     """
#     Test that the aggregation logic correctly calculates averages for numeric fields.
#     """
#     import pandas as pd

#     # Convert mock data to DataFrame
#     df = pd.DataFrame(mock_data)
#     df["fhora"] = pd.to_datetime(df["fhora"])

#     # Aggregate data
#     result = aggregate_data(df, aggregation, start_date, end_date)

#     # Check the average value for the column
#     calculated_average = result[column].mean()
#     assert pytest.approx(calculated_average, rel=1e-2) == expected_average

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


# Error: precisa calcular as medias
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


def test_get_timeseries_with_nan_data(test_client, mock_data_leap_year, monkeypatch):
    """Test the get_timeseries function to ensure it handles 'NaN' values properly."""
    
    # Mock dependencies
    def mock_get_antartida_data(*args, **kwargs):
        return mock_data_leap_year

    monkeypatch.setattr("app.api.v1.antartida.get_antartida_data", mock_get_antartida_data)

    # Simulate API call
    response = test_client.get(
        "/v1/antartida/timeseries/",
        params={
            "datetime_start": "2020-02-28T00:00:00",
            "datetime_end": "2020-02-28T23:59:59",
            "station": "89064",
            "location": "UTC",
            "time_aggregation": "Hourly",
            "data_types": ["temperature", "pressure", "speed"],
        },
    )

    # Validate response
    assert response.status_code == 200, response.text
    result = response.json()

    # Ensure cleaned data contains no "NaN" or None in required fields
    for record in result:
        assert record["temp"] is not None
        assert record["vel"] is not None
        assert record["pres"] is not None

    # Ensure valid datetime conversion
    for record in result:
        pd.Timestamp(record["fhora"])  # Will raise ValueError if invalid

# Error
# @pytest.mark.parametrize(
#     "aggregation, expected_count",
#     [
#         ("Hourly", 3),
#         ("Daily", 1),
#         ("None", 3),
#     ],
# )
# def test_aggregation_levels(test_client, mock_data_leap_year, monkeypatch, aggregation, expected_count):
#     def mock_get_antartida_data(*args, **kwargs):
#         return mock_data_leap_year

#     monkeypatch.setattr("app.api.v1.antartida.get_antartida_data", mock_get_antartida_data)

#     response = test_client.get(
#         "/v1/antartida/timeseries/",
#         params={
#             "datetime_start": "2020-02-28T00:00:00",
#             "datetime_end": "2020-02-28T23:59:59",
#             "station": "89064",
#             "location": "UTC",
#             "time_aggregation": aggregation,
#             "data_types": None,
#         },
#     )

#     assert response.status_code == 200
#     result = response.json()
#     assert len(result) == expected_count
