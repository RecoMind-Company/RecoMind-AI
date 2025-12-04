# tools/base.py
"""Base class for all CrewAI tools."""

import os
from pydantic import Field
from crewai.tools import BaseTool
from sqlalchemy import create_engine
from config.database import get_vector_db_url


class BaseSQLTool(BaseTool):
    """Base tool providing database connection helpers."""
    
    # Source DB settings
    db_server: str = Field(default="", description="SQL Server host name")
    db_database: str = Field(default="", description="SQL Server database name")
    db_username: str = Field(default="", description="SQL Server user name")
    db_password: str = Field(default="", description="SQL Server password")

    # Vector DB settings
    vector_db_host: str = Field(default=os.getenv("VECTOR_DB_HOST", ""))
    vector_db_name: str = Field(default=os.getenv("VECTOR_DB_NAME", ""))
    vector_db_user: str = Field(default=os.getenv("VECTOR_DB_USER", ""))
    vector_db_password: str = Field(default=os.getenv("VECTOR_DB_PASSWORD", ""))
    
    # Company context
    company_id: str = Field(default="", description="Company unique identifier")
    metadata_url: str = Field(default_factory=get_vector_db_url)

    def get_vector_db_params(self) -> dict:
        """Get psycopg2 connection parameters for Vector DB."""
        from config.settings import VECTOR_DB_PORT
        return {
            "host": self.vector_db_host,
            "database": self.vector_db_name,
            "user": self.vector_db_user,
            "password": self.vector_db_password,
            "port": VECTOR_DB_PORT
        }

    def get_metadata_engine(self):
        """Get SQLAlchemy engine for metadata database."""
        try:
            return create_engine(self.metadata_url)
        except Exception as e:
            print(f"Cannot connect to Metadata DB: {e}")
            return None
