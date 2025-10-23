import pandas as pd
import numpy as np
import re
import io 
import time 
from json import JSONDecodeError 
from ..graph.state import GraphState
from ..core.config import llm_model
from ..utils.json_parser import extract_and_parse_json

# --- Node Functions ---

def data_cleaning_advisor(state: GraphState):
    """
    Asks the LLM to generate a JSON cleaning plan.
    This is the final, production-grade version, enforcing strict JSON structures.
    """
    print("---GENERATING PRODUCTION-GRADE CLEANING PLAN---")
    df = state.get("dataframe")

    if df is None or df.empty:
        print("❌ No DataFrame found in state. Skipping advisor.")
        return {"cleaning_plan": None}

    # --- BUG FIX: Handle duplicate columns AT THE START ---
    # This prevents the 'ValueError: The truth value of a Series is ambiguous'
    if len(df.columns) != len(set(df.columns)):
        print("⚠️ Duplicate column names detected in advisor. Removing duplicates (keeping first occurrence).")
        # Use a copy to avoid modifying the original state DataFrame prematurely
        df_cleaned = df.loc[:, ~df.columns.duplicated()]
    else:
        df_cleaned = df 
    # --- All subsequent operations in this function will use df_cleaned ---

    # --- Comprehensive Context Gathering ---
    info_buffer = io.StringIO()
    # Use df_cleaned for all analysis
    df_cleaned.info(buf=info_buffer)
    info_str = info_buffer.getvalue()
    
    description_str = df_cleaned.describe(include='all').to_string()
    
    head_str = df_cleaned.head(10).to_csv(index=False)
    
    # Use df_cleaned for all analysis
    constant_value_cols = [col for col in df_cleaned.columns if df_cleaned[col].nunique(dropna=False) <= 1]
    constant_cols_str = ", ".join(constant_value_cols) if constant_value_cols else "None"


    # --- Advanced Prompt Engineering for Production Robustness ---
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
    
    - "action": "handle_ids", "details": ["ID_Column_1", "ID_Column_2"]  # MUST be a list
    - "action": "handle_dates", "details": ["Date_Column_1", "Date_Column_2"] # MUST be a list
    - "action": "handle_numeric_values", "details": ["Numeric_Col_1", "Numeric_Col_2"] # MUST be a list of columns with errors
    - "action": "handle_missing_values", "details": ["Critical_Column_1", "Critical_Column_2"] # MUST be a list
    
    - "action": "validate_relationships", "details": {{"start_date_col": "OrderDate_col", "end_date_col": "ShipDate_col"}} # MUST be a dict

    --- CORE INSTRUCTIONS ---
    1.  **Strict JSON Formatting**: You must follow the `details` format for each action precisely. For actions requiring a list of columns, provide a JSON list of strings.
    2.  **Dynamic Relationship Validation**: If you find date columns with a logical sequence (e.g., order before ship), use "validate_relationships" and provide the exact column names in the details dictionary.
    3.  **Intelligent Outlier Analysis**: Only suggest "handle_numeric_values" for columns with **Bad Outliers** (impossible values). Do not suggest it for columns with plausible but rare **Good Outliers**.
    4.  **Contextual Decisions**: Use the provided summaries to make all decisions dynamically. Do not use fixed column names unless they are present in the data summary.
    5.  **NOTE**: The system will automatically handle columns with >40% nulls. You do not need to suggest actions for them.
    6.  **Contextual Constant Columns**: The following columns have been identified as having only one unique value: [{constant_cols_str}]. Your task is to decide if this constant value provides important context (e.g., 'Status: Active', 'Country: Egypt') or if the column is genuinely useless. Only suggest dropping the column if it provides NO analytical value. Otherwise, state in your reasoning that you are preserving it for its contextual value.


    --- FULL DATAFRAME SUMMARY ---
    {info_str}
    --- STATISTICAL OVERVIEW ---
    {description_str}
    --- FIRST 10 ROWS SAMPLE ---
    {head_str}

    Now, generate the JSON cleaning plan.
    """
    
    # --- Retry Mechanism for API Robustness ---
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1}/{max_retries} to generate cleaning plan...")
            response = llm_model.invoke(prompt)
            cleaning_plan = extract_and_parse_json(response.content)
            
            if cleaning_plan and isinstance(cleaning_plan, list):
                print("✅ Cleaning plan generated successfully.")
                return {"cleaning_plan": cleaning_plan}
            else:
                print(f"⚠️ Warning: Parsed content is not a valid list on attempt {attempt + 1}.")
                if attempt + 1 < max_retries: time.sleep(5)
                
        except (JSONDecodeError, Exception) as e:
            print(f"⚠️ Warning: An error occurred on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt + 1 < max_retries:
                time.sleep(5)  
            else:
                print("❌ Error: Failed to get a valid response after multiple retries.")
                return {"cleaning_plan": None}

    print("❌ Failed to generate or parse the cleaning plan after all retries.")
    return {"cleaning_plan": None}


def data_cleaning_executor(state: GraphState):
    """
    Executes a robust, production-grade cleaning plan on the entire DataFrame.
    """
    print("---EXECUTING PRODUCTION-GRADE CLEANING PLAN---")
    df = state.get("dataframe")
    cleaning_plan = state.get("cleaning_plan")
    
    NULL_THRESHOLD = 0.40

    if df is None or cleaning_plan is None:
        print("❌ Missing DataFrame or cleaning plan. Skipping executor.")
        return {"dataframe": df} 
    
    cleaned_df = df.copy()

    # This duplicate handling is still needed here in case advisor fails
    if len(cleaned_df.columns) != len(set(cleaned_df.columns)):
        print("⚠️ Duplicate column names detected. Removing duplicates (keeping first occurrence).")
        cleaned_df = cleaned_df.loc[:, ~cleaned_df.columns.duplicated()]

    print("---Executing Automatic Cleaning Rules---")
    cols_to_drop = []
    for col in cleaned_df.columns:
        if not isinstance(col, str): continue
        
        if cleaned_df[col].isnull().mean() > NULL_THRESHOLD:
            print(f"    - Dropping column '{col}' due to >{int(NULL_THRESHOLD*100)}% missing values.")
            cols_to_drop.append(col)
    
    if cols_to_drop:
        cleaned_df.drop(columns=cols_to_drop, inplace=True)

    try:
        print("---Executing LLM-Generated Cleaning Plan---")
        for action in cleaning_plan:
            action_type = action.get("action")
            details = action.get("details")
            reasoning = action.get("reasoning", "No reasoning provided.")
            
            print(f"  - Action: {action_type} | Reason: {reasoning}")

            if not isinstance(details, (str, list, dict)): continue 

            if action_type == "drop_column":
                columns_to_drop = re.findall(r"['\"](.*?)['\"]", str(details))
                for col in columns_to_drop:
                    print(f"    - Dropping column: '{col}'")
                    if col in cleaned_df.columns:
                        cleaned_df.drop(col, axis=1, inplace=True)
            
            elif action_type == "rename_column":
                if isinstance(details, dict) and "old_name" in details and "new_name" in details:
                    print(f"    - Renaming column '{details['old_name']}' to '{details['new_name']}'")
                    cleaned_df.rename(columns={details["old_name"]: details["new_name"]}, inplace=True)

            elif action_type == "map_text_values":
                if isinstance(details, dict) and "column" in details and "mapping" in details:
                    col_name, mapping = details["column"], details["mapping"]
                    if col_name in cleaned_df.columns and isinstance(mapping, dict):
                        print(f"    - Applying text mapping to column '{col_name}'")
                        cleaned_df[col_name] = cleaned_df[col_name].map(mapping).fillna(cleaned_df[col_name])

            elif action_type == "handle_ids":
                if not isinstance(details, list): continue
                for col in details:
                    if col in cleaned_df.columns:
                        print(f"    - Standardizing ID format for column '{col}'")
                        cleaned_df[col] = cleaned_df[col].astype(str).str.extract(r'([a-zA-Z0-9-._]+)')[0].astype(str)

            elif action_type == "unify_format":
                print("    - Replacing ['-', 'NA', '', ' '] with NaN globally.")
                cleaned_df.replace(['-', 'NA', '', ' '], np.nan, inplace=True)
            
            elif action_type == "standardize_text":
                print("    - Applying lowercase and stripping whitespace to all text columns.")
                for col in cleaned_df.select_dtypes(include=['object']).columns:
                    cleaned_df[col] = cleaned_df[col].astype(str).str.lower().str.strip()
            
            elif action_type == "impute_missing_values":
                print("    - Searching for columns to impute...")
                for col in cleaned_df.columns:
                    if cleaned_df[col].isnull().any():
                        dtype = cleaned_df[col].dtype
                        if pd.api.types.is_numeric_dtype(dtype):
                            impute_value = cleaned_df[col].median()
                            print(f"      - Imputing numeric column '{col}' with median value ({impute_value})")
                            cleaned_df[col].fillna(impute_value, inplace=True)
                        elif pd.api.types.is_object_dtype(dtype):
                            mode_val = cleaned_df[col].mode()
                            if not mode_val.empty:
                                impute_value = mode_val[0]
                                print(f"      - Imputing categorical column '{col}' with mode value ('{impute_value}')")
                                cleaned_df[col].fillna(impute_value, inplace=True)
                        
                        # --- ENHANCEMENT: Handle NaT values in datetime columns ---
                        elif pd.api.types.is_datetime64_any_dtype(dtype):
                            mode_val = cleaned_df[col].mode()
                            if not mode_val.empty:
                                impute_value = mode_val[0]
                                print(f"      - Imputing datetime column '{col}' with mode value ('{impute_value}')")
                                cleaned_df[col].fillna(impute_value, inplace=True)


            elif action_type == "handle_dates":
                if not isinstance(details, list): continue
                for col in details:
                    if col in cleaned_df.columns:
                        print(f"    - Converting column '{col}' to datetime format.")
                        cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
            
            elif action_type == "validate_relationships":
                if isinstance(details, dict) and "start_date_col" in details and "end_date_col" in details:
                    start_col, end_col = details["start_date_col"], details["end_date_col"]
                    if start_col in cleaned_df.columns and end_col in cleaned_df.columns:
                        print(f"    - Validating relationship: '{start_col}' must be before '{end_col}'")
                        original_rows = len(cleaned_df)
                        cleaned_df.drop(cleaned_df[cleaned_df[start_col] > cleaned_df[end_col]].index, inplace=True)
                        rows_dropped = original_rows - len(cleaned_df)
                        if rows_dropped > 0:
                            print(f"      - Dropped {rows_dropped} rows with invalid date logic.")


            elif action_type == "handle_numeric_values":
                if not isinstance(details, list): continue
                for col in details:
                    if col in cleaned_df.columns and pd.api.types.is_numeric_dtype(cleaned_df[col]):
                        print(f"    - Handling bad outliers in numeric column '{col}'")
                        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                        Q1, Q3 = cleaned_df[col].quantile(0.25), cleaned_df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound, upper_bound = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
                        cleaned_df.loc[(cleaned_df[col] < lower_bound) | (cleaned_df[col] > upper_bound), col] = np.nan
            
            elif action_type == "remove_duplicates":
                original_rows = len(cleaned_df)
                cleaned_df.drop_duplicates(inplace=True)
                rows_dropped = original_rows - len(cleaned_df)
                if rows_dropped > 0:
                    print(f"    - Dropped {rows_dropped} duplicate rows.")
                else:
                    print("    - No duplicate rows found.")


            elif action_type == "handle_missing_values":
                if not isinstance(details, list): continue
                valid_columns = [col for col in details if col in cleaned_df.columns]
                if valid_columns:
                    print(f"    - Dropping rows with nulls in critical columns: {valid_columns}")
                    original_rows = len(cleaned_df)
                    cleaned_df.dropna(subset=valid_columns, inplace=True)
                    rows_dropped = original_rows - len(cleaned_df)
                    if rows_dropped > 0:
                        print(f"      - Dropped {rows_dropped} rows.")

            
        print("✅ cleaning plan executed successfully.")
        return {"dataframe": cleaned_df}

    except Exception as e:
        print(f"❌ Error during cleaning plan execution: {e}")
        return {"dataframe": df}