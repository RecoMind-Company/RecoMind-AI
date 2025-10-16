from typing import TypedDict, Optional, List, Dict, Any
import pandas as pd

# --- Define Graph State --- (Copied from your code)
class GraphState(TypedDict):
    """
    Represents the state of the graph.
    Attributes:
        data_type: The type of data identified (e.g., 'employees').
        dataframe: The loaded pandas DataFrame.
        cleaning_plan: The JSON plan from the LLM.
        kpi_plan: The JSON plan from the LLM for KPI calculation.
        kpis: A dictionary of calculated key performance indicators.
        analysis_report: The final, generated report text.
    """
    data_type: Optional[str]
    dataframe: Optional[pd.DataFrame]
    cleaning_plan: Optional[List[Dict]]
    kpi_plan: Optional[List[Dict]]
    kpis: Optional[Dict[str, Any]]
    analysis_report: Optional[str]