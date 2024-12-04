from datetime import datetime, time

import altair as alt
import pandas as pd
import requests
import streamlit as st

# Session State Initialization
if "fetched_data" not in st.session_state:
    st.session_state["fetched_data"] = None
if "fetched_full_data" not in st.session_state:
    st.session_state["fetched_full_data"] = None
if "metrics_to_display" not in st.session_state:
    st.session_state["metrics_to_display"] = ["temp", "pres", "vel"]
if "time_series_metrics" not in st.session_state:
    st.session_state["time_series_metrics"] = ["tcielo", "ttierra", "uvi"]


@st.cache_data
def fetch_weather_data(
    station_code, datetime_start, datetime_end, location, time_aggregation
):
    base_url = "http://localhost:8000/v1/antartida/timeseries/"

    if time_aggregation:
        time_aggregation = time_aggregation.capitalize()

    params = {
        "datetime_start": datetime_start,
        "datetime_end": datetime_end,
        "station": station_code,
        "location": location,
    }
    if time_aggregation and time_aggregation != "None":
        params["time_aggregation"] = time_aggregation

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    return pd.DataFrame(response.json())


@st.cache_data
def fetch_full_weather_data(
    station_code, datetime_start, datetime_end, location, time_aggregation
):
    base_url = "http://localhost:8000/v1/antartida/timeseries/full/"

    if time_aggregation:
        time_aggregation = time_aggregation.capitalize()

    params = {
        "datetime_start": datetime_start,
        "datetime_end": datetime_end,
        "station": station_code,
        "location": location,
        "time_aggregation": time_aggregation,
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    return pd.DataFrame(response.json())


# Sidebar for inputs
st.sidebar.header("Filter Parameters")

station_mapping = {
    "JUAN_CARLOS_I": "89064",
    "JUAN_CARLOS_I_RADIO": "89064R",
    "JUAN_CARLOS_I_RADIO_OLD": "89064RA",
    "GABRIEL_DE_CASTILLA": "89070",
}

station_descriptions = {
    "JUAN_CARLOS_I": "Meteorological station 'Juan Carlos I.'",
    "JUAN_CARLOS_I_RADIO": "Radiometric station 'Juan Carlos I.'",
    "JUAN_CARLOS_I_RADIO_OLD": "Old radiometric station 'Juan Carlos I' (until 08/03/2007).",
    "GABRIEL_DE_CASTILLA": "Meteorological station 'Gabriel de Castilla.'",
}

selected_station = st.sidebar.selectbox(
    "Select a Station",
    options=list(station_mapping.keys()),
    format_func=lambda x: station_descriptions[x],
)

start_date = st.sidebar.date_input("Start Date", value=datetime(2020, 12, 1).date())
start_time = st.sidebar.time_input("Start Time", value=time(0, 0))
datetime_start = datetime.combine(start_date, start_time)

end_date = st.sidebar.date_input("End Date", value=datetime(2020, 12, 2).date())
end_time = st.sidebar.time_input("End Time", value=time(23, 59))
datetime_end = datetime.combine(end_date, end_time)

location = st.sidebar.text_input("Location", value="Europe/Madrid")
time_aggregation = st.sidebar.selectbox(
    "Time Aggregation",
    options=[None, "hourly", "daily", "monthly"],
    format_func=lambda x: x or "None",
)

normalize_data = st.sidebar.checkbox("Normalize Metrics", value=False)

# Main Interface
st.title("Meteorological Data Viewer")

tabs = st.tabs(["Timeseries Data", "Full Timeseries Data"])

# Timeseries Tab
with tabs[0]:
    st.header("Timeseries Data")

    # Filter default values to ensure they exist in the options
    available_options = ["temp", "pres", "vel"]
    default_metrics = st.session_state.get("metrics_to_display", available_options)
    st.session_state["metrics_to_display"] = [
        m for m in default_metrics if m in available_options
    ]

    # Multiselect with safe defaults
    st.session_state["metrics_to_display"] = st.sidebar.multiselect(
        "Select Metrics to Display (Timeseries)",
        options=available_options,
        default=st.session_state["metrics_to_display"],
    )

    if st.sidebar.button("Fetch Timeseries Data"):
        try:
            df = fetch_weather_data(
                station_code=station_mapping[selected_station],
                datetime_start=datetime_start.isoformat(),
                datetime_end=datetime_end.isoformat(),
                location=location,
                time_aggregation=time_aggregation,
            )
            df["fhora"] = pd.to_datetime(df["fhora"])
            st.session_state["fetched_data"] = df
        except Exception as e:
            st.error(f"Error fetching timeseries data: {e}")

    if st.session_state["fetched_data"] is not None:
        df = st.session_state["fetched_data"]

        # Normalize data if needed
        if normalize_data:
            for metric in st.session_state["metrics_to_display"]:
                df[f"norm_{metric}"] = (df[metric] - df[metric].min()) / (
                    df[metric].max() - df[metric].min()
                )
            st.session_state["metrics_to_display"] = [
                f"norm_{metric}" for metric in st.session_state["metrics_to_display"]
            ]

        st.write("### Metrics Visualization")
        combined_chart = (
            alt.Chart(df)
            .transform_fold(
                st.session_state["metrics_to_display"], as_=["Metric", "Value"]
            )
            .mark_line()
            .encode(
                x=alt.X("fhora:T", title="Time"),
                y=alt.Y("Value:Q", title="Value"),
                color=alt.Color("Metric:N", title="Metric"),
                tooltip=["fhora:T", "Metric:N", "Value:Q"],
            )
            .properties(width=700, height=400)
        )
        st.altair_chart(combined_chart, use_container_width=True)

        # Summary Table
        st.write("### Summary Statistics")
        summary_stats = df[st.session_state["metrics_to_display"]].describe()
        st.dataframe(summary_stats)

        # Raw Data
        st.write("### Raw Data")
        st.dataframe(df[["fhora"] + st.session_state["metrics_to_display"]])

# Full Timeseries Tab
with tabs[1]:
    st.header("Full Timeseries Data")

    if st.sidebar.button("Fetch Full Timeseries Data"):
        try:
            df_full = fetch_full_weather_data(
                station_code=station_mapping[selected_station],
                datetime_start=datetime_start.isoformat(),
                datetime_end=datetime_end.isoformat(),
                location=location,
                time_aggregation=time_aggregation,
            )
            st.session_state["fetched_full_data"] = df_full
        except Exception as e:
            st.error(f"Error fetching full timeseries data: {e}")

    if st.session_state["fetched_full_data"] is not None:
        df_full = st.session_state["fetched_full_data"]

        # Map Visualization
        st.write("### Map Visualization")
        if "latitud" in df_full.columns and "longitud" in df_full.columns:
            st.map(df_full.rename(columns={"latitud": "lat", "longitud": "lon"}))
        else:
            st.warning("Latitude and longitude data not found for mapping.")

        # Summary Table
        st.write("### Data Summary")
        numerical_columns = [
            col
            for col in df_full.columns
            if pd.api.types.is_numeric_dtype(df_full[col])
        ]
        if numerical_columns:
            summary_table = df_full[numerical_columns].describe().transpose()
            summary_table["range"] = summary_table["max"] - summary_table["min"]
            st.dataframe(summary_table)
        else:
            st.warning("No numerical columns available for summary.")

        # Histogram
        st.write("### Histogram of a Selected Metric")
        if numerical_columns:
            selected_metric = st.selectbox(
                "Select Metric for Histogram", options=numerical_columns
            )
            histogram = (
                alt.Chart(df_full)
                .mark_bar()
                .encode(
                    x=alt.X(f"{selected_metric}:Q", bin=True, title=selected_metric),
                    y=alt.Y("count()", title="Frequency"),
                )
                .properties(width=700, height=400)
            )
            st.altair_chart(histogram, use_container_width=True)
        else:
            st.warning("No numerical columns available for histogram.")

        # Time Series Visualization
        st.write("### Time Series of Selected Metrics")
        time_series_metrics = st.multiselect(
            "Select Metrics to Plot", numerical_columns, default=numerical_columns[:3]
        )
        if time_series_metrics:
            time_series_chart = (
                alt.Chart(df_full)
                .transform_fold(time_series_metrics, as_=["Metric", "Value"])
                .mark_line()
                .encode(
                    x=alt.X("fhora:T", title="Time"),
                    y=alt.Y("Value:Q", title="Value"),
                    color=alt.Color("Metric:N", title="Metric"),
                    tooltip=["fhora:T", "Metric:N", "Value:Q"],
                )
                .properties(width=700, height=400)
            )
            st.altair_chart(time_series_chart, use_container_width=True)
        else:
            st.warning("No metrics selected for time series visualization.")

        # Scatter Plot
        st.write("### Scatter Plot of Two Metrics")
        if len(numerical_columns) >= 2:
            scatter_x = st.selectbox(
                "Select X-Axis Metric", options=numerical_columns, index=0
            )
            scatter_y = st.selectbox(
                "Select Y-Axis Metric", options=numerical_columns, index=1
            )
            scatter_plot = (
                alt.Chart(df_full)
                .mark_circle(size=60)
                .encode(
                    x=alt.X(f"{scatter_x}:Q", title=scatter_x),
                    y=alt.Y(f"{scatter_y}:Q", title=scatter_y),
                    tooltip=[scatter_x, scatter_y],
                )
                .properties(width=700, height=400)
            )
            st.altair_chart(scatter_plot, use_container_width=True)
        else:
            st.warning("Not enough numerical columns for scatter plot.")

        # Raw Data
        st.write("### Raw Data")
        st.dataframe(df_full)
