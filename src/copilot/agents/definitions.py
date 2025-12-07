# agents/definitions.py
"""Agent factory functions for all CrewAI agents."""

from crewai import Agent
from crewai.llm import LLM
from agents.prompts import (
    INTENT_UNDERSTANDING_PROMPT,
    TABLE_SELECTION_PROMPT,
    SCHEMA_FETCHER_PROMPT,
    SQL_GENERATION_PROMPT,
    ANSWER_FORMATTING_PROMPT,
)


def create_intent_understanding_agent(llm: LLM) -> Agent:
    """Create Agent 1: Intent Understanding."""
    return Agent(
        role="Intent Understanding Agent",
        goal="Understand user questions semantically and identify correct SQL aggregation intent",
        backstory=INTENT_UNDERSTANDING_PROMPT,
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )


def create_table_selection_agent(llm: LLM, tools: list) -> Agent:
    """Create Agent 2: Table Selection with RBAC + Vector Search."""
    return Agent(
        role="Table Selection Agent",
        goal="Select relevant tables based on RBAC permissions and semantic relevance",
        backstory=TABLE_SELECTION_PROMPT,
        llm=llm,
        tools=tools,
        allow_delegation=False,
        verbose=True,
    )


def create_schema_fetcher_agent(llm: LLM, tools: list) -> Agent:
    """Create Agent 3: Schema Fetcher."""
    return Agent(
        role="Schema Fetcher Agent",
        goal="Fetch column definitions for selected tables",
        backstory=SCHEMA_FETCHER_PROMPT,
        llm=llm,
        tools=tools,
        allow_delegation=False,
        verbose=True,
    )


def create_sql_generation_agent(llm: LLM) -> Agent:
    """Create Agent 4: SQL Generation."""
    return Agent(
        role="SQL Generation Agent",
        goal="Generate accurate MS SQL Server queries following the intent exactly",
        backstory=SQL_GENERATION_PROMPT,
        llm=llm,
        allow_delegation=False,
        verbose=True,
        cache=False,  # Disable caching to allow tool re-execution
    )





def create_answer_formatting_agent(llm: LLM) -> Agent:
    """Create Agent 6: Answer Formatting."""
    return Agent(
        role="Answer Formatting Agent",
        goal="Format query results into user-friendly, contextual responses",
        backstory=ANSWER_FORMATTING_PROMPT,
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )


def create_all_agents(llm: LLM, table_selection_tools: list, schema_tools: list) -> list:
    """Create all 5 agents in sequence (SQL execution done directly, not via agent)."""
    return [
        create_intent_understanding_agent(llm),
        create_table_selection_agent(llm, table_selection_tools),
        create_schema_fetcher_agent(llm, schema_tools),
        create_sql_generation_agent(llm),
        create_answer_formatting_agent(llm),
    ]
