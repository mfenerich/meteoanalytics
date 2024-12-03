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

        # Return an empty DataFrame early if input is empty
        if df.empty:
            return pd.DataFrame()

        # Ensure 'fhora' is datetime
        df["fhora"] = pd.to_datetime(df["fhora"])

        # If 'fhora' is timezone-naive, localize to UTC
        if not pd.api.types.is_datetime64tz_dtype(df["fhora"]):
            df["fhora"] = df["fhora"].dt.tz_localize("UTC")

        # Ensure start and end are timezone-aware
        start = pd.Timestamp(start)
        end = pd.Timestamp(end)
        if start.tzinfo is None:
            start = start.tz_localize("UTC")
        if end.tzinfo is None:
            end = end.tz_localize("UTC")

        # Validate time range
        if start >= end:
            raise ValueError("Start time must be before end time.")

        # Set 'fhora' as the index
        df = df.set_index("fhora")

        # Filter data within the specified range
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
        raise HTTPException(status_code=500, detail=f"Error aggregating data: {str(e)}")
