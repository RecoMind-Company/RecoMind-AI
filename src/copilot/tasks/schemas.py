# tasks/schemas.py
"""Pydantic schemas for task outputs."""

from typing import List
from pydantic import BaseModel, Field


class IntentOutput(BaseModel):
    """Output from Intent Understanding Agent."""
    user_question: str = Field(description="Original user question")
    sql_intent: str = Field(description="Clear SQL intent description")
    query_key: str = Field(description="Key word for vector search")
    date_context: str = Field(default="", description="Date context for relative dates")


class TableSelectionOutput(BaseModel):
    """Output from Table Selection Agent."""
    relevant_tables: List[str] = Field(description="List of relevant table names")


class SchemaOutput(BaseModel):
    """Output from Schema Fetcher Agent."""
    table_schemas: dict = Field(description="Dictionary of table schemas (table_name -> columns)")


class SQLQueryOutput(BaseModel):
    """Output from SQL Generation Agent."""
    sql_query: str = Field(description="Generated SQL query")


class SQLResultOutput(BaseModel):
    """Output from SQL Execution Agent."""
    raw_result: str = Field(description="Raw query result")


class FinalAnswerOutput(BaseModel):
    """Output from Answer Formatting Agent."""
    formatted_answer: str = Field(description="User-friendly formatted answer")
