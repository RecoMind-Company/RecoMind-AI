# src/recomind/main.py

# No need for os or sys imports for path manipulation anymore.

# =============================================================================
# --- Main Application Imports ---
# These are now standard package imports that will work correctly
# when you run the project as a module.
# =============================================================================
from ..shared import config
from .data_collection.core import db_executor
from .data_collection.core.crew_factory import create_crew
from .auto_analyst.graph.workflow import get_analysis_app

def run_full_pipeline():
    """
    Orchestrates the entire process:
    1. Runs CrewAI to generate a SQL query.
    2. Executes the query to get a DataFrame.
    3. Runs LangGraph to analyze the DataFrame and generate a report.
    """
    # === KICKOFF STAGE 1: CrewAI ===
    # Unpack the crew object and the settings dictionary
    recomind_crew, source_db_settings = create_crew()

    if not recomind_crew:
        print("❌ Crew creation failed. Aborting pipeline.")
        return

    user_request = input("Enter your data request (e.g., 'Sales overview' or 'Active Employees'): ")
    print(f"\n🚀 STAGE 1: RUNNING DATA COLLECTION CREW FOR: '{user_request}'")

    sql_query = recomind_crew.kickoff(inputs={'user_request': user_request})

    if not sql_query or "ERROR:" in str(sql_query):
        print(f"\n❌ PIPELINE HALTED: CrewAI failed to generate a valid SQL query.")
        return

    print(f"\n✅ STAGE 1 COMPLETE. Final SQL Query:\n{sql_query}")

    # === EXECUTE QUERY ===
    print(f"\n🚀 STAGE 2: EXECUTING QUERY TO FETCH DATA...")
    # Pass the correct settings dictionary to the executor
    data_df = db_executor.execute_query_to_dataframe(sql_query, source_db_settings)

    if data_df is None or data_df.empty:
        print(f"\n❌ PIPELINE HALTED: Query execution failed or returned no data.")
        return

    print(f"✅ STAGE 2 COMPLETE. Data fetched successfully. Shape: {data_df.shape}")

    # === KICKOFF STAGE 3: LangGraph ===
    print(f"\n🚀 STAGE 3: RUNNING DATA ANALYSIS GRAPH...")
    analysis_app = get_analysis_app()

    initial_state = {"dataframe": data_df}
    final_state = analysis_app.invoke(initial_state)

    if final_state and final_state.get("analysis_report"):
        print("\n--- FINAL ANALYSIS REPORT ---")
        print(final_state["analysis_report"])

    print("\n🎉 FULL PIPELINE FINISHED SUCCESSFULLY!")
    
if __name__ == "__main__":
    run_full_pipeline()