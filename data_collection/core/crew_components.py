# data_collection/core/crew_components.py

import os
from crewai.llm import LLM
from typing import List, Dict, Any

# Import base agents and tasks that have no configuration yet
from .agents import (
    retrieval_agent, 
    table_analyzer_agent, 
    data_analyst_agent, 
    query_generator_agent, 
    query_reviewer_agent
)
from .tools import VectorDBTableSearchTool, GetTableSchemaTool
from .tasks import (
    task_retrieve_context, 
    task_analyze_tables, 
    task_analyze_schema, 
    task_generate_query, 
    task_review_query
)

def get_llm() -> LLM:
    """Creates and configures the Language Model for the crew."""
    return LLM(
        model="openrouter/mistralai/mistral-7b-instruct:free",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

def get_configured_agents(tool_params: Dict[str, Any], llm: LLM) -> List:
    """
    Configures and returns the list of agents with their tools and LLM.
    """
    # Assign tools to specific agents
    retrieval_agent.tools = [VectorDBTableSearchTool(**tool_params)]
    data_analyst_agent.tools = [GetTableSchemaTool(**tool_params)]

    # Define the full list of agents
    all_agents = [
        retrieval_agent, 
        table_analyzer_agent, 
        data_analyst_agent, 
        query_generator_agent, 
        query_reviewer_agent
    ]
    
    # Assign the same LLM to all agents
    for agent in all_agents:
        agent.llm = llm
        
    return all_agents

def get_tasks() -> List:
    """Returns the list of tasks for the crew."""
    return [
        task_retrieve_context, 
        task_analyze_tables, 
        task_analyze_schema, 
        task_generate_query, 
        task_review_query
    ]