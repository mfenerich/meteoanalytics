"""
Database models for the FastAPI application.

This module defines the SQLAlchemy ORM models used for database tables.
"""

from sqlalchemy import JSON, TIMESTAMP, Column, Index, Integer, String, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class WeatherData(Base):
    """
    ORM model for weather data.

    Represents meteorological data collected from weather stations.
    """
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    identificacion = Column(String, nullable=False, index=True)
    fhora = Column(TIMESTAMP, nullable=False, index=True)
    data = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now(), index=True)

    __table_args__ = (
        Index("idx_identificacion_fhora", "identificacion", "fhora"),
    )
