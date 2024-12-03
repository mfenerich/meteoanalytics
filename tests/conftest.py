"""Test fixtures."""

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def test_client() -> TestClient:
    """API test client.

    :return:
    """
    return TestClient(app)


@pytest.fixture
def mock_data():
    with open("tests/mock_data/valid_mock_data.json") as file:
        return json.load(file)


@pytest.fixture
def mock_data_leap_year():
    with open("tests/mock_data/valid_mock_data_leap_year.json") as file:
        return json.load(file)
