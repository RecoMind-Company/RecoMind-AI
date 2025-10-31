# =============================================================================
# --- Main Application Imports ---
# =============================================================================
import asyncio
import logging
from .shared import config
from .data_collection.core import db_executor # IMPORTANT: This must have an async version
from .data_collection.core.crew_factory import create_crew
from .auto_analyst.graph.workflow import get_analysis_app

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_full_pipeline(company_id: str, user_request: str) -> str:
    """
    Orchestrates the entire asynchronous process.
    This function is now async and returns the final report string.
    """
    
    # === KICKOFF STAGE 1: CrewAI ===
    logger.info(f"Pipeline started for company: {company_id}")
    recomind_crew, source_db_settings = create_crew(company_id)

    if not recomind_crew:
        logger.error("❌ Crew creation failed. Aborting pipeline.")
        return "Error: Crew creation failed."

    logger.info(f"🚀 STAGE 1: RUNNING DATA COLLECTION CREW FOR: '{user_request}'")
    
    # Use the async method for CrewAI
    sql_query = await asyncio.to_thread(recomind_crew.kickoff, inputs={'user_request': user_request})

    if not sql_query or "ERROR:" in str(sql_query):
        logger.error(f"❌ PIPELINE HALTED: CrewAI failed to generate a valid SQL query.")
        return "Error: Failed to generate SQL query."

    logger.info(f"✅ STAGE 1 COMPLETE. Final SQL Query generated.")

    # === EXECUTE QUERY ===
    logger.info(f"🚀 STAGE 2: EXECUTING QUERY TO FETCH DATA...")
    
    # IMPORTANT: This executor must be async (e.g., db_executor.execute_query_async)
    # Using a sync function here will block the server.
    # We'll assume db_executor.execute_query_to_dataframe is async for this example
    try:
        # This is a placeholder. You MUST replace this with a real async db call
        data_df = await db_executor.execute_query_to_dataframe_async(sql_query, source_db_settings)
    except Exception as e:
        logger.error(f"❌ PIPELINE HALTED: Async query execution failed: {e}")
        return f"Error: Database query failed. {e}"

    if data_df is None or data_df.empty:
        logger.error(f"❌ PIPELINE HALTED: Query execution returned no data.")
        return "Error: Query returned no data."

    logger.info(f"✅ STAGE 2 COMPLETE. Data fetched successfully. Shape: {data_df.shape}")

    # === KICKOFF STAGE 3: LangGraph ===
    logger.info(f"🚀 STAGE 3: RUNNING DATA ANALYSIS GRAPH...")
    analysis_app = get_analysis_app()

    initial_state = {"dataframe": data_df, "user_request": user_request}
    
    # Use the async method for LangGraph
    final_state = await analysis_app.ainvoke(initial_state)

    if final_state and final_state.get("analysis_report"):
        logger.info("✅ STAGE 3 COMPLETE. Analysis report generated.")
        
        # --- [MODIFICATION] Return the report string, do not save or print ---
        return final_state["analysis_report"]
    else:
        logger.error("❌ PIPELINE HALTED: LangGraph failed to generate a report.")
        return "Error: Analysis graph failed to produce a report."

# The __name__ == "__main__" block is for testing the async function
# You need asyncio.run() to test it
if __name__ == "__main__":
    import asyncio
    
    test_company_id = "fb140d33-7e96-474d-a06d-ab3a6c65d1a9"
    test_user_request = "Full Employees Report including their Salaries."

    print("--- Running Async Pipeline Test ---")
    
    # This is how you run an async function from a sync script
    try:
        report = asyncio.run(run_full_pipeline(company_id=test_company_id, user_request=test_user_request))
        print("\n--- FINAL ANALYSIS REPORT (from test) ---")
        print(report)
    except Exception as e:
        print(f"Test run failed: {e}")
        print("NOTE: This might be because 'execute_query_to_dataframe_async' is not yet implemented.")
