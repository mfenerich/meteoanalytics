import datetime
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
import httpx
import pytz
import pandas as pd
from open_data_client.aemet_open_data_client import AuthenticatedClient
from open_data_client.aemet_open_data_client.api.antartida.datos_antartida import sync_detailed
from open_data_client.aemet_open_data_client.models import Field200, Field404
from dateutil.parser import parse

app = FastAPI()

# Base URL and token are constants in this example
BASE_URL = "https://opendata.aemet.es/opendata/"
TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJsaW51eG1lbm5AZ21haWwuY29tIiwianRpIjoiZjBkODEyYjQtZGIzZC00Mjc5LWJjODYtMTExMWRmMmExMjA4IiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE3MzMxMzEwNTUsInVzZXJJZCI6ImYwZDgxMmI0LWRiM2QtNDI3OS1iYzg2LTExMTFkZjJhMTIwOCIsInJvbGUiOiIifQ.CqDUSl9u2JjrH812_QjLX0pPHxktAb9vVOdGwj7RuOI"

# Constants
CET = pytz.timezone("Europe/Madrid")
STATIONS = {
    "Gabriel de Castilla": "89070",
    "Juan Carlos I": "89064"
}

DATA_TYPE_MAP = {
    "temperature": "temp",
    "pressure": "pres",
    "speed": "vel",
}


# Utility: Convert time to CET/CEST with offset
def convert_to_cet(dt: datetime) -> str:
    cet_time = dt.astimezone(CET)
    return cet_time.isoformat()

def aggregate_data(df: pd.DataFrame, aggregation: str) -> pd.DataFrame:
    try:
        # Ensure 'fhora' is the datetime index
        df = df.set_index("fhora")

        # Convert applicable columns to numeric for aggregation
        numeric_columns = df.select_dtypes(include=["number"]).columns

        # Aggregation functions: mean for numeric, first for 'nombre'
        agg_dict = {col: 'mean' for col in numeric_columns}
        if 'nombre' in df.columns:
            agg_dict['nombre'] = 'first'

        # Group and aggregate based on the selected level
        if aggregation == "Hourly":
            df = df.resample("H").agg(agg_dict)
        elif aggregation == "Daily":
            df = df.resample("D").agg(agg_dict)
        elif aggregation == "Monthly":
            df = df.resample("ME").agg(agg_dict)
        else:
            raise ValueError(f"Invalid aggregation level: {aggregation}")

        # Reset the index to make 'fhora' a column again
        df = df.reset_index()

        return df
    except Exception as e:
        logging.error(f"Error during aggregation: {str(e)}")
        raise


logging.basicConfig(level=logging.INFO)


def validate_date(date_str: str) -> bool:
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SUTC")
        return True
    except ValueError:
        return False

