from crewai import Task
### START MODIFICATION ###
# Import the new and renamed agents
from .agents import (
    retrieval_agent, 
    table_analyzer_agent, 
    data_analyst_agent, 
    query_generator_agent, 
    query_reviewer_agent,
    query_orchestrator_agent # <-- Import the new manager agent
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
        "Your final output must be a new JSON object string that includes the columns you selected, the original 'key_info', AND the raw schema string you retrieved."
    ),
    expected_output=(
        "A single, valid JSON object string. The JSON object must have three keys: "
        "'selected_columns' (a list of fully qualified column name strings), "
        "'key_info' (the original, unmodified 'key_info' object from the input), and "
        "'full_schema_string' (the raw text string returned by the 'get_table_schema' tool)."
    ),
    agent=data_analyst_agent,
    context=[task_analyze_tables] # Depends on the output of the second task
)

# --- MANAGER TASK ---
# This task replaces the old Task 4 and Task 5 in the main sequential flow.
task_orchestrate_query_generation = Task(
    description=(
        "Oversee the query generation and review process.\n"
        "You will receive the JSON string from the 'Data Analyst and Schema Validator' containing 'selected_columns', 'key_info', 'full_schema_string' and the original '{user_request}'.\n"
        "Your job is to manage the loop between the 'Fact-Based SQL Query Generator' and the 'SQL Query Reviewer' agents until a correct query is produced.\n"
        "1. Delegate generation to 'Fact-Based SQL Query Generator' with all context.\n"
        "2. Delegate review to 'SQL Query Reviewer'.\n"
        "3. If error is found, loop back to step 1, providing the error as 'correction_feedback'."
    ),
    expected_output="The final, 100% validated SQL Server SELECT query string.",
    agent=query_orchestrator_agent,
    context=[task_analyze_schema] # This task starts AFTER the schema is analyzed
)


# --- WORKER TASKS (NO LONGER IN MAIN FLOW) ---
# These tasks are now called by the orchestrator agent, so they don't need 'context'.

# TASK 4: Generate the query using the definitive key_info and user context.
task_generate_query = Task(
    description=(
        "You will receive a JSON string from the manager containing 'selected_columns', 'key_info', 'full_schema_string', and the original '{user_request}'.\n"
        "You might also receive 'correction_feedback' from a reviewer. If you do, YOU MUST FIX your query based on this feedback.\n"
        "Your MANDATORY process is:\n"
        "1.  **Analyze Schema:** Read the 'full_schema_string' to understand all available columns for the tables in 'key_info'.\n"
        "2.  **Construct the base query:** Use 'selected_columns' for the SELECT statement. Use the 'key_info' object as the **absolute and ONLY source of truth** for constructing all JOIN ON clauses. "
        "    **Cross-reference** your join columns with the 'full_schema_string' to ensure they exist. Do not guess any join conditions.\n"
        "3.  **Enhance with user logic:** Based on the '{user_request}', add the necessary clauses:\n"
        "    - If the user asks for filtering (e.g., 'for a specific year', 'only certain products'), add a `WHERE` clause.\n"
        "    - If the user asks for calculations (e.g., 'total amount', 'count of users'), add aggregate functions (`SUM`, `COUNT`) and a `GROUP BY` clause.\n"
        "    - If the user asks for sorting (e.g., 'top 5', 'newest first'), add an `ORDER BY` clause.\n"
        "4.  **Apply Final Formatting Rules:**\n"
        "    - Ensure any SQL reserved keywords used as names are escaped with square brackets (e.g., `[Order]`).\n"
        "    - Do NOT include a trailing semicolon (;) at the end.\n\n"
        "**Output:** Return ONLY the final, complete SQL query as a raw string. No markdown, no explanations."
    ),
    expected_output="A single, valid SQL Server SELECT query string that correctly reflects the user's request, including all necessary joins, filters, aggregations, and sorting.",
    agent=query_generator_agent
    # context removed
)

# TASK 5: Review the final query.
task_review_query = Task(
    description=(
        "Critically review and validate the SQL query generated in the previous task. "
        "You will receive context from previous tasks containing the 'full_schema_string'. "
        "**Your primary job is to validate that every single column in the query (SELECT, ON, WHERE) exists in the 'full_schema_string' for its respective table.** "
        "If the query is INCORRECT (e.g., uses a non-existent column like `Sales.SpecialOfferProduct.SalesOrderID`), state the error clearly. "
        "If the query is 100% syntactically correct, return ONLY the validated/corrected SQL query string."
    ),
    expected_output="The final, valid SQL Server SELECT query string, OR an error message starting with 'ERROR:'.",
    agent=query_reviewer_agent
    # context removed
)

### END MODIFICATION ###
