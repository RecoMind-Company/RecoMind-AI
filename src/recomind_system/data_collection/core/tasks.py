# core/tasks.py

from crewai import Task
### START MODIFICATION ###
# Import the new and renamed agents
from .agents import (
    retrieval_agent, 
    table_analyzer_agent, 
    data_analyst_agent, 
    query_generator_agent, 
    query_reviewer_agent
)
### END MODIFICATION ###

### START MODIFICATION ###
# The entire task sequence has been rebuilt to force the new workflow.

# TASK 1: Force the tool call.
task_retrieve_context = Task(
    description="Based on the user's full request '{user_request}', execute the 'vector_db_table_search' tool. Your only job is to run the tool and return its raw output.",
    expected_output="The raw, complete, and unmodified text output from the 'vector_db_table_search' tool.",
    agent=retrieval_agent,
    human_input=False
)

# TASK 2: Analyze the tool output and create the first JSON packet.
task_analyze_tables = Task(
    description=(
        "You will receive a raw text block from a database search tool. This is your only source of information. "
        "Analyze this text to identify a set of tables that are both semantically relevant and form a connected, joinable graph. "
        "Your final output must be a JSON object string containing 'selected_tables' and their corresponding 'key_info'."
    ),
    expected_output=(
        "A single, valid JSON object string. The JSON object must have two keys: "
        "'selected_tables' (a list of table name strings) and "
        "'key_info' (an object mapping each selected table name to its relations JSON object containing its 'pk' and 'fks')."
    ),
    agent=table_analyzer_agent,
    context=[task_retrieve_context] # Depends on the output of the first task
)

# TASK 3: Select columns and pass the key_info forward.
task_analyze_schema = Task(
    description=(
        "You will receive a JSON string from the previous task containing 'selected_tables' and 'key_info'. "
        "Analyze the schema for the tables listed in 'selected_tables' using the 'get_table_schema' tool. "
        "Based on the original user's request '{user_request}', select the most relevant columns. "
        "Your final output must be a new JSON object string that includes the columns you selected AND the original 'key_info'."
    ),
    expected_output=(
        "A single, valid JSON object string. The JSON object must have two keys: "
        "'selected_columns' (a list of fully qualified column name strings) and "
        "'key_info' (the original, unmodified 'key_info' object from the input)."
    ),
    agent=data_analyst_agent,
    context=[task_analyze_tables] # Depends on the output of the second task
)

# TASK 4: Generate the query using the definitive key_info.
task_generate_query = Task(
    description=(
        "You will receive a JSON string from the previous task containing 'selected_columns' and 'key_info'. "
        "Your task is to generate a complete and correct SQL Server query. "
        "Use the 'selected_columns' for your SELECT statement. "
        "Use the 'key_info' object as the definitive source for constructing all JOIN ON clauses. You must not guess column names for joins. "
        "Return ONLY the final SQL query as a string."
    ),
    expected_output="A single, valid SQL Server SELECT query string with all necessary joins and filters.",
    agent=query_generator_agent,
    context=[task_analyze_schema] # Depends on the output of the third task
)

# TASK 5: Review the final query.
task_review_query = Task(
    description=(
        "Critically review and validate the SQL query generated in the previous task. "
        "If the query is INCORRECT, state the error clearly. "
        "If the query is 100% syntactically correct, return ONLY the validated/corrected SQL query string."
    ),
    expected_output="The final, valid SQL Server SELECT query string, OR an error message starting with 'ERROR:'.",
    agent=query_reviewer_agent,
    context=[task_generate_query] # Depends on the output of the fourth task
)

### END MODIFICATION ###