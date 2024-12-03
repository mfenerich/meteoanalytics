"""
This module defines enumerations for use in the application.

Such as station identifiers, time aggregation levels,
and weather data types.
"""

from enum import Enum


class Station(str, Enum):
    """
    Enumeration of weather stations in Antarctica.

    Attributes:
        JUAN_CARLOS_I: Meteorological station "Juan Carlos I."
        JUAN_CARLOS_I_RADIO: Radiometric station "Juan Carlos I."
        JUAN_CARLOS_I_RADIO_OLD: Old radiometric station
            "Juan Carlos I" (until 08/03/2007).
        GABRIEL_DE_CASTILLA: Meteorological station "Gabriel de Castilla."
    """

    JUAN_CARLOS_I = "89064"  # Estación Meteorológica Juan Carlos I
    JUAN_CARLOS_I_RADIO = "89064R"  # Estación Radiométrica Juan Carlos I
    JUAN_CARLOS_I_RADIO_OLD = (
        "89064RA"  # Estación Radiométrica Juan Carlos I (until 08/03/2007)
    )
    GABRIEL_DE_CASTILLA = "89070"  # Estación Meteorológica Gabriel de Castilla


class TimeAggregation(str, Enum):
    """
    Enumeration of time aggregation levels for meteorological data.

    Attributes:
        NONE: No aggregation applied.
        HOURLY: Data aggregated hourly.
        DAILY: Data aggregated daily.
        MONTHLY: Data aggregated monthly.
    """

    NONE = "None"
    HOURLY = "Hourly"
    DAILY = "Daily"
    MONTHLY = "Monthly"


class DataType(str, Enum):
    """
    Enumeration of meteorological data types.

    Attributes:
        TEMPERATURE: Temperature data in Celsius.
        PRESSURE: Atmospheric pressure data in hPa.
        SPEED: Wind speed data in m/s.
    """

    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    SPEED = "speed"
