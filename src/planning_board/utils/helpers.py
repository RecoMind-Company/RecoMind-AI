"""
Utility Helpers
"""

from typing import Any, Dict, List


def clean_text(text: str) -> str:
    """Clean text from extra whitespace"""
    return " ".join(text.split())


def safe_get(data: Dict, *keys, default: Any = None) -> Any:
    """Safely extract value from nested dict"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
