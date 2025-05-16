# DataTech 2025 Demo

This project demonstrates the use of the Hamilton Framework for Feaure engineering and machine learning, using a simulated dataset vaguely based on transportaion and logistics.

## Environment Setup

This project uses `uv`, a fast Python package installer and resolver, for dependency management.

### Setting up a Virtual Environment

1. Install `uv` if you haven't already:

4. Install dependencies:
   ```bash
   uv sync
   ```

## Project Structure

### Simulation Scripts

The project includes several simulation modules:

- **simulation.py**: Main entry point that coordinates load generation and carrier acceptance simulation. Run this script to generate a full simulation dataset.
  ```bash
  python simulation.py
  ```

- **load_simulation.py**: Generates random freight loads with realistic parameters.

- **carrier_simulation.py**: Simulates carrier decision-making for accepting loads.

### Data Storage

- **load_simulation_results.db**: SQLite database storing simulation results.
- **feature_store.db**: SQLite database for storing preprocessed features.
- **feature_store.py**: Helper module providing interface to store and retrieve features.


### Hamilton Dataflows

The `dataflows/` directory contains modular data processing pipelines built with Hamilton:

- **feature_engineering_dataflow.py**: Transforms raw simulation data into ML-ready features.
- **modeling_dataflow.py**: Facilitates model training, evaluation, and inference.
- **offline_etl_dataflow.py**: Handles batch data processing.
- **online_inference_dataflow.py**: Supports real-time inference.

Hamilton is used to create composable, maintainable data transformation pipelines with clear dependencies.

### Model Demo Notebook

- **model_demo.ipynb**: Jupyter notebook demonstrating the complete workflow:
  - Loading simulation data
  - Feature engineering with Hamilton
  - Training a model to predict load acceptance
  - Evaluating model performance
  - Making predictions

## Example Workflow

1. Run the simulation to generate data:
   ```bash
   python simulation.py
   ```

2. Explore the data and workflow in the notebook.

## Dependencies

Key dependencies include:
- pandas - Data manipulation
- hamilton - Feature engineering and dataflow orchestration
- prophet - Time series forecasting
- xgboost - Machine learning model
- matplotlib/plotly - Visualization

See pyproject.toml for a complete list of dependencies.