# data_collection/core/crew_factory.py

from crewai import Crew, Process

# Import the shared application config using a direct, absolute path
from ....shared import config

# Import the component builders from the sibling components file
from .crew_components import get_llm, get_configured_agents, get_tasks

def create_crew() -> Crew:
    """
    Creates and assembles the CrewAI crew by fetching configured components.
    This function acts as the final assembly line.
    """
    # 1. Get the configured LLM
    llm = get_llm()

    # 2. Prepare the parameters needed for the tools
    tool_params = {
        'db_server': config.DB_SERVER,
        'db_database': config.DB_DATABASE,
        'db_username': config.DB_USERNAME,
        'db_password': config.DB_PASSWORD,
        'vector_db_host': config.VECTOR_DB_HOST,
        'vector_db_name': config.VECTOR_DB_NAME,
        'vector_db_user': config.VECTOR_DB_USER,
        'vector_db_password': config.VECTOR_DB_PASSWORD,
        'company_id': int(config.COMPANY_ID)
    }

    # 3. Get the configured agents and the list of tasks
    agents = get_configured_agents(tool_params, llm)
    tasks = get_tasks()

    # 4. Assemble and return the final Crew object
    return Crew(
        agents=agents,
        tasks=tasks,
        verbose=True,
        process=Process.sequential,
        llm=llm
    )