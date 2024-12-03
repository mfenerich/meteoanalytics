"""
Database models for the FastAPI application.

This module defines the SQLAlchemy ORM models used for database tables.
"""

from sqlalchemy import Column, Float, Integer, String, TIMESTAMP
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class WeatherData(Base):
    """
    ORM model for weather data.

    Represents meteorological data collected from weather stations.
    """
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    temperature = Column(Float)
    pressure = Column(Float)
    wind_speed = Column(Float)
