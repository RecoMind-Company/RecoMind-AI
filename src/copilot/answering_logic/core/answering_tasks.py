# answering_tasks.py
from crewai import Task
from pydantic import BaseModel, Field
from typing import Any, List, Dict , Optional

# ---------------------------------------------------------------
# Import your 6 answering agents
# ---------------------------------------------------------------
from .answering_agents import (
    intent_understanding_agent, 
    access_control_filter_agent,
    table_column_detection_agent,
    sql_generator_agent,
    sql_execution_agent,
    final_answer_agent
)

# ===================================================================
# 1. Pydantic Models (Structured outputs)
# ===================================================================

class IntentOutput(BaseModel):
    operation: str = Field(description="SUM | COUNT | AVG | SHOW")
    metric_word: str = Field(description="The metric to analyze")
    conditions: Dict[str, Any] = Field(description="Filtering conditions extracted from the user query")

class RBACOutput(BaseModel):
    allowed_tables: List[str] = Field(description="Tables the team is allowed to access")

class SchemaMappingOutput(BaseModel):
    table_name: str = Field(description="Selected table most relevant to the query")
    selected_column: str = Field(description="Column used for metric")
    group_by_column: Optional[str] = Field(default=None, description="Optional column used for grouping")

class SQLQueryOutput(BaseModel):
    sql_query: str = Field(description="Final SQL SELECT query")

class SQLResultOutput(BaseModel):
    result: Any = Field(description="Executed SQL result or error JSON")

task_intent = Task(
    name="intent_task",
    description=(
        "Analyze the user query and extract:\n"
        "1) operation\n"
        "2) metric_word\n"
        "3) conditions\n"
        "Return ONLY a valid JSON."
    ),
    expected_output="A JSON with keys: operation, metric_word, conditions.",
    agent=intent_understanding_agent,
    human_input=False,
    output_pydantic=IntentOutput,
)


# -------------------------------------------------
# TASK 2 — RBAC Filtering (ديناميكي)
# -------------------------------------------------
def create_rbac_task(company_id: int, team_name: str, task_intent: Task) -> Task:
    """
    ترجع نسخة من RBAC task بالقيم runtime.
    """
    return Task(
        name="rbac_task",
        description=(
            f"Call GetAllowedTablesTool using company_id={company_id}, team_name='{team_name}'.\n"
            "Return ONLY the allowed tables JSON."
        ),
        expected_output="A JSON object with key: allowed_tables.",
        agent=access_control_filter_agent,
        context=[task_intent],
        human_input=False,
        output_pydantic=RBACOutput,
    )


# -------------------------------------------------
# TASK 3 — Semantic Table + Column Detection
# -------------------------------------------------
def create_schema_task(task_intent: Task, task_rbac: Task) -> Task:
    return Task(
        name="schema_task",
        description=(
            "Using Intent JSON and RBAC JSON:\n"
            "1) Perform semantic table search\n"
            "2) Fetch full schema columns\n"
            "3) Return: table_name, selected_column, group_by_column"
        ),
        expected_output="A JSON object with keys: table_name, selected_column, group_by_column.",
        agent=table_column_detection_agent,
        context=[task_intent, task_rbac],
        human_input=False,
        output_pydantic=SchemaMappingOutput,
        llm_delegate=False
    )


# -------------------------------------------------
# TASK 4 — SQL Generation
# -------------------------------------------------
def create_sql_gen_task(task_intent: Task, task_schema: Task) -> Task:
    return Task(
        name="sql_gen_task",
        description=(
            "Using Intent JSON and Schema Mapping JSON:\n"
            "Generate ONLY the raw SQL SELECT query."
        ),
        expected_output="SQL query string.",
        agent=sql_generator_agent,
        context=[task_intent, task_schema],
        human_input=False,
        output_pydantic=SQLQueryOutput,
    )


# -------------------------------------------------
# TASK 5 — SQL Execution
# -------------------------------------------------
def create_sql_exec_task(task_sql_gen: Task) -> Task:
    return Task(
        name="sql_exec_task",
        description=(
            "Validate SQL is safe, then execute it using ExecuteSQLQueryTool.\n"
            "Return raw DataFrame markdown OR error."
        ),
        expected_output="Markdown table OR error JSON.",
        agent=sql_execution_agent,
        context=[task_sql_gen],
        human_input=False,
        output_pydantic=SQLResultOutput,
    )


# -------------------------------------------------
# TASK 6 — Final User-Friendly Answer
# -------------------------------------------------
def create_final_task(task_sql_exec: Task) -> Task:
    return Task(
        name="final_answer_task",
        description=(
            "Interpret the SQL result and answer the user in natural language.\n"
            "Never reveal SQL or database details."
        ),
        expected_output="Friendly natural language answer.",
        agent=final_answer_agent,
        context=[task_sql_exec],
        human_input=False,
    )
