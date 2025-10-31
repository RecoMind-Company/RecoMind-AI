import json
import re
import pandas as pd
import numpy as np
import time
from json import JSONDecodeError
from ..graph.state import GraphState
from ..components.config import graph_llm as llm_model
# [MODIFICATION] We import the manual parser again
from ..utils.json_parser import extract_and_parse_json

# --- Node Functions ---

def kpi_advisor(state: GraphState):
    """
    Uses an LLM to generate a JSON plan for KPI calculation and trends.
    [MODIFIED] Reverted to manual JSON parsing (extract_and_parse_json)
    to support LLMs without .with_structured_output().
    """
    print("---GENERATING KPI CALCULATION PLAN (MANUAL PARSING)---")
    df = state.get("dataframe")
    data_type = state.get("data_type")
    # === MODIFICATION START: Get the user_request from the state ===
    user_request = state.get("user_request", "Generate a general analysis.")
    # === MODIFICATION END ===

    if df is None:
        print("❌ No DataFrame found in state. Skipping KPI advisor.")
        return {"kpi_plan": None}

    columns = df.columns.tolist()

    # === [MODIFICATION] The prompt is the key ===
    # This prompt *only* needs to worry about the *plan* and
    # using the correct column *names*.
    prompt = f"""
    You are a data analyst expert. Your task is to analyze the columns of a cleaned DataFrame and provide a JSON plan to calculate Key Performance Indicators (KPIs) and identify key trends. The data has been identified as '{data_type}'.
    
    Your response must be ONLY a valid JSON object. The JSON should be a list of objects, where each object represents a KPI or trend to be calculated.
    
    Each object must have two keys:
    - "kpi_name": A descriptive name for the KPI or trend (e.g., "Total Revenue", "Top 5 Selling Products").
    - "calculation_details": A detailed description of the columns to use and the mathematical/analytical operation to perform, in natural language. This will be given to a Pandas Agent.

    Return ONLY a valid JSON object, with no extra text, explanation, or punctuation.
    
    Here are the available columns in the cleaned DataFrame: {columns}.

    **CRITICAL RULE: You MUST use the exact column names provided in the list above.**
    Do NOT infer, guess, or change column names. If a column is 'Product_Name', use 'Product_Name'. If a column is 'SpecialOffer_DiscountPct', use 'SpecialOffer_DiscountPct'.
    Do NOT invent names like 'ProductName' or 'SpecialOfferProduct_DiscountPct'.
    
    **IMPORTANT**: The user's specific request is: "{user_request}".
    You MUST generate a KPI plan that is *highly relevant* to answering this specific request. Prioritize KPIs that directly address the user's query.
    """
    
    # [MODIFICATION] Reverted to the original retry loop
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} to generate KPI plan...")
            response = llm_model.invoke(prompt)
            # We use the manual parser again
            kpi_plan = extract_and_parse_json(response.content)
            
            if kpi_plan and isinstance(kpi_plan, list):
                print("✅ KPI calculation plan generated successfully.")
                return {"kpi_plan": kpi_plan}
            else:
                print(f"⚠️ Warning: Parsed content is not a valid list on attempt {attempt + 1}.")
                if attempt + 1 < max_retries:
                    time.sleep(5)
                    
        except (JSONDecodeError, Exception) as e:
            print(f"⚠️ Warning: An error occurred on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt + 1 < max_retries:
                time.sleep(5) 
            else:
                print("❌ Error: Failed to get a valid response for KPI plan after multiple retries.")
                return {"kpi_plan": None}

    print("❌ Failed to generate or parse the KPI plan after all retries.")
    return {"kpi_plan": None}


def kpi_executor(state: GraphState):
    """
    Generates and executes Python code to calculate KPIs.
    
    [MODIFIED] The prompt for this function is now updated
    to be highly defensive, preventing multiple error types.
    """
    print("---GENERATING AND EXECUTING KPI CALCULATION CODE---")
    df = state.get("dataframe")
    kpi_plan = state.get("kpi_plan")
    
    if df is None or kpi_plan is None:
        print("❌ Missing DataFrame or KPI plan. Skipping executor.")
        return {"kpis": None}

    # === [MODIFICATION] ---
    # This is the correct place to add rules for code generation.
    # We have added all 3 rules we discussed to make the code robust.
    code_generation_prompt = f"""
    You are an expert Python data analyst. Your task is to write Python code to calculate a list of Key Performance Indicators (KPIs) based on a pandas DataFrame named `df`.
    The code should calculate the KPIs and store the results in a dictionary named `results`.

    **CRITICAL RULE 1: You MUST operate on the DataFrame variable named `df`.**
    Do NOT use any raw data, numbers, or example strings (like '779136.9979...') directly in your code.
    Your code must only reference the `df` variable and its columns.
    
    GOOD EXAMPLE (Defensive):
    results['total_sales'] = df['SalesOrderDetail_LineTotal'].sum()

    BAD EXAMPLE (Will crash):
    results['total_sales'] = pd.to_numeric("779136.997987.2729...")

    **CRITICAL RULE 2: When writing calculations, YOU MUST write defensive code to prevent 'division by zero' errors.**
    Always check if the denominator is zero BEFORE performing a division.

    GOOD EXAMPLE (Defensive):
    total_sales = df['TotalDue'].sum()
    order_count = df['SalesOrderID'].nunique()
    if order_count > 0:
        results['average_order_value'] = total_sales / order_count
    else:
        results['average_order_value'] = 0 

    BAD EXAMPLE (Will crash):
    results['average_order_value'] = df['TotalDue'].sum() / df['SalesOrderID'].nunique()
    
    **CRITICAL RULE 3: YOU MUST ensure columns are numeric before performing math.**
    Always use `pd.to_numeric(df['column_name'], errors='coerce').fillna(0)` on any column you plan to use in a calculation (like .sum(), .mean(), or division) to prevent TypeErrors (e.g., 'str' / 'int').
    
    GOOD EXAMPLE (Defensive):
    # This is safe code
    df['SalesOrderDetail_LineTotal'] = pd.to_numeric(df['SalesOrderDetail_LineTotal'], errors='coerce').fillna(0)
    results['total_sales'] = df['SalesOrderDetail_LineTotal'].sum()

    BAD EXAMPLE (Will crash):
    # This will crash if 'SalesOrderDetail_LineTotal' is a string
    results['total_sales'] = df['SalesOrderDetail_LineTotal'].sum()

    Here is the list of KPIs to calculate:
    {json.dumps(kpi_plan, indent=2)}

    Your response must be ONLY the Python code block. Do NOT include any explanations, Markdown, or surrounding text.
    """

    # --- NEW: Added a robust retry mechanism for the code generation call ---
    max_retries = 3
    code_response = None
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} to generate KPI calculation code...")
            code_response = llm_model.invoke(code_generation_prompt)
            if code_response and code_response.content:
                print("✅ KPI code generated successfully.")
                break # Exit loop on success
            else:
                print(f"⚠️ Warning: Received an empty response on attempt {attempt + 1}.")
                if attempt + 1 < max_retries:
                    time.sleep(5)

        except (JSONDecodeError, Exception) as e:
            print(f"⚠️ Warning: An error occurred during code generation on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt + 1 < max_retries:
                time.sleep(5)
            else:
                print("❌ Error: Failed to get a valid response for code generation after multiple retries.")
                return {"kpis": {"error": "Failed to generate KPI code due to API errors."}}

    # If loop finished without a successful response
    if not code_response or not code_response.content:
        print("❌ Failed to generate KPI code after all retries.")
        return {"kpis": {"error": "Failed to generate KPI code after all retries."}}
    
    # --- The rest of the function executes only if the API call was successful ---
    try:
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
        print(f"❌ An error occurred during KPI code execution: {e}")
        return {"kpis": {"error": f"An error occurred during KPI code execution: {e}"}}
