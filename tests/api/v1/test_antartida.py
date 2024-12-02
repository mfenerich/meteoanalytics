"""
Tests for the temperature-related API endpoints.

Includes tests for adding temperature data and fetching average temperature data.
"""

import pytest

from app.enums.enums import Station, TimeAggregation, DataType

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
    """
    Test the time range validation.
    """
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
    """
    Test filtering by data types (temperature, pressure, speed).
    """
    response = test_client.get("/v1/antartida/timeseries/", params=query_params)
    assert response.status_code == 200
    for record in response.json():
        print(record)
        assert all(field in record for field in expected_fields)


def test_timezone_adjustment(test_client):
    """
    Test that the timezone adjustment works as expected.
    """
    query_params = (
        f"/v1/antartida/timeseries/?datetime_start=2020-12-01T00:00:00&datetime_end=2020-12-31T23:59:59&station={Station.JUAN_CARLOS_I.value}&location=Europe/Berlin"
    )
    response = test_client.get(query_params)
    assert response.status_code == 200

    # Verify the timezone in the datetime field
    for record in response.json():
        assert record["fhora"].endswith("+01:00") or record["fhora"].endswith("+02:00")

@pytest.mark.parametrize(
    "time_aggregation, expected_count",
    [
        (TimeAggregation.HOURLY.value, 24),  # One day = 24 hours
        (TimeAggregation.DAILY.value, 1),    # One day = 1 record
    ],
)
def test_time_aggregation(test_client, time_aggregation, expected_count):
    """
    Test aggregation levels (hourly, daily, monthly).
    """
    query_params = (
        f"/v1/antartida/timeseries/?"
        f"datetime_start=2020-12-01T00:00:00&"
        f"datetime_end=2020-12-02T00:00:00&"
        f"station={Station.JUAN_CARLOS_I.value}&"
        f"time_aggregation={time_aggregation}"
    )
    response = test_client.get(query_params)
    assert response.status_code == 200
    assert len(response.json()) == expected_count
