import time

import httpx
from fastapi import HTTPException

from app.core.logging_config import logger

MAX_RETRIES = 5
RETRY_DELAY = 2  # seconds


def fetch_data_from_url(url: str):
    """Fetch data from the given URL with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client() as client:
                response = client.get(url)
                if response.status_code == 200:
                    logger.info(f"Data successfully fetched from {url}")
                    return response.json()
                logger.warning(
                    f"Attempt {attempt + 1}: Unexpected HTTP status {response.status_code}"
                )
        except Exception as e:
            logger.error(
                f"Attempt {attempt + 1}: Error fetching data from {url}: {e!s}"
            )
        finally:
            # Sleep only if this is not the last attempt
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    logger.error("Failed to fetch data after multiple attempts.")
    raise HTTPException(
        status_code=502, detail="Failed to fetch data after multiple attempts."
    )
