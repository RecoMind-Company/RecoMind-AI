import os
from crewai.llm import LLM
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer

from ...shared.config import get_llm

# ... (imports)

# Make sure you only import the 5 agents you are using
from .agents import (
    retrieval_agent, 
    table_analyzer_agent, 
    schema_retriever_agent,
    column_selector_agent,
    query_generator_agent
)
from .tools import VectorDBTableSearchTool, GetTableSchemaTool

# Make sure you only import the 5 tasks you are using
from .tasks import (
    task_retrieve_context, 
    task_analyze_tables, 
    task_retrieve_schema,
    task_select_columns,
    task_generate_final_query #<-- The new final task
)

llm = get_llm()


def get_configured_agents(tool_params: Dict[str, Any], llm) -> List:
    """
    Configures and returns the list of agents with their tools and LLM.
    """
    ### START MODIFICATION ###
    # Assign tools to specific agents
    retrieval_agent.tools = [VectorDBTableSearchTool(**tool_params)]
    schema_retriever_agent.tools = [GetTableSchemaTool(**tool_params)]

    # Define the NEW list of agents (ONLY 5)
    all_agents = [
        retrieval_agent, 
        table_analyzer_agent, 
        schema_retriever_agent,
        column_selector_agent,
        query_generator_agent, 
    ]
    ### END MODIFICATION ###
    
    # Assign the same LLM to all agents
    for agent in all_agents:
        agent.llm = llm
        
    return all_agents

def get_tasks() -> List:
    """Returns the list of tasks for the crew."""
    
    ### START MODIFICATION ###
    # This is the NEW sequential list of tasks (ONLY 5)
    return [
        task_retrieve_context, 
        task_analyze_tables, 
        task_retrieve_schema,
        task_select_columns,
        task_generate_final_query #<-- This is the new step 5
    ]
    ### END MODIFICATION ###

# ... (rest of your file, like the create_crew function)
# Make sure your create_crew function uses process=Process.sequential