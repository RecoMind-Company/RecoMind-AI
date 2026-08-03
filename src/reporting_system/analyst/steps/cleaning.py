"""Data cleaning advisor and executor steps for LangGraph workflow."""

import io
import logging
import re
import time
from typing import Dict, Any
import numpy as np
import pandas as pd
from json import JSONDecodeError

from analyst.state import GraphState
from config.database import get_langgraph_llm
from utils.json_parser import extract_and_parse_json

logger = logging.getLogger(__name__)


def data_cleaning_advisor(state: GraphState) -> Dict[str, Any]:
    """Generates a JSON cleaning plan using LLM based on DataFrame context."""
    logger.info("--- STAGE 3.2: GENERATING CLEANING PLAN ---")
    df = state.get("dataframe")

    if df is None or df.empty:
        logger.warning("No DataFrame found in state. Skipping cleaning advisor.")
        return {"cleaning_plan": None}

    # Handle duplicate columns initially
    if len(df.columns) != len(set(df.columns)):
        logger.warning("Duplicate column names detected. Removing duplicates (keeping first).")
        df_cleaned = df.loc[:, ~df.columns.duplicated()]
    else:
        df_cleaned = df

    info_buffer = io.StringIO()
    df_cleaned.info(buf=info_buffer)
    info_str = info_buffer.getvalue()
    description_str = df_cleaned.describe(include="all").to_string()
    head_str = df_cleaned.head(10).to_csv(index=False)

    constant_value_cols = [col for col in df_cleaned.columns if df_cleaned[col].nunique(dropna=False) <= 1]
    constant_cols_str = ", ".join(constant_value_cols) if constant_value_cols else "None"

    prompt = f"""
    You are an expert and meticulous data analyst. Your primary goal is to create a robust and reliable JSON cleaning plan.
    
    Your response MUST be ONLY a valid JSON object. The JSON must be a list of objects, where each object has "action", "details", and "reasoning" keys.

    --- AVAILABLE ACTIONS & STRICT DETAILS FORMAT ---
    - "action": "remove_duplicates", "details": "Remove fully duplicated rows."
    - "action": "drop_column", "details": "Column 'column_name_to_drop'."
    - "action": "rename_column", "details": {{"old_name": "current_name", "new_name": "suggested_name"}}
    - "action": "map_text_values", "details": {{"column": "col_name", "mapping": {{"ny": "new york"}}}}
    - "action": "unify_format", "details": "Replace common null placeholders like '-', 'NA', '' with proper NaN."
    - "action": "standardize_text", "details": "Apply lowercase and strip whitespace to all text columns."
    - "action": "impute_missing_values", "details": "Impute missing values in all eligible columns."
    
    - "action": "handle_ids", "details": ["ID_Column_1", "ID_Column_2"]
    - "action": "handle_dates", "details": ["Date_Column_1", "Date_Column_2"]
    - "action": "handle_numeric_values", "details": ["Numeric_Col_1", "Numeric_Col_2"]
    - "action": "handle_missing_values", "details": ["Critical_Column_1", "Critical_Column_2"]
    
    - "action": "validate_relationships", "details": {{"start_date_col": "OrderDate_col", "end_date_col": "ShipDate_col"}}

    --- FULL DATAFRAME SUMMARY ---
    {info_str}
    --- STATISTICAL OVERVIEW ---
    {description_str}
    --- FIRST 10 ROWS SAMPLE ---
    {head_str}
    --- CONSTANT COLUMNS ---
    [{constant_cols_str}]

    Now, generate the JSON cleaning plan.
    """

    llm = get_langgraph_llm()
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Attempt {attempt}/{max_retries} generating cleaning plan...")
            response = llm.invoke(prompt)
            cleaning_plan = extract_and_parse_json(response.content)

            if cleaning_plan and isinstance(cleaning_plan, list):
                logger.info("Cleaning plan generated successfully.")
                return {"cleaning_plan": cleaning_plan}

            logger.warning(f"Parsed cleaning plan content is invalid on attempt {attempt}.")
            if attempt < max_retries:
                time.sleep(2)

        except (JSONDecodeError, Exception) as e:
            logger.warning(f"Attempt {attempt}/{max_retries} error generating cleaning plan: {e}")
            if attempt < max_retries:
                time.sleep(2)

    logger.error("Failed to generate valid cleaning plan after all retries.")
    return {"cleaning_plan": None}


