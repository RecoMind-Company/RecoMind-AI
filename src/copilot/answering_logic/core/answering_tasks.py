# answering_tasks.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crewai import Task
from pydantic import BaseModel, Field
from typing import Any, List, Dict, Optional

from core.answering_agents import (
    intent_understanding_agent,
    access_control_filter_agent,
    table_column_detection_agent,
    sql_generator_agent,
    sql_execution_agent,
    final_answer_agent
)


# Pydantic Models
class IntentOutput(BaseModel):
    operation: str = Field(description="SUM | COUNT | AVG | SHOW")
    metric_word: Optional[str] = Field(default=None, description="The metric to analyze")
    group_by: Optional[str] = Field(default=None, description="Field to group results by (e.g., customer, city, product)")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Filtering conditions extracted from the user query")


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


from datetime import datetime, timedelta

def get_date_context() -> str:
    """Generate date context for relative date conversion."""
    today = datetime.now()
    last_month = today.replace(day=1) - timedelta(days=1)
    last_week_end = today - timedelta(days=today.weekday() + 1)
    last_week_start = last_week_end - timedelta(days=6)
    
    return (
        f"Today is {today.strftime('%Y-%m-%d')}. "
        f"Current year: {today.year}. "
        f"Last year: {today.year - 1}. "
        f"Last month: {last_month.month}, year: {last_month.year}. "
        f"Yesterday: {(today - timedelta(days=1)).strftime('%Y-%m-%d')}. "
        f"Last week: {last_week_start.strftime('%Y-%m-%d')} to {last_week_end.strftime('%Y-%m-%d')}."
    )


def create_intent_task(user_query: str) -> Task:
    """Creates intent task with date context."""
    date_context = get_date_context()
    return Task(
        name="intent_task",
        description=(
            f"Analyze this user query: '{user_query}'\n\n"
            f"DATE CONTEXT: {date_context}\n\n"
            "Extract:\n"
            "1) operation (SUM, COUNT, AVG, SHOW)\n"
            "2) metric_word (the thing being measured)\n"
            "3) group_by (if 'per', 'by', 'for each' is mentioned)\n"
            "4) conditions (filters like year, city - convert relative dates!)\n\n"
            "Return ONLY a valid JSON."
        ),
        expected_output="A JSON with keys: operation, metric_word, group_by, conditions.",
        agent=intent_understanding_agent,
        human_input=False,
        output_pydantic=IntentOutput,
    )


# Default task for backward compatibility
task_intent = Task(
    name="intent_task",
    description=(
        "Analyze the user query and extract:\n"
        "1) operation\n"
        "2) metric_word\n"
        "3) group_by\n"
        "4) conditions\n"
        "Return ONLY a valid JSON."
    ),
    expected_output="A JSON with keys: operation, metric_word, group_by, conditions.",
    agent=intent_understanding_agent,
    human_input=False,
    output_pydantic=IntentOutput,
)


def create_rbac_task(company_id: int, team_name: str, task_intent: Task) -> Task:
    """Creates RBAC task with runtime values."""
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


def create_schema_task(task_intent: Task, task_rbac: Task) -> Task:
    """Creates schema detection task."""
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


def create_sql_gen_task(task_intent: Task, task_schema: Task) -> Task:
    """Creates SQL generation task."""
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


def create_sql_exec_task(task_sql_gen: Task) -> Task:
    """Creates SQL execution task."""
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


def create_final_task(task_sql_exec: Task) -> Task:
    """Creates final answer task."""
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
