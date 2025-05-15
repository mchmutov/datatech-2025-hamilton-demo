"""
Feature store utilities for the load simulation.

This module provides helper functions to read from and write to the feature store.
"""

import pandas as pd
import sqlite3
import logging
from typing import List, Optional


def save_to_feature_store(
    data: pd.DataFrame, table_name: str, feature_store_path: str
) -> None:
    """
    Save data to the feature store (SQLite database).

    The data is written to the specified table, replacing any existing data.
    Logs the number of records saved after completion.
    """
    # Create SQLite database connection
    conn = sqlite3.connect(feature_store_path)

    # Write the data to the database, replacing if it exists
    data.to_sql(name=table_name, con=conn, if_exists="replace", index=False)

    # Close the connection
    conn.close()

    logging.info(f"Saved {len(data)} records to feature store table '{table_name}'")


def read_from_feature_store(
    table_name: str, columns: Optional[List[str]], feature_store_path: str
) -> pd.DataFrame:
    """
    Read data from the feature store (SQLite database).

    Retrieves data from the specified table in the feature store.
    If columns are provided, only those columns will be selected.
    Returns an empty DataFrame if an error occurs.
    """
    try:
        # Create SQLite database connection
        conn = sqlite3.connect(feature_store_path)

        # Build the SQL query
        if columns is not None:
            column_names = ", ".join(columns)
            query = f"SELECT {column_names} FROM {table_name}"
        else:
            query = f"SELECT * FROM {table_name}"

        # Execute the query
        df = pd.read_sql(query, conn)

        # Close the connection
        conn.close()

        return df

    except Exception as e:
        logging.error(f"Error reading from feature store: {e}")
        # Return empty DataFrame if there's an error
        if columns is not None:
            return pd.DataFrame(columns=columns)
        else:
            return pd.DataFrame()
