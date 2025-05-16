from load_simulation import generate_random_load
from carrier_simulation import process_load_offers
from datetime import date, timedelta
import pandas as pd
import sqlite3
import os


def run_simulation(db_path="load_simulation_results.db"):
    """
    Run the full simulation and save results to a database

    Args:
        db_path (str): Path to the SQLite database file

    Returns:
        pandas.DataFrame: DataFrame containing the simulation results
    """
    print("Generating loads for every weekday between February and May 2025...")

    # Define the date range
    start_date = date(2025, 2, 1)
    end_date = date(2025, 5, 31)

    # Create a list of all weekdays in the range
    current_date = start_date
    weekdays = []
    while current_date <= end_date:
        # Check if it's a weekday (0 = Monday, ..., 4 = Friday)
        if current_date.weekday() < 5:
            weekdays.append(current_date)
        current_date += timedelta(days=1)

    print(f"Found {len(weekdays)} weekdays between February and May 2025")

    # Prepare a list for all load data
    all_loads_data = []

    # Process 500 loads per weekday
    for weekday in weekdays:
        print(f"Processing loads for {weekday.strftime('%Y-%m-%d')}...")

        # Generate 500 loads for this date
        loads = []
        for _ in range(500):
            load = generate_random_load(weekday)
            loads.append(load)

        # Process loads through carrier simulation
        accepted_loads, rejected_loads = process_load_offers(loads)

        # Store data for each load
        for load in loads:
            is_accepted = load in accepted_loads

            # Create a dictionary with all load data
            load_data = {
                "id": load.id,
                "pickup_date": load.pickup_date.isoformat(),
                "origin_kma": load.origin.kma.value,
                "origin_lat": load.origin.latitude,
                "origin_lon": load.origin.longitude,
                "destination_kma": load.destination.kma.value,
                "destination_lat": load.destination.latitude,
                "destination_lon": load.destination.longitude,
                "miles": load.miles,
                "cost": load.cost,
                "weight": load.weight,
                "is_accepted": is_accepted,
            }

            all_loads_data.append(load_data)

    # Create a DataFrame with all load data
    df = pd.DataFrame(all_loads_data)

    print(f"Total loads processed: {len(df)}")
    print(f"Accepted loads: {df['is_accepted'].sum()} ({df['is_accepted'].mean():.1%})")

    # Save to SQLite database
    print(f"Saving results to SQLite database: {db_path}")

    # Create connection to SQLite database
    conn = sqlite3.connect(db_path)

    # Save DataFrame to database
    df.to_sql("loads", conn, if_exists="replace", index=False)

    # Create helpful indices
    conn.execute("CREATE INDEX IF NOT EXISTS idx_pickup_date ON loads (pickup_date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_origin_kma ON loads (origin_kma)")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_destination_kma ON loads (destination_kma)"
    )

    # Close connection
    conn.close()

    print("Data successfully saved to SQLite database.")

    return df


def load_simulation_data(db_path="load_simulation_results.db"):
    """
    Load simulation data from a database

    Args:
        db_path (str): Path to the SQLite database file

    Returns:
        pandas.DataFrame: DataFrame containing the simulation results
    """
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT * FROM loads", conn)
    conn.close()

    return df


def main():
    db_path = "load_simulation_results.db"

    # Check if the database already exists
    if os.path.exists(db_path):
        print(f"Database found at {db_path}. Loading existing data...")
        df = load_simulation_data(db_path)

        print(f"Loaded {len(df)} records from database.")
        print(
            f"Accepted loads: {df['is_accepted'].sum()} ({df['is_accepted'].mean():.1%})"
        )
        print("Data preview:")
        print(df.head())
        return

    # Run the simulation if the database doesn't exist
    run_simulation(db_path)


if __name__ == "__main__":
    main()
