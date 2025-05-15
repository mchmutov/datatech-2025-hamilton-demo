from simulation import run_simulation, load_simulation_data
import os


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
