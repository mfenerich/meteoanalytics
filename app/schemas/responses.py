"""
Schemas for API responses.

This module defines the data models used for structuring API responses. These schemas
ensure consistency and provide metadata for automatic documentation generation.
"""

from typing import Optional

from pydantic import BaseModel, Field


class TimeSeriesResponse(BaseModel):
    """
    Schema for time series data response.

    Attributes:
        nombre (str): Name of the meteorological station.
        fhora (str): Datetime in ISO format with timezone offset.
        temp (Optional[float]): Temperature in Celsius.
        pres (Optional[float]): Atmospheric pressure in hPa.
        vel (Optional[float]): Wind speed in m/s.
    """

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


class TimeSeriesFullResponse(BaseModel):
    """
    Schema for time series data response.

    Attributes:
        Represents meteorological station data with optional fields for missing values.
    """

    identificacion: Optional[str] = Field(
        None,
        description="Identification code of the station.",
        json_schema_extra={"example": "89064"},
    )
    nombre: Optional[str] = Field(
        None,
        description="Name of the meteorological station.",
        json_schema_extra={"example": "JCI Estacion meteorologica"},
    )
    latitud: Optional[float] = Field(
        None,
        description="Latitude of the station.",
        json_schema_extra={"example": -62.66325},
    )
    longitud: Optional[float] = Field(
        None,
        description="Longitude of the station.",
        json_schema_extra={"example": -60.38959},
    )
    altitud: Optional[float] = Field(
        None, description="Altitude in meters.", json_schema_extra={"example": 12.0}
    )
    srs: Optional[str] = Field(
        None,
        description="Spatial Reference System.",
        json_schema_extra={"example": "WGS84"},
    )
    alt_nieve: Optional[float] = Field(
        None,
        description="Snow altitude in meters.",
        json_schema_extra={"example": None},
    )
    ddd: Optional[float] = Field(
        None,
        description="Wind direction (degrees).",
        json_schema_extra={"example": 237},
    )
    dddstd: Optional[float] = Field(
        None,
        description="Standard deviation of wind direction.",
        json_schema_extra={"example": 66},
    )
    dddx: Optional[float] = Field(
        None, description="Extreme wind direction.", json_schema_extra={"example": 291}
    )
    fhora: Optional[str] = Field(
        None,
        description="Datetime in ISO format with timezone offset.",
        json_schema_extra={"example": "2020-12-03T15:30:00+0000"},
    )
    hr: Optional[float] = Field(
        None, description="Relative humidity (%).", json_schema_extra={"example": 61}
    )
    ins: Optional[float] = Field(
        None,
        description="Incoming solar radiation in W/m².",
        json_schema_extra={"example": None},
    )
    lluv: Optional[float] = Field(
        None, description="Rainfall (mm).", json_schema_extra={"example": 0.0}
    )
    pres: Optional[float] = Field(
        None,
        description="Atmospheric pressure in hPa.",
        json_schema_extra={"example": 990.4},
    )
    rad_kj_m2: Optional[float] = Field(
        None, description="Radiation in kJ/m².", json_schema_extra={"example": None}
    )
    rad_w_m2: Optional[float] = Field(
        None, description="Radiation in W/m².", json_schema_extra={"example": 949.0}
    )
    rec: Optional[float | None] = Field(
        None, description="Record information.", json_schema_extra={"example": None}
    )
    temp: Optional[float] = Field(
        None, description="Temperature in Celsius.", json_schema_extra={"example": 1.4}
    )
    tmn: Optional[float] = Field(
        None,
        description="Minimum temperature in Celsius.",
        json_schema_extra={"example": 1.1},
    )
    tmx: Optional[float] = Field(
        None,
        description="Maximum temperature in Celsius.",
        json_schema_extra={"example": 1.8},
    )
    ts: Optional[float] = Field(
        None,
        description="Surface temperature in Celsius.",
        json_schema_extra={"example": 4.3},
    )
    tsb: Optional[float] = Field(
        None,
        description="Soil baseline temperature in Celsius.",
        json_schema_extra={"example": None},
    )
    tsmn: Optional[float] = Field(
        None,
        description="Minimum soil temperature in Celsius.",
        json_schema_extra={"example": None},
    )
    tsmx: Optional[float] = Field(
        None,
        description="Maximum soil temperature in Celsius.",
        json_schema_extra={"example": None},
    )
    vel: Optional[float] = Field(
        None, description="Wind speed in m/s.", json_schema_extra={"example": 1.9}
    )
    velx: Optional[float] = Field(
        None,
        description="Extreme wind speed in m/s.",
        json_schema_extra={"example": 3.6},
    )
    albedo: Optional[float] = Field(
        None, description="Surface albedo.", json_schema_extra={"example": 0.0}
    )
    difusa: Optional[float] = Field(
        None, description="Diffuse radiation.", json_schema_extra={"example": 0.0}
    )
    directa: Optional[float] = Field(
        None, description="Direct radiation.", json_schema_extra={"example": 0.0}
    )
    global_: Optional[float] = Field(
        None, description="Global radiation.", json_schema_extra={"example": 0.0}
    )
    ir_solar: Optional[float] = Field(
        None,
        description="Infrared solar radiation.",
        json_schema_extra={"example": 0.0},
    )
    neta: Optional[float] = Field(
        None, description="Net radiation.", json_schema_extra={"example": 0.0}
    )
    par: Optional[float] = Field(
        None,
        description="Photosynthetically active radiation.",
        json_schema_extra={"example": 0.0},
    )
    tcielo: Optional[float] = Field(
        None,
        description="Sky temperature in Celsius.",
        json_schema_extra={"example": 0.0},
    )
    ttierra: Optional[float] = Field(
        None,
        description="Ground temperature in Celsius.",
        json_schema_extra={"example": 0.0},
    )
    uvab: Optional[float] = Field(
        None, description="UVAB radiation.", json_schema_extra={"example": 0.0}
    )
    uvb: Optional[float] = Field(
        None, description="UVB radiation.", json_schema_extra={"example": 0.0}
    )
    uvi: Optional[float] = Field(
        None, description="UV index.", json_schema_extra={"example": 0.0}
    )
    qdato: Optional[float] = Field(
        None, description="Data quality indicator.", json_schema_extra={"example": 0}
    )
