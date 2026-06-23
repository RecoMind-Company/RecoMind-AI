"""
Utility Helpers
"""

from typing import Any, Dict, List


def clean_text(text: str) -> str:
    """تنظيف النص من المسافات الزائدة"""
    return " ".join(text.split())


def safe_get(data: Dict, *keys, default: Any = None) -> Any:
    """استخراج قيمة من dict متداخل بأمان"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """تقسيم قائمة لـ chunks"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
