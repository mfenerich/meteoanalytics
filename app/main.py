from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from app.core.logging_config import logger

from app.api.v1.aemet import router as aemet_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for FastAPI to handle startup and shutdown events."""
    # Startup logic
    logger.info("Starting FastAPI Meteo Service")
    yield
    # Shutdown logic
    logger.info("Shutting down FastAPI Meteo Service")

app = FastAPI(
    title="Meteo API",
    description="""
    Add here some nice documentation

    And features
    """,
    version="0.0.1",
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
    lifespan=lifespan,  # Register the lifespan context
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

# Include Temperature Router
app.include_router(
    aemet_router, prefix="/v1/antartida", tags=["Temperature Management"]
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions by logging and returning a standardized response.

    Args:
        request (Request): The incoming request object.
        exc (HTTPException): The exception being handled.

    Returns:
        JSONResponse: A JSON response with the error details.
    """
    logger.error(f"HTTP Exception: {exc.detail} - Path: {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "code": exc.status_code},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions by logging and returning a generic response.

    Args:
        request (Request): The incoming request object.
        exc (Exception): The exception being handled.

    Returns:
        JSONResponse: A JSON response indicating an internal server error.
    """
    logger.error(f"Unexpected error: {exc} - Path: {request.url}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "An unexpected error occurred. Please try again later.",
            "code": 500,
        },
    )
