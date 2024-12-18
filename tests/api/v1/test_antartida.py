"""
Tests for the temperature-related API endpoints.

Includes tests for adding temperature data and fetching average temperature data.
"""

import pytest

from app.enums.enums import DataType, Station, TimeAggregation


@pytest.mark.parametrize(
    "query_params, expected_status, expected_detail",
    [
        (
            "/v1/antartida/timeseries/?datetime_end=2020-12-02T14%3A00%3A00&station=89064",
            422,
            "detail",
        ),  # Missing datetime_start
        (
            "/v1/antartida/timeseries/?datetime_start=2020-12-01T14%3A00%3A00&station=89064",
            422,
            "detail",
        ),  # Missing datetime_end
        (
            "/v1/antartida/timeseries/?datetime_start=2020-12-01T14%3A00%3A00&datetime_end=2020-12-02T14%3A00%3A00",
            422,
            "detail",
        ),  # Missing station
    ],
)
def test_add_temperature_missing_fields(
    test_client, query_params, expected_status, expected_detail
):
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
        (
            "/v1/antartida/timeseries/?datetime_start=2020-12-01T00:00:00&datetime_end=2020-12-31T23:59:59&station=89064",
            200,
        ),
        (
            "/v1/antartida/timeseries/?datetime_start=2020-12-01T00:00:00&datetime_end=2021-01-31T23:59:59&station=89064",
            400,
        ),  # > 1 month
    ],
)
def test_time_range_validation(
    test_client, mock_data, monkeypatch, query_params, expected_status
):
    """Test the time range validation with mocked data."""

    # Mock `get_antartida_data` to return the mock data
    def mock_get_antartida_data(*args, **kwargs):
        return mock_data

    monkeypatch.setattr(
        "app.api.v1.antartida.get_antartida_data", mock_get_antartida_data
    )

    # Simulate the API call
    response = test_client.get(query_params)

    # Validate the response
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
def test_data_type_filters(
    test_client, mock_data, monkeypatch, query_params, expected_fields
):
    """Test filtering by data types (temperature, pressure, speed)."""

    # Mock `get_antartida_data` to return the mock data
    def mock_get_antartida_data(*args, **kwargs):
        return mock_data

    monkeypatch.setattr(
        "app.api.v1.antartida.get_antartida_data", mock_get_antartida_data
    )

    response = test_client.get("/v1/antartida/timeseries/", params=query_params)
    assert response.status_code == 200
    for record in response.json():
        print(record)
        assert all(field in record for field in expected_fields)


def test_timezone_adjustment(
    test_client,
    mock_data,
    monkeypatch,
):
    """Test that the timezone adjustment works as expected."""

    # Mock `get_antartida_data` to return the mock data
    def mock_get_antartida_data(*args, **kwargs):
        return mock_data

    monkeypatch.setattr(
        "app.api.v1.antartida.get_antartida_data", mock_get_antartida_data
    )

    query_params = (
        f"/v1/antartida/timeseries/"
        f"?datetime_start=2020-12-01T00:00:00"
        f"&datetime_end=2020-12-31T23:59:59"
        f"&station={Station.JUAN_CARLOS_I.value}"
        f"&location=Europe/Berlin"
    )
    response = test_client.get(query_params)
    assert response.status_code == 200

    # Verify the timezone in the datetime field
    for record in response.json():
        assert record["fhora"].endswith("+01:00") or record["fhora"].endswith("+02:00")


@pytest.mark.parametrize(
    "time_aggregation, start, end, expected_count",
    [
        (
            TimeAggregation.HOURLY.value,
            "2020-12-01T00:00:00",
            "2020-12-02T00:00:00",
            24,
        ),  # One day = 24 hours
        (
            TimeAggregation.DAILY.value,
            "2020-12-01T00:00:00",
            "2020-12-01T01:00:00",
            1,
        ),  # One day = 1 record
        (
            TimeAggregation.DAILY.value,
            "2020-12-01T00:00:00",
            "2020-12-02T00:00:00",
            2,
        ),  # Two days = 2 record
        (
            TimeAggregation.MONTHLY.value,
            "2020-12-01T00:00:00",
            "2020-12-02T00:00:00",
            1,
        ),  # One month = 1 record
    ],
)
def test_time_aggregation(
    test_client, mock_data, monkeypatch, time_aggregation, start, end, expected_count
):
    """Test different time aggregation levels."""

    # Mock `get_antartida_data` to return the mock data
    def mock_get_antartida_data(*args, **kwargs):
        return mock_data

    monkeypatch.setattr(
        "app.api.v1.antartida.get_antartida_data", mock_get_antartida_data
    )

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


