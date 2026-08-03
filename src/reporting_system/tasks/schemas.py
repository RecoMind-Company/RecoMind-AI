"""Pydantic schemas for CrewAI task outputs."""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class TableAnalysisOutput(BaseModel):
    """Output schema for table analyzer task."""

    selected_tables: List[str] = Field(description="A list of table name strings that are relevant and joinable.")
    key_info: Dict[str, Any] = Field(description="An object mapping each selected table name to its relations JSON object (containing 'pk' and 'fks').")


class ColumnSelectionOutput(BaseModel):
    """Output schema for column selection task."""

    selected_columns: List[str] = Field(description="A list of fully qualified column name strings (e.g., 'Schema.Table.Column').")
    key_info: Dict[str, Any] = Field(description="The original, unmodified 'key_info' object from the input.")
    full_schema_string: str = Field(description="The raw text string of the schema received from the previous task.")
