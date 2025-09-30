from crewai import Agent
from langchain_openai import ChatOpenAI
import os
from .tools import GetAllTablesTool, GetTableSchemaTool, ExecuteSQLQueryTool

llm_model = ChatOpenAI(
    model="openrouter/z-ai/glm-4.5-air:free",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1"
)

table_selector_agent = Agent(
    role='SQL Table Selector',
    goal='Identify all relevant fully qualified table names (Schema.Table) based on a user request key, focusing on a highly accurate selection.',
    backstory=(
        "You are an expert SQL database analyst. You have no prior knowledge of the database structure. "
        "Your task is to use tools to fetch all table names with their schemas and then select all relevant ones based on the user request. "
        "Your final answer MUST be a comma-separated list of EXACT fully qualified table names ONLY, with no extra text or explanation."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm_model,
    tools=[GetAllTablesTool()]
)

data_analyst_agent = Agent(
    role='Data Analyst and Column Selector',
    goal='Analyze table schemas and identify the most relevant columns for data analysis based on the user request, ensuring no duplicate column names are selected.',
    backstory=(
        "You are an experienced data analyst. Your job is to review the schema of a set of tables and select all columns "
        "that are most useful for analytical purposes. You must eliminate redundant or duplicate column names across the tables "
        "by selecting the column from the primary or most relevant table. Your selection must exclude sensitive data, irrelevant technical IDs, "
        "and primary keys that are not needed for joining or direct analysis. "
        "The final answer must be a comma-separated list of EXACT fully qualified column names (e.g., 'Schema.Table.ColumnA, Schema.Table.ColumnB') with no duplicates."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm_model,
    tools=[GetTableSchemaTool()]
)

query_generator_agent = Agent(
    role='SQL Query Generator',
    goal='Generate a correct SQL query that joins the provided tables and selects the specified columns for analysis, ensuring column aliases are used to prevent duplicates.',
    backstory=(
        "You are a master SQL query writer with no prior knowledge of the database. You receive a list of fully qualified columns "
        "and must generate a query that joins the relevant tables on their primary/foreign keys. "
        "To prevent duplicate column names in the final result, you must use column aliases like 'TableName.ColumnName AS UniqueName' when two or more columns share the same name. "
        "Fetch ALL rows (no limits). The query must be valid SQL syntax, using aliases for tables and columns (e.g., 'SELECT T1.Col1, T2.Col2 FROM Schema.Table1 T1 JOIN Schema.Table2 T2 ON...')."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm_model
)

query_executor_agent = Agent(
    role='SQL Query Executor',
    goal='Execute a given SQL query, save all results to CSV, and return the result or error.',
    backstory=(
        "You are a professional database administrator. You receive a SQL query, execute it, save the full results to a CSV file, "
        "and return the data preview or an error if it fails."
    ),
    verbose=True,
    allow_delegation=False,
    llm=llm_model,
    tools=[ExecuteSQLQueryTool()]
)