"""Tasks package for reporting_system CrewAI tasks."""

from tasks.schemas import TableAnalysisOutput, ColumnSelectionOutput
from tasks.definitions import create_all_tasks

__all__ = [
    "TableAnalysisOutput",
    "ColumnSelectionOutput",
    "create_all_tasks",
]
