import psycopg2
from crewai import Crew, Process

# Second: Now we can safely import the config module. The API will not be called.
from ...shared import config

# Import the component builders
from .crew_components import llm, get_configured_agents, get_tasks


def get_source_db_settings_from_postgres(company_id: str) -> dict:
    """
    Connects to the PostgreSQL database to fetch the Source DB connection details
    using the provided company_id.
    """
    conn = None
    try:
        # Use the Vector DB connection details from the config file to connect.
        conn = psycopg2.connect(
            host=config.VECTOR_DB_HOST,
            dbname=config.VECTOR_DB_NAME,
            user=config.VECTOR_DB_USER,
            password=config.VECTOR_DB_PASSWORD
        )
        cur = conn.cursor()
        # Fetch the most recent connection details for the given company_id
        query = "SELECT server, database, username, password FROM source_connections WHERE company_id = %s ORDER BY created_at DESC LIMIT 1;"
        cur.execute(query, (company_id,))
        record = cur.fetchone()

        if record:
            print(f"✔ Successfully fetched source connection settings for Company ID: {company_id} from the database.")
            return {'db_server': record[0], 'db_database': record[1], 'db_username': record[2], 'db_password': record[3]}
        else:
            return None
    except (Exception, psycopg2.Error) as error:
        print(f"✖ Error fetching settings from PostgreSQL: {error}")
        return None
    finally:
        if conn:
            cur.close()
            conn.close()


def create_crew(company_id: str) -> Crew:
    """
    Assembles the CrewAI crew, dynamically fetching Source DB settings from the database.
    This function now takes company_id as a parameter instead of prompting the user.
    """
    # 1. Validate the provided Company ID
    if not company_id:
        print("✖ Company ID cannot be empty. Exiting.")
        return None, None

    # 2. Fetch the SOURCE DB settings from the database
    source_db_settings = get_source_db_settings_from_postgres(company_id)
    
    if not source_db_settings:
        print(f"✖ Could not find settings for Company ID '{company_id}'.")
        return None, None

    # 4. Prepare the parameters needed for the tools
    tool_params = {
        # Source DB details are from the new function (not from config)
        'db_server': source_db_settings['db_server'],
        'db_database': source_db_settings['db_database'],
        'db_username': source_db_settings['db_username'],
        'db_password': source_db_settings['db_password'],
        
        # Vector DB details are from the config file directly (as requested)
        'vector_db_host': config.VECTOR_DB_HOST,
        'vector_db_name': config.VECTOR_DB_NAME,
        'vector_db_user': config.VECTOR_DB_USER,
        'vector_db_password': config.VECTOR_DB_PASSWORD,
        'company_id': company_id
    }

    # 5. Get the agents and tasks
    agents = get_configured_agents(tool_params, llm)
    tasks = get_tasks()

    # 6. Assemble and return the final Crew
    final_crew = Crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        process=Process.sequential, 
        llm=llm 
    )
    
    return final_crew, source_db_settings

