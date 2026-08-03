"""Base tool definition holding parameterized database credentials for CrewAI tools."""

from typing import Dict, Any, Optional
from crewai.tools import BaseTool
from pydantic import Field


class BaseSQLTool(BaseTool):
    """Base class for SQL Server and Vector DB parameterized tools."""

    # SQL Server connection parameters
    db_server: str = Field(description="SQL Server host name.")
    db_database: str = Field(description="SQL Server database name.")
    db_username: str = Field(description="SQL Server user name.")
    db_password: str = Field(description="SQL Server password.")

    # Vector DB connection parameters
    vector_db_host: str = Field(description="PostgreSQL Vector DB host.")
    vector_db_name: str = Field(description="PostgreSQL Vector DB name.")
    vector_db_user: str = Field(description="PostgreSQL Vector DB user.")
    vector_db_password: str = Field(description="PostgreSQL Vector DB password.")
    vector_db_port: int = Field(default=5432, description="PostgreSQL Vector DB port.")
    
    company_id: str = Field(description="The unique ID of the client company.")
    team_name: Optional[str] = Field(default=None, description="Optional team name for filtering (e.g. 'Sales').")

    def get_sql_conn_string(self) -> str:
        """Returns ODBC connection string for MS SQL Server."""
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.db_server},1433;"
            f"DATABASE={self.db_database};"
            f"UID={self.db_username};"
            f"PWD={self.db_password};"
            f"LoginTimeout=30"
        )

    def get_vector_db_conn_params(self) -> Dict[str, Any]:
        """Returns connection parameters for PostgreSQL vector database."""
        return {
            "host": self.vector_db_host,
            "database": self.vector_db_name,
            "user": self.vector_db_user,
            "password": self.vector_db_password,
            "port": self.vector_db_port,
        }
