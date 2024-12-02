"""This module defines the logging configuration for the application."""

import logging
from logging.handlers import RotatingFileHandler
from app.core.config import settings

# Configuration
LOG_FILE = "app.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
LOG_LEVEL = settings.log_level.upper()

# Create a custom logger
logger = logging.getLogger("meteo_app")
logger.setLevel(LOG_LEVEL)

# Handlers
stream_handler = logging.StreamHandler()
stream_handler.setLevel(LOG_LEVEL)

try:
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5)  # 5 MB max size
    file_handler.setLevel(LOG_LEVEL)
except IOError as e:
    print(f"Warning: Could not create log file handler: {e}")
    file_handler = None

# Formatter
formatter = logging.Formatter(LOG_FORMAT)
stream_handler.setFormatter(formatter)
if file_handler:
    file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(stream_handler)
if file_handler:
    logger.addHandler(file_handler)
