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
    """
    conn = sqlite3.connect(feature_store_path)
    data.to_sql(name=table_name, con=conn, if_exists="replace", index=False)
    conn.close()
    logging.info(f"Saved {len(data)} records to feature store table '{table_name}'")


def read_from_feature_store(
    table_name: str, columns: Optional[List[str]], feature_store_path: str
) -> pd.DataFrame:
    """
    Read data from the feature store (SQLite database).
    """
    try:
        conn = sqlite3.connect(feature_store_path)
        if columns is not None:
            column_names = ", ".join(columns)
            query = f"SELECT {column_names} FROM {table_name}"
        else:
            query = f"SELECT * FROM {table_name}"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        logging.error(f"Error reading from feature store: {e}")
        if columns is not None:
            return pd.DataFrame(columns=columns)
        else:
            return pd.DataFrame()
