"""JSON parsing utility for extracting structured data from LLM responses."""

import json
import logging
import re
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


def extract_and_parse_json(llm_content: str) -> Optional[List[Dict[str, Any]]]:
    """
    Extracts a JSON list from an LLM response string, handling markdown code blocks.
    
    Args:
        llm_content: Raw string response from the LLM.
        
    Returns:
        Parsed JSON list of dictionaries, or None if extraction/parsing fails.
    """
    if not llm_content:
        logger.warning("Empty LLM content provided for JSON parsing.")
        return None

    # 1. First, try to find a JSON block inside ```json ... ```
    match = re.search(r"```json\s*(\[.*?\])\s*```", llm_content, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # 2. If not found, try to find any list [...] in the content
        match = re.search(r"(\[.*\])", llm_content, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            # 3. Fallback: content itself might be raw JSON
            json_str = llm_content

    try:
        parsed = json.loads(json_str)
        if isinstance(parsed, list):
            return parsed
        logger.warning("Parsed JSON is not a list structure.")
        return None
    except json.JSONDecodeError as err:
        logger.error(f"JSON decoding failed: {err}")
        logger.debug(f"Content that caused JSONDecodeError: {llm_content}")
        return None
