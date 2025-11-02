# === [MODIFIED FILE] ===

import asyncio
import logging
# [MODIFICATION] Import the celery_app we just defined
from celery_worker import celery_app
# ---
from shared import config
from data_collection.core import db_executor 
from data_collection.core.crew_factory import create_crew
from auto_analyst.graph.workflow import get_analysis_app

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === [MODIFICATION] ===
# We wrap the *entire* pipeline function with the @celery_app.task decorator.
# This turns it from a regular function into a Background Task.
# We also add 'bind=True' so we can update the status.
@celery_app.task(bind=True)
def run_full_pipeline(self, company_id: str, user_request: str) -> str:
    """
    (This is now a Celery Task)
    Orchestrates the entire asynchronous process.
    This function is now async and returns the final report string.
    """
    
    try:
        # === KICKOFF STAGE 1: CrewAI ===
        self.update_state(state='PROGRESS', meta={'status': 'STAGE 1: CrewAI Started...'})
        logger.info(f"Pipeline started for company: {company_id}")
        recomind_crew, source_db_settings = create_crew(company_id)

        if not recomind_crew:
            logger.error("❌ Crew creation failed. Aborting pipeline.")
            raise Exception("Error: Crew creation failed.")

        logger.info(f"🚀 STAGE 1: RUNNING DATA COLLECTION CREW FOR: '{user_request}'")
        
        # [MODIFICATION] We can't use 'await' inside a sync Celery task.
        # We must call the 'blocking' version 'kickoff' directly.
        # Celery runs this in its own process, so it's safe to block.
        sql_query = recomind_crew.kickoff(inputs={'user_request': user_request})

        if not sql_query or "ERROR:" in str(sql_query):
            logger.error(f"❌ PIPELINE HALTED: CrewAI failed to generate a valid SQL query.")
            raise Exception("Error: Failed to generate SQL query.")

        logger.info(f"✅ STAGE 1 COMPLETE. Final SQL Query generated.")

        # === EXECUTE QUERY ===
        self.update_state(state='PROGRESS', meta={'status': 'STAGE 2: Fetching Data...'})
        logger.info(f"🚀 STAGE 2: EXECUTING QUERY TO FETCH DATA...")
        
        # [MODIFICATION] We MUST use the *synchronous* (blocking) executor here.
        # The Celery worker is a separate process and *should* block.
        try:
            data_df = db_executor.execute_query_to_dataframe(sql_query, source_db_settings)
        except Exception as e:
            logger.error(f"❌ PIPELINE HALTED: Sync query execution failed: {e}")
            raise Exception(f"Error: Database query failed. {e}")

        if data_df is None or data_df.empty:
            logger.error(f"❌ PIPELINE HALTED: Query execution returned no data.")
            raise Exception("Error: Query returned no data.")

        logger.info(f"✅ STAGE 2 COMPLETE. Data fetched successfully. Shape: {data_df.shape}")

        # === KICKOFF STAGE 3: LangGraph ===
        self.update_state(state='PROGRESS', meta={'status': 'STAGE 3: Analyzing Data...'})
        logger.info(f"🚀 STAGE 3: RUNNING DATA ANALYSIS GRAPH...")
        analysis_app = get_analysis_app()

        initial_state = {"dataframe": data_df, "user_request": user_request}
        
        # [MODIFICATION] We must use the *synchronous* (blocking) 'invoke'
        # 'ainvoke' cannot be used in a sync Celery task.
        final_state = analysis_app.invoke(initial_state)

        if final_state and final_state.get("analysis_report"):
            logger.info("✅ STAGE 3 COMPLETE. Analysis report generated.")
            
            # This is the final, successful return value
            return final_state["analysis_report"]
        else:
            logger.error("❌ PIPELINE HALTED: LangGraph failed to generate a report.")
            raise Exception("Error: Analysis graph failed to produce a report.")
            
    except Exception as e:
        # If any step fails, update the task state to FAILURE
        self.update_state(state='FAILURE', meta={'status': str(e)})
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        # Re-raise the exception so Celery knows it failed
        raise e

# Note: The __name__ == "__main__" block is no longer needed here,
# as the task will only be run by a Celery worker.

