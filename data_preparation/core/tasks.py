from crewai import Task
from .agents import table_selector_agent, data_analyst_agent, query_generator_agent, query_executor_agent

task1_select_tables = Task(
    description=(
        "Based on the user's key '{user_request}', use the 'get_all_tables' tool to find all "
        "fully qualified table names that are highly relevant to this key. "
        "Return a comma-separated list of EXACT fully qualified table names ONLY, "
        "with no extra text or explanation."
    ),
    expected_output="A comma-separated string of all relevant fully qualified table names (e.g., 'Sales.SalesOrderHeader, Sales.SalesOrderDetail, Production.Product').",
    agent=table_selector_agent,
    human_input=False
)

task2_analyze_schema = Task(
    description=(
        "For the user's request '{user_request}', first, internally translate this into a brief analytical summary "
        "focusing on specific data needs for analysis (e.g., 'customer performance metrics, profile data, and key relationships'). "
        "Using the selected tables from the previous task, get their schemas using the 'get_table_schema' tool. "
        "Analyze the schemas to select columns relevant to the analytical summary and suitable for analysis "
        "(e.g., numerical, dates, IDs). The final output must be a comma-separated list of fully qualified column names "
        "(e.g., 'Schema.Table.ColumnA, Schema.Table.ColumnB')."
        "This agent will receive the output from the 'get_table_schema' tool and must parse it to select relevant columns."
    ),
    expected_output="A single comma-separated string of fully qualified column names (e.g., 'Sales.SalesOrderHeader.OrderID, Sales.SalesOrderDetail.ProductID').",
    agent=data_analyst_agent,
    context=[task1_select_tables]
)

task3_generate_query = Task(
    description=(
        "Using the selected columns from the previous task, generate a correct SQL query that joins the tables and selects ONLY those columns."
        "Join tables on their primary/foreign keys and fetch ALL rows (no limits). The query must be valid SQL syntax."
    ),
    expected_output="A single valid SQL query (e.g., 'SELECT T1.col1, T2.col2 FROM Schema.Table1 T1 JOIN Schema.Table2 T2 ON...').",
    agent=query_generator_agent,
    context=[task2_analyze_schema]
)

task4_execute_query = Task(
    description=(
        "Take the generated SQL query and execute it using the 'execute_sql_query' tool. "
        "Return the result of the SQL query as a pandas DataFrame."
    ),
    expected_output="The result of the SQL query as a pandas DataFrame.",
    agent=query_executor_agent,
    context=[task3_generate_query]
)