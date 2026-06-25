
"""
service.py
==========
Business Logic layer.
Runs the full resource simulation and returns the Readiness Report as a dict.

Used from agent.py (and directly from test.py for testing).
"""

from __future__ import annotations
import json
from typing import Any

from langchain_core.messages import SystemMessage, HumanMessage

from llm_config import get_llm
from RE.processor import build_user_prompt, parse_output, validate_output


# ── Fixed System Prompt ───────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a Strategic Resource Simulator AI.
Your sole task is to receive a proposed business plan and compare it against \
the company's current available resources (financial, human, and operational).

Strict analysis rules:
- Compare precisely between the plan's requirements and the actual figures in the company data.
- If current cash does not cover setup costs and salaries for a safe period (minimum 9 months), \
immediately flag financial resources as insufficient.
- If current employees are utilized at >= 85%, flag human resources as needing urgent hiring.
- If the plan requires a physical location the company does not have, flag operational resources as insufficient.
- The 'why' field must be a list of specific, explainable bullet points — not vague summaries.
- The 'key_metrics' field must contain real numbers extracted from the input data.
- Output the entire response as JSON matching exactly the required structure, \
with no text outside it and no backticks."""


# ── Main Service Function ─────────────────────────────────────────────────────
def run_simulation(plan_input: str, company_resources: str) -> dict[str, Any]:
    """
    Runs the full simulation and returns the Readiness Report.

    Args:
        plan_input:        Text/JSON describing the plan and its requirements
        company_resources: Text/JSON describing the company's current resources

    Returns:
        dict: The structured Readiness Report

    Raises:
        ValueError:   If JSON parsing or schema validation fails
        RuntimeError: If the LLM connection fails
    """
    llm         = get_llm()
    user_prompt = build_user_prompt(plan_input, company_resources)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    # ── Call the LLM ─────────────────────────────────────────────────────────
    try:
        response = llm.invoke(messages)
        raw_text = response.content
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Claude API: {e}") from e

    # ── Parse and Validate Output ─────────────────────────────────────────────
    result = parse_output(raw_text)

    is_valid, errors = validate_output(result)
    if not is_valid:
        raise ValueError("Output does not match required schema:\n" + "\n".join(errors))

    return result


# ── Pretty Print Helper ───────────────────────────────────────────────────────
def format_report(report: dict[str, Any]) -> str:
    """Converts the report to formatted JSON for display."""
    return json.dumps(report, ensure_ascii=False, indent=2)