
from crewai import Crew, Process
from typing import List, Dict, Any
from shared.config import get_llm

# -------------------------------
# Import Agents
# -------------------------------
from .answering_agents import (
    intent_understanding_agent,
    access_control_filter_agent,
    table_column_detection_agent,
    sql_generator_agent,
    sql_execution_agent,
    final_answer_agent
)

# -------------------------------
# Import Tools
# -------------------------------
from .answering_tools import (
    GetAllowedTablesTool,
    VectorDBTableSearchTool,
    GetAvailableColumnsTool,
    ExecuteSQLQueryTool
)

# -------------------------------
# Import the Final Task (which contains the entire task chain in its context)
# -------------------------------
from .answering_tasks import get_final_answer_task

# ================================================================
# 1. Agent Configuration (Tools and LLM Assignment)
# ================================================================

def get_configured_agents(tool_params: Dict[str, Any], llm) -> List:
    """
    Configures all six agents by assigning their required tools and the LLM instance.
    """
    
    # List of all agents in the pipeline
    all_agents = [
        intent_understanding_agent,
        access_control_filter_agent,
        table_column_detection_agent,
        sql_generator_agent,
        sql_execution_agent,
        final_answer_agent
    ]

    # -------------------------------
    # Assign tools to the relevant agents
    # -------------------------------
    # Agent 2: RBAC Filter
    access_control_filter_agent.tools = [GetAllowedTablesTool]
    
    # Agent 3: Schema Mapping
    table_column_detection_agent.tools = [VectorDBTableSearchTool, GetAvailableColumnsTool]
    
    # Agent 5: SQL Executor
    sql_execution_agent.tools = [ExecuteSQLQueryTool]

    # Assign the LLM instance to all agents
    for agent in all_agents:
        agent.llm = llm

    return all_agents

# ================================================================
# 2. Crew Creation Function (The Builder)
# ================================================================

def create_sql_generation_crew(user_query: str, company_id: int, team_name: str, tool_params: Dict[str, Any]) -> Crew:
    """
    Creates the complete CrewAI setup for the Auto-SQL system.
    
    The process is set to sequential to enforce the necessary step-by-step
    data flow (Intent -> RBAC -> Schema -> SQL Gen -> SQL Exec -> Answer).
    """
    
    # 1. Get the configured LLM instance
    llm = get_llm()
    
    # 2. Configure agents with tools and LLM
    agents = get_configured_agents(tool_params, llm)

    # 3. Define Tasks: The final task encapsulates the entire sequential pipeline 
    # through its context dependency chain defined in tasks_answer.py
    tasks = [get_final_answer_task(company_id, team_name, user_query)]

    # 4. Create the Crew
    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.sequential,  
        verbose=2                    
    )

    return crew

