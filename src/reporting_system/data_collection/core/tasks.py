### START MODIFICATIONS ###
from crewai import Task
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# Import your agents (only 5)
from .agents import (
    retrieval_agent, 
    table_analyzer_agent, 
    schema_retriever_agent,
    column_selector_agent,
    query_generator_agent
)

# ===================================================================
# 1. Pydantic Output Models (No changes)
# ===================================================================

class TableAnalysisOutput(BaseModel):
    selected_tables: List[str] = Field(description="A list of table name strings that are relevant and joinable.")
    key_info: Dict[str, Any] = Field(description="An object mapping each selected table name to its relations JSON object (containing 'pk' and 'fks').")

class ColumnSelectionOutput(BaseModel):
    selected_columns: List[str] = Field(description="A list of fully qualified column name strings (e.g., 'Schema.Table.Column').")
    key_info: Dict[str, Any] = Field(description="The original, unmodified 'key_info' object from the input.")
    full_schema_string: str = Field(description="The raw text string of the schema received from the previous task.")

# ===================================================================
# 2. Task Definitions (Simplified to 5 tasks)
# ===================================================================

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
    expected_output="A single, valid JSON object string with 'selected_tables' and 'key_info' keys.",
    agent=table_analyzer_agent,
    context=[task_retrieve_context],
    output_pydantic=TableAnalysisOutput
)

# TASK 3 (NEW): Retrieve the full schema string.
task_retrieve_schema = Task(
    description=(
        "You will receive a JSON string from the previous task containing 'selected_tables' and 'key_info'. "
        "Your ONLY job is to extract the 'selected_tables' list and call the 'get_table_schema' tool with it. "
        "You must pass on the raw string output from the tool."
    ),
    expected_output="The raw, complete, and unmodified text output (the 'full_schema_string') from the 'get_table_schema' tool.",
    agent=schema_retriever_agent,
    context=[task_analyze_tables] 
)

# TASK 4 (NEW): Select columns and finalize the data plan.
task_select_columns = Task(
    description=(
        "You will receive the raw 'full_schema_string' from the previous task (task 3). "
        "You will ALSO receive the JSON output from task 2, which contains the 'key_info' object. "
        "You also have access to the original '{user_request}'. "
        "Your job is to analyze the 'full_schema_string' and '{user_request}' to select relevant columns. "
        "Your final output must be a new JSON object string that includes the columns you selected, the original 'key_info', AND the raw schema string you received."
    ),
    expected_output="A single, valid JSON object string with 'selected_columns', 'key_info', and 'full_schema_string' keys.",
    agent=column_selector_agent,
    context=[task_retrieve_schema, task_analyze_tables],
    output_pydantic=ColumnSelectionOutput
)

# TASK 5 (MODIFIED): Generate the final query. (*** MODIFIED WITH ESCAPE RULE ***)
task_generate_final_query = Task(
    description=(
        "You will receive a complete JSON string from the 'Column Selector' containing 'selected_columns', 'key_info', and 'full_schema_string'.\n"
        "Your MANDATORY process is:\n"
        "1. Construct a base query using 'selected_columns' for the SELECT statement.\n"
        "2. Use the 'key_info' object as the **absolute and ONLY source of truth** for constructing all join clauses.\n"
        "3. **CRITICAL (USE LEFT JOIN):** You MUST use `LEFT JOIN` for all joins to ensure all data is retrieved.\n"
        "4. **CRITICAL (NO LOGIC):** You are **STRICTLY FORBIDDEN** from using `WHERE`, `ORDER BY`, `GROUP BY`, `WITH`, or any aggregate functions (SUM, COUNT, etc.).\n"
        "5. **CRITICAL (ALIASES):** You MUST check `selected_columns` for duplicate base names (e.g., `soh.SalesOrderID` and `sod.SalesOrderID`) or generic names (e.g., `prod.Name`). You **MUST** create unique `AS` aliases for them (e.g., `soh.SalesOrderID AS HeaderSalesOrderID`, `prod.Name AS ProductName`).\n"
        "6. **CRITICAL (ESCAPE KEYWORDS):** You MUST wrap any SQL reserved keywords (like `Group`, `Order`, `Key`) in square brackets `[]` (e.g., `Sales.SalesTerritory.[Group]`).\n"
        "7. Do NOT include a trailing semicolon (;) at the end."
    ),
    expected_output="**ONLY** the final, raw SQL Server SELECT query string. All columns must have unique aliases and SQL keywords must be escaped with `[]`. NO other text, NO markdown, NO explanations.",
    agent=query_generator_agent,
    context=[task_select_columns]
)
### END MODIFICATIONS ###