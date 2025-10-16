# main.py

import os
import sys
import importlib.util
from dotenv import load_dotenv

# --- Step 1: Set up environment variables ---
load_dotenv()

# --- Step 2: Import libraries AFTER setting the environment ---
from langchain_openai import ChatOpenAI
from data_collection.core import db_executor
from crewai import Crew, Process
from crewai.llm import LLM
from auto_analyst.graph.workflow import get_analysis_app # This import is for Stage 3

### START MODIFICATION ###
# Import the new 5-agent and 5-task structure
from data_collection.core.agents import (
    retrieval_agent, 
    table_analyzer_agent, 
    data_analyst_agent, 
    query_generator_agent, 
    query_reviewer_agent
)
from data_collection.core.tools import VectorDBTableSearchTool, GetTableSchemaTool
from data_collection.core.tasks import (
    task_retrieve_context, 
    task_analyze_tables, 
    task_analyze_schema, 
    task_generate_query, 
    task_review_query
)
### END MODIFICATION ###

# Load database config (No changes here)
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    ingestion_path = os.path.join(current_dir, 'data_embedding', 'config.py')
    spec = importlib.util.spec_from_file_location("config", ingestion_path)
    config = importlib.util.module_from_spec(spec)
    sys.modules["config"] = config
    spec.loader.exec_module(config)
except FileNotFoundError:
    print("❌ CONFIGURATION ERROR: 'data_embedding/config.py' was not found.")
    sys.exit(1)

### START MODIFICATION ###
# The initialize_crew function is updated with the new 5-agent structure
def initialize_crew():
    """Initializes the CrewAI with the new 5-agent LLM and tool structure."""

    CREWAI_LLM_MODEL = "openrouter/mistralai/mistral-7b-instruct:free" 

    llm_model = LLM(
        model=CREWAI_LLM_MODEL,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    COMPANY_ID = int(config.COMPANY_ID)
    base_params = {
        'db_server': config.DB_SERVER, 'db_database': config.DB_DATABASE, 'db_username': config.DB_USERNAME,
        'db_password': config.DB_PASSWORD, 'vector_db_host': config.VECTOR_DB_HOST, 'vector_db_name': config.VECTOR_DB_NAME,
        'vector_db_user': config.VECTOR_DB_USER, 'vector_db_password': config.VECTOR_DB_PASSWORD, 'company_id': COMPANY_ID
    }

    # --- Tool Assignment ---
    # Assign the search tool to the new, dedicated retrieval_agent
    retrieval_agent.tools = [VectorDBTableSearchTool(**base_params)]
    # The data_analyst_agent still needs its schema tool
    data_analyst_agent.tools = [GetTableSchemaTool(**base_params)]

    # --- LLM Assignment ---
    # Define the new, full list of 5 agents
    all_agents = [
        retrieval_agent, 
        table_analyzer_agent, 
        data_analyst_agent, 
        query_generator_agent, 
        query_reviewer_agent
    ]
    for agent in all_agents:
        agent.llm = llm_model

    # --- Crew Assembly ---
    # Define the new, full list of 5 tasks in the correct order
    all_tasks = [
        task_retrieve_context, 
        task_analyze_tables, 
        task_analyze_schema, 
        task_generate_query, 
        task_review_query
    ]
    
    return Crew(
        agents=all_agents,
        tasks=all_tasks,
        verbose=True, 
        process=Process.sequential,
        llm=llm_model
    )
### END MODIFICATION ###


# This is the full, correct version of the function including Stage 3
def run_full_pipeline():
    """
    Orchestrates the entire process:
    1. Runs CrewAI to generate a SQL query.
    2. Executes the query to get a DataFrame.
    3. Runs LangGraph to analyze the DataFrame and generate a report.
    """
    # === KICKOFF STAGE 1: CrewAI ===
    recomind_crew = initialize_crew()
    user_request = input("Enter your data request (e.g., 'Sales overview' or 'Active Employees'): ")
    print(f"\n🚀 STAGE 1: RUNNING DATA COLLECTION CREW FOR: '{user_request}'")
    print("=" * 80)
    
    sql_query = recomind_crew.kickoff(inputs={'user_request': user_request})
    
    if not sql_query or "ERROR:" in str(sql_query):
        print(f"\n❌ PIPELINE HALTED: CrewAI failed to generate a valid SQL query.")
        print(f"   Final Crew Output: {sql_query}")
        return

    print(f"\n✅ STAGE 1 COMPLETE. Final SQL Query:\n{sql_query}")
    print("=" * 80)

    # === EXECUTE QUERY ===
    print(f"\n🚀 STAGE 2: EXECUTING QUERY TO FETCH DATA...")
    data_df = db_executor.execute_query_to_dataframe(sql_query, config)

    if data_df is None or data_df.empty:
        print("\n❌ PIPELINE HALTED: Query execution failed or returned no data.")
        return

    print(f"✅ STAGE 2 COMPLETE. Data fetched successfully. Shape: {data_df.shape}")
    print("=" * 80)

    ### THIS IS THE RESTORED STAGE 3 ###
    # === KICKOFF STAGE 3: LangGraph ===
    print(f"\n🚀 STAGE 3: RUNNING DATA ANALYSIS GRAPH...")
    analysis_app = get_analysis_app()
    
    # We now pass the fetched DataFrame directly into the initial state.
    initial_state = {
        "dataframe": data_df,
        "data_type": None, 
        "cleaning_plan": None, 
        "kpi_plan": None, 
        "kpis": None, 
        "analysis_report": None
    }
    
    # You might need to adjust how you handle the output of the graph invocation
    # For now, we just invoke it.
    final_state = analysis_app.invoke(initial_state)
    
    # You can print the final report from the state if it exists
    if final_state and final_state.get("analysis_report"):
        print("\n--- FINAL ANALYSIS REPORT ---")
        print(final_state["analysis_report"])
    
    print("\n🎉 FULL PIPELINE FINISHED SUCCESSFULLY!")
    print("Check the 'final_output' directory for the report and cleaned data if your graph saves them.")
    print("=" * 80)

if __name__ == "__main__":
    run_full_pipeline()