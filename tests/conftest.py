"""Test fixtures."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def test_client() -> TestClient:
    """Provide a test client for API testing.

    Returns:
        TestClient: FastAPI test client instance.
    """
    return TestClient(app)


@pytest.fixture
def mock_data():
    """
    Load valid mock data for testing.

    Returns:
        dict: Parsed JSON data from the `valid_mock_data.json` file.
    """
    with open("tests/mock_data/valid_mock_data.json") as file:
        return json.load(file)


@pytest.fixture
def mock_data_leap_year():
    """
    Load valid mock data for leap year testing.

    Returns:
        dict: Parsed JSON data from the `valid_mock_data_leap_year.json` file.
    """
    with open("tests/mock_data/valid_mock_data_leap_year.json") as file:
        return json.load(file)
