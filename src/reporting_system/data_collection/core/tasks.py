from crewai import Task
from pydantic import BaseModel, Field
from typing import List, Dict, Any

from .agents import (
    retrieval_agent,
    table_analyzer_agent,
    schema_retriever_agent,
    column_selector_agent,
    query_generator_agent,
)


class TableAnalysisOutput(BaseModel):
    selected_tables: List[str] = Field(description="A list of table name strings that are relevant and joinable.")
    key_info: Dict[str, Any] = Field(description="An object mapping each selected table name to its relations JSON object (containing 'pk' and 'fks').")


class ColumnSelectionOutput(BaseModel):
    selected_columns: List[str] = Field(description="A list of fully qualified column name strings (e.g., 'Schema.Table.Column').")
    key_info: Dict[str, Any] = Field(description="The original, unmodified 'key_info' object from the input.")
    full_schema_string: str = Field(description="The raw text string of the schema received from the previous task.")


def create_tasks(agents: list) -> list[Task]:
    (
        retrieval_agent_instance,
        table_analyzer_agent_instance,
        schema_retriever_agent_instance,
        column_selector_agent_instance,
        query_generator_agent_instance,
    ) = agents

    task_retrieve_context = Task(
        description="Based on the user's full request '{user_request}', execute the 'vector_db_table_search' tool. Your only job is to run the tool and return its raw output.",
        expected_output="The raw, complete, and unmodified text output from the 'vector_db_table_search' tool.",
        agent=retrieval_agent_instance,
        human_input=False,
    )

    task_analyze_tables = Task(
        description=(
            "You will receive a raw text block from a database search tool. This is your only source of information. "
            "Analyze this text to identify a set of tables that are both semantically relevant and form a connected, joinable graph. "
            "Your final output must be a JSON object string containing 'selected_tables' and their corresponding 'key_info'."
        ),
        expected_output="A single, valid JSON object string with 'selected_tables' and 'key_info' keys.",
        agent=table_analyzer_agent_instance,
        context=[task_retrieve_context],
        output_pydantic=TableAnalysisOutput,
    )

    task_retrieve_schema = Task(
        description=(
            "You will receive a JSON string from the previous task containing 'selected_tables' and 'key_info'. "
            "Your ONLY job is to extract the 'selected_tables' list and call the 'get_table_schema' tool with it. "
            "You must pass on the raw string output from the tool."
        ),
        expected_output="The raw, complete, and unmodified text output (the 'full_schema_string') from the 'get_table_schema' tool.",
        agent=schema_retriever_agent_instance,
        context=[task_analyze_tables],
    )

    task_select_columns = Task(
        description=(
            "You will receive the raw 'full_schema_string' from the previous task (task 3). "
            "You will ALSO receive the JSON output from task 2, which contains the 'key_info' object. "
            "You also have access to the original '{user_request}'. "
            "Your job is to analyze the 'full_schema_string' and '{user_request}' to select relevant columns. "
            "Your final output must be a new JSON object string that includes the columns you selected, the original 'key_info', AND the raw schema string you received."
        ),
        expected_output="A single, valid JSON object string with 'selected_columns', 'key_info', and 'full_schema_string' keys.",
        agent=column_selector_agent_instance,
        context=[task_retrieve_schema, task_analyze_tables],
        output_pydantic=ColumnSelectionOutput,
    )

    task_generate_final_query = Task(
        description=(
            "You will receive a complete JSON string from the 'Column Selector' containing 'selected_columns', 'key_info', and 'full_schema_string'.\n"
            "Your MANDATORY process is:\n"
            "1. Construct a base query using 'selected_columns', 'key_info', keeping strict aliases.\n"
            "2. **CRITICAL:** You MUST call the `execute_sql_query` tool passing your generated SQL to test it.\n"
            "3. If the tool returns an error, use the error message and 'full_schema_string' to fix invalid columns/tables, then test again.\n"
            "4. **CRITICAL (USE LEFT JOIN):** You MUST use `LEFT JOIN` for all joins to ensure all data is retrieved.\n"
            "5. **CRITICAL (NO LOGIC):** You are **STRICTLY FORBIDDEN** from using `WHERE`, `ORDER BY`, `GROUP BY`, `WITH`, or any aggregate functions.\n"
            "6. **CRITICAL (TABLE & COLUMN ALIASES):** You MUST assign a unique table alias to EVERY table... \n"
            "7. **CRITICAL (ESCAPE KEYWORDS):** You MUST wrap any SQL reserved keywords in square brackets `[]`.\n"
            "8. Return the final query ONLY when the tool returns 'SUCCESS!'. Do NOT include a trailing semicolon (;)."
        ),
        expected_output="**ONLY** the final, MATHEMATICALLY VALIDATED, raw SQL Server SELECT query string. NO other text, NO markdown.",
        agent=query_generator_agent_instance,
        context=[task_select_columns],
    )

    return [
        task_retrieve_context,
        task_analyze_tables,
        task_retrieve_schema,
        task_select_columns,
        task_generate_final_query,
    ]


# Backward-compatible module-level tasks. Runtime crew creation should use
# create_tasks(fresh_agents) so task context cannot retain old job state.
(
    task_retrieve_context,
    task_analyze_tables,
    task_retrieve_schema,
    task_select_columns,
    task_generate_final_query,
) = create_tasks(
    [
        retrieval_agent,
        table_analyzer_agent,
        schema_retriever_agent,
        column_selector_agent,
        query_generator_agent,
    ]
)
