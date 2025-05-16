import sqlite3
import pandas as pd
from datetime import date
from hamilton.function_modifiers import extract_columns, config


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
