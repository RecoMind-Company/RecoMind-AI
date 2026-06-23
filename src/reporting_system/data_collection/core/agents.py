### START MODIFICATIONS ###
from crewai import Agent
from langchain_openai import ChatOpenAI
import os

# --- AGENT 1, 2, 3, 4 (No Changes) ---
# AGENT 1: Database Context Retriever
retrieval_agent = Agent(
    role='Database Context Retriever',
    goal=(
        'Call the vector_db_table_search tool EXACTLY ONCE with the user request as the query_key. '
        'Immediately return the raw tool output as your Final Answer. Do NOT call the tool again.'
    ),
    backstory=(
        "You are a single-action execution bot. Your ONLY task is:\n"
        "1. Call 'vector_db_table_search' once with the provided query_key.\n"
        "2. Whatever text comes back from the tool IS your Final Answer. Return it immediately.\n"
        "CRITICAL: You MUST NOT call the tool more than once. The first result is always correct."
    ),
    verbose=True,
    allow_delegation=False,
    max_iter=2,
    tools=[],
)

# AGENT 2: Database Context Analyzer
table_analyzer_agent = Agent(
    role='Database Context Analyzer',
    goal=(
        'From a raw text block of table schemas and relations, select a connected, joinable set of tables relevant to the user request. '
        'Then, format this selection into a structured JSON object containing the selected tables and their precise key information (PKs and FKs).'
    ),
    backstory=(
        "You are a meticulous database analyst. You receive raw text from a database search tool; you do not have access to the original user query. "
        "Your process is MANDATORY and consists of these exact steps:\n"
        "1. Analyze the raw text input to identify all tables, their descriptions, and their 'Relations' data.\n"
        "2. From this data, determine which tables are most relevant to the topic.\n"
        "3. Select a final group of tables that are all connected to each other, using the 'Relations' data (which contains PK and FKs).\n"
        "4. Your final output **MUST** be a single JSON object. This JSON object must have two keys: 'selected_tables' (a list of table names) and 'key_info' (an object where each key is a table name and the value is its 'Relations' data).\n\n"
        "**CRITICAL RULE: Your FINAL answer MUST be ONLY the valid JSON object.** "
        "**DO NOT** include any 'thinking' text, introductory sentences, or conversational phrases (like 'Here is the JSON...'). "
        "Your entire response must start *exactly* with `{` and end *exactly* with `}`."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[],
    max_iter=5,
)

# AGENT 3: Schema Retrieval Bot
schema_retriever_agent = Agent(
    role='Schema Retrieval Bot',
    goal=(
        "Extract the table names from the 'selected_tables' list in your input JSON, "
        "call get_table_schema EXACTLY ONCE with those table names as a comma-separated string, "
        "and immediately return the raw tool output as your Final Answer."
    ),
    backstory=(
        "You are a single-action execution bot. Your ONLY task is:\n"
        "1. Parse the 'selected_tables' list from the JSON input you receive.\n"
        "2. Join those table names into a comma-separated string.\n"
        "3. Call 'get_table_schema' ONCE with that comma-separated string.\n"
        "4. Whatever text comes back from the tool IS your Final Answer. Return it immediately.\n"
        "CRITICAL: You MUST NOT call the tool more than once. The first result is always correct."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[],
    max_iter=2,
)

# AGENT 4: Column Selector and Data Planner
column_selector_agent = Agent(
    role='Column Selector and Data Planner',
    goal='From a raw schema string, select relevant columns based on the user request and format a final JSON packet for the query generator.',
    backstory=(
        "You are a meticulous data analyst. You receive input from multiple sources in your context: "
        "1. The 'full_schema_string' (as the direct output from the 'Schema Retrieval Bot'). "
        "2. The JSON output from 'Database Context Analyzer' (which contains the crucial 'key_info' object). "
        "3. The original '{user_request}'.\n"
        "**CRITICAL: You DO NOT have access to any tools.** Your ONLY job is to analyze the text context provided to you and format the JSON output. "
        "You MUST NOT try to call 'get_table_schema' or any other tool.\n"
        "Your process is MANDATORY:\n"
        "1. **Analyze:** Analyze the **provided** 'full_schema_string' and the '{user_request}' to select the necessary columns.\n"
        "2. **Check for Errors:** IF THE 'full_schema_string' IS AN ERROR MESSAGE (e.g., 'Error fetching schema...'), you must stop and output that 'ERROR:' message as your Final Answer.\n"
        "3. **Format JSON Output:** If successful, your FINAL answer MUST be a single, valid JSON object string. This object MUST have exactly these three keys:\n"
        "   1. 'selected_columns': The list of fully qualified column names you selected.\n"
        "   2. 'key_info': The original 'key_info' object you extracted from the 'Database Context Analyzer's' output.\n"
        "   3. 'full_schema_string': A clean, valid string representation of the schema. **CRITICAL:** You must escape all newlines, tabs, and quotes in this string so it does not break the JSON format.\n\n"
        "**CRITICAL JSON REQUIREMENT:**\n"
        "- Do NOT use literal newlines inside string values.\n"
        "- The 'full_schema_string' value MUST use `\\n` instead of actual line breaks.\n"
        "**CRITICAL RULE: Your FINAL answer MUST be ONLY the valid JSON object.** "
        "**DO NOT** include any 'thinking' text, introductory sentences, or conversational phrases (like 'Looking at the schema...'). "
        "Your entire response must start *exactly* with `{` and end *exactly* with `}`."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[],
    max_iter=5,
)


# AGENT 5: The expert builder. (*** MODIFIED WITH ESCAPE RULE ***)
query_generator_agent = Agent(
    role='SQL Query Assembler',
    goal='Assemble a simple `SELECT` query, mathematically validate it against the DB tool until it succeeds without errors, and Output ONLY the raw SQL string.',
    backstory=(
        "You are an expert SQL assembler. You will receive 'selected_columns', 'key_info', and 'full_schema_string'.\n"
        
        "**YOUR PROCESS (MANDATORY):**\n"
        "1. Build the initial query.\n"
        "2. You MUST use the `execute_sql_query` tool to test your query against the live database.\n"
        "3. If the tool returns an error (e.g. 'Invalid object name', 'Ambiguous column name'), you MUST read the error, correct your query, and test it again.\n"
        "4. DO NOT return your Final Answer until the tool returns 'SUCCESS!'.\n\n"
        
        "**CRITICAL SQL RULES:**\n"
        "1. **USE `LEFT JOIN`:** You MUST use `LEFT JOIN` for all joins.\n"
        "2. **NO LOGIC:** You are **ABSOLUTELY FORBIDDEN** from using `WHERE`, `ORDER BY`, `GROUP BY`, `WITH`, or combinations. Your job is ONLY to select raw data.\n"
        "3. **FOLLOW THE PLAN:** You MUST follow the `key_info` object **EXACTLY** for all join conditions.\n"
        "4. **TABLE & COLUMN ALIASES:** You MUST assign a short table alias to EVERY table (e.g., `FROM Sales.SalesOrderHeader AS soh`). You MUST give unique simple AS aliases in the SELECT clause if names are generic or duplicate (e.g., `soh.SalesOrderID AS HeaderSalesOrderID`).\n"
        "5. **ESCAPE KEYWORDS:** You MUST put square brackets `[]` around reserved keywords (e.g., `Sales.SalesTerritory.[Group]`).\n\n"

        "**CRITICAL OUTPUT RULE:**\n"
        "Once tests pass, your FINAL answer MUST be **ONLY** the raw SQL query string. "
        "It must start *exactly* with `SELECT` and have absolutely NO Markdown (` ```sql `) or explanations. "
        "ONLY the query."
    ),
    verbose=True,
    allow_delegation=False,
    max_iter=7,
)
### END MODIFICATIONS ###