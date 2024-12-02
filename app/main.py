import datetime
import logging
from fastapi import FastAPI, HTTPException
import httpx
from open_data_client.aemet_open_data_client import AuthenticatedClient
from open_data_client.aemet_open_data_client.api.antartida.datos_antartida import sync_detailed
from open_data_client.aemet_open_data_client.models import Field200, Field404
from open_data_client.aemet_open_data_client.types import Response

app = FastAPI()

# Base URL and token are constants in this example
BASE_URL = "https://opendata.aemet.es/opendata/"
TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJsaW51eG1lbm5AZ21haWwuY29tIiwianRpIjoiZjBkODEyYjQtZGIzZC00Mjc5LWJjODYtMTExMWRmMmExMjA4IiwiaXNzIjoiQUVNRVQiLCJpYXQiOjE3MzMxMzEwNTUsInVzZXJJZCI6ImYwZDgxMmI0LWRiM2QtNDI3OS1iYzg2LTExMTFkZjJhMTIwOCIsInJvbGUiOiIifQ.CqDUSl9u2JjrH812_QjLX0pPHxktAb9vVOdGwj7RuOI"

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
