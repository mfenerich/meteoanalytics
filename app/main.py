import datetime
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
import httpx
import pytz
import pandas as pd
from open_data_client.aemet_open_data_client import AuthenticatedClient
from open_data_client.aemet_open_data_client.api.antartida.datos_antartida import sync_detailed
from open_data_client.aemet_open_data_client.models import Field200, Field404
from dateutil.parser import parse
import time
from app.core.config import settings
from app.core.logging_config import logger

app = FastAPI()

# Constants
BASE_URL = settings.base_url
TOKEN = settings.token
CET = pytz.timezone(settings.timezone)
STATIONS = {"Gabriel de Castilla": "89070", "Juan Carlos I": "89064"}
DATA_TYPE_MAP = {"temperature": "temp", "pressure": "pres", "speed": "vel"}
MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds

# Utility Functions
def convert_to_cet(dt: datetime.datetime) -> str:
    """Convert a datetime object to CET/CEST with offset."""
    cet_time = dt.astimezone(CET)
    return cet_time.isoformat()

def aggregate_data(df: pd.DataFrame, aggregation: str) -> pd.DataFrame:
    """Aggregate data based on the specified granularity."""
    try:
        df = df.set_index("fhora")
        numeric_columns = df.select_dtypes(include=["number"]).columns
        agg_dict = {col: "mean" for col in numeric_columns}
        if "nombre" in df.columns:
            agg_dict["nombre"] = "first"

        resample_map = {"Hourly": "H", "Daily": "D", "Monthly": "M"}
        if aggregation in resample_map:
            df = df.resample(resample_map[aggregation]).agg(agg_dict).reset_index()
        else:
            raise ValueError(f"Invalid aggregation level: {aggregation}")
        return df
    except Exception as e:
        logger.error(f"Error during aggregation: {str(e)}")
        raise

def validate_and_localize_datetime(
    datetime_start: str, datetime_end: str, location: str
) -> tuple[datetime.datetime, datetime.datetime]:
    """Validate and localize datetime strings."""
    try:
        if location.startswith("+") or location.startswith("-"):
            location_tz = datetime.timezone(
                datetime.timedelta(hours=int(location[:3]), minutes=int(location[4:]))
            )
        else:
            location_tz = pytz.timezone(location)

        start = parse(datetime_start).replace(tzinfo=None)
        end = parse(datetime_end).replace(tzinfo=None)
        start = location_tz.localize(start)
        end = location_tz.localize(end)

        if start >= end:
            raise ValueError("datetime_start must be before datetime_end")
        return start, end
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime or location: {str(e)}")

def fetch_data_from_url(url: str) -> Any:
    """Fetch data from the given URL with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client() as client:
                response = client.get(url)
                if response.status_code == 200:
                    return response.json()
                logger.warning(f"Attempt {attempt + 1}: Unexpected HTTP status {response.status_code}")
            time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error(f"Attempt {attempt + 1}: Error fetching data: {str(e)}")
    raise HTTPException(status_code=502, detail="Failed to fetch data after multiple attempts.")

def get_antartida_data(fecha_ini_str: str, fecha_fin_str: str, identificacion: str) -> Dict[str, Any]:
    """Fetch data from the AEMET API and handle retries for the dataset."""
    with AuthenticatedClient(base_url=BASE_URL, token=TOKEN) as client:
        response = sync_detailed(
            fecha_ini_str=fecha_ini_str, fecha_fin_str=fecha_fin_str, identificacion=identificacion, client=client
        )
        if isinstance(response.parsed, Field200):
            datos_url = response.parsed.datos
            return fetch_data_from_url(datos_url)
        elif isinstance(response.parsed, Field404):
            raise HTTPException(status_code=404, detail=response.parsed.descripcion)
        raise HTTPException(status_code=500, detail="Unexpected response structure.")

# Endpoints
@app.get("/timeseries/")
def get_timeseries(
    datetime_start: str,
    datetime_end: str,
    station: str = Query(..., description="Meteo Station: Gabriel de Castilla or Juan Carlos I"),
    location: Optional[str] = "Europe/Madrid",
    time_aggregation: Optional[str] = Query("None", enum=["None", "Hourly", "Daily", "Monthly"]),
    data_types: Optional[List[str]] = Query(None, enum=["temperature", "pressure", "speed"]),
):
    # Validate station
    if station not in STATIONS:
        raise HTTPException(status_code=400, detail="Invalid meteo station")
    identificacion = STATIONS[station]

    # Validate and localize datetime
    start, end = validate_and_localize_datetime(datetime_start, datetime_end, location)

    # Convert to API-required format
    start_api_format = start.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SUTC")
    end_api_format = end.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SUTC")

    # Fetch data
    data = get_antartida_data(start_api_format, end_api_format, identificacion)

    # Parse and process data
    df = pd.DataFrame(data)

    # Ensure `fhora` is parsed as datetime and timezone-aware
    df["fhora"] = pd.to_datetime(df["fhora"], errors="coerce")
    if df["fhora"].isnull().any():
        logger.error("Invalid datetime found in 'fhora' column")
        df = df.dropna(subset=["fhora"])

    # Adjust timezone handling
    if not pd.api.types.is_datetime64tz_dtype(df["fhora"]):
        # If not timezone-aware, localize to UTC
        df["fhora"] = df["fhora"].dt.tz_localize("UTC")
    else:
        # If already timezone-aware, convert to UTC first
        df["fhora"] = df["fhora"].dt.tz_convert("UTC")

    # Convert `fhora` to the user-specified timezone
    user_tz = pytz.timezone(location)
    df["fhora"] = df["fhora"].dt.tz_convert(user_tz)

    # Filter columns
    selected_columns = ["nombre", "fhora"] + [DATA_TYPE_MAP[dt] for dt in data_types or DATA_TYPE_MAP.keys()]
    df = df[[col for col in selected_columns if col in df.columns]]

    # Aggregate data
    if time_aggregation != "None":
        df = aggregate_data(df, time_aggregation)

    # Convert datetime to ISO format
    df["fhora"] = df["fhora"].apply(lambda x: x.isoformat())

    return df.to_dict(orient="records")