def data_cleaning_executor(state: GraphState) -> Dict[str, Any]:
    """Executes the generated cleaning plan on the DataFrame."""
    logger.info("--- STAGE 3.3: EXECUTING CLEANING PLAN ---")
    df = state.get("dataframe")
    cleaning_plan = state.get("cleaning_plan")
    NULL_THRESHOLD = 0.40

    if df is None or cleaning_plan is None:
        logger.warning("Missing DataFrame or cleaning plan. Skipping cleaning execution.")
        return {"dataframe": df}

    cleaned_df = df.copy()

    if len(cleaned_df.columns) != len(set(cleaned_df.columns)):
        logger.info("Removing duplicate column names.")
        cleaned_df = cleaned_df.loc[:, ~cleaned_df.columns.duplicated()]

    cols_to_drop = []
    for col in cleaned_df.columns:
        if isinstance(col, str) and cleaned_df[col].isnull().mean() > NULL_THRESHOLD:
            logger.info(f"Auto-dropping column '{col}' due to >{int(NULL_THRESHOLD * 100)}% missing values.")
            cols_to_drop.append(col)

    if cols_to_drop:
        cleaned_df.drop(columns=cols_to_drop, inplace=True)

    try:
        for action in cleaning_plan:
            action_type = action.get("action")
            details = action.get("details")
            reasoning = action.get("reasoning", "No reasoning provided.")
            logger.info(f"Applying action: {action_type} | Reason: {reasoning}")

            if not isinstance(details, (str, list, dict)):
                continue

            if action_type == "drop_column":
                columns_to_drop = re.findall(r"['\"](.*?)['\"]", str(details))
                for col in columns_to_drop:
                    if col in cleaned_df.columns:
                        cleaned_df.drop(col, axis=1, inplace=True)

            elif action_type == "rename_column":
                if isinstance(details, dict) and "old_name" in details and "new_name" in details:
                    if details["old_name"] in cleaned_df.columns:
                        cleaned_df.rename(columns={details["old_name"]: details["new_name"]}, inplace=True)

            elif action_type == "map_text_values":
                if isinstance(details, dict) and "column" in details and "mapping" in details:
                    col_name, mapping = details["column"], details["mapping"]
                    if col_name in cleaned_df.columns and isinstance(mapping, dict):
                        cleaned_df[col_name] = cleaned_df[col_name].map(mapping).fillna(cleaned_df[col_name])

            elif action_type == "handle_ids":
                if isinstance(details, list):
                    for col in details:
                        if col in cleaned_df.columns:
                            cleaned_df[col] = (
                                cleaned_df[col].astype(str).str.extract(r"([a-zA-Z0-9-._]+)")[0].astype(str)
                            )

            elif action_type == "unify_format":
                cleaned_df.replace(["-", "NA", "", " "], np.nan, inplace=True)

            elif action_type == "standardize_text":
                for col in cleaned_df.select_dtypes(include=["object"]).columns:
                    cleaned_df[col] = cleaned_df[col].astype(str).str.lower().str.strip()

            elif action_type == "impute_missing_values":
                for col in cleaned_df.columns:
                    if cleaned_df[col].isnull().any():
                        dtype = cleaned_df[col].dtype
                        if pd.api.types.is_numeric_dtype(dtype):
                            impute_value = cleaned_df[col].median()
                            cleaned_df[col].fillna(impute_value, inplace=True)
                        elif pd.api.types.is_object_dtype(dtype):
                            mode_val = cleaned_df[col].mode()
                            if not mode_val.empty:
                                cleaned_df[col].fillna(mode_val[0], inplace=True)
                        elif pd.api.types.is_datetime64_any_dtype(dtype):
                            mode_val = cleaned_df[col].mode()
                            if not mode_val.empty:
                                cleaned_df[col].fillna(mode_val[0], inplace=True)

            elif action_type == "handle_dates":
                if isinstance(details, list):
                    for col in details:
                        if col in cleaned_df.columns:
                            cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors="coerce")

            elif action_type == "validate_relationships":
                if isinstance(details, dict) and "start_date_col" in details and "end_date_col" in details:
                    start_col, end_col = details["start_date_col"], details["end_date_col"]
                    if start_col in cleaned_df.columns and end_col in cleaned_df.columns:
                        original_rows = len(cleaned_df)
                        cleaned_df.drop(cleaned_df[cleaned_df[start_col] > cleaned_df[end_col]].index, inplace=True)
                        rows_dropped = original_rows - len(cleaned_df)
                        if rows_dropped > 0:
                            logger.info(f"Dropped {rows_dropped} rows with invalid date logic.")

            elif action_type == "handle_numeric_values":
                if isinstance(details, list):
                    for col in details:
                        if col in cleaned_df.columns and pd.api.types.is_numeric_dtype(cleaned_df[col]):
                            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors="coerce")
                            Q1, Q3 = cleaned_df[col].quantile(0.25), cleaned_df[col].quantile(0.75)
                            IQR = Q3 - Q1
                            lower_bound, upper_bound = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
                            cleaned_df.loc[(cleaned_df[col] < lower_bound) | (cleaned_df[col] > upper_bound), col] = np.nan

            elif action_type == "remove_duplicates":
                cleaned_df.drop_duplicates(inplace=True)

            elif action_type == "handle_missing_values":
                if isinstance(details, list):
                    valid_columns = [col for col in details if col in cleaned_df.columns]
                    if valid_columns:
                        cleaned_df.dropna(subset=valid_columns, inplace=True)

        logger.info("Cleaning plan execution complete.")
        return {"dataframe": cleaned_df}

    except Exception as e:
        logger.error(f"Error during cleaning plan execution: {e}", exc_info=True)
        return {"dataframe": df}
