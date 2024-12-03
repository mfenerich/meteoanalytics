"""
Main entry point for the FastAPI application.

This module sets up the FastAPI app, including routes, exception handlers
and startup/shutdown events for the Meteo API.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.v1.antartida import router as aemet_router
from app.core.logging_config import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for FastAPI to handle startup and shutdown events."""
    logger.info("Starting FastAPI Meteo Service")
    yield
    logger.info("Shutting down FastAPI Meteo Service")


app = FastAPI(
    title="Meteo API",
    description="""
    API providing access to weather data for Antarctica.

    Features:
    - Retrieve temperature, pressure, and wind speed data.
    - Supports time aggregation (hourly, daily, monthly).
    - Handles daylight saving adjustments (CET/CEST).
    """,
    version="0.1.0",
    terms_of_service="http://example.com/terms/",
    contact={
        "name": "API Support",
        "url": "http://feneri.ch",
        "email": "marcel@feneri.ch",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
)


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Check the health of the service.

    Returns:
        JSONResponse: Status and message indicating health.
    """
    return JSONResponse(
        content={"status": "ok", "message": "Service is healthy"}, status_code=200
    )


# Include AEMET Router
app.include_router(aemet_router, prefix="/v1/antartida", tags=["AEMET Antarctica Data"])


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions by logging and returning a standardized response."""
    logger.error(f"HTTP Exception: {exc.detail} - Path: {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": exc.status_code},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions by logging and returning a generic response."""
    logger.error(f"Unexpected error: {exc} - Path: {request.url}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred. Please try again later.",
            "code": 500,
        },
    )
