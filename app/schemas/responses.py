from typing import Optional

from pydantic import BaseModel, Field


class TimeSeriesResponse(BaseModel):
    nombre: str = Field(
        ...,
        description="Name of the meteo station.",
        json_schema_extra={"example": "Gabriel de Castilla"},
    )
    fhora: str = Field(
        ...,
        description="Datetime in ISO format with timezone offset.",
        json_schema_extra={"example": "2020-12-01T14:00:00+01:00"},
    )
    temp: Optional[float] = Field(
        None, description="Temperature in Celsius.", json_schema_extra={"example": 10.5}
    )
    pres: Optional[float] = Field(
        None, description="Pressure in hPa.", json_schema_extra={"example": 1013.25}
    )
    vel: Optional[float] = Field(
        None, description="Wind speed in m/s.", json_schema_extra={"example": 5.5}
    )
