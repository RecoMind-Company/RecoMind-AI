# auto_analyst/steps/step_01_load_data.py

import pandas as pd
from ..graph.state import GraphState
from ..components.config import graph_llm as llm_model

def classify_data_with_llm(columns: list) -> str:
    """
    Uses an LLM to classify the data type based on a list of column names.
    (This function remains unchanged)
    """
    system_prompt = (
        "You are an expert data classifier. Your task is to analyze a list of CSV "
        "column names and determine the primary topic of the dataset. "
        "You must respond with a single, lowercase word from the following list: "
        "'employees', 'sales', 'customers', 'products', 'marketing', 'finance', 'logistics', 'support', 'unknown'."
    )
    user_prompt = f"""
    Based on the following list of column names, what is the main topic of the data?
    
    Column Names: {', '.join(columns)}
    
    Return ONLY one word from the allowed list, with no extra text, explanation, or punctuation.
    """
    response = llm_model.invoke(f"{system_prompt}\n\n{user_prompt}")
    return response.content.strip().lower()

def data_identifier(state: GraphState):
    """
    MODIFIED: Receives a DataFrame from the state and uses an LLM to identify its type.
    It no longer loads data from a CSV file.
    """
    print("---IDENTIFYING DATA TYPE---")
    
    # MODIFICATION: Get the DataFrame directly from the graph's state.
    df = state.get("dataframe")

    if df is None or df.empty:
        print(f"❌ Error: No DataFrame was passed into the state for analysis.")
        return {"data_type": "error", "dataframe": None}
    
    # The classification logic remains the same.
    data_type = classify_data_with_llm(df.columns.tolist())
    
    print(f"✅ Data received successfully. Identified as '{data_type}'.")
    
    # Pass the dataframe along with its identified type to the next step.
    return {"data_type": data_type, "dataframe": df}