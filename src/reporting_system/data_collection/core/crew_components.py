from typing import List, Dict, Any

from shared.config import get_llm

from .agents import create_agents
from .tasks import create_tasks
from .tools import VectorDBTableSearchTool, GetTableSchemaTool, ExecuteSQLQueryTool


llm = get_llm()


def get_configured_agents(tool_params: Dict[str, Any], llm) -> List:
    """
    Configures and returns fresh agents with request-specific tools.

    Celery workers are long-lived, so mutating module-level Agent objects can
    leak tool state such as team_name between separate analysis requests.
    """
    agents = create_agents()
    retrieval_agent, _, schema_retriever_agent, _, query_generator_agent = agents

    retrieval_agent.tools = [VectorDBTableSearchTool(**tool_params)]
    schema_retriever_agent.tools = [GetTableSchemaTool(**tool_params)]
    query_generator_agent.tools = [ExecuteSQLQueryTool(**tool_params)]

    for agent in agents:
        agent.llm = llm

    return agents


def get_tasks(agents: List) -> List:
    """Returns fresh tasks bound to the provided fresh agents."""
    return create_tasks(agents)
