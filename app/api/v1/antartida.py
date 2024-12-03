"""
This module defines API endpoints and helper functions.

For retrieving meteorological data from the AEMET API. It processes and returns
time series data for specified stations in Antarctica.
"""

from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd
import pytz
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pytest import Session
from sqlalchemy import text

from app.core.config import settings
from app.core.logging_config import logger
from app.db.connection import get_db
from app.db.models import WeatherData
from app.enums import enums
from app.schemas.responses import TimeSeriesResponse
from app.utils.data_processing import aggregate_data
from app.utils.network_utils import fetch_data_from_url
from app.utils.time_utils import validate_and_localize_datetime
from open_data_client.aemet_open_data_client.api.antartida.datos_antartida import (
    sync_detailed,
)
from open_data_client.aemet_open_data_client.client import AuthenticatedClient
from open_data_client.aemet_open_data_client.models.field_200 import Field200
from open_data_client.aemet_open_data_client.models.field_404 import Field404

db_dependency = Depends(get_db)

router = APIRouter()

# Configuration
BASE_URL = settings.base_url
TOKEN = settings.token
DATA_TYPE_MAP = {"temperature": "temp", "pressure": "pres", "speed": "vel"}

import json

def get_antartida_data(
    station_id: str,
    start_api_format: str,
    end_api_format: str,
    db: Session,
    location: Optional[str] = "UTC",
) -> list[dict[str, Any]]:
    """
    Fetch data from the AEMET API or retrieve it from the cache.

    If the requested interval is not fully covered by the cache,
    fetch the missing data from the API or mock data file.

    Args:
        db (Session): Database session.
        station_id (str): ID of the weather station.
        start_api_format (str): Start datetime in API format (UTC).
        end_api_format (str): End datetime in API format (UTC).
        location (Optional[str]): Requested timezone for the output.

    Returns:
        list[dict]: List of weather data records.
    """
    # Ensure UTC conversion for database filtering
    start_utc = pd.to_datetime(start_api_format).tz_convert("UTC")
    end_utc = pd.to_datetime(end_api_format).tz_convert("UTC")

    logger.info(f"Querying database: start={start_utc}, end={end_utc}")

    # Query cached data
    cached_data = (
        db.query(WeatherData)
        .filter(
            WeatherData.identificacion == station_id,
            WeatherData.fhora >= start_utc,
            WeatherData.fhora <= end_utc,
        )
        .all()
    )

    # Check if cache fully covers the requested interval
    if cached_data:
        cached_timestamps = {row.fhora for row in cached_data}
        requested_timestamps = pd.date_range(start=start_utc, end=end_utc, freq="10T", tz="UTC")
        missing_timestamps = [ts for ts in requested_timestamps if ts not in cached_timestamps]

        if not missing_timestamps:
            logger.info(f"Data for station {station_id} fully retrieved from cache.")
            timezone = pytz.timezone(location) if location != "UTC" else pytz.UTC
            for row in cached_data:
                row.data["fhora"] = (
                    pd.to_datetime(row.data["fhora"]).tz_convert("UTC").astimezone(timezone).isoformat()
                )
            return [row.data for row in cached_data]

        logger.warning(f"Missing timestamps detected: {len(missing_timestamps)} entries.")
    else:
        logger.warning(f"No cached data for station {station_id}.")

    # Fetch or mock data from API
    api_data = None
    if True:  # Mocking condition
        logger.info("Using mock data from 'tests/mock_data/valid_mock_data.json'")
        mock_data_path = "tests/mock_data/valid_mock_data.json"
        with open(mock_data_path, "r") as file:
            api_data = json.load(file)
    else:
        with AuthenticatedClient(base_url=BASE_URL, token=TOKEN) as client:
            response = sync_detailed(
                fecha_ini_str=start_api_format,
                fecha_fin_str=end_api_format,
                identificacion=station_id,
                client=client,
            )
            if isinstance(response.parsed, Field200):
                datos_url = response.parsed.datos
                api_data = fetch_data_from_url(datos_url)
            elif isinstance(response.parsed, Field404):
                raise HTTPException(status_code=404, detail=response.parsed.descripcion)

    if not api_data:
        raise HTTPException(status_code=500, detail="Failed to fetch data.")

    # Cache the newly fetched data
    cache_weather_data(db, api_data)

    # Merge cached and newly fetched data
    if cached_data:
        cached_data_dict = {row.fhora: row.data for row in cached_data}
        for record in api_data:
            ts = pd.to_datetime(record["fhora"]).tz_convert("UTC")
            cached_data_dict[ts] = record
        merged_data = list(cached_data_dict.values())
    else:
        merged_data = api_data

    return merged_data




