from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.enums import enums


from app.core.logging_config import logger
from app.core.config import settings
import pytz
import pandas as pd

from app.schemas.responses import TimeSeriesResponse
from app.utils.data_processing import aggregate_data
from app.utils.network_utils import fetch_data_from_url
from app.utils.time_utils import validate_and_localize_datetime
from open_data_client.aemet_open_data_client.api.antartida.datos_antartida import sync_detailed
from open_data_client.aemet_open_data_client.client import AuthenticatedClient
from open_data_client.aemet_open_data_client.models.field_200 import Field200
from open_data_client.aemet_open_data_client.models.field_404 import Field404

router = APIRouter()

# Configuration
BASE_URL = settings.base_url
TOKEN = settings.token
DATA_TYPE_MAP = {"temperature": "temp", "pressure": "pres", "speed": "vel"}

def get_antartida_data(fecha_ini_str: str, fecha_fin_str: str, identificacion: str) -> List[Dict[str, Any]]:
    """Fetch data from the AEMET API and handle retries for the dataset."""
    with AuthenticatedClient(base_url=BASE_URL, token=TOKEN) as client:
        response = sync_detailed(
            fecha_ini_str=fecha_ini_str, fecha_fin_str=fecha_fin_str, identificacion=identificacion, client=client
        )
        if isinstance(response.parsed, Field200):
            datos_url = response.parsed.datos
            logger.info(f"Fetched 'datos' URL: {datos_url}")
            return fetch_data_from_url(datos_url) # Fetch actual data from AEMET
        elif isinstance(response.parsed, Field404):
            raise HTTPException(status_code=404, detail=response.parsed.descripcion)
        raise HTTPException(status_code=500, detail="Unexpected response structure.")
    
# Endpoints
@router.get(
    "/timeseries/",
    response_model=List[TimeSeriesResponse],
    response_model_exclude_unset=True,
    summary="Retrieve time series data for a meteo station",
    description="""
    Retrieve meteorological time series data for a specified station over a defined time range.

    ### Overview:
    This endpoint allows you to fetch meteorological data for selected weather stations within a specified time range. The data can be aggregated at hourly, daily, or monthly intervals and adjusted to a specified timezone.

    ### Key Features:
    - Fetch raw or aggregated data from specific stations.
    - Perform aggregations based on hourly, daily, or monthly intervals.
    - Adjust timezone or offset for response datetime values.
    - Filter results by specific weather parameters such as temperature, pressure, and wind speed.

    ### Inputs:
    - **`datetime_start`**: Start datetime in ISO format (e.g., `2020-12-01T00:00:00`).
    - **`datetime_end`**: End datetime in ISO format (e.g., `2020-12-31T23:59:59`).
    - **`station`**: Specify the weather station to fetch data from. Supported values:
      - `89064`: Estación Meteorológica Juan Carlos I
      - `89064R`: Estación Radiométrica Juan Carlos I
      - `89064RA`: Estación Radiométrica Juan Carlos I (until 08/03/2007)
      - `89070`: Estación Meteorológica Gabriel de Castilla
    - **`location`** (optional): Specify the timezone or offset for the datetime values (e.g., `Europe/Madrid`, `+02:00`). Defaults to `Europe/Madrid`.
    - **`time_aggregation`** (optional): Specify the aggregation level.
    - **`data_types`** (optional): Specify the weather parameters to include in the response. Supported values:
      - `temperature`: Include temperature data in Celsius.
      - `pressure`: Include atmospheric pressure in hPa.
      - `speed`: Include wind speed in m/s.

    ### Output:
    A list of dictionaries containing:
    - **`nombre`**: Name of the weather station.
    - **`fhora`**: ISO-formatted datetime adjusted to the specified timezone.
    - Weather parameters (`temperature`, `pressure`, `speed`) based on the selected data types.
    """
)
def get_timeseries(
    datetime_start: str,
    datetime_end: str,
    station: enums.Station = Query(...),
    location: Optional[str] = settings.timezone,
    time_aggregation: Optional[enums.TimeAggregation] = Query("None"),
    data_types: Optional[List[enums.DataType]] = Query(None),
):
    # Validate and localize datetime
    start, end = validate_and_localize_datetime(datetime_start, datetime_end, location)

    # Convert to API-required format
    start_api_format = start.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SUTC")
    end_api_format = end.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SUTC")

    # Fetch data
    data = get_antartida_data(start_api_format, end_api_format, station.value)

    # Parse and process data
    df = pd.DataFrame(data)
    df["fhora"] = pd.to_datetime(df["fhora"], errors="coerce")
    if not pd.api.types.is_datetime64tz_dtype(df["fhora"]):
        # If timezone-naive, localize to UTC
        df["fhora"] = df["fhora"].dt.tz_localize("UTC")
    # Convert to the specified timezone
    df["fhora"] = df["fhora"].dt.tz_convert(location)

    # Filter columns
    selected_columns = ["nombre", "fhora"] + [DATA_TYPE_MAP[dt] for dt in data_types or DATA_TYPE_MAP.keys()]
    df = df[selected_columns]

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
        logger.error(f"Error validating response data: {str(e)}")
        raise HTTPException(status_code=500, detail="Error preparing the response.")