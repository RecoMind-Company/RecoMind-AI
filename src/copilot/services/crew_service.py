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
from tools.schema_tool import GetAvailableColumnsTool
from tools.sql_executor_tool import ExecuteSQLQueryTool


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
        self.sql_executor_tool = ExecuteSQLQueryTool(**tool_config)

        # Group tools by agent
        self.table_selection_tools = [self.rbac_tool, self.vector_search_tool]
        self.schema_tools = [self.schema_tool]
        self.sql_tools = [self.sql_executor_tool]

    def create_crew(self, user_question: str) -> Crew:
        """Create a Crew for processing a user question."""
        
        # Get date context
        date_context = get_date_context()
        
        # Create all agents
        agents = create_all_agents(
            llm=self.llm,
            table_selection_tools=self.table_selection_tools,
            schema_tools=self.schema_tools,
            sql_tools=self.sql_tools,
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
        """Run the crew pipeline and return the final answer."""
        crew = self.create_crew(user_question)
        result = crew.kickoff()
        
        # Extract final answer
        if hasattr(result, 'pydantic') and result.pydantic:
            return result.pydantic.formatted_answer
        elif hasattr(result, 'raw'):
            return result.raw
        else:
            return str(result)
