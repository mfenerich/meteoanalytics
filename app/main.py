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

# Utility: Convert time to CET/CEST with offset
def convert_to_cet(dt: datetime) -> str:
    cet_time = dt.astimezone(CET)
    return cet_time.isoformat()

# Utility: Aggregate data based on time
def aggregate_data(df: pd.DataFrame, aggregation: str) -> pd.DataFrame:
    if aggregation == "Hourly":
        df = df.resample("H", on="fhora").mean()
    elif aggregation == "Daily":
        df = df.resample("D", on="fhora").mean()
    elif aggregation == "Monthly":
        df = df.resample("M", on="fhora").mean()
    return df

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
    location: Optional[str] = "Europe/Berlin",
    time_aggregation: Optional[str] = Query("None", enum=["None", "Hourly", "Daily", "Monthly"]),
    data_types: Optional[List[str]] = Query(None, enum=["temperature", "pressure", "speed"]),
):
    # Validate station
    if station not in STATIONS:
        raise HTTPException(status_code=400, detail="Invalid meteo station")

    # Validate and parse datetime
    try:
        start = parse(datetime_start).astimezone(pytz.timezone(location))
        end = parse(datetime_end).astimezone(pytz.timezone(location))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {str(e)}")

    if start >= end:
        raise HTTPException(status_code=400, detail="datetime_start must be before datetime_end")

    # Fetch data from API
    try:
        # Simulate API call (replace with actual API client)
        data = [
            {"fhora": start + datetime.timedelta(minutes=10 * i), "temp": 1.5, "pres": 960, "vel": 4.7}
            for i in range(int((end - start).total_seconds() / 600))
        ]
        df = pd.DataFrame(data)

        # Check if `fhora` is timezone-aware and convert to CET/CEST
        if pd.api.types.is_datetime64tz_dtype(df["fhora"]):
            df["fhora"] = df["fhora"].dt.tz_convert("Europe/Madrid")
        else:
            df["fhora"] = pd.to_datetime(df["fhora"]).dt.tz_localize(location).dt.tz_convert("Europe/Madrid")

        # Filter data types
        if data_types:
            df = df[[col for col in df.columns if col in data_types or col == "fhora"]]

        # Aggregate data
        if time_aggregation != "None":
            df = aggregate_data(df, time_aggregation)

        # Convert timestamps to CET/CEST
        df["fhora"] = df["fhora"].apply(lambda x: convert_to_cet(x))

        return df.to_dict(orient="records")
    except Exception as e:
        logging.error(f"Error processing data: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while processing data")
