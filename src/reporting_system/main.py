# =============================================================================
# --- Main Application Imports ---
# These are now standard package imports that will work correctly
# when you run the project as a module.
# =============================================================================
from .shared import config
from .data_collection.core import db_executor
from .data_collection.core.crew_factory import create_crew
from .auto_analyst.graph.workflow import get_analysis_app

def run_full_pipeline(company_id: str, user_request: str):
    """
    Orchestrates the entire process.
    This function is now parameterized to accept company_id and user_request,
    making it suitable for programmatic calls (e.g., from an API).
    """
    # === KICKOFF STAGE 1: CrewAI ===
    # Pass the company_id to the create_crew function
    recomind_crew, source_db_settings = create_crew(company_id)

    if not recomind_crew:
        print("❌ Crew creation failed. Aborting pipeline.")
        return

    # The user_request is now passed in as a parameter, not from input()
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

    # === MODIFICATION START: Pass the user_request into the graph's initial state ===
    initial_state = {"dataframe": data_df, "user_request": user_request}
    # === MODIFICATION END ===
    
    final_state = analysis_app.invoke(initial_state)

    if final_state and final_state.get("analysis_report"):
        print("\n--- FINAL ANALYSIS REPORT ---")
        print(final_state["analysis_report"])

    print("\n🎉 FULL PIPELINE FINISHED SUCCESSFULLY!")
    
if __name__ == "__main__":
    # Example of how to run the refactored pipeline.
    # These values will eventually come from your API endpoint.
    test_company_id = "fb140d33-7e96-474d-a06d-ab3a6c65d1a9"
    test_user_request = "Full Sales Report including the Products Sales."

    print("--- Running Pipeline with Test Data ---")
    run_full_pipeline(company_id=test_company_id, user_request=test_user_request)
