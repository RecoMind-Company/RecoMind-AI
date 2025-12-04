# utils/date_helpers.py
"""Date utilities for query processing."""

from datetime import datetime, timedelta


def get_date_context() -> str:
    """
    Generate date context string for relative date conversion.
    
    This helps the LLM convert relative dates like 'last year', 
    'last month' to actual values.
    """
    today = datetime.now()
    last_month = today.replace(day=1) - timedelta(days=1)
    last_week_end = today - timedelta(days=today.weekday() + 1)
    last_week_start = last_week_end - timedelta(days=6)
    
    return (
        f"Today is {today.strftime('%Y-%m-%d')}. "
        f"Current year: {today.year}. "
        f"Last year: {today.year - 1}. "
        f"Last month: {last_month.month}, year: {last_month.year}. "
        f"Yesterday: {(today - timedelta(days=1)).strftime('%Y-%m-%d')}. "
        f"Last week: {last_week_start.strftime('%Y-%m-%d')} to {last_week_end.strftime('%Y-%m-%d')}."
    )
