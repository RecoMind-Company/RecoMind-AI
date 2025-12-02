# answering_engine.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any
from shared.config import get_llm

from core.answering_agents import (
    intent_understanding_agent,
    access_control_filter_agent,
    table_column_detection_agent,
    sql_generator_agent,
    sql_execution_agent,
    final_answer_agent
)
from core.answering_tools import (
    GetAllowedTablesTool,
    VectorDBTableSearchTool,
    GetAvailableColumnsTool,
    ExecuteSQLQueryTool
)
from core.answering_tasks import (
    task_intent,
    create_rbac_task,
    create_schema_task,
    create_sql_gen_task,
    create_sql_exec_task,
    create_final_task
)

llm = get_llm()


def get_configured_agents(tool_params: Dict[str, Any], llm) -> List:
    """Configures and returns the list of agents with their tools and LLM."""
    access_control_filter_agent.tools = [GetAllowedTablesTool(**tool_params)]
    table_column_detection_agent.tools = [
        VectorDBTableSearchTool(**tool_params),
        GetAvailableColumnsTool(**tool_params)
    ]
    sql_execution_agent.tools = [ExecuteSQLQueryTool(**tool_params)]

    all_agents = [
        intent_understanding_agent,
        access_control_filter_agent,
        table_column_detection_agent,
        sql_generator_agent,
        sql_execution_agent,
        final_answer_agent
    ]

    for agent in all_agents:
        agent.llm = llm

    return all_agents


def get_tasks(company_id: int, team_name: str) -> List:
    """Returns the sequential list of tasks for the crew."""
    task_rbac = create_rbac_task(company_id=company_id, team_name=team_name, task_intent=task_intent)
    task_schema = create_schema_task(task_intent, task_rbac)
    task_sql_gen = create_sql_gen_task(task_intent, task_schema)
    task_sql_exec = create_sql_exec_task(task_sql_gen)
    task_final = create_final_task(task_sql_exec)

    return [
        task_intent,
        task_rbac,
        task_schema,
        task_sql_gen,
        task_sql_exec,
        task_final
    ]