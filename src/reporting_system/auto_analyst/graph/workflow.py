from langgraph.graph import StateGraph, END
from ..graph.state import GraphState
# [MODIFICATION] We no longer need step_05_output
from ..steps import step_01_load_data, step_02_clean_data, step_03_kpi_analysis, step_04_reporting 
# from ..steps import step_01_load_data, step_02_clean_data, step_03_kpi_analysis, step_04_reporting, step_05_output

def get_analysis_app():
    workflow = StateGraph(GraphState)

    # --- Define Nodes ---
    workflow.add_node("loader", step_01_load_data.data_identifier)
    workflow.add_node("advisor", step_02_clean_data.data_cleaning_advisor)
    workflow.add_node("executor", step_02_clean_data.data_cleaning_executor)
    workflow.add_node("kpi_advisor", step_03_kpi_analysis.kpi_advisor)
    workflow.add_node("kpi_executor", step_03_kpi_analysis.kpi_executor)
    workflow.add_node("sales_analysis_agent", step_04_reporting.sales_analysis_and_recommendations_generator)
    workflow.add_node("employee_analysis_agent", step_04_reporting.employee_analysis_and_recommendations_generator)
    
    # [MODIFICATION] Removed the output nodes as they are no longer needed for the API.
    # The final report is returned in the graph state.
    # workflow.add_node("save_outputs", step_05_output.save_outputs)
    # workflow.add_node("final_output_viewer", step_05_output.final_output_viewer)

    # --- Define Routing Functions ---
    def check_cleaning_plan(state):
        return "skip_cleaning" if state.get("cleaning_plan") is None else "continue"

    # [MODIFICATION] Simplified the routing logic
    def route_to_analysis_agent(state):
        data_type = state.get("data_type")
        if data_type == "employees":
            return "employee_analysis_agent"
        elif data_type == "sales":
            return "sales_analysis_agent"
        else:
            # If data type is unknown or not supported for reporting, end the graph.
            return "skip_report"

    # --- Define Edges ---
    workflow.set_entry_point("loader")
    workflow.add_edge("loader", "advisor")
    
    workflow.add_conditional_edges(
        "advisor",
        check_cleaning_plan,
        {"continue": "executor", "skip_cleaning": "kpi_advisor"}
    )
    
    workflow.add_edge("executor", "kpi_advisor")
    workflow.add_edge("kpi_advisor", "kpi_executor")
    
    # [MODIFICATION] Updated the conditional edges from kpi_executor
    workflow.add_conditional_edges(
        "kpi_executor",
        route_to_analysis_agent,
        {
            "sales_analysis_agent": "sales_analysis_agent",
            "employee_analysis_agent": "employee_analysis_agent",
            # This new key "skip_report" correctly maps to the END state.
            "skip_report": END 
        }
    )

    # [MODIFICATION] The report agents now go directly to END
    # The pipeline.py file will get the report from the final state.
    workflow.add_edge("sales_analysis_agent", END)
    workflow.add_edge("employee_analysis_agent", END)

    # [MODIFICATION] Removed all old edges related to step_05
    # workflow.add_edge("sales_analysis_agent", "save_outputs")
    # workflow.add_edge("employee_analysis_agent", "save_outputs")
    # workflow.add_edge("save_outputs", "final_output_viewer")
    # workflow.add_edge("final_output_viewer", END)

    app = workflow.compile()
    return app

