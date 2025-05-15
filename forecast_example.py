"""
Example script showing how to use the lane_acceptance_forecast feature.

This script demonstrates:
1. Loading data from the simulation database
2. Using Hamilton to generate lane acceptance forecasts with extracted components
3. Visualizing the forecast results with Prophet's built-in plotting capabilities
"""

import matplotlib.pyplot as plt
import os
from hamilton import driver
import hamilton_dataflow


def main():
    print("Lane Acceptance Forecast Example")
    print("--------------------------------")

    db_path = "load_simulation_results.db"

    # Configure Hamilton driver
    adapter = driver.Builder().with_modules(hamilton_dataflow).build()

    # Load data and forecast using the extracted components directly
    print("Generating forecasts...")

    # Execute the dataflow to get our forecasts using the extracted components
    results = adapter.execute(
        ["forecast_models", "prophet_forecasts", "lane_forecast_summary"],
        inputs={"db_path": db_path},
    )

    # Get the forecast results from the extracted components
    forecast_models = results["forecast_models"]
    prophet_forecasts = results["prophet_forecasts"]
    forecast_summary = results["lane_forecast_summary"]

    if forecast_summary.empty:
        print("No forecast data available. Make sure you have enough historical data.")
        return

    print(f"Generated forecasts for {len(forecast_summary)} lane-date combinations")
    print(f"Created {len(forecast_models)} models for {len(prophet_forecasts)} lanes")
    print(f"Forecast summary sample:\n{forecast_summary.sample(60)}")

    # Create a directory for plots if it doesn't exist
    plots_dir = "forecast_plots"
    os.makedirs(plots_dir, exist_ok=True)

    # Get the available keys from the forecast_models dictionary
    model_keys = list(forecast_models.keys())
    lanes_to_plot = [("CA_LAX", "CA_STK"), ("GA_ATL", "IL_CHI"), ("FL_LAK", "IL_CHI")]

    # Create individual plots for each lane
    for origin, dest in lanes_to_plot:
        # Find keys that contain both origin and destination
        matching_keys = [k for k in model_keys if origin in k and dest in k]

        if matching_keys:
            lane_key = matching_keys[0]  # Use the first matching key
            # Get the model, forecast and history for this lane
            model = forecast_models[lane_key]
            forecast = prophet_forecasts[lane_key]
            fig = model.plot(forecast)
            # print(f"\nCreating Prophet plots for lane: {origin} to {dest} using key {lane_key}. Forecast tail:\n{forecast.tail(5)}")
            # Save the plot
            plt.tight_layout()
            plot_path = f"{plots_dir}/{origin}_to_{dest}_forecast.png"
            plt.savefig(plot_path)
            plt.close(fig)  # Close the figure to free memory
            # Create components plot for this lane
            fig = plt.figure(figsize=(12, 10))
            components_fig = model.plot_components(forecast)
            plt.tight_layout()
            components_path = f"{plots_dir}/{origin}_to_{dest}_components.png"
            plt.savefig(components_path)
            plt.close(components_fig)  # Close the figure to free memory
        else:
            print(f"\nNo matching key found for lane {origin} to {dest}")

    # Create summary plot of all top lanes
    plt.figure(figsize=(12, 6))

    for origin, dest in lanes_to_plot:

        # Find keys that contain both origin and destination
        matching_keys = [
            k for k in prophet_forecasts.keys() if origin in k and dest in k
        ]

        if matching_keys:
            lane_key = matching_keys[0]
            forecast = prophet_forecasts[lane_key]
            plt.plot(
                forecast["ds"],
                forecast["yhat"],
                marker="o",
                label=f"{origin} to {dest}",
            )
            # Add uncertainty intervals
            plt.fill_between(
                forecast["ds"],
                forecast["yhat_lower"],
                forecast["yhat_upper"],
                alpha=0.2,
            )
    plt.title("Lane Acceptance Rate Forecasts")
    plt.xlabel("Date")
    plt.ylabel("Forecasted Acceptance Rate")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{plots_dir}/lane_acceptance_summary.png")

    # Close database connection
    adapter.execute(["close_connection"], inputs={"db_path": db_path})
    print("\nDone!")


if __name__ == "__main__":
    main()
