"""Database and LLM factory utilities."""

from typing import Dict, Any
from crewai.llm import LLM
from langchain_openai import ChatOpenAI
from config.settings import (
    CREWAI_LLM_MODEL,
    LANGGRAPH_LLM_MODEL,
    BASE_URL,
    OPENROUTER_API_KEY,
    VECTOR_DB_HOST,
    VECTOR_DB_NAME,
    VECTOR_DB_USER,
    VECTOR_DB_PASSWORD,
    VECTOR_DB_PORT,
)


def get_crew_llm() -> LLM:
    """Creates and configures the CrewAI-compatible LLM instance."""
    return LLM(
        model=CREWAI_LLM_MODEL,
        base_url=BASE_URL,
        api_key=OPENROUTER_API_KEY,
        temperature=0.0,
        max_retries=10,
        max_tokens=4096,
    )


def get_langgraph_llm() -> ChatOpenAI:
    """Creates and configures the LangChain/LangGraph-compatible ChatOpenAI instance."""
    return ChatOpenAI(
        model=LANGGRAPH_LLM_MODEL,
        base_url=BASE_URL,
        api_key=OPENROUTER_API_KEY,
        max_retries=10,
        max_tokens=4096,
        timeout=120,
    )


def get_vector_db_params() -> Dict[str, Any]:
    """Returns PostgreSQL connection parameters dictionary for psycopg2."""
    return {
        "host": VECTOR_DB_HOST,
        "database": VECTOR_DB_NAME,
        "user": VECTOR_DB_USER,
        "password": VECTOR_DB_PASSWORD,
        "port": VECTOR_DB_PORT,
    }
