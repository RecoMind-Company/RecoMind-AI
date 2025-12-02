# answering_context_builder.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from crewai import Crew, Process
from typing import Dict, Any, Tuple
from shared.config import get_vector_db_url, get_llm
from shared import config
from core.answering_engine import get_configured_agents, get_tasks


def get_source_db_settings_from_postgres(company_id: str) -> Dict[str, str] | None:
    """Retrieves source DB connection details for a specific company."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=config.VECTOR_DB_HOST,
            database=config.VECTOR_DB_NAME,
            user=config.VECTOR_DB_USER,
            password=config.VECTOR_DB_PASSWORD
        )
        cur = conn.cursor()
        
        query = """
            SELECT server, database, username, password 
            FROM source_connections 
            WHERE company_id = %s 
            ORDER BY created_at DESC 
            LIMIT 1;
        """
        
        cur.execute(query, (company_id,))
        record = cur.fetchone()

        if record:
            print("Source DB settings loaded successfully.")
            return {
                "db_server": record[0],
                "db_database": record[1],
                "db_username": record[2],
                "db_password": record[3]
            }
        else:
            print("No DB settings found.")
            return None

    except Exception as err:
        print(f"Error loading source DB settings: {err}")
        return None

    finally:
        if conn:
            cur.close()
            conn.close()


def get_all_company_tables(company_id: str) -> list[str]:
    """Fetches all tables belonging to the company from metadata DB."""
    conn = None
    try:
        conn = psycopg2.connect(
            host=config.VECTOR_DB_HOST,
            database=config.VECTOR_DB_NAME,
            user=config.VECTOR_DB_USER,
            password=config.VECTOR_DB_PASSWORD
        )
        cur = conn.cursor()

        query = """
            SELECT table_name
            FROM rbac_table_metadata
            WHERE company_id = %s;
        """
        
        cur.execute(query, (company_id,))
        rows = cur.fetchall()

        all_tables = [r[0] for r in rows]
        print(f"Loaded {len(all_tables)} tables.")
        return all_tables

    except Exception as e:
        print(f"Error fetching company tables: {e}")
        return []

    finally:
        if conn:
            cur.close()
            conn.close()


def create_crew_and_params(user_query: str, company_id: str, team_name: str) -> Tuple[Crew | None, Dict[str, Any] | None]:
    """Creates and configures the Crew with all agents and tasks."""
    if not company_id or not team_name:
        print("company_id and team_name are required.")
        return None, None

    source_db_settings = get_source_db_settings_from_postgres(company_id)
    if not source_db_settings:
        return None, None

    all_company_tables = get_all_company_tables(company_id)

    tool_params = {
        "db_server": source_db_settings["db_server"],
        "db_database": source_db_settings["db_database"],
        "db_username": source_db_settings["db_username"],
        "db_password": source_db_settings["db_password"],
        "vector_db_host": config.VECTOR_DB_HOST,
        "vector_db_name": config.VECTOR_DB_NAME,
        "vector_db_user": config.VECTOR_DB_USER,
        "vector_db_password": config.VECTOR_DB_PASSWORD,
        "company_id": company_id,
        "team_name": team_name,
        "all_company_tables": all_company_tables,
        "metadata_url": get_vector_db_url()
    }

    llm_instance = get_llm()
    agents = get_configured_agents(tool_params, llm_instance)
    tasks = get_tasks(company_id=company_id, team_name=team_name)

    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
        llm=llm_instance
    )

    return crew, source_db_settings
