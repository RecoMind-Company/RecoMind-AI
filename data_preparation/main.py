import os
from dotenv import load_dotenv
from core.crew_setup import recomind_crew
import pandas as pd

load_dotenv()

if __name__ == "__main__":
    user_request = input("Enter your key (e.g., 'sales' or 'employees'): ")
    print("Starting the CrewAI process for the user request: " + user_request)

    result = recomind_crew.kickoff(inputs={'user_request': user_request})

    if isinstance(result, pd.DataFrame):
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_filename = os.path.join(parent_dir, "data.csv")
        
        try:
            result.to_csv(csv_filename, index=False)
            print(f"\n--- Final Result ---")
            print(f"Data saved successfully to {csv_filename} with {len(result)} rows.")
            print("\nPreview of the data:")
            print(result.head())
        except Exception as e:
            print(f"\n--- Error ---")
            print(f"Failed to save CSV file: {e}")
    else:
        print("\n--- Error ---")
        print("Crew failed to return a DataFrame. Result was:")
        print(result)