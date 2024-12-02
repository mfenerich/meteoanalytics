import pandas as pd
from fastapi import HTTPException
from app.core.logging_config import logger

def aggregate_data(df: pd.DataFrame, aggregation: str) -> pd.DataFrame:
    """Aggregate data based on the specified granularity."""
    try:
        df = df.set_index("fhora")
        numeric_columns = df.select_dtypes(include=["number"]).columns
        agg_dict = {col: "mean" for col in numeric_columns}
        if "nombre" in df.columns:
            agg_dict["nombre"] = "first"

        resample_map = {"Hourly": "H", "Daily": "D", "Monthly": "M"}
        if aggregation in resample_map:
            df = df.resample(resample_map[aggregation]).agg(agg_dict).reset_index()
        else:
            raise ValueError(f"Invalid aggregation level: {aggregation}")
        return df
    except Exception as e:
        logger.error(f"Error during aggregation: {str(e)}")
        raise HTTPException(status_code=500, detail="Error aggregating data.")