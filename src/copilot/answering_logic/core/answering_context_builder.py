
import psycopg2
from crewai import Crew, Process
from typing import Dict, Any, Tuple

# Import configurations (PostgreSQL credentials for metadata DB)
from shared import config

# Import internal components
from .answering_engine import get_configured_agents
from .answering_tasks import get_final_answer_task
from shared.config import get_llm


# ================================================================
# 1. Fetch Source DB Settings for the Given Company
# ================================================================
def get_source_db_settings_from_postgres(company_id: str) -> Dict[str, str] | None:
    """
    Retrieves source DB connection details for a specific company from the metadata DB.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=config.VECTOR_DB_HOST,
            dbname=config.VECTOR_DB_NAME,
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
            print(f"✔ Source DB settings loaded for Company {company_id}")
            return {
                "db_server": record[0],
                "db_database": record[1],
                "db_username": record[2],
                "db_password": record[3]
            }
        else:
            print(f"✖ No DB settings found for company {company_id}")
            return None

    except Exception as err:
        print(f"✖ Error loading source DB settings: {err}")
        return None

    finally:
        if conn:
            cur.close()
            conn.close()


# ================================================================
# 2. (OPTIONAL) Fetch ALL Company Tables
# ================================================================
def get_all_company_tables(company_id: str) -> list[str]:
    """
    Fetches **all tables belonging to the company** from metadata DB.
    Used by RBAC Agent to perform:
        all tables → allowed tables  → final table
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=config.VECTOR_DB_HOST,
            dbname=config.VECTOR_DB_NAME,
            user=config.VECTOR_DB_USER,
            password=config.VECTOR_DB_PASSWORD
        )
        cur = conn.cursor()

        query = """
            SELECT table_name
            FROM table_registry
            WHERE company_id = %s;
        """
        
        cur.execute(query, (company_id,))
        rows = cur.fetchall()

        all_tables = [r[0] for r in rows]
        print(f"✔ Loaded {len(all_tables)} total tables for company {company_id}")
        return all_tables

    except Exception as e:
        print(f"✖ Error fetching company tables: {e}")
        return []

    finally:
        if conn:
            cur.close()
            conn.close()


# ================================================================
# 3. Crew Factory – Build Agents + Tasks + Params
# ================================================================
def create_crew_and_params(user_query: str, company_id: str, team_name: str) -> Tuple[Crew | None, Dict[str, Any] | None]:

    if not company_id or not team_name:
        print("✖ company_id and team_name are required.")
        return None, None

    # 1️⃣ Fetch Source DB Settings
    source_db_settings = get_source_db_settings_from_postgres(company_id)
    if not source_db_settings:
        return None, None

    # 2️⃣ (Optional but recommended)
    #    Load ALL tables for this company (100 tables)
    all_company_tables = get_all_company_tables(company_id)

    # 3️⃣ Tool Parameters passed to all agents
    tool_params = {
        # Source DB (Agent 5)
        "db_server": source_db_settings["db_server"],
        "db_database": source_db_settings["db_database"],
        "db_username": source_db_settings["db_username"],
        "db_password": source_db_settings["db_password"],

        # Metadata DB (Agent 2 & 3)
        "vector_db_host": config.VECTOR_DB_HOST,
        "vector_db_name": config.VECTOR_DB_NAME,
        "vector_db_user": config.VECTOR_DB_USER,
        "vector_db_password": config.VECTOR_DB_PASSWORD,

        # User Context (RBAC filtering)
        "company_id": company_id,
        "team_name": team_name,

        # For RBAC table filtering logic
        "all_company_tables": all_company_tables
    }

    # 4️⃣ LLM Instance
    llm_instance = get_llm()

    # 5️⃣ Configure Agents
    agents = get_configured_agents(tool_params, llm_instance)

    # 6️⃣ Create Tasks
    tasks = [
        get_final_answer_task(
            company_id=company_id,    
            team_name=team_name,
            user_query=user_query
        )
    ]

    # 7️⃣ Build Crew
    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,
        verbose=2,
        llm=llm_instance
    )

    print(f"✔ Crew is ready for Company {company_id}")
    return crew, tool_params



