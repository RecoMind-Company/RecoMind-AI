from crewai import Task
from typing import Any, List

# Import your agents (only 6 agents)
from .answering_agents import (
    intent_understanding_agent, 
    access_control_filter_agent, 
    table_column_detection_agent,
    sql_generator_agent,
    sql_execution_agent,
    final_answer_agent
)

# ================================================================
# --- 1. Intent Extraction Task (JSON 1)
#     Detect user intent and convert it into a structured JSON.
# ================================================================

def get_intent_task(user_query: str) -> Task:
    return Task(
        description=(
            f"Analyze the following user query: '{user_query}'. "
            "Extract operation, metric_word, and filtering conditions. "
            "Return ONLY a single JSON object following the STRICT RULES."
        ),
        expected_output=(
            "{'operation': 'SUM|COUNT|AVG|SHOW', "
            "'metric_word': 'str', "
            "'conditions': {key: value}}"
        ),
        agent=intent_understanding_agent,
        human_input=False
    )


# ================================================================
# --- 2. RBAC Filtering Task (JSON 2)
#     Determine which tables this team is allowed to access.
# ================================================================

def get_rbac_task(company_id: int, team_name: str, user_query: str) -> Task:
    return Task(
        description=(
            f"Execute GetAllowedTablesTool with Company ID={company_id}, Team='{team_name}'. "
            "Return ONLY the tool's JSON output 'allowed_tables'."
        ),
        expected_output="{ 'allowed_tables': ['table1', 'table2', ...] }",
        agent=access_control_filter_agent,
        context=[
            get_intent_task(user_query)
        ],
        human_input=False
    )


# ================================================================
# --- 3. Schema/Table Detection Task (JSON 3)
#     Detect the correct table + column(s) using intent + RBAC output.
# ================================================================

def get_schema_mapping_task(company_id: int, team_name: str, user_query: str) -> Task:
    return Task(
        description=(
            "Use JSON 1 (intent) and JSON 2 (allowed tables). "
            "1) Run VectorDBTableSearchTool to detect best table. "
            "2) Run GetAvailableColumnsTool for schema. "
            "3) Return JSON 3: table_name, selected_column, group_by_column."
        ),
        expected_output=(
            "{ 'table_name': 'str', "
            "'selected_column': 'str', "
            "'group_by_column': 'str|null' }"
        ),
        agent=table_column_detection_agent,
        context=[
            get_intent_task(user_query),
            get_rbac_task(company_id, team_name, user_query)
        ],
        human_input=False
    )


# ================================================================
# --- 4. SQL Generation Task
#     Generate the final SQL SELECT statement from JSON 1 + JSON 3.
# ================================================================

def get_sql_generation_task(company_id: int, team_name: str, user_query: str) -> Task:
    return Task(
        description=(
            "Compile SQL using JSON 1 (intent) and JSON 3 (schema mapping). "
            "Return ONLY the raw SQL SELECT query."
        ),
        expected_output="SELECT ...",
        agent=sql_generator_agent,
        context=[
            get_intent_task(user_query),
            get_schema_mapping_task(company_id, team_name, user_query)
        ],
        human_input=False
    )


# ================================================================
# --- 5. SQL Execution Task
#     Validate SQL for security and execute it using the ExecuteSQLQueryTool.
# ================================================================

def get_sql_execution_task(company_id: int, team_name: str, user_query: str) -> Task:
    return Task(
        description=(
            "Validate SQL for security. "
            "Execute it using ExecuteSQLQueryTool. "
            "Return Markdown table or error JSON."
        ),
        expected_output="Markdown table OR error JSON.",
        agent=sql_execution_agent,
        context=[
            get_sql_generation_task(company_id, team_name, user_query)
        ],
        human_input=False
    )


# ================================================================
# --- 6. Final Answer Generation Task
#     Convert the SQL result into a friendly natural-language answer.
# ================================================================

def get_final_answer_task(company_id: int, team_name: str, user_query: str) -> Task:
    return Task(
        description=(
            "Interpret the SQL result and convert it into a natural language "
            f"answer for the user query: '{user_query}'. "
            "Do NOT include any backend or technical details."
        ),
        expected_output="A friendly natural language answer.",
        agent=final_answer_agent,
        context=[
            get_sql_execution_task(company_id, team_name, user_query)
        ],
        human_input=False
    )
