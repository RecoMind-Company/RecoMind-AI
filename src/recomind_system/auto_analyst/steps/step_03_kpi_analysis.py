import json
import re
import pandas as pd
import numpy as np
from ..graph.state import GraphState
from ..core.config import llm_model
from ..utils.json_parser import extract_and_parse_json

# --- Node Functions --- (Copied from your code)

def kpi_advisor(state: GraphState):
    """
    Uses an LLM to generate a JSON plan for KPI calculation and trends based on cleaned data.
    """
    print("---GENERATING KPI CALCULATION PLAN---")
    df = state.get("dataframe")
    data_type = state.get("data_type")

    if df is None:
        print("❌ No DataFrame found in state. Skipping KPI advisor.")
        return {"kpi_plan": None}

    columns = df.columns.tolist()

    prompt = f"""
    You are a data analyst expert. Your task is to analyze the columns of a cleaned DataFrame and provide a JSON plan to calculate Key Performance Indicators (KPIs) and identify key trends. The data has been identified as '{data_type}'.
    
    Your response must be ONLY a valid JSON object. The JSON should be a list of objects, where each object represents a KPI or trend to be calculated.
    
    Each object must have two keys:
    - "kpi_name": A descriptive name for the KPI or trend (e.g., "Total Revenue", "Top 5 Selling Products").
    - "calculation_details": A detailed description of the columns to use and the mathematical/analytical operation to perform, in natural language. This will be given to a Pandas Agent.

    If you cannot find suitable columns for a specific KPI, do not include it.
    
    Return ONLY a valid JSON object, with no extra text, explanation, or punctuation.
    
    Here are the available columns in the cleaned DataFrame: {columns}.
    
    Example for 'employees' data:
    [
        {{
            "kpi_name": "Average Employee Salary",
            "calculation_details": "Calculate the mean of the 'Salary' or 'Rate' column."
        }},
        {{
            "kpi_name": "Gender Distribution",
            "calculation_details": "Count the occurrences of each gender in the 'Gender' column and return a dictionary."
        }}
    ]

    Example for 'sales' data:
    [
        {{
            "kpi_name": "Total Revenue",
            "calculation_details": "Calculate the sum of the 'TotalDue' column."
        }},
        {{
            "kpi_name": "Average Order Value",
            "calculation_details": "Calculate the average of the 'TotalDue' column, grouped by a unique order identifier if available. Otherwise, calculate the overall average."
        }}
    ]
    """
    
    response = llm_model.invoke(prompt)
    
    kpi_plan = extract_and_parse_json(response.content)
    
    if kpi_plan:
        print("✅ KPI calculation plan generated successfully.")
        return {"kpi_plan": kpi_plan}
    else:
        print("❌ Failed to generate or parse the KPI plan.")
        return {"kpi_plan": None}


def kpi_executor(state: GraphState):
    """
    Generates and executes Python code to calculate KPIs.
    """
    print("---GENERATING AND EXECUTING KPI CALCULATION CODE---")
    df = state.get("dataframe")
    kpi_plan = state.get("kpi_plan")
    kpis = {}

    if df is None or kpi_plan is None:
        print("❌ Missing DataFrame or KPI plan. Skipping executor.")
        return {"kpis": None}

    code_generation_prompt = f"""
    You are an expert Python data analyst. Your task is to write Python code to calculate a list of Key Performance Indicators (KPIs) based on a pandas DataFrame named `df`.
    The code should calculate the KPIs and store the results in a dictionary named `results`.

    Here is the list of KPIs to calculate:
    {json.dumps(kpi_plan, indent=2)}

    Your response must be ONLY the Python code block. Do NOT include any explanations, Markdown, or surrounding text.
    """

    try:
        code_response = llm_model.invoke(code_generation_prompt)
        code_block = re.search(r'```python(.*?)```', code_response.content, re.DOTALL)
        if code_block:
            code_to_execute = code_block.group(1).strip()
        else:
            code_to_execute = code_response.content.strip()

        safe_globals = {'pd': pd, 'np': np, 'df': df}
        safe_locals = {'results': {}}

        exec(code_to_execute, safe_globals, safe_locals)
        kpis = safe_locals.get('results', {})
        
        def sanitize_value(value):
            if isinstance(value, (dict, list)):
                return sanitize_dict_or_list(value)
            elif isinstance(value, (pd.Series, pd.Index, np.ndarray)):
                return value.tolist()
            elif isinstance(value, (float, np.float64)):
                return round(float(value), 2)
            else:
                return str(value)
        
        def sanitize_dict_or_list(obj):
            if isinstance(obj, dict):
                return {sanitize_value(k): sanitize_value(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_value(item) for item in obj]
            else:
                return str(obj)

        sanitized_kpis = sanitize_dict_or_list(kpis)

        print("✅ KPIs calculated successfully.")
        return {"kpis": sanitized_kpis}

    except Exception as e:
        print(f"❌ An error occurred during KPI calculation: {e}")
        return {"kpis": {"error": f"An error occurred during KPI calculation: {e}"}}