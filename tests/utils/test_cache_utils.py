"""
Unit tests for the cache utility functions.

This module tests the behavior of caching utilities, focusing on the cleanup
of outdated cache entries, query integrity, exception handling, and boundary conditions.
"""

import datetime
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.utils.cache_utils import cleanup_cache


def test_cleanup_cache_removal():
    """Test cleanup_cache to ensure old cache entries are removed."""
    mock_session = MagicMock(spec=Session)

    # Mock current time
    mocked_now = datetime.datetime(2024, 12, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)
    old_time = mocked_now - datetime.timedelta(hours=12)

    with patch("app.utils.cache_utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = mocked_now
        mock_datetime.timedelta = datetime.timedelta

        mock_session.execute = MagicMock()
        mock_session.commit = MagicMock()

        cleanup_cache(mock_session)

        # Extract the actual call arguments
        actual_call_args = mock_session.execute.call_args
        assert actual_call_args is not None, "Expected execute to be called once."

        actual_query, actual_params = actual_call_args[0]
        assert (
            str(actual_query)
            == "DELETE FROM weather_data WHERE created_at <= :expiration_time"
        )
        assert actual_params["expiration_time"] == old_time

        mock_session.commit.assert_called_once()


def test_cleanup_cache_no_removal():
    """Test cleanup_cache when no old cache entries are found."""
    mock_session = MagicMock(spec=Session)

    # Mock current time
    mocked_now = datetime.datetime(2024, 12, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)

    with patch("app.utils.cache_utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = mocked_now
        mock_datetime.timedelta = datetime.timedelta

        mock_session.execute = MagicMock()
        mock_session.commit = MagicMock()

        cleanup_cache(mock_session)

        # Assert the DELETE query was executed, but no entries were removed
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


def test_cleanup_cache_exception():
    """Test cleanup_cache handles exceptions during execution."""
    mock_session = MagicMock(spec=Session)

    # Mock current time
    mocked_now = datetime.datetime(2024, 12, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)

    with patch("app.utils.cache_utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = mocked_now
        mock_datetime.timedelta = datetime.timedelta

        mock_session.execute.side_effect = Exception("Database error")
        mock_session.rollback = MagicMock()
        mock_session.commit = MagicMock()

        with patch("app.utils.cache_utils.logger") as mock_logger:
            cleanup_cache(mock_session)

            # Assert rollback was called
            mock_session.rollback.assert_called_once()
            mock_session.commit.assert_not_called()

            # Assert an error was logged
            mock_logger.error.assert_called_once_with(
                "Failed to clean up cache: Database error"
            )


def test_cleanup_cache_query_integrity():
    """Test the SQL query string used in cleanup_cache."""
    query_text = "DELETE FROM weather_data WHERE created_at <= :expiration_time"

    with patch("app.utils.cache_utils.text") as mock_text:
        mock_text.return_value = query_text

        mock_session = MagicMock(spec=Session)
        cleanup_cache(mock_session)

        # Ensure the text method was called with the correct query
        mock_text.assert_called_once_with(query_text)


def test_cleanup_cache_boundary():
    """Test cleanup_cache when entries are exactly at the threshold."""
    mock_session = MagicMock(spec=Session)

    # Mock current time
    mocked_now = datetime.datetime(2024, 12, 3, 12, 0, 0, tzinfo=datetime.timezone.utc)
    boundary_time = mocked_now - datetime.timedelta(hours=12)

    with patch("app.utils.cache_utils.datetime") as mock_datetime:
        mock_datetime.now.return_value = mocked_now
        mock_datetime.timedelta = datetime.timedelta

        mock_session.execute = MagicMock()
        mock_session.commit = MagicMock()

        cleanup_cache(mock_session)

        # Extract the actual call arguments
        actual_call_args = mock_session.execute.call_args
        assert actual_call_args is not None, "Expected execute to be called once."

        _, actual_params = actual_call_args[0]
        assert actual_params["expiration_time"] == boundary_time

        mock_session.commit.assert_called_once()
