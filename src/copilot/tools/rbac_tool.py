# tools/rbac_tool.py
"""RBAC Tool - fetches allowed tables for a team."""

import json
import traceback
from pydantic import BaseModel, Field
from sqlalchemy import text
from tools.base import BaseSQLTool
from typing import List


class RBACInput(BaseModel):
    """Input schema for RBAC tool."""
    team_name: str = Field(description="The name of the user's team for access control")


class GetAllowedTablesTool(BaseSQLTool):
    """Fetch allowed tables for a user team from Metadata DB."""
    
    name: str = "get_allowed_tables"
    description: str = "Fetch allowed tables for a user team from Metadata DB."
    args_schema: type[BaseModel] = RBACInput
    all_company_tables: List[str] = Field(default_factory=list)

    def _run(self, team_name: str) -> str:
        """Execute the tool."""
        engine = self.get_metadata_engine()
        if engine is None:
            return json.dumps({"error": "Metadata DB not available"})

        try:
            team_name = team_name.strip()
            db_type = engine.url.get_backend_name()

            if db_type == "postgresql":
                query = text("""
                    SELECT table_name
                    FROM client_schema_vectors
                    WHERE company_id = :cid
                    AND team_name @> ARRAY[:team_name]::text[]
                """)
                params = {"cid": self.company_id, "team_name": team_name}
            else:
                query = text("""
                    SELECT table_name
                    FROM client_schema_vectors
                    WHERE company_id = :cid
                    AND REPLACE(team_name,' ','') LIKE :contains
                """)
                params = {"cid": self.company_id, "contains": f"%{team_name}%"}

            with engine.connect() as conn:
                rows = conn.execute(query, params).fetchall()

            return json.dumps({"allowed_tables": [r[0] for r in rows]}, indent=2)

        except Exception as e:
            traceback.print_exc()
            return json.dumps({"error": f"RBAC query failed: {e}"})
