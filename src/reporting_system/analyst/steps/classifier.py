"""Data topic classification step for LangGraph workflow."""

import logging
from typing import List, Dict, Any
from analyst.state import GraphState
from config.database import get_langgraph_llm

logger = logging.getLogger(__name__)


def classify_data_with_llm(columns: List[str], user_request: str) -> str:
    """Uses LLM to classify dataset topic based on column names and user request."""
    llm = get_langgraph_llm()
    system_prompt = (
        "You are an expert data classifier. Your task is to analyze a dataset's column names "
        "along with the user's original request, and determine the primary topic of the dataset. "
        "The user's request provides crucial context for determining the true intent if columns are ambiguous. "
        "You must respond with a single, lowercase word from the following list: "
        "'employees', 'sales', 'customers', 'products', 'marketing', 'finance', 'logistics', 'support', 'unknown'."
    )
    user_prompt = f"""
    Based on the user's request and the list of column names, what is the main topic of the data?
    
    User Request: "{user_request}"
    Column Names: {', '.join(columns)}
    
    Return ONLY one word from the allowed list, with no extra text, explanation, or punctuation.
    """
    response = llm.invoke(f"{system_prompt}\n\n{user_prompt}")
    return response.content.strip().lower()


def data_identifier(state: GraphState) -> Dict[str, Any]:
    """Identifies dataset topic from state DataFrame and user_request."""
    logger.info("--- STAGE 3.1: IDENTIFYING DATA TYPE ---")
    df = state.get("dataframe")
    user_request = state.get("user_request", "No specific request provided")

    if df is None or df.empty:
        logger.error("No DataFrame passed into state for analysis.")
        return {"data_type": "error", "dataframe": None}

    data_type = classify_data_with_llm(df.columns.tolist(), user_request)
    logger.info(f"Data successfully classified as '{data_type}'.")
    return {"data_type": data_type, "dataframe": df}
