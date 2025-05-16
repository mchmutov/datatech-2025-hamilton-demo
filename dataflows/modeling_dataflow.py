import pickle
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import shap
from hamilton.function_modifiers import dataloader, datasaver
from matplotlib import pyplot as plt
from sklearn.base import ClassifierMixin
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    PrecisionRecallDisplay,
    accuracy_score,
    average_precision_score,
    precision_score,
    recall_score,
)
from xgboost import XGBClassifier

# ------------------- #
# XGBoost Model


def base_model(hyperparams: Optional[dict]) -> ClassifierMixin:
    """Function that creates the (not yet fit) model."""
    if hyperparams is not None:
        return XGBClassifier(**hyperparams)
    else:
        return XGBClassifier(
            max_depth=3,
            learning_rate=0.2,
            objective="binary:logistic",
            eval_metric="logloss",
            enable_categorical=True,
        )


def trained_model(
    base_model: ClassifierMixin,
    features_df: pd.DataFrame,
    target_df: pd.DataFrame,
) -> ClassifierMixin:
    """Function that creates the (not yet fit) model."""
    base_model.fit(features_df, target_df)
    return base_model


@datasaver()
def save_model(
    trained_model: ClassifierMixin,
    model_file_path: str,
) -> dict:
    """Save the trained model to blob storage."""
    with open(model_file_path, "wb") as f:
        pickle.dump(trained_model, f)
    return {}


@dataloader()
def pretrained_model(
    model_file_path: str,
) -> Tuple[ClassifierMixin, dict]:
    """Load the trained model from blob storage."""
    with open(model_file_path, "rb") as f:
        model = pickle.load(f)
    return (
        model,
        {},
    )


def predicted_probabilities(
    pretrained_model: ClassifierMixin,
    features_df: pd.DataFrame,
) -> np.ndarray:
    """Evaluate the model on the test set."""
    return pretrained_model.predict_proba(features_df)[:, 1]


def predictions(
    predicted_probabilities: np.ndarray, prediction_threshold: float
) -> np.ndarray:
    """Thershold predicted probabilities to get binary prediction."""
    return predicted_probabilities > prediction_threshold


# ------------------- #
# Evaluation metrics


def accuracy(
    predictions: np.ndarray,
    target_df: pd.DataFrame,
) -> float:
    """Compute the accuracy."""
    accuracy = accuracy_score(target_df, predictions)
    print(f"Accuracy: {accuracy*100:.1f}%")
    return accuracy


def precision(
    predictions: np.ndarray,
    target_df: pd.DataFrame,
) -> float:
    """Compute the precision."""
    precision = precision_score(target_df, predictions)
    print(f"Precision: {precision*100:.1f}%")
    return precision


def average_precision(
    predicted_probabilities: np.ndarray, target_df: pd.DataFrame
) -> float:
    """Compute the average precision."""
    avg_precision = average_precision_score(target_df, predicted_probabilities)
    print(f"Average precision: {avg_precision*100:.5f}%")
    return avg_precision


def recall(
    predictions: np.ndarray,
    target_df: pd.DataFrame,
) -> float:
    """Compute the recall on the test set."""
    recall_value = recall_score(target_df, predictions)
    print(f"Recall: {recall_value*100:.1f}%")
    return recall_value


def confusion_matrix(predictions: np.ndarray, target_df: pd.DataFrame) -> None:
    """Plot the confusion matrix."""
    ConfusionMatrixDisplay.from_predictions(target_df, predictions, cmap="Greens")
    plt.show()


def precision_recall_curve(
    predicted_probabilities: np.ndarray, target_df: pd.DataFrame
) -> None:
    """Plot the precision recall curve."""
    PrecisionRecallDisplay.from_predictions(target_df, predicted_probabilities)
    plt.show()


def feature_importances(
    pretrained_model: ClassifierMixin, features_df: pd.DataFrame
) -> None:
    """Plot the feature importances from the XGBoostClassifier."""
    feature_importance = pretrained_model.feature_importances_
    sorted_idx = np.argsort(feature_importance)
    plt.figure(figsize=(12, 4))
    plt.barh(range(len(sorted_idx)), feature_importance[sorted_idx], align="center")
    plt.yticks(range(len(sorted_idx)), np.array(features_df.columns)[sorted_idx])
    plt.title("Feature Importance")
    plt.show()


def shap_beeswarm(pretrained_model: ClassifierMixin, features_df: pd.DataFrame) -> None:
    """Plot the shap beeswarm."""
    explainer = shap.Explainer(pretrained_model, features_df)
    shap_values = explainer(features_df)
    shap.plots.beeswarm(shap_values, max_display=20)
