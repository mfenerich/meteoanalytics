from unittest.mock import MagicMock, patch

import httpx
import pytest
from fastapi import HTTPException

from app.utils.network_utils import MAX_RETRIES, fetch_data_from_url


@pytest.fixture
def mock_response():
    """Create a mock response for testing."""
    mock = MagicMock()
    mock.json.return_value = {"key": "value"}
    mock.status_code = 200
    return mock


def test_fetch_data_success(mock_response):
    """Test successful data fetch with HTTP 200 status."""
    with patch("httpx.Client.get", return_value=mock_response):
        result = fetch_data_from_url("http://test-url.com")
        assert result == {"key": "value"}


def test_fetch_data_http_error():
    """Test data fetch with non-200 HTTP status code."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    with (
        patch("httpx.Client.get", return_value=mock_response),
        patch("time.sleep") as mock_sleep,
    ):
        with pytest.raises(HTTPException) as exc_info:
            fetch_data_from_url("http://test-url.com")
        assert exc_info.value.status_code == 502
        assert "Failed to fetch data after multiple attempts" in exc_info.value.detail
        # Adjust to expect MAX_RETRIES - 1 sleep calls
        assert mock_sleep.call_count == MAX_RETRIES - 1


def test_fetch_data_retry_on_exception():
    """Test retry logic when an exception occurs during fetch."""
    with (
        patch("httpx.Client.get", side_effect=httpx.RequestError("Connection error")),
        patch("time.sleep") as mock_sleep,
    ):
        with pytest.raises(HTTPException) as exc_info:
            fetch_data_from_url("http://test-url.com")
        assert exc_info.value.status_code == 502
        assert "Failed to fetch data after multiple attempts" in exc_info.value.detail
        # Adjust to expect MAX_RETRIES - 1 sleep calls
        assert mock_sleep.call_count == MAX_RETRIES - 1


def test_fetch_data_retries_log_errors(caplog):
    """Test that fetch logs warnings/errors during retries."""
    with (
        patch("httpx.Client.get", side_effect=httpx.RequestError("Connection error")),
        patch("time.sleep"),
    ):
        with pytest.raises(HTTPException):
            fetch_data_from_url("http://test-url.com")
    log_messages = [record.message for record in caplog.records]
    assert any("Attempt 1: Error fetching data" in msg for msg in log_messages)
    assert any(
        "Failed to fetch data after multiple attempts" in msg for msg in log_messages
    )