def cache_weather_data(db: Session, api_data: list[dict[str, Any]]) -> None:
    """
    Cache weather data in the database using optimized techniques.

    Args:
        db (Session): Database session.
        api_data (list[dict]): Weather data fetched from the API.
    """
    try:
        utc = pytz.UTC
        formatted_records = []
        for record in api_data:
            timestamp = pd.to_datetime(record["fhora"], errors="coerce")
            if timestamp.tzinfo is None:
                # If the timestamp is naive, assume it is in UTC
                timestamp = utc.localize(timestamp)
            else:
                # Convert any localized timestamp to UTC
                timestamp = timestamp.astimezone(utc)

            # Convert pandas.Timestamp to Python datetime
            timestamp = timestamp.to_pydatetime()

            # Format the record for bulk insertion
            formatted_records.append({
                "identificacion": record["identificacion"],
                "fhora": timestamp,
                "data": json.dumps(record),  # Serialize JSON data
            })

        # Optimize SQLite journal mode
        db.execute(text("PRAGMA journal_mode = WAL;"))

        # Create a temporary table for staging data
        db.execute(text("""
            CREATE TEMP TABLE temp_weather_data (
                identificacion TEXT NOT NULL,
                fhora TIMESTAMP NOT NULL,
                data JSON NOT NULL
            );
        """))

        # Use executemany for bulk insertion into the temp table
        insert_query = """
            INSERT INTO temp_weather_data (identificacion, fhora, data)
            VALUES (:identificacion, :fhora, :data);
        """
        db.execute(text(insert_query), formatted_records)

        # Move data from the temporary table to the main table
        db.execute(text("""
            INSERT OR IGNORE INTO weather_data (identificacion, fhora, data)
            SELECT identificacion, fhora, data 
            FROM temp_weather_data;
        """))

        # Drop the temporary table
        db.execute(text("DROP TABLE temp_weather_data;"))

        # Commit the transaction
        db.commit()
        logger.info(f"Successfully cached {len(formatted_records)} records to the database.")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cache data: {e}")

# Endpoints
@router.get(
    "/timeseries/",
    response_model=list[TimeSeriesResponse],
    response_model_exclude_unset=True,
    summary="Retrieve time series data for a meteo station",
    description="""
    Retrieve meteorological time series data for a specified station over
        a defined time range.

    ### Overview:
    This endpoint allows you to fetch meteorological data for selected
        weather stations within a specified time range.
            The data can be aggregated at hourly,
        daily, or monthly intervals and adjusted to a specified timezone.

    ### Key Features:
    - Fetch raw or aggregated data from specific stations.
    - Perform aggregations based on hourly, daily,
        or monthly intervals.
    - Adjust timezone or offset for response datetime values.
    - Filter results by specific weather parameters
        such as temperature, pressure, and wind speed.

    ### Inputs:
    - **`datetime_start`**: Start datetime in ISO format (e.g., `2020-12-01T00:00:00`).
    - **`datetime_end`**: End datetime in ISO format (e.g., `2020-12-31T23:59:59`).
    - **`station`**: Specify the weather station to fetch data from.
        Supported values:
      - `89064`: Estación Meteorológica Juan Carlos I
      - `89064R`: Estación Radiométrica Juan Carlos I
      - `89064RA`: Estación Radiométrica Juan Carlos I (until 08/03/2007)
      - `89070`: Estación Meteorológica Gabriel de Castilla
    - **`location`** (optional):
        Specify the timezone or offset for the datetime
        values (e.g., `Europe/Madrid`, `+02:00`). Defaults to `Europe/Madrid`.
    - **`time_aggregation`** (optional): Specify the aggregation level.
    - **`data_types`** (optional): Specify the weather
        parameters to include in the response. Supported values:
      - `temperature`: Include temperature data in Celsius.
      - `pressure`: Include atmospheric pressure in hPa.
      - `speed`: Include wind speed in m/s.

    ### Output:
    A list of dictionaries containing:
    - **`nombre`**: Name of the weather station.
    - **`fhora`**: ISO-formatted datetime adjusted to the specified timezone.
    - Weather parameters (`temperature`, `pressure`, `speed`)
        based on the selected data types.
    """,
)
def get_timeseries(
    datetime_start: str,
    datetime_end: str,
    station: enums.Station = Query(...),
    location: Optional[str] = settings.timezone,
    time_aggregation: Optional[enums.TimeAggregation] = Query("None"),
    data_types: Optional[list[enums.DataType]] = Query(None),
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
    data = get_antartida_data(station.value, start_api_format, end_api_format, db, location)

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
    df = df.replace("NaN", np.nan, inplace=False)
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
