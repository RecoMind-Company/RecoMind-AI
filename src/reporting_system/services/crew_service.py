"""CrewAI orchestration service for data collection and SQL generation."""

import logging
from typing import Optional, Dict, Any, Tuple
from crewai import Crew, Process

from agents.definitions import create_all_agents
from config.database import get_crew_llm, get_vector_db_params
from exceptions import CrewExecutionError, MetadataNotFoundError
from repositories.metadata_db import MetadataRepository
from tasks.definitions import create_all_tasks
from tools.schema_tool import GetTableSchemaTool
from tools.sql_executor_tool import ExecuteSQLQueryTool
from tools.vector_search_tool import VectorDBTableSearchTool

logger = logging.getLogger(__name__)


class CrewService:
    """Service for configuring and executing CrewAI data collection crews."""

    def __init__(self, company_id: str, team_name: Optional[str] = None):
        """
        Initializes CrewService for a given company and optional team context.
        
        Args:
            company_id: Client company identifier.
            team_name: Optional team filter for RBAC/table scope.
        """
        self.company_id = company_id
        self.team_name = team_name
        self.llm = get_crew_llm()

    def create_crew(self) -> Tuple[Crew, Dict[str, str]]:
        """
        Fetches metadata settings, configures tools and agents, and constructs the Crew instance.
        
        Returns:
            Tuple of (Crew instance, source_db_settings dict)
        """
        if not self.company_id:
            raise ValueError("company_id cannot be empty.")

        source_db_settings = MetadataRepository.get_source_db_settings(self.company_id)
        if not source_db_settings:
            logger.error(f"Source DB settings not found for company_id: {self.company_id}")
            raise MetadataNotFoundError(f"Could not find source database settings for company '{self.company_id}'.")

        vector_db_params = get_vector_db_params()

        tool_params = {
            "db_server": source_db_settings["db_server"],
            "db_database": source_db_settings["db_database"],
            "db_username": source_db_settings["db_username"],
            "db_password": source_db_settings["db_password"],
            "vector_db_host": vector_db_params["host"],
            "vector_db_name": vector_db_params["database"],
            "vector_db_user": vector_db_params["user"],
            "vector_db_password": vector_db_params["password"],
            "vector_db_port": vector_db_params["port"],
            "company_id": self.company_id,
            "team_name": self.team_name,
        }

        agents = create_all_agents()
        agents[0].tools = [VectorDBTableSearchTool(**tool_params)]
        agents[2].tools = [GetTableSchemaTool(**tool_params)]
        agents[4].tools = [ExecuteSQLQueryTool(**tool_params)]

        for agent in agents:
            agent.llm = self.llm

        tasks = create_all_tasks(agents)

        crew = Crew(
            agents=agents,
            tasks=tasks,
            verbose=True,
            process=Process.sequential,
            llm=self.llm,
        )

        return crew, source_db_settings

    def run(self, user_request: str) -> Tuple[str, Dict[str, str]]:
        """
        Executes the CrewAI workflow to generate a SQL query string based on user request.
        
        Args:
            user_request: Natural language request from the user.
            
        Returns:
            Tuple of (generated SQL query string, source_db_settings dict)
        """
        logger.info(f"Running CrewAI data collection for company: {self.company_id}, team: {self.team_name}")
        crew, source_db_settings = self.create_crew()

        sql_query_result = crew.kickoff(inputs={"user_request": user_request})
        query_str = str(sql_query_result).strip()

        if not query_str or "ERROR:" in query_str.upper():
            logger.error(f"CrewAI failed to generate a valid SQL query: {query_str}")
            raise CrewExecutionError(f"Failed to generate SQL query from user request: '{user_request}'")

        logger.info("CrewAI data collection stage completed successfully.")
        return query_str, source_db_settings
