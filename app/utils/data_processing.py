from typing import Any
import pandas as pd
from fastapi import HTTPException
from app.core.logging_config import logger

def aggregate_data(df: pd.DataFrame, aggregation: str, start: Any, end: Any) -> pd.DataFrame:
    """
    Aggregate data based on the specified granularity, respecting the time zone in 'fhora'.

    Args:
        df (pd.DataFrame): Input DataFrame.
        aggregation (str): Aggregation level ("Hourly", "Daily", "Monthly").
        start (Any): Start datetime (can be str or pd.Timestamp).
        end (Any): End datetime (can be str or pd.Timestamp).

    Returns:
        pd.DataFrame: Aggregated DataFrame.
    """
    try:
        logger.warning(f"Data before aggregationNNNNNNNNNNNNNNNNNNNNN: {df.head()}")

        # Ensure 'fhora' is datetime and timezone-aware
        df["fhora"] = pd.to_datetime(df["fhora"])
        if not pd.api.types.is_datetime64tz_dtype(df["fhora"]):
            raise ValueError("Column 'fhora' must be timezone-aware.")

        # Set 'fhora' as the index
        df = df.set_index("fhora")

        # Convert start and end to pd.Timestamp if they are strings
        # start = pd.to_datetime(start) if isinstance(start, str) else start
        # end = pd.to_datetime(end) if isinstance(end, str) else end

        # # Ensure start and end are timezone-aware and align with DataFrame index timezone
        # tz = df.index.tz  # Get the timezone of the DataFrame index
        # if start.tzinfo is None:
        #     start = start.tz_localize(tz)
        # else:
        #     start = start.astimezone(tz)
        # if end.tzinfo is None:
        #     end = end.tz_localize(tz)
        # else:
        #     end = end.astimezone(tz)

        # Filter data within the given range
        df = df[(df.index >= start) & (df.index < end)]

        # Prepare aggregation logic
        numeric_columns = df.select_dtypes(include=["number"]).columns
        agg_dict = {col: "mean" for col in numeric_columns}
        if "nombre" in df.columns:
            agg_dict["nombre"] = "first"

        # Define resampling rules
        resample_map = {"Hourly": "h", "Daily": "D", "Monthly": "ME"}
        if aggregation in resample_map:
            df = df.resample(resample_map[aggregation]).agg(agg_dict).reset_index()
        else:
            raise ValueError(f"Invalid aggregation level: {aggregation}")

        return df
    except Exception as e:
        logger.error(f"Error during aggregation: {str(e)}")
        raise HTTPException(status_code=500, detail="Error aggregating data.")
