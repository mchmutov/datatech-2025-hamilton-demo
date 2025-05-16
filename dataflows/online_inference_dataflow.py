"""
Online inference dataflow
"""

from typing import Dict, Any
from models import Load
from hamilton.function_modifiers import extract_fields
import pandas as pd

FIELDS = {
    "pickup_date": pd.Series,
    "origin_kma": pd.Series,
    "destination_kma": pd.Series,
    "cost": pd.Series,
    "miles": pd.Series,
    # "weight": pd.Series,
}


@extract_fields(FIELDS)
def load_to_features(load: Load) -> Dict[str, Any]:
    """
    Convert a Load object to a dictionary with features needed for inference.

    Args:
        load: A Load object from the models module

    Returns:
        Dictionary with extracted features for model input
    """
    return {
        "pickup_date": pd.to_datetime(pd.Series([load.pickup_date], index=[0])),
        "origin_kma": pd.Series([load.origin.kma], index=[0]).astype(str),
        "destination_kma": pd.Series([load.destination.kma], index=[0]).astype(str),
        "cost": pd.Series([load.cost], index=[0]).astype(float),
        "miles": pd.Series([load.miles], index=[0]).astype(float),
        "weight": pd.Series([load.weight], index=[0]).astype(float),
    }
