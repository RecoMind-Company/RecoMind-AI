# auto_analyst/graph/workflow.py

from langgraph.graph import StateGraph, END
from auto_analyst.graph.state import GraphState
from auto_analyst.steps import step_01_load_data, step_02_clean_data, step_03_kpi_analysis, step_04_reporting, step_05_output

def get_analysis_app():
    workflow = StateGraph(GraphState)

    # MODIFICATION: Updated the node to call the new 'data_identifier' function.
    workflow.add_node("loader", step_01_load_data.data_identifier)
    
    # The rest of the nodes remain the same
    workflow.add_node("advisor", step_02_clean_data.data_cleaning_advisor)
    workflow.add_node("executor", step_02_clean_data.data_cleaning_executor)
    workflow.add_node("kpi_advisor", step_03_kpi_analysis.kpi_advisor)
    workflow.add_node("kpi_executor", step_03_kpi_analysis.kpi_executor)
    workflow.add_node("sales_analysis_agent", step_04_reporting.sales_analysis_and_recommendations_generator)
    workflow.add_node("employee_analysis_agent", step_04_reporting.employee_analysis_and_recommendations_generator)
    workflow.add_node("save_outputs", step_05_output.save_outputs)
    workflow.add_node("final_output_viewer", step_05_output.final_output_viewer)

    # The graph logic and flow remain unchanged.
    def check_cleaning_plan(state):
        return "skip_cleaning" if state.get("cleaning_plan") is None else "continue"

    def route_to_analysis_agent(state):
        data_type = state.get("data_type")
        if data_type == "employees":
            return "employee_analysis_agent"
        elif data_type == "sales":
            return "sales_analysis_agent"
        else:
            return "final_output_viewer"

    workflow.set_entry_point("loader")
    workflow.add_edge("loader", "advisor")
    workflow.add_conditional_edges(
        "advisor",
        check_cleaning_plan,
        {"continue": "executor", "skip_cleaning": "kpi_advisor"}
    )
    workflow.add_edge("executor", "kpi_advisor")
    workflow.add_edge("kpi_advisor", "kpi_executor")
    workflow.add_conditional_edges(
        "kpi_executor",
        route_to_analysis_agent,
        {
            "sales_analysis_agent": "sales_analysis_agent",
            "employee_analysis_agent": "employee_analysis_agent",
            "final_output_viewer": "final_output_viewer"
        }
    )
    workflow.add_edge("sales_analysis_agent", "save_outputs")
    workflow.add_edge("employee_analysis_agent", "save_outputs")
    workflow.add_edge("save_outputs", "final_output_viewer")
    workflow.add_edge("final_output_viewer", END)

    app = workflow.compile()
    return app