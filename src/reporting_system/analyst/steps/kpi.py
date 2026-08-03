"""KPI calculation advisor and executor steps for LangGraph workflow."""

import json
import logging
import re
import time
from typing import Dict, Any
from json import JSONDecodeError
import numpy as np
import pandas as pd

from analyst.state import GraphState
from config.database import get_langgraph_llm
from utils.json_parser import extract_and_parse_json

logger = logging.getLogger(__name__)


def kpi_advisor(state: GraphState) -> Dict[str, Any]:
    """Generates KPI calculation plan via LLM."""
    logger.info("--- STAGE 3.4: GENERATING KPI PLAN ---")
    df = state.get("dataframe")
    data_type = state.get("data_type")
    user_request = state.get("user_request", "Generate a general analysis.")

    if df is None or df.empty:
        logger.warning("No DataFrame found in state. Skipping KPI advisor.")
        return {"kpi_plan": None}

    columns = df.columns.tolist()

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

    llm = get_langgraph_llm()
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} generating KPI plan...")
            response = llm.invoke(prompt)
            kpi_plan = extract_and_parse_json(response.content)

            if kpi_plan and isinstance(kpi_plan, list):
                logger.info("KPI calculation plan generated successfully.")
                return {"kpi_plan": kpi_plan}

            logger.warning(f"Parsed content is not a valid list on attempt {attempt}.")
            if attempt < max_retries:
                time.sleep(2)

        except (JSONDecodeError, Exception) as e:
            logger.warning(f"Attempt {attempt}/{max_retries} error generating KPI plan: {e}")
            if attempt < max_retries:
                time.sleep(2)

    logger.error("Failed to generate KPI plan after all retries.")
    return {"kpi_plan": None}


def kpi_executor(state: GraphState) -> Dict[str, Any]:
    """Generates Python code to execute KPI calculations safely."""
    logger.info("--- STAGE 3.5: EXECUTING KPI CALCULATIONS ---")
    df = state.get("dataframe")
    kpi_plan = state.get("kpi_plan")

    if df is None or kpi_plan is None:
        logger.warning("Missing DataFrame or KPI plan. Skipping KPI execution.")
        return {"kpis": None}

    code_generation_prompt = f"""
    You are an expert Python data analyst. Your task is to write Python code to calculate a list of Key Performance Indicators (KPIs) based on a pandas DataFrame named `df`.
    The code should calculate the KPIs and store the results in a dictionary named `results`.

    **CRITICAL RULE 1: You MUST operate on the DataFrame variable named `df`.**
    Do NOT use any raw data, numbers, or example strings directly in your code.
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
    Always use `pd.to_numeric(df['column_name'], errors='coerce').fillna(0)` on any column you plan to use in a calculation (like .sum(), .mean(), or division).
    
    GOOD EXAMPLE (Defensive):
    df['SalesOrderDetail_LineTotal'] = pd.to_numeric(df['SalesOrderDetail_LineTotal'], errors='coerce').fillna(0)
    results['total_sales'] = df['SalesOrderDetail_LineTotal'].sum()

    Here is the list of KPIs to calculate:
    {json.dumps(kpi_plan, indent=2)}

    Your response must be ONLY the Python code block. Do NOT include any explanations, Markdown, or surrounding text.
    """

    llm = get_langgraph_llm()
    max_retries = 3
    code_response = None
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} generating KPI code...")
            code_response = llm.invoke(code_generation_prompt)
            if code_response and code_response.content:
                logger.info("KPI calculation code generated successfully.")
                break
            if attempt < max_retries:
                time.sleep(2)
        except Exception as e:
            logger.warning(f"Attempt {attempt}/{max_retries} error generating KPI code: {e}")
            if attempt < max_retries:
                time.sleep(2)

    if not code_response or not code_response.content:
        logger.error("Failed to generate KPI code after retries.")
        return {"kpis": {"error": "Failed to generate KPI code after all retries."}}

    try:
        code_block = re.search(r"```python(.*?)```", code_response.content, re.DOTALL)
        code_to_execute = code_block.group(1).strip() if code_block else code_response.content.strip()

        safe_globals = {"pd": pd, "np": np, "df": df}
        safe_locals = {"results": {}}

        exec(code_to_execute, safe_globals, safe_locals)
        raw_kpis = safe_locals.get("results", {})

        def sanitize_val(val: Any) -> Any:
            if isinstance(val, (dict, list)):
                return sanitize_obj(val)
            if isinstance(val, (pd.Series, pd.Index, np.ndarray)):
                return val.tolist()
            if isinstance(val, (float, np.float64)):
                return round(float(val), 2)
            return str(val)

        def sanitize_obj(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {sanitize_val(k): sanitize_val(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [sanitize_val(item) for item in obj]
            return str(obj)

        sanitized_kpis = sanitize_obj(raw_kpis)
        logger.info("KPI calculations executed successfully.")
        return {"kpis": sanitized_kpis}

    except Exception as e:
        logger.error(f"Error during KPI code execution: {e}", exc_info=True)
        return {"kpis": {"error": f"An error occurred during KPI code execution: {e}"}}
