from typing import Optional
from pydantic import BaseModel, Field


class TimeSeriesResponse(BaseModel):
    nombre: str = Field(..., example="Gabriel de Castilla", description="Name of the meteo station.")
    fhora: str = Field(..., example="2020-12-01T14:00:00+01:00", description="Datetime in ISO format with timezone offset.")
    temp: Optional[float] = Field(None, example=10.5, description="Temperature in Celsius.")
    pres: Optional[float] = Field(None, example=1013.25, description="Pressure in hPa.")
    vel: Optional[float] = Field(None, example=5.5, description="Wind speed in m/s.")
