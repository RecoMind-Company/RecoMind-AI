from crewai import Crew, Process
from .agents import table_selector_agent, data_analyst_agent, query_generator_agent, query_executor_agent
from .tasks import task1_select_tables, task2_analyze_schema, task3_generate_query, task4_execute_query

recomind_crew = Crew(
    agents=[table_selector_agent, data_analyst_agent, query_generator_agent, query_executor_agent],
    tasks=[task1_select_tables, task2_analyze_schema, task3_generate_query, task4_execute_query],
    verbose=True,
    process=Process.sequential
)