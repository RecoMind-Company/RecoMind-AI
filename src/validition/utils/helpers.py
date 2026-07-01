"""
Utility Helpers
================
Generic helper functions
"""

import json
import re
from typing import Any, Dict, List


def safe_json_load(raw: str) -> Any:
    """
    Robust JSON parsing with fallbacks for common LLM output issues.
    Handles markdown fences, trailing commas, and partial JSON extraction.
    """
    if not raw:
        return []

    try:
        return json.loads(raw)
    except Exception:
        pass

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        parts = cleaned.split("```")
        cleaned = parts[1] if len(parts) > 1 else cleaned
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    fixed = re.sub(r",\s*}", "}", cleaned)
    fixed = re.sub(r",\s*]", "]", fixed)
    try:
        return json.loads(fixed)
    except Exception:
        pass

    match = re.search(r"\[.*\]", fixed, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    return []


def clean_llm_output(raw: str) -> str:
    """Strip markdown fences and backticks from LLM output"""
    return re.sub(r"```(?:json)?", "", raw).strip().strip("`").strip()


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of the given size"""
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def safe_get(data: Dict[str, Any], *keys, default: Any = None) -> Any:
    """Safely navigate nested dicts"""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current if current is not None else default
