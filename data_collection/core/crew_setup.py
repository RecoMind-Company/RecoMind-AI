# # data_collection/core/crew_setup.py

# from crewai import Crew, Process
# from .agents import table_selector_agent, data_analyst_agent, query_generator_agent, query_reviewer_agent
# from .tasks import task1_select_tables, task2_analyze_schema, task3_generate_query, task4_review_query

# # --- IMPORT THE CENTRAL LLM ---
# # We import the single llm_model instance from the central config file.
# from auto_analyst.core.config import llm_model


# # --- CREATE THE CREW USING THE CENTRAL LLM ---
# recomind_crew = Crew(
#     agents=[table_selector_agent, data_analyst_agent, query_generator_agent, query_reviewer_agent],
#     tasks=[task1_select_tables, task2_analyze_schema, task3_generate_query, task4_review_query],
#     verbose=True,
#     process=Process.sequential,
#     llm=llm_model  # Pass the centrally defined LLM to the crew
# )