import pandas as pd
from fastapi import HTTPException
from app.core.logging_config import logger

def aggregate_data(df: pd.DataFrame, aggregation: str) -> pd.DataFrame:
    """
    Aggregate data based on the specified granularity, respecting the time zone in 'fhora'.

    Args:
        df (pd.DataFrame): Input DataFrame.
        aggregation (str): Aggregation level ("Hourly", "Daily", "Monthly").

    Returns:
        pd.DataFrame: Aggregated DataFrame.
    """
    try:
        # Ensure 'fhora' is datetime and timezone-aware
        df["fhora"] = pd.to_datetime(df["fhora"])
        if not pd.api.types.is_datetime64tz_dtype(df["fhora"]):
            raise ValueError("Column 'fhora' must be timezone-aware.")

        # Set 'fhora' as the index
        df = df.set_index("fhora")

        # Prepare aggregation logic
        numeric_columns = df.select_dtypes(include=["number"]).columns
        agg_dict = {col: "mean" for col in numeric_columns}
        if "nombre" in df.columns:
            agg_dict["nombre"] = "first"

        # Define resampling rules
        resample_map = {"Hourly": "h", "Daily": "D", "Monthly": "M"}
        if aggregation in resample_map:
            df = df.resample(resample_map[aggregation], origin="start").agg(agg_dict).reset_index()
        else:
            raise ValueError(f"Invalid aggregation level: {aggregation}")

        return df
    except Exception as e:
        logger.error(f"Error during aggregation: {str(e)}")
        raise HTTPException(status_code=500, detail="Error aggregating data.")
