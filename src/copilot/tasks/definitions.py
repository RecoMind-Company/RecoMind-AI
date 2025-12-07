# tasks/definitions.py
"""Task factory functions for all CrewAI tasks."""

from crewai import Task, Agent
from tasks.schemas import (
    IntentOutput,
    TableSelectionOutput,
    SchemaOutput,
    SQLQueryOutput,
    FinalAnswerOutput,
)


def create_intent_understanding_task(
    agent: Agent,
    user_question: str,
    date_context: str
) -> Task:
    """Create Task 1: Intent Understanding."""
    return Task(
        description=f"""
Analyze this user question and determine the correct SQL intent:

User Question: "{user_question}"
Date Context: {date_context}

IMPORTANT: Carefully determine if the user wants:
- COUNT (counting rows/items)
- SUM (adding numeric values)
- AVG (averaging values)
- Other aggregation

Return your analysis as structured JSON.
""",
        expected_output="JSON with user_question, sql_intent, query_key, date_context",
        agent=agent,
        output_pydantic=IntentOutput,
    )


def create_table_selection_task(
    agent: Agent,
    team_name: str,
    context: list
) -> Task:
    """Create Task 2: Table Selection."""
    return Task(
        description=f"""
MANDATORY: You MUST use both tools before providing any answer. DO NOT guess or assume table names.

STEP 1 - REQUIRED (execute this tool first):
Call the get_allowed_tables tool with team_name="{team_name}"
This will return the RBAC-permitted tables for this team.

STEP 2 - REQUIRED (execute this tool second):
Call the vector_db_table_search tool with the query_key from the previous task's context.
This will return semantically relevant tables.

STEP 3 - Filter and Return (LIMIT: 2-5 tables):
Only include tables that appear in BOTH the allowed tables (Step 1) AND the relevant tables (Step 2).
If more than 5 tables match, select the TOP 5 MOST RELEVANT ones.
You MUST return between 2 and 5 tables (not more, not less unless fewer than 2 exist).

CRITICAL RULES:
- You MUST execute get_allowed_tables tool - DO NOT skip this step
- You MUST execute vector_db_table_search tool - DO NOT skip this step  
- NEVER guess table names like "Employee" or "Person" without calling the tools first
- If you don't call both tools, your answer is INVALID
- **MAXIMUM 5 tables, MINIMUM 2 tables**

Return the filtered list of 2-5 relevant and allowed table names.
""",
        expected_output="List of 2-5 relevant and allowed table names obtained from tool calls",
        agent=agent,
        context=context,
        output_pydantic=TableSelectionOutput,
    )


def create_schema_fetcher_task(
    agent: Agent,
    context: list
) -> Task:
    """Create Task 3: Schema Fetching."""
    return Task(
        description="""
MANDATORY: You MUST use the get_multiple_tables_schemas tool to fetch ALL tables at ONCE.

STEP 1 - Get the table list:
Extract the list of relevant tables from the previous task's context.

STEP 2 - REQUIRED (execute ONE time for ALL tables):
Call the get_multiple_tables_schemas tool with table_names parameter as a LIST.
Example: {"table_names": ["Sales.Customer", "Person.Person", "Sales.SalesOrderHeader"]}
This will return ALL column definitions in ONE request - MUCH FASTER than calling get_available_columns multiple times.

STEP 3 - Parse and Return:
The tool returns a JSON string. Parse it into a dictionary and return it as-is.
DO NOT wrap it in another JSON string - just return the parsed dictionary.

CRITICAL RULES:
- You MUST call get_multiple_tables_schemas tool ONCE with ALL tables - DO NOT call it multiple times
- NEVER use get_available_columns unless get_multiple_tables_schemas fails
- NEVER guess column names like "EmployeeID", "Name", "Salary" without calling the tool
- NEVER assume what columns exist in a table
- If you respond without calling the tool for each table, your answer is INVALID
- Return the tool output as a DICTIONARY, not as a JSON string

IMPORTANT OUTPUT FORMAT:
Your final answer should be a dictionary like:
{
  "table_schemas": {
    "Sales.Customer": [{"name": "CustomerID", "type": "int"}, ...],
    "Person.Person": [{"name": "BusinessEntityID", "type": "int"}, ...]
  }
}

Return complete schema information for SQL generation.
""",
        expected_output="Dictionary with table_schemas containing column definitions for all relevant tables",
        agent=agent,
        context=context,
        output_pydantic=SchemaOutput,
    )


def create_sql_generation_task(
    agent: Agent,
    context: list
) -> Task:
    """Create Task 4: SQL Generation."""
    return Task(
        description="""
Generate an MS SQL Server query based on:

1. The sql_intent from the Intent Understanding task
2. The table schemas from the Schema Fetcher task

CRITICAL: Follow the sql_intent EXACTLY:
- If it says COUNT → use COUNT()
- If it says SUM → use SUM()
- DO NOT substitute one for another!

Return only the SQL query.
""",
        expected_output="Valid MS SQL Server SELECT query",
        agent=agent,
        context=context,
        output_pydantic=SQLQueryOutput,
    )





def create_answer_formatting_task(
    agent: Agent,
    user_question: str,
    context: list
) -> Task:
    """Create Task 6: Answer Formatting."""
    return Task(
        description=f"""
Format the SQL results into a user-friendly response:

Original User Question: "{user_question}"

CRITICAL RULES:
1. NEVER just say "The result is X"
2. ALWAYS make the response contextual to the user's question
3. Include units, currency symbols, and proper formatting

Examples of GOOD response patterns:
- "You have X items in your system."
- "The total revenue is $X."
- "There are X pending records this month."

Create a helpful, contextual response based on the actual data returned.
""",
        expected_output="User-friendly, contextual answer",
        agent=agent,
        context=context,
        output_pydantic=FinalAnswerOutput,
    )


def create_all_tasks(
    agents: list,
    user_question: str,
    team_name: str,
    date_context: str
) -> list:
    """Create all 5 tasks with proper context chaining (SQL execution done directly in pipeline)."""
    
    # Task 1: Intent Understanding
    task1 = create_intent_understanding_task(
        agent=agents[0],
        user_question=user_question,
        date_context=date_context,
    )
    
    # Task 2: Table Selection (depends on Task 1)
    task2 = create_table_selection_task(
        agent=agents[1],
        team_name=team_name,
        context=[task1],
    )
    
    # Task 3: Schema Fetching (depends on Task 2)
    task3 = create_schema_fetcher_task(
        agent=agents[2],
        context=[task2],
    )
    
    # Task 4: SQL Generation (depends on Tasks 1, 3)
    task4 = create_sql_generation_task(
        agent=agents[3],
        context=[task1, task3],
    )
    
    # Task 5: Answer Formatting (depends on Task 1 and will receive SQL results from direct execution)
    task5 = create_answer_formatting_task(
        agent=agents[4],
        user_question=user_question,
        context=[task1],
    )
    
    return [task1, task2, task3, task4, task5]
