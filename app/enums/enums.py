from enum import Enum


class Station(str, Enum):
    JUAN_CARLOS_I = "89064"  # Estación Meteorológica Juan Carlos I
    JUAN_CARLOS_I_RADIO = "89064R"  # Estación Radiométrica Juan Carlos I
    JUAN_CARLOS_I_RADIO_OLD = (
        "89064RA"  # Estación Radiométrica Juan Carlos I (until 08/03/2007)
    )
    GABRIEL_DE_CASTILLA = "89070"  # Estación Meteorológica Gabriel de Castilla


class TimeAggregation(str, Enum):
    NONE = "None"
    HOURLY = "Hourly"
    DAILY = "Daily"
    MONTHLY = "Monthly"


class DataType(str, Enum):
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    SPEED = "speed"
