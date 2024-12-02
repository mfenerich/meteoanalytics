"""
This module defines the application configuration using Pydantic's BaseSettings.

The configuration is loaded from environment variables and supports default values.
"""

from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import load_dotenv

# Load the .env file
dotenv_path = Path(".env")
load_dotenv(dotenv_path)

class Settings(BaseSettings):
    """
    Application settings configuration.

    Attributes:
        app_name (str): The name of the application.
        debug (bool): Flag to enable or disable debug mode.
        base_url (str): Base URL for the API.
        timezone (str): Default timezone for the application.
        token (str): API token for authentication.
    """

    app_name: str = "FastAPI IoT Meteo"
    debug: bool = True
    base_url: str = ""
    timezone: str = "Europe/Madrid"
    token: str

    class Config:
        env_file = ".env"  # Specifies the .env file
        env_file_encoding = "utf-8"  # Optional: Ensures proper encoding for .env

# Instantiate the settings object
settings = Settings()
