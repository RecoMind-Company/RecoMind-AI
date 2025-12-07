# tasks/__init__.py
"""Tasks package."""

from tasks.schemas import (
    IntentOutput,
    TableSelectionOutput,
    SchemaOutput,
    SQLQueryOutput,
    SQLResultOutput,
    FinalAnswerOutput,
)
from tasks.definitions import (
    create_intent_understanding_task,
    create_table_selection_task,
    create_schema_fetcher_task,
    create_sql_generation_task,
    create_sql_execution_task,
    create_answer_formatting_task,
    create_all_tasks,
)

__all__ = [
    # Schemas
    'IntentOutput',
    'TableSelectionOutput',
    'SchemaOutput',
    'SQLQueryOutput',
    'SQLResultOutput',
    'FinalAnswerOutput',
    # Task factories
    'create_intent_understanding_task',
    'create_table_selection_task',
    'create_schema_fetcher_task',
    'create_sql_generation_task',
    'create_sql_execution_task',
    'create_answer_formatting_task',
    'create_all_tasks',
]