@app.get("/antartida/{fecha_ini_str}/{fecha_fin_str}/{identificacion}")
def get_antartida_data(fecha_ini_str: str, fecha_fin_str: str, identificacion: str):
    try:
        # Step 1: Fetch the initial response
        with AuthenticatedClient(base_url=BASE_URL, token=TOKEN) as client:
            response = sync_detailed(
                fecha_ini_str=fecha_ini_str,
                fecha_fin_str=fecha_fin_str,
                identificacion=identificacion,
                client=client,
            )

            if isinstance(response.parsed, Field200):
                datos_url = response.parsed.datos
                logging.info(f"'datos' URL: {datos_url}")

                # Step 2: Fetch the actual dataset from 'datos' URL
                try:
                    with httpx.Client() as http_client:
                        datos_response = http_client.get(datos_url)
                        datos_response.raise_for_status()  # Ensure HTTP response is OK

                        # Validate that the response is JSON
                        try:
                            data = datos_response.json()
                        except ValueError as ve:
                            logging.error(f"Malformed JSON in 'datos' URL response: {ve}")
                            raise HTTPException(
                                status_code=500,
                                detail="The 'datos' URL returned malformed JSON data.",
                            )

                except httpx.RequestError as re:
                    logging.error(f"Error fetching 'datos' URL: {re}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"Failed to fetch data from 'datos' URL: {str(re)}",
                    )

                except httpx.HTTPStatusError as he:
                    logging.error(f"Unexpected HTTP status from 'datos' URL: {he}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"The 'datos' URL returned an unexpected status code: {he.response.status_code}",
                    )

                # Return the full dataset along with metadata
                return {
                    "descripcion": response.parsed.descripcion,
                    "estado": response.parsed.estado,
                    "metadatos": response.parsed.metadatos,
                    "datos": data,
                }

            if isinstance(response.parsed, Field404):
                raise HTTPException(status_code=404, detail=response.parsed.descripcion)

            raise HTTPException(status_code=500, detail="Unexpected response structure")

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred while processing the request.")


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
    station_map = {
        "Gabriel de Castilla": "89070",
        "Juan Carlos I": "89064",
    }
    if station not in station_map:
        raise HTTPException(status_code=400, detail="Invalid meteo station")

    # Parse and validate location
    try:
        if location.startswith("+") or location.startswith("-"):  # Handle offset like +02:00
            location_tz = datetime.timezone(datetime.timedelta(hours=int(location[:3]), minutes=int(location[4:])))
        else:  # Handle named timezones like Europe/Berlin
            location_tz = pytz.timezone(location)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid location or timezone offset: {location}")

    # Validate and localize datetime
    try:
        start = parse(datetime_start).replace(tzinfo=None)  # Ensure naive datetime
        end = parse(datetime_end).replace(tzinfo=None)      # Ensure naive datetime

        # Localize to provided timezone
        start = location_tz.localize(start)
        end = location_tz.localize(end)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")

    if start >= end:
        raise HTTPException(status_code=400, detail="datetime_start must be before datetime_end")

    # Convert to the required API format (AAAA-MM-DDTHH:MM:SSUTC)
    start_api_format = start.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SUTC")
    end_api_format = end.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SUTC")

    # Fetch data from API
    try:
        # Call the real API using get_antartida_data
        data_response = get_antartida_data(
            fecha_ini_str=start_api_format,
            fecha_fin_str=end_api_format,
            identificacion=station_map[station],
        )

        # Parse the 'datos' field from the API response
        if "datos" not in data_response:
            raise HTTPException(status_code=500, detail="Missing 'datos' field in the API response")

        data = data_response["datos"]
        df = pd.DataFrame(data)

        # Ensure `fhora` is parsed as datetime
        df["fhora"] = pd.to_datetime(df["fhora"], errors="coerce")
        if df["fhora"].isnull().any():
            logging.error("Invalid datetime found in 'fhora' column")
            df = df.dropna(subset=["fhora"])

        # Ensure `fhora` is timezone-aware
        if not pd.api.types.is_datetime64tz_dtype(df["fhora"]):
            df["fhora"] = df["fhora"].dt.tz_localize("UTC")

        # Convert `fhora` to the user-specified timezone
        user_tz = pytz.timezone(location)
        df["fhora"] = df["fhora"].dt.tz_convert(user_tz)

        # Map data_types to actual column names
        DATA_TYPE_MAP = {
            "temperature": "temp",
            "pressure": "pres",
            "speed": "vel",
        }
        if data_types:
            selected_columns = ["nombre", "fhora"] + [DATA_TYPE_MAP[dt] for dt in data_types if dt in DATA_TYPE_MAP]
        else:
            # If no data_types specified, include all
            selected_columns = ["nombre", "fhora", "temp", "pres", "vel"]

        # Select the required columns
        df = df[[col for col in selected_columns if col in df.columns]]

        # Aggregate data
        if time_aggregation != "None":
            df = aggregate_data(df, time_aggregation)

        # Convert timestamps to ISO format with timezone offset
        df["fhora"] = df["fhora"].apply(lambda x: x.isoformat())

        return df.to_dict(orient="records")
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logging.error(f"Error processing data: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing data")
