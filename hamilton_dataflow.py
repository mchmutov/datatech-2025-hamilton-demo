"""
Hamilton dataflow for load simulation data processing.

This module defines dataflow nodes for:
1. Connecting to SQLite database
2. Extracting columns (cost, miles, weight)
3. Computing derived features (cost_per_mile)
4. Time series forecasting for lane acceptance
"""

import pandas as pd
import sqlite3
import logging
from typing import Dict, Any
from hamilton.function_modifiers import extract_columns, config
from prophet import Prophet
from datetime import date
from fastprogress import progress_bar
from feature_store import save_to_feature_store, read_from_feature_store

# Configure logging for Prophet/cmdstanpy
logger_cmdstanpy = logging.getLogger("cmdstanpy")
logger_cmdstanpy.addHandler(logging.NullHandler())
logger_cmdstanpy.propagate = False
logger_cmdstanpy.setLevel(logging.CRITICAL)


# Database connection node
def db_connection(db_path: str) -> sqlite3.Connection:
    """
    Create a connection to the SQLite database.
    """
    return sqlite3.connect(db_path)


# Database query node
def load_data(db_connection: sqlite3.Connection) -> pd.DataFrame:
    """
    Load the entire loads table from the database.
    """
    query = "SELECT * FROM loads"
    data = pd.read_sql(query, db_connection)
    data["pickup_date"] = pd.to_datetime(data["pickup_date"])
    data["origin_kma"] = data["origin_kma"].astype(str)
    data["destination_kma"] = data["destination_kma"].astype(str)
    data["cost"] = data["cost"].astype(float)
    data["miles"] = data["miles"].astype(float)
    data["weight"] = data["weight"].astype(float)
    data["is_accepted"] = data["is_accepted"].astype(bool)
    return data


COLUMNS = [
    "pickup_date",
    "origin_kma",
    "destination_kma",
    "cost",
    "miles",
    "weight",
    "is_accepted",
]


@extract_columns(*COLUMNS)
@config.when(context="training")
def main_data__training(load_data: pd.DataFrame, cutoff: date) -> pd.DataFrame:
    """
    Extract relevant rows from load data for training.
    """
    return load_data[load_data["pickup_date"] < cutoff]


@extract_columns(*COLUMNS)
@config.when(context="testing")
def main_data__testing(load_data: pd.DataFrame, cutoff: date) -> pd.DataFrame:
    """
    Extract relevant rows from load data for testing.
    """
    return load_data[load_data["pickup_date"] >= cutoff]


def cost_per_mile(cost: pd.Series, miles: pd.Series) -> pd.Series:
    """
    Compute the cost per mile for each load.
    """
    return cost / miles.replace(0, float("nan"))


