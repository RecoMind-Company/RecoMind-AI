import pandas as pd
import numpy as np
import re
from auto_analyst.graph.state import GraphState
from auto_analyst.core.config import llm_model
from auto_analyst.utils.json_parser import extract_and_parse_json

# --- Node Functions --- (Copied from your code)

def data_cleaning_advisor(state: GraphState):
    """
    Asks the LLM to generate a JSON cleaning plan based on a data sample.
    """
    print("---GENERATING CLEANING PLAN---")
    df = state.get("dataframe")

    if df is None:
        print("❌ No DataFrame found in state. Skipping advisor.")
        return {"cleaning_plan": None}
    
    sample_size = min(30, len(df))
    sample_df = df.sample(n=sample_size, random_state=42)
    
    prompt = f"""
    You are a data cleaning expert. Your task is to analyze a sample of a DataFrame and recommend a list of cleaning actions.
    Your response must be ONLY a valid JSON object. The JSON should be a list of objects, where each object represents a cleaning action.
    
    Each action object must have two keys:
    - "action": A string representing the type of cleaning operation. Possible values are: "remove_duplicates", "drop_column", "handle_ids", "unify_format", "standardize_text", "standardize_text_complex", "handle_dates", "handle_numeric_values", "validate_relationships", "impute_missing_values".
    - "details": A string providing the name of the column(s) and any specific instructions for the action.

    Do not recommend dropping columns that contain constant values or have a high percentage of nulls; those are handled separately. Focus on logical cleaning tasks.
    
    Example JSON response:
    [
        {{
            "action": "drop_column",
            "details": "Drop redundant columns like 'SalesOrderID.1' and 'ModifiedDate.1'."
        }},
        {{
            "action": "handle_ids",
            "details": "Ensure 'SalesOrderNumber' and 'ProductID' are treated as unique identifiers by removing non-numeric characters and converting to string."
        }},
        {{
            "action": "handle_dates",
            "details": "Convert columns 'OrderDate', 'DueDate', 'ShipDate' to datetime objects."
        }},
        {{
            "action": "validate_relationships",
            "details": "Ensure 'OrderDate' is before 'ShipDate' to maintain logical consistency."
        }},
        {{
            "action": "impute_missing_values",
            "details": "Fill missing values in numeric columns like 'OrganizationLevel' with the median."
        }}
    ]

    Do not return any text or explanations outside the JSON object.
    Here is a sample of the DataFrame in CSV format ({sample_size} random rows):
    {sample_df.to_csv(index=False)}
    """
    
    response = llm_model.invoke(prompt)
    
    cleaning_plan = extract_and_parse_json(response.content)
    
    if cleaning_plan:
        print("✅ Cleaning plan generated successfully.")
        return {"cleaning_plan": cleaning_plan}
    else:
        print("❌ Failed to generate or parse the cleaning plan.")
        return {"cleaning_plan": None}

