"""
Utility functions and helper methods for interacting with external APIs.

This module provides functions to fetch data from APIs, cache data into
a database, and perform necessary data transformations and validations.
"""

import json
from typing import Any, Optional

import pandas as pd
import pytz
from fastapi import HTTPException
from sqlalchemy import DateTime, cast, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging_config import logger
from app.db.models import WeatherData
from app.utils.cache_utils import cleanup_cache
from app.utils.network_utils import fetch_data_from_url
from open_data_client.aemet_open_data_client.api.antartida.datos_antartida import (
    sync_detailed,
)
from open_data_client.aemet_open_data_client.client import AuthenticatedClient
from open_data_client.aemet_open_data_client.models.field_200 import Field200
from open_data_client.aemet_open_data_client.models.field_404 import Field404

# Configuration
BASE_URL = settings.base_url
TOKEN = settings.token
DATA_TYPE_MAP = {"temperature": "temp", "pressure": "pres", "speed": "vel"}


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
    start_utc = pd.to_datetime(start_api_format)
    if start_utc.tzinfo is None:
        start_utc = start_utc.tz_localize("UTC")
    else:
        start_utc = start_utc.tz_convert("UTC")

    end_utc = pd.to_datetime(end_api_format)
    if end_utc.tzinfo is None:
        end_utc = end_utc.tz_localize("UTC")
    else:
        end_utc = end_utc.tz_convert("UTC")

    logger.info(f"Querying database: start={start_utc}, end={end_utc}")

    # Query cached data
    cached_data = (
        db.query(WeatherData)
        .filter(
            WeatherData.identificacion == station_id,
            cast(WeatherData.fhora, DateTime) >= cast(start_utc, DateTime),
            cast(WeatherData.fhora, DateTime) <= cast(end_utc, DateTime),
        )
        .all()
    )

    # Check if cache fully covers the requested interval
    if cached_data:
        # Normalize cached timestamps to 10-minute intervals
        cached_timestamps = {row.fhora for row in cached_data}

        # Normalize requested timestamps to 10-minute intervals
        requested_timestamps = pd.date_range(
            start=start_utc.floor("10T"),  # Align start to 10-minute intervals
            end=end_utc.ceil("10T"),  # Align end to 10-minute intervals
            freq="10T",
            tz="UTC",
        )

        # Check if all requested timestamps are in the cache
        missing_timestamps = [
            ts for ts in requested_timestamps if ts not in cached_timestamps
        ]

        # Log missing timestamps
        if missing_timestamps:
            logger.debug(f"Missing timestamps: {missing_timestamps}")

        # If there are missing timestamps, fetch from the server
        if missing_timestamps:
            logger.info("Partial cache hit. Fetching missing data from the server.")
        else:
            logger.info("Complete cache hit. Returning cached data.")
            timezone = pytz.timezone(location) if location != "UTC" else pytz.UTC
            for row in cached_data:
                row.data["fhora"] = (
                    pd.to_datetime(row.data["fhora"])
                    .tz_convert("UTC")
                    .astimezone(timezone)
                    .isoformat()
                )
            return [row.data for row in cached_data]

    # Fetch or mock data from API
    api_data = None
    if False:  # TODO Mocking condition
        logger.info("Using mock data from 'tests/mock_data/valid_mock_data.json'")
        mock_data_path = "tests/mock_data/valid_mock_data.json"
        with open(mock_data_path) as file:
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

    return api_data


def cache_weather_data(db: Session, api_data: list[dict[str, Any]]) -> None:
    """
    Cache weather data in the database using optimized techniques.

    Args:
        db (Session): Database session.
        api_data (list[dict]): Weather data fetched from the API.
    """
    try:
        cleanup_cache(db)  # Cleanup old cache entries
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
            formatted_records.append(
                {
                    "identificacion": record["identificacion"],
                    "fhora": timestamp,
                    "data": json.dumps(record),  # Serialize JSON data
                }
            )

        # Optimize SQLite journal mode
        db.execute(text("PRAGMA journal_mode = WAL;"))

        # Create a temporary table for staging data
        db.execute(
            text("""
            CREATE TEMP TABLE temp_weather_data (
                identificacion TEXT NOT NULL,
                fhora TIMESTAMP NOT NULL,
                data JSON NOT NULL
            );
        """)
        )

        # Use executemany for bulk insertion into the temp table
        insert_query = """
            INSERT INTO temp_weather_data (identificacion, fhora, data)
            VALUES (:identificacion, :fhora, :data);
        """
        db.execute(text(insert_query), formatted_records)

        # Move data from the temporary table to the main table
        db.execute(
            text("""
            INSERT OR IGNORE INTO weather_data (identificacion, fhora, data)
            SELECT identificacion, fhora, data
            FROM temp_weather_data;
            """)
        )

        # Drop the temporary table
        db.execute(text("DROP TABLE temp_weather_data;"))

        # Commit the transaction
        db.commit()
        logger.info(
            f"Successfully cached {len(formatted_records)} records to the database."
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cache data: {e}")