@pytest.mark.parametrize(
    "aggregation, expected_count, expected_values",
    [
        ("Hourly", 3, [10.0, 20.0, 30.0]),  # Mock data should aggregate by hour
        ("Daily", 1, [20.0]),  # Mock data should aggregate by day
        ("None", 3, [10.0, 20.0, 30.0]),  # No aggregation, raw data
    ],
)
def test_aggregation_levels(
    test_client, monkeypatch, aggregation, expected_count, expected_values
):
    """
    Test aggregation levels for temperature data.

    Ensures that data is correctly aggregated at hourly
        daily, or no aggregation levels.
    """
    # Inline mock data
    mock_data = [
        {
            "fhora": "2020-02-28T00:00:00",
            "temp": 10.0,
            "vel": 1.0,
            "pres": 1000.0,
            "nombre": "Station 1",
        },
        {
            "fhora": "2020-02-28T01:00:00",
            "temp": 20.0,
            "vel": 2.0,
            "pres": 1010.0,
            "nombre": "Station 1",
        },
        {
            "fhora": "2020-02-28T02:00:00",
            "temp": 30.0,
            "vel": 3.0,
            "pres": 1020.0,
            "nombre": "Station 1",
        },
    ]

    # Mock the data-fetching function
    def mock_get_antartida_data(*args, **kwargs):
        return mock_data

    monkeypatch.setattr(
        "app.api.v1.antartida.get_antartida_data", mock_get_antartida_data
    )

    # Simulate API call
    response = test_client.get(
        "/v1/antartida/timeseries/",
        params={
            "datetime_start": "2020-02-28T00:00:00",
            "datetime_end": "2020-02-28T23:59:59",
            "station": "89064",
            "location": "UTC",
            "time_aggregation": aggregation,
            "data_types": ["temperature"],
        },
    )

    # Validate response
    assert response.status_code == 200
    result = response.json()

    # Check number of records returned
    assert (
        len(result) == expected_count
    ), f"Expected {expected_count} records, got {len(result)}."

    # Check aggregated values
    aggregated_temps = [round(record["temp"], 2) for record in result]
    assert (
        aggregated_temps == expected_values
    ), f"Expected {expected_values}, got {aggregated_temps}."


def test_unsupported_data_type(test_client):
    """
    Test response for unsupported data types.

    Ensures that the API returns a 422 status code for invalid data types.
    """
    response = test_client.get(
        "/v1/antartida/timeseries/",
        params={
            "datetime_start": "2020-12-01T00:00:00",
            "datetime_end": "2020-12-31T23:59:59",
            "station": "89064",
            "data_types": ["unsupported_type"],
        },
    )
    assert response.status_code == 422
    assert "data_types" in response.json()["detail"][0]["loc"]


def test_missing_columns_still_retuning(test_client, monkeypatch):
    """
    Test handling of missing columns in the response.

    Ensures that responses with missing columns are handled gracefully.
    """
    mock_data = [
        {
            "fhora": "2020-12-01T00:00:00",
            "vel": 1.0,
            "pres": 1000.0,
            "nombre": "Estación Meteorológica Juan Carlos I",
        },  # Missing 'temp'
        {
            "fhora": "2020-12-01T01:00:00",
            "temp": 20.0,
            "pres": 1010.0,
            "nombre": "Estación Meteorológica Juan Carlos I",
        },  # Missing 'vel'
    ]

    def mock_get_antartida_data(*args, **kwargs):
        return mock_data

    monkeypatch.setattr(
        "app.api.v1.antartida.get_antartida_data", mock_get_antartida_data
    )

    response = test_client.get(
        "/v1/antartida/timeseries/",
        params={
            "datetime_start": "2020-12-01T00:00:00",
            "datetime_end": "2020-12-01T02:00:00",
            "station": "89064",
        },
    )
    assert response.status_code == 200


def test_multiple_data_type_aggregation(test_client, monkeypatch):
    """
    Test aggregation for multiple data types.

    Ensures that temperature and pressure data are aggregated
        correctly when requested together.
    """
    mock_data = [
        {
            "fhora": "2020-12-01T00:00:00",
            "temp": 10.0,
            "pres": 1000.0,
            "nombre": "Estación Meteorológica Juan Carlos I",
        },
        {
            "fhora": "2020-12-01T01:00:00",
            "temp": 20.0,
            "pres": 1010.0,
            "nombre": "Estación Meteorológica Juan Carlos I",
        },
    ]

    def mock_get_antartida_data(*args, **kwargs):
        return mock_data

    monkeypatch.setattr(
        "app.api.v1.antartida.get_antartida_data", mock_get_antartida_data
    )

    response = test_client.get(
        "/v1/antartida/timeseries/",
        params={
            "datetime_start": "2020-12-01T00:00:00",
            "datetime_end": "2020-12-01T23:59:59",
            "station": "89064",
            "time_aggregation": "Daily",
            "data_types": ["temperature", "pressure"],
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert len(result) == 1
    assert result[0]["temp"] == 15.0  # Average temperature
    assert result[0]["pres"] == 1005.0  # Average pressure


def test_empty_dataframe_response(test_client, monkeypatch):
    """Test that the endpoint returns 204 No Content for an empty data response."""

    # Mock data-fetching function to return an empty list
    def mock_get_antartida_data(*args, **kwargs):
        return []  # Simulate no data returned from the external API

    monkeypatch.setattr(
        "app.api.v1.antartida.get_antartida_data", mock_get_antartida_data
    )

    # Simulate API call
    response = test_client.get(
        "/v1/antartida/timeseries/",
        params={
            "datetime_start": "2020-12-01T00:00:00",
            "datetime_end": "2020-12-31T23:59:59",
            "station": "89064",
            "location": "UTC",
            "time_aggregation": "Hourly",
            "data_types": ["temperature", "pressure", "speed"],
        },
    )

    # Validate response
    assert response.status_code == 204, f"Expected 204, got {response.status_code}."
    assert response.text == "", "Expected no content in the response body."
