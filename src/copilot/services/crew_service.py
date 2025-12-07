# services/crew_service.py
"""CrewAI Crew orchestration service."""

import os
from crewai import Crew, Process
from config.database import get_llm
from utils.date_helpers import get_date_context
from agents.definitions import create_all_agents
from tasks.definitions import create_all_tasks
from tools.rbac_tool import GetAllowedTablesTool
from tools.vector_search_tool import VectorDBTableSearchTool
from tools.schema_tool import GetAvailableColumnsTool, GetMultipleTablesSchemasTool
from services.sql_executor import execute_sql_query


class CrewService:
    """Service for creating and running CrewAI crews."""

    def __init__(
        self,
        company_id: str,
        team_name: str,
        db_server: str,
        db_database: str,
        db_username: str,
        db_password: str,
    ):
        """Initialize service with connection parameters."""
        self.company_id = company_id
        self.team_name = team_name
        self.db_server = db_server
        self.db_database = db_database
        self.db_username = db_username
        self.db_password = db_password
        
        # Initialize LLM
        self.llm = get_llm()
        
        # Initialize tools
        self._init_tools()

    def _init_tools(self):
        """Initialize all CrewAI tools with connection parameters."""
        # Shared tool config
        tool_config = {
            "company_id": self.company_id,
            "db_server": self.db_server,
            "db_database": self.db_database,
            "db_username": self.db_username,
            "db_password": self.db_password,
            "vector_db_host": os.getenv("VECTOR_DB_HOST", ""),
            "vector_db_name": os.getenv("VECTOR_DB_NAME", ""),
            "vector_db_user": os.getenv("VECTOR_DB_USER", ""),
            "vector_db_password": os.getenv("VECTOR_DB_PASSWORD", ""),
        }

        # Create tool instances
        self.rbac_tool = GetAllowedTablesTool(**tool_config)
        self.vector_search_tool = VectorDBTableSearchTool(**tool_config)
        self.schema_tool = GetAvailableColumnsTool(**tool_config)
        self.schema_multi_tool = GetMultipleTablesSchemasTool(**tool_config)

        # Group tools by agent
        self.table_selection_tools = [self.rbac_tool, self.vector_search_tool]
        self.schema_tools = [self.schema_multi_tool, self.schema_tool]

    def create_crew(self, user_question: str) -> Crew:
        """Create a Crew for processing a user question."""
        
        # Get date context
        date_context = get_date_context()
        
        # Create all agents (no SQL tools needed - executing directly)
        agents = create_all_agents(
            llm=self.llm,
            table_selection_tools=self.table_selection_tools,
            schema_tools=self.schema_tools,
        )
        
        # Create all tasks
        tasks = create_all_tasks(
            agents=agents,
            user_question=user_question,
            team_name=self.team_name,
            date_context=date_context,
        )
        
        # Create and return Crew
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

    def run(self, user_question: str) -> str:
        """Run the crew pipeline with direct SQL execution between tasks."""
        from crewai import Task
        from tasks.schemas import FinalAnswerOutput
        
        # Get date context
        date_context = get_date_context()
        
        # Create agents
        agents = create_all_agents(
            llm=self.llm,
            table_selection_tools=self.table_selection_tools,
            schema_tools=self.schema_tools,
        )
        
        # Create tasks
        tasks = create_all_tasks(
            agents=agents,
            user_question=user_question,
            team_name=self.team_name,
            date_context=date_context,
        )
        
        # Run first 4 tasks (Intent -> Table Selection -> Schema -> SQL Generation)
        crew_part1 = Crew(
            agents=agents[:4],  # First 4 agents
            tasks=tasks[:4],    # First 4 tasks
            process=Process.sequential,
            verbose=True,
        )
        
        part1_result = crew_part1.kickoff()
        
        # Extract SQL query from Task 4 output
        if hasattr(part1_result, 'pydantic') and hasattr(part1_result.pydantic, 'sql_query'):
            sql_query = part1_result.pydantic.sql_query
        elif hasattr(part1_result, 'raw'):
            sql_query = part1_result.raw
        else:
            sql_query = str(part1_result)
        
        # Execute SQL directly (no agent involved)
        sql_result = execute_sql_query(
            sql_query=sql_query,
            db_server=self.db_server,
            db_database=self.db_database,
            db_username=self.db_username,
            db_password=self.db_password,
        )
        
        # Create a new standalone Answer Formatting task with SQL results embedded
        answer_task = Task(
            description=f"""
Format the SQL results into a user-friendly response:

Original User Question: "{user_question}"

SQL Query Executed: {sql_query}

Query Results: {sql_result['result'] if sql_result['success'] else f"Error: {sql_result['error']}"}

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
            agent=agents[4],
            output_pydantic=FinalAnswerOutput,
        )
        
        # Run Answer Formatting task (without Pydantic to avoid parsing issues)
        answer_task_simple = Task(
            description=f"""
Format the SQL results into a user-friendly response:

Original User Question: "{user_question}"

SQL Query Executed: {sql_query}

Query Results: {sql_result['result'] if sql_result['success'] else f"Error: {sql_result['error']}"}

CRITICAL RULES:
1. NEVER just say "The result is X"
2. ALWAYS make the response contextual to the user's question
3. Include units, currency symbols, and proper formatting

Examples of GOOD response patterns:
- "You have X items in your system."
- "The total revenue is $X."
- "There are X pending records this month."

Create a helpful, contextual response based on the actual data returned.
Return ONLY the formatted answer text, nothing else.
""",
            expected_output="User-friendly, contextual answer as plain text",
            agent=agents[4],
        )
        
        crew_part2 = Crew(
            agents=[agents[4]],
            tasks=[answer_task_simple],
            process=Process.sequential,
            verbose=True,
        )
        
        final_result = crew_part2.kickoff()
        
        # Extract answer - try multiple approaches
        if hasattr(final_result, 'raw') and final_result.raw:
            return str(final_result.raw).strip()
        elif hasattr(final_result, 'pydantic'):
            return str(final_result.pydantic).strip()
        else:
            return str(final_result).strip()
