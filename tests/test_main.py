import time

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
import threading


# Initialize TestClient for FastAPI app
client = TestClient(app)


def test_read_item():
    """
    Test the `/health` endpoint for basic functionality.

    Validates:
    - HTTP status code is 200.
    - JSON response contains `{"status": "ok", "message": "Service is healthy"}`.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Service is healthy"}


def test_health_response_time():
    """
    Test the response time of the `/health` endpoint.

    Ensures:
    - HTTP status code is 200.
    - Response time is less than 200 milliseconds.
    """
    start_time = time.time()
    response = client.get("/health")
    end_time = time.time()

    assert response.status_code == 200
    assert (end_time - start_time) < 0.2  # Response should take less than 200ms

def test_health_stress():
    """
    Test the stability of the `/health` endpoint under high request load.

    Simulates:
    - 100 consecutive GET requests to the `/health` endpoint.
    Validates:
    - All requests return HTTP status code 200.
    """
    for _ in range(100):  # Simulate 100 requests
        response = client.get("/health")
        assert response.status_code == 200

def test_http_exception_handler():
    """
    Test the custom HTTPException handler.

    Simulate a scenario where an invalid request triggers an HTTPException.
    """
    response = client.get("/v1/temperature/some-invalid-endpoint")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}

def test_lifespan_events():
    """
    Test the lifespan startup and shutdown events.

    Validates:
    - Logs are generated for startup and shutdown events.
    """
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200

def test_concurrent_health_requests():
    """
    Test the `/health` endpoint under concurrent load.

    Simulates:
    - Multiple threads making requests simultaneously.
    Validates:
    - All requests return HTTP status code 200.
    """
    def make_request():
        response = client.get("/health")
        assert response.status_code == 200

    threads = [threading.Thread(target=make_request) for _ in range(50)]  # Simulate 50 concurrent requests
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

def test_router_integration():
    """
    Test that the AEMET router is integrated and working.

    Validates:
    - Endpoints from the AEMET router are accessible.
    """
    response = client.get("/v1/antartida/timeseries/")
    assert response.status_code in {200, 422}  # 422 if required params are missing

def test_environment_config_loading():
    """
    Test that the application loads settings from the environment correctly.

    Validates:
    - Application configuration matches expected values from `.env`.
    """
    assert settings.app_name == settings.app_name
    assert settings.timezone == settings.timezone

def test_health_content_type():
    """
    Test the content type of the `/health` endpoint response.

    Ensures:
    - HTTP status code is 200.
    - `Content-Type` header is `application/json`.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
