import json
import re
from typing import Optional, List, Dict

# --- Helper Function for Robust JSON Parsing --- (Copied from your code)
def extract_and_parse_json(llm_content: str) -> Optional[List[Dict]]:
    """
    Extracts a JSON list from the LLM's response, handling markdown code blocks.
    """
    # 1. First, try to find a JSON block inside ```json ... ```
    match = re.search(r'```json\s*(\[.*?\])\s*```', llm_content, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # 2. If not found, try to find any list [...] in the content
        match = re.search(r'(\[.*\])', llm_content, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            # 3. If still no list found, the content itself might be the JSON
            json_str = llm_content

    try:
        # 4. Try to parse the extracted string
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        # 5. If parsing fails, print the error and the problematic content
        print(f"❌ JSON decoding failed: {e}")
        print(f"--- LLM Response that caused the error ---")
        print(llm_content)
        print("-----------------------------------------")
        return None