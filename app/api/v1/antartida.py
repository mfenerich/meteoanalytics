"""
This module defines API endpoints and helper functions.

For retrieving meteorological data from the AEMET API. It processes and returns
time series data for specified stations in Antarctica.
"""

from typing import Optional

import pandas as pd
import pytz
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import logger
from app.db.connection import get_db
from app.enums import enums
from app.schemas.responses import TimeSeriesFullResponse, TimeSeriesResponse
from app.utils.api_utils import get_antartida_data
from app.utils.data_processing import aggregate_data
from app.utils.time_utils import validate_and_localize_datetime

db_dependency = Depends(get_db)

router = APIRouter()

# Configuration
BASE_URL = settings.base_url
TOKEN = settings.token
DATA_TYPE_MAP = {"temperature": "temp", "pressure": "pres", "speed": "vel"}


# Endpoints
@router.get(
    "/timeseries/",
    response_model=list[TimeSeriesResponse],
    response_model_exclude_unset=True,
    summary="Retrieve time series data for a meteo station",
    description="""
    Retrieve selected meteorological time series data for a specified
        station over a defined time range.

    ### Overview:
    This endpoint allows you to fetch meteorological data for
        selected weather stations within a specified time range.
            The data can be aggregated at hourly, daily, or monthly intervals
            and adjusted to a specified timezone. You can specify which weather
            parameters to include in the response using the `data_types` parameter.

    ### Key Features:
    - Fetch raw or aggregated data from specific stations.
    - Perform aggregations based on hourly, daily, or monthly intervals.
    - Adjust timezone or offset for response datetime values.
    - **Filter results by specific weather parameters such as temperature,
        pressure, and wind speed using the `data_types` parameter.**

    ### Inputs:
    - **`datetime_start`**: Start datetime in ISO format (e.g., `2020-12-01T00:00:00`).
    - **`datetime_end`**: End datetime in ISO format (e.g., `2020-12-31T23:59:59`).
    - **`station`**: Specify the weather station to fetch data from. Supported values:
    - `89064`: Estación Meteorológica Juan Carlos I
    - `89064R`: Estación Radiométrica Juan Carlos I
    - `89064RA`: Estación Radiométrica Juan Carlos I (until 08/03/2007)
    - `89070`: Estación Meteorológica Gabriel de Castilla
    - **`location`** (optional): Specify the timezone or offset for
        the datetime values (e.g., `Europe/Madrid`, `+02:00`).
            Defaults to `Europe/Madrid`.
    - **`time_aggregation`** (optional): Specify the aggregation
        level (`hourly`, `daily`, `monthly`, or `None`).
    - **`data_types`** (optional): Specify the weather parameters
        to include in the response. Supported values:
    - `temperature`: Include temperature data in Celsius.
    - `pressure`: Include atmospheric pressure in hPa.
    - `speed`: Include wind speed in m/s.

    ### Output:
    A list of dictionaries containing:
    - **`nombre`**: Name of the weather station.
    - **`fhora`**: ISO-formatted datetime adjusted to the specified timezone.
    - Weather parameters (`temperature`, `pressure`, `speed`)
        based on the selected `data_types`.
    """,
)
def get_short_response(
    datetime_start: str,
    datetime_end: str,
    station: enums.Station = Query(...),
    location: Optional[str] = settings.timezone,
    time_aggregation: Optional[enums.TimeAggregation] = Query("None"),
    data_types: Optional[list[enums.DataType]] = Query(None),
    db: Session = Depends(get_db),
):
    return get_timeseries(
        datetime_start,
        datetime_end,
        station,
        location,
        time_aggregation,
        data_types,
        False,
        db,
    )


@router.get(
    "/timeseries/full",
    response_model=list[TimeSeriesFullResponse],
    summary="Retrieve time series data for a meteo station",
    description="""
    Retrieve full meteorological time series data for a specified
        station over a defined time range.

    ### Overview:
    This endpoint allows you to fetch the full set of meteorological
        data for selected weather stations within a specified time range.
        The data can be aggregated at hourly, daily, or monthly intervals
        and adjusted to a specified timezone. All available weather parameters
        are included in the response.

    ### Key Features:
    - Fetch raw or aggregated data from specific stations.
    - Perform aggregations based on hourly, daily, or monthly intervals.
    - Adjust timezone or offset for response datetime values.
    - **Includes all available weather parameters in the response.**

    ### Inputs:
    - **`datetime_start`**: Start datetime in ISO format (e.g., `2020-12-01T00:00:00`).
    - **`datetime_end`**: End datetime in ISO format (e.g., `2020-12-31T23:59:59`).
    - **`station`**: Specify the weather station to fetch data from. Supported values:
      - `89064`: Estación Meteorológica Juan Carlos I
      - `89064R`: Estación Radiométrica Juan Carlos I
      - `89064RA`: Estación Radiométrica Juan Carlos I (until 08/03/2007)
      - `89070`: Estación Meteorológica Gabriel de Castilla
    - **`location`** (optional): Specify the timezone or offset for the datetime
        values (e.g., `Europe/Madrid`, `+02:00`). Defaults to `Europe/Madrid`.
    - **`time_aggregation`** (optional): Specify the aggregation level
        (`hourly`, `daily`, `monthly`, or `None`).

    ### Output:
    A list of dictionaries containing:
    - **`nombre`**: Name of the weather station.
    - **`fhora`**: ISO-formatted datetime adjusted to the specified timezone.
    - **All available weather parameters**, such as temperature, pressure,
        wind speed, humidity, and more.
    """,
)
def get_full_response(
    datetime_start: str,
    datetime_end: str,
    station: enums.Station = Query(...),
    location: Optional[str] = settings.timezone,
    time_aggregation: Optional[enums.TimeAggregation] = Query("None"),
    db: Session = Depends(get_db),
):
    return get_timeseries(
        datetime_start,
        datetime_end,
        station,
        location,
        time_aggregation,
        None,
        True,
        db,
    )


