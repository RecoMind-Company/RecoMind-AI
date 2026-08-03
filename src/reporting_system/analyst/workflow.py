"""LangGraph StateGraph compilation for data analysis workflow."""

import logging
from langgraph.graph import StateGraph, END
from analyst.state import GraphState
from analyst.steps.classifier import data_identifier
from analyst.steps.cleaning import data_cleaning_advisor, data_cleaning_executor
from analyst.steps.kpi import kpi_advisor, kpi_executor
from analyst.steps.reporting import (
    sales_analysis_and_recommendations_generator,
    employee_analysis_and_recommendations_generator,
)

logger = logging.getLogger(__name__)


def get_analysis_app():
    """Builds and compiles the LangGraph StateGraph workflow."""
    workflow = StateGraph(GraphState)

    # Add Nodes
    workflow.add_node("loader", data_identifier)
    workflow.add_node("advisor", data_cleaning_advisor)
    workflow.add_node("executor", data_cleaning_executor)
    workflow.add_node("kpi_advisor", kpi_advisor)
    workflow.add_node("kpi_executor", kpi_executor)
    workflow.add_node("sales_analysis_agent", sales_analysis_and_recommendations_generator)
    workflow.add_node("employee_analysis_agent", employee_analysis_and_recommendations_generator)

    # Routing Functions
    def check_cleaning_plan(state: GraphState) -> str:
        return "skip_cleaning" if state.get("cleaning_plan") is None else "continue"

    def route_to_analysis_agent(state: GraphState) -> str:
        data_type = state.get("data_type")
        if data_type == "employees":
            return "employee_analysis_agent"
        if data_type == "sales":
            return "sales_analysis_agent"
        return "skip_report"

    # Define Edges
    workflow.set_entry_point("loader")
    workflow.add_edge("loader", "advisor")

    workflow.add_conditional_edges(
        "advisor",
        check_cleaning_plan,
        {"continue": "executor", "skip_cleaning": "kpi_advisor"},
    )

    workflow.add_edge("executor", "kpi_advisor")
    workflow.add_edge("kpi_advisor", "kpi_executor")

    workflow.add_conditional_edges(
        "kpi_executor",
        route_to_analysis_agent,
        {
            "sales_analysis_agent": "sales_analysis_agent",
            "employee_analysis_agent": "employee_analysis_agent",
            "skip_report": END,
        },
    )

    workflow.add_edge("sales_analysis_agent", END)
    workflow.add_edge("employee_analysis_agent", END)

    app = workflow.compile()
    logger.info("LangGraph workflow successfully compiled.")
    return app
