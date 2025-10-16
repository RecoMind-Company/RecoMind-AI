# # main.py

# import os
# from dotenv import load_dotenv
# from crewai import Crew, Process
# import importlib.util
# import sys
# import time
# from typing import Any

# # Import the new execution module
# from core import db_executor


# # Dynamically construct the path to config.py
# current_dir = os.path.dirname(os.path.abspath(__file__))
# root_dir = os.path.dirname(current_dir)
# ingestion_path = os.path.join(root_dir, 'ingestion', 'config.py')


# # Load config.py dynamically
# spec = importlib.util.spec_from_file_location("config", ingestion_path)
# config = importlib.util.module_from_spec(spec)
# sys.modules["config"] = config
# spec.loader.exec_module(config)


# # Import agent and tool types
# from core.agents import table_selector_agent, data_analyst_agent, query_generator_agent, query_reviewer_agent
# from core.tools import VectorDBTableSearchTool, GetTableSchemaTool
# from core.tasks import task1_select_tables, task2_analyze_schema, task3_generate_query, task4_review_query


# # Load environment variables
# load_dotenv()


# # =========================================================================
# # CREW INITIALIZATION LOGIC (No major change)
# # =========================================================================


# def initialize_crew():
#     """Initializes the CrewAI with parameterized tools based on config."""
    
#     try:
#         COMPANY_ID = int(config.COMPANY_ID)
#     except (TypeError, ValueError):
#         raise ValueError("COMPANY_ID must be set as an integer in the config/environment.")
        
#     base_params = {
#         'db_server': config.DB_SERVER,
#         'db_database': config.DB_DATABASE,
#         'db_username': config.DB_USERNAME,
#         'db_password': config.DB_PASSWORD,
#         'vector_db_host': config.VECTOR_DB_HOST,
#         'vector_db_name': config.VECTOR_DB_NAME,
#         'vector_db_user': config.VECTOR_DB_USER,
#         'vector_db_password': config.VECTOR_DB_PASSWORD,
#         'company_id': COMPANY_ID
#     }


#     vector_search_tool_inst = VectorDBTableSearchTool(**base_params)
#     get_schema_tool_inst = GetTableSchemaTool(**base_params)
    
#     table_selector_agent.tools = [vector_search_tool_inst]
#     data_analyst_agent.tools = [get_schema_tool_inst]
    
#     return Crew(
#         agents=[table_selector_agent, data_analyst_agent, query_generator_agent, query_reviewer_agent],
#         tasks=[task1_select_tables, task2_analyze_schema, task3_generate_query, task4_review_query],
#         verbose=True,
#         process=Process.sequential
#     )


# # =========================================================================
# # MAIN EXECUTION
# # =========================================================================


# if __name__ == "__main__":
#     recomind_crew = initialize_crew()


#     user_request = input("Enter your request (e.g., 'Sales' or 'Employees'): ")
#     print(f"\n🚀 Starting the CrewAI process for: '{user_request}'")
#     print("=" * 80)


#     max_retries = 1 # No more retries logic needed without a robust fallback
#     sql_query = None
#     csv_path = None
    
#     # We rely entirely on the 4 Agents for success
#     try:
        
#         # Kickoff the crew (Crew now returns the FINAL SQL query from the Reviewer Agent)
#         result = recomind_crew.kickoff(inputs={'user_request': user_request})
        
#         # Extract the final, validated SQL query string (output of Task 4)
#         if hasattr(result, 'raw'):
#             sql_query = str(result.raw).strip()
#         else:
#             sql_query = str(result).strip() if result else ""

#         if not sql_query:
#             raise Exception("CrewAI process failed to generate a valid SQL query.")
        
#         print("\n" + "=" * 80)
#         print(f"✅ Final Validated SQL Query Received:\n{sql_query}")
#         print("=" * 80)
        
#         # --- EXECUTION STAGE VIA PYTHON CODE (Moved to db_executor.py) ---
#         csv_path = db_executor.execute_and_save_query(sql_query, config)
#         # --- EXECUTION STAGE VIA PYTHON CODE ---
        
#         print("\n" + "=" * 80)
#         print(f"🎉 Success! Data saved to: {csv_path}")
#         print("=" * 80)
        
#     except Exception as e:
#         print(f"\n❌ Execution or Crew error: {e}")
#         print(f"Last known generated query (if available): {sql_query if sql_query else 'N/A'}")


#     print("\n" + "=" * 80)
#     print("CrewAI Process Finished.")
#     if csv_path:
#         print(f"Output File: {csv_path}")
#     else:
#         print("Final result: Failed to generate a valid output file.")