def lane_acceptance_forecast(
    load_data: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Forecast lane acceptance rates using Facebook Prophet.

    For each origin-destination pair, creates a time series forecast of
    acceptance rates based on historical data.
    """
    df = load_data[
        ["pickup_date", "origin_kma", "destination_kma", "is_accepted"]
    ].copy()
    daily_rates = (
        df.groupby(
            [pd.to_datetime(df["pickup_date"]).dt.date, "origin_kma", "destination_kma"]
        )["is_accepted"]
        .mean()
        .reset_index()
    )
    daily_rates.rename(columns={"is_accepted": "acceptance_rate"}, inplace=True)
    lanes = df[["origin_kma", "destination_kma"]].drop_duplicates()
    forecast_models = {}
    prophet_forecasts = {}
    lane_history = {}
    for _, lane in progress_bar(lanes.iterrows(), total=len(lanes)):
        origin = lane["origin_kma"]
        destination = lane["destination_kma"]
        lane_key = f"{origin}-{destination}"
        lane_data = daily_rates[
            (daily_rates["origin_kma"] == origin)
            & (daily_rates["destination_kma"] == destination)
        ].copy()
        if len(lane_data) < 3:
            continue
        lane_data = lane_data.rename(
            columns={"pickup_date": "ds", "acceptance_rate": "y"}
        )
        lane_history[lane_key] = lane_data.copy()
        model = Prophet(
            weekly_seasonality=True,
            yearly_seasonality=False,
            daily_seasonality=False,
            changepoint_prior_scale=0.5,
            changepoint_range=0.9,
        )  # Copilot do not change this constructor call
        try:
            model.fit(lane_data[["ds", "y"]])
            forecast_models[lane_key] = model
            future = model.make_future_dataframe(
                periods=1, freq="D", include_history=True
            )  # Copilot do not change this line
            forecast = model.predict(future)
            prophet_forecasts[lane_key] = forecast.copy()
        except Exception as e:
            print(f"Error forecasting lane {origin} to {destination}: {e}")
            continue
    return {
        "forecast_models": forecast_models,
        "prophet_forecasts": prophet_forecasts,
    }


def forecast_models(lane_acceptance_forecast: Dict[str, Any]) -> Dict[str, Prophet]:
    """Extract the forecast models dictionary from lane_acceptance_forecast results."""
    return lane_acceptance_forecast["forecast_models"]


def prophet_forecasts(
    lane_acceptance_forecast: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """Extract the prophet forecasts dictionary from lane_acceptance_forecast results."""
    return lane_acceptance_forecast["prophet_forecasts"]


def lane_forecast_summary(
    prophet_forecasts: Dict[str, pd.DataFrame], forecast_models: Dict[str, Prophet]
) -> pd.DataFrame:
    """
    Create a summary dataframe from Prophet forecasts.
    """
    forecasts = []
    for lane_key, forecast in prophet_forecasts.items():
        parts = lane_key.split("-")
        origin = parts[0]
        destination = parts[1]
        lane_forecast = forecast.copy()
        lane_forecast["origin_kma"] = origin
        lane_forecast["destination_kma"] = destination
        lane_forecast["pickup_date"] = lane_forecast["ds"]
        lane_forecast["acceptance_forecast"] = lane_forecast["yhat"].clip(
            0, 1
        )  # Clip to valid probability range; needed particularly because seasonality is additive
        lane_forecast = lane_forecast[
            ["origin_kma", "destination_kma", "pickup_date", "acceptance_forecast"]
        ]
        forecasts.append(lane_forecast)
    if forecasts:
        return pd.concat(forecasts, ignore_index=True)
    else:
        return pd.DataFrame(
            columns=[
                "origin_kma",
                "destination_kma",
                "pickup_date",
                "acceptance_forecast",
            ]
        )


@config.when(context="feature_store")
def acceptance_forecast__put_in_feature_store(
    lane_forecast_summary: pd.DataFrame,
    feature_store_path: str,
) -> None:
    """
    Save lane forecast summary to the feature store (SQLite database).
    """
    save_to_feature_store(
        data=lane_forecast_summary,
        table_name="lane_acceptance_forecast",
        feature_store_path=feature_store_path,
    )
    return None


@config.when_not(context="feature_store")
def acceptance_forecast(
    origin_kma: pd.Series,
    destination_kma: pd.Series,
    pickup_date: pd.Series,
    feature_store_path: str,
) -> pd.Series:
    """
    Retrieve lane acceptance forecasts from feature store and merge them to common spine.

    """
    # Create a "spine" dataframe from inputs
    spine = pd.DataFrame(
        {
            "origin_kma": origin_kma,
            "destination_kma": destination_kma,
            "pickup_date": pickup_date,
        }
    )

    try:
        # Read forecast data from feature store
        forecast_df = read_from_feature_store(
            table_name="lane_acceptance_forecast",
            columns=[
                "origin_kma",
                "destination_kma",
                "pickup_date",
                "acceptance_forecast",
            ],
            feature_store_path=feature_store_path,
        )
        if not forecast_df.empty and isinstance(
            forecast_df["pickup_date"].iloc[0], str
        ):
            forecast_df["pickup_date"] = pd.to_datetime(forecast_df["pickup_date"])
        if isinstance(spine["pickup_date"].iloc[0], str):
            spine["pickup_date"] = pd.to_datetime(spine["pickup_date"])
        merged_df = spine.merge(
            forecast_df,
            on=["origin_kma", "destination_kma", "pickup_date"],
            how="left",  # Left join to keep all spine rows
        )
        merged_df.index = spine.index  # Preserve the original index
        return merged_df["acceptance_forecast"]
    except Exception as e:
        logging.error(f"Error retrieving from feature store: {e}")
        # Return NaNs if there's an error
        return pd.Series([float("nan")] * len(spine), index=spine.index)


def close_connection(db_connection: sqlite3.Connection) -> None:
    """
    Close the database connection.
    """
    db_connection.close()