def data_cleaning_executor(state: GraphState):
    """
    Executes the cleaning plan on the entire DataFrame.
    """
    print("---EXECUTING CLEANING PLAN---")
    df = state.get("dataframe")
    cleaning_plan = state.get("cleaning_plan")

    if df is None or cleaning_plan is None:
        print("❌ Missing DataFrame or cleaning plan. Skipping executor.")
        return {"dataframe": None}
    
    cleaned_df = df.copy()

    # NEW: Check for and remove duplicate column names to prevent ambiguity errors
    # This keeps the first occurrence of each column
    if len(cleaned_df.columns) != len(set(cleaned_df.columns)):
        print("⚠️ Duplicate column names detected. Removing duplicates (keeping first occurrence).")
        cleaned_df = cleaned_df.loc[:, ~cleaned_df.columns.duplicated()]

    print("---Executing Automatic Cleaning Rules---")
    cols_to_drop = []
    for col in cleaned_df.columns:
        # NEW: Ensure col is a string (single column name)
        if not isinstance(col, str):
            print(f"❌ Skipping invalid column name: {col} (not a string)")
            continue
        
        # The original check, now safe since no duplicates
        unique_count = cleaned_df[col].nunique(dropna=False)
        if unique_count <= 1:
            print(f"     - Dropping column '{col}' due to constant values (unique: {unique_count}).")
            cols_to_drop.append(col)
        elif cleaned_df[col].isnull().mean() > 0.40:
            print(f"     - Dropping column '{col}' due to high percentage of missing values (>40%).")
            cols_to_drop.append(col)
    
    if cols_to_drop:
        cleaned_df.drop(columns=cols_to_drop, inplace=True)

    TEXT_MAPPING = {
        'ny': 'new york',
        'alex': 'alexandria',
    }

    try:
        for action in cleaning_plan:
            action_type = action.get("action")
            details = action.get("details")

            if action_type == "drop_column":
                print(f"     - Dropping column: {details}")
                columns_to_drop = re.findall(r"['\"](.*?)['\"]", details)
                for col in columns_to_drop:
                    if col in cleaned_df.columns:
                        cleaned_df.drop(col, axis=1, inplace=True)
            
            elif action_type == "handle_ids":
                print(f"     - Handling ID columns: {details}")
                for col in [c.strip().replace("'", "") for c in re.findall(r"'([^']*)'", details)]:
                    if col in cleaned_df.columns:
                        cleaned_df[col] = cleaned_df[col].astype(str).str.extract('(\d+)').astype(str)

            elif action_type == "unify_format":
                print(f"     - Unifying format and handling hidden nulls: {details}")
                cleaned_df.replace(['-', 'NA', '', ' '], np.nan, inplace=True)
            
            elif action_type == "standardize_text":
                print(f"     - Standardizing text: {details}")
                for col in cleaned_df.columns:
                    if pd.api.types.is_object_dtype(cleaned_df[col]):
                        cleaned_df[col] = cleaned_df[col].astype(str).str.lower().str.strip()

            elif action_type == "standardize_text_complex":
                print(f"     - Complex text standardization: {details}")
                for col in cleaned_df.columns:
                    if pd.api.types.is_object_dtype(cleaned_df[col]):
                        cleaned_df[col] = cleaned_df[col].astype(str).str.lower().str.replace(' ', '').map(TEXT_MAPPING).fillna(cleaned_df[col])

            elif action_type == "impute_missing_values":
                print(f"     - Imputing missing values: {details}")
                for col in cleaned_df.columns:
                    if cleaned_df[col].isnull().any():
                        if pd.api.types.is_numeric_dtype(cleaned_df[col]):
                            cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
                        elif pd.api.types.is_object_dtype(cleaned_df[col]):
                            mode_val = cleaned_df[col].mode()
                            if not mode_val.empty:
                                cleaned_df[col] = cleaned_df[col].fillna(mode_val[0])

            elif action_type == "handle_dates":
                print(f"     - Handling dates: {details}")
                for col in [c.strip().replace("'", "") for c in re.findall(r"'([^']*)'", details)]:
                    if col in cleaned_df.columns:
                        cleaned_df[col] = pd.to_datetime(cleaned_df[col], errors='coerce')
            
            elif action_type == "validate_relationships":
                print(f"     - Validating logical relationships: {details}")
                if 'OrderDate' in cleaned_df.columns and 'ShipDate' in cleaned_df.columns:
                    cleaned_df.drop(cleaned_df[cleaned_df['OrderDate'] > cleaned_df['ShipDate']].index, inplace=True)

            elif action_type == "handle_numeric_values":
                print(f"     - Handling numeric values: {details}")
                numerical_cols_from_plan = [col.strip().replace("'", "") for col in re.findall(r"'([^']*)'", details)]
                for col in numerical_cols_from_plan:
                    if col in cleaned_df.columns:
                        cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce')
                        cleaned_df.loc[cleaned_df[col] < 0, col] = np.nan
                        Q1 = cleaned_df[col].quantile(0.25)
                        Q3 = cleaned_df[col].quantile(0.75)
                        IQR = Q3 - Q1
                        lower_bound = Q1 - 1.5 * IQR
                        upper_bound = Q3 + 1.5 * IQR
                        cleaned_df.loc[(cleaned_df[col] < lower_bound) | (cleaned_df[col] > upper_bound), col] = np.nan
            
            elif action_type == "remove_duplicates":
                print(f"     - Removing duplicates: {details}")
                cleaned_df.drop_duplicates(inplace=True)

            elif action_type == "handle_missing_values":
                print(f"     - Handling missing values: {details}")
                cleaned_df.dropna(subset=['CustomerID', 'SalesOrderID'], inplace=True)
            
        print("✅ Cleaning plan executed successfully.")
        return {"dataframe": cleaned_df}

    except Exception as e:
        print(f"❌ Error during execution: {e}")
        return {"dataframe": None}