def get_timeseries(
    datetime_start: str,
    datetime_end: str,
    station: enums.Station = Query(...),
    location: Optional[str] = settings.timezone,
    time_aggregation: Optional[enums.TimeAggregation] = Query("None"),
    data_types: Optional[list[enums.DataType]] = Query(None),
    full_response=False,
    db: Session = Depends(get_db),
):
    """
    Retrieve meteorological time series data for a specified station.

    This function fetches and processes meteorological data from a given station
    for the specified time range. Data can be aggregated at hourly, daily, or
    monthly intervals, and adjusted to a specified timezone.

    Args:
        datetime_start (str): Start datetime
            in ISO format (e.g., "2020-12-01T00:00:00").
        datetime_end (str): End datetime in ISO format (e.g., "2020-12-31T23:59:59").
        station (enums.Station): Weather station to fetch data from.
        location (Optional[str]): Timezone or offset
            for datetime values (default: "Europe/Madrid").
        time_aggregation (Optional[enums.TimeAggregation]):
            Aggregation level ("None" by default).
        data_types (Optional[list[enums.DataType]]):
            Weather parameters to include (e.g., temperature, pressure).
        full_response (bool): Define if the response will be full or short

    Returns:
        list[dict]: Processed meteorological data
            for the specified station and time range.

    Raises:
        HTTPException: If no data is found (204)
            or an error occurs during processing (500).
    """
    # Validate and localize datetime
    start, end = validate_and_localize_datetime(datetime_start, datetime_end, location)

    # Convert to API-required format
    start_api_format = start.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SUTC")
    end_api_format = end.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SUTC")

    # Fetch data
    data = get_antartida_data(
        station.value, start_api_format, end_api_format, db, location
    )

    # Handle empty DataFrame
    if len(data) == 0:
        logger.warning("Processed DataFrame is empty. Returning 204 No Content.")
        return Response(status_code=204)

    # Parse and process data
    df = pd.DataFrame(data)
    df["fhora"] = pd.to_datetime(df["fhora"], errors="coerce")
    if not isinstance(df["fhora"].dtype, pd.DatetimeTZDtype):
        df["fhora"] = df["fhora"].dt.tz_localize("UTC")
    df["fhora"] = df["fhora"].dt.tz_convert(location)

    # Filter columns
    if not full_response:
        selected_columns = ["nombre", "fhora"] + [
            DATA_TYPE_MAP[dt] for dt in data_types or DATA_TYPE_MAP.keys()
        ]
        df = df[selected_columns]

    # Handle missing values
    # Note: Here we delete rows with missing values
    #   in critical columns (e.g., 'temp', 'vel', 'pres').
    # Other approaches, such as filling missing values
    #   with the mean, median, interpolation, or
    # using forward/backward filling, could also be considered
    #   depending on the use case and dataset size.
    df = df.replace("NaN", None, inplace=False)
    required_columns = ["temp", "vel", "pres"]
    existing_columns = [col for col in required_columns if col in df.columns]

    if existing_columns:
        df = df[df[existing_columns].notna().all(axis=1)]
    else:
        logger.warning(f"Missing required columns {required_columns} in the data.")
        df = pd.DataFrame(columns=selected_columns)

    # Aggregate data
    if time_aggregation != "None":
        df = aggregate_data(df, time_aggregation, datetime_start, datetime_end)

    # Convert datetime to ISO format
    df["fhora"] = df["fhora"].apply(lambda x: x.isoformat())

    # Validate final response
    try:
        response_data = df.to_dict(orient="records")
        return response_data
    except Exception as e:
        logger.error(f"Error validating response data: {e!s}")
        raise HTTPException(status_code=500, detail="Error preparing the response.")
