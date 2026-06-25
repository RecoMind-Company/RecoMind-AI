
"""
processor.py
============
Responsible for:
  1. Building the User Prompt from both inputs (plan + company data)
  2. Cleaning the raw output and converting it to a dict
  3. Validating the structure of the output JSON (Schema Validation)
"""

import json
import re
from typing import Any

# ── Output JSON Schema (Expected Structure) ───────────────────────────────────
REQUIRED_KEYS = {
    "financial_resources",
    "human_resources",
    "operational_resources",
    "overall_execution_verdict",
}


# ── 1. Prompt Builder ─────────────────────────────────────────────────────────
def build_user_prompt(plan_input: str, company_resources: str) -> str:
    """
    Merges both system inputs into a single structured message to send to the LLM.

    Args:
        plan_input:        Text or JSON describing the plan and its requirements
        company_resources: Text or JSON describing the company's current resources

    Returns:
        str: The ready-to-send user prompt
    """
    schema = json.dumps(_get_output_schema(), ensure_ascii=False, indent=2)

    return f"""Here is the proposed strategic plan and its requirements:
---
{plan_input}
---

Here is the company's current available resources data:
---
{company_resources}
---

Perform a precise simulation and comparison, then output the final Readiness Report \
as JSON following this exact structure with no text outside it and no backticks:
{schema}"""


# ── 2. Output Parser ──────────────────────────────────────────────────────────
def parse_output(raw_text: str) -> dict[str, Any]:
    """
    Converts the raw string from the LLM into a clean dict.

    Raises:
        ValueError: If JSON parsing fails
    """
    clean = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`").strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM: {e}\nRaw text:\n{raw_text}")


# ── 3. Schema Validator ───────────────────────────────────────────────────────
def validate_output(data: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validates that the JSON contains all required fields.

    Returns:
        (is_valid: bool, errors: list[str])
    """
    errors: list[str] = []

    # Check top-level keys
    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        errors.append(f"Missing top-level keys: {missing}")

    # Check financial_resources
    fin = data.get("financial_resources", {})
    for key in ["is_sufficient", "status", "why", "key_metrics"]:
        if key not in fin:
            errors.append(f"financial_resources.{key} missing")

    # Check human_resources
    human = data.get("human_resources", {})
    for key in ["is_sufficient", "status", "why", "key_metrics"]:
        if key not in human:
            errors.append(f"human_resources.{key} missing")

    # Check operational_resources
    ops = data.get("operational_resources", {})
    for key in ["is_sufficient", "status", "why"]:
        if key not in ops:
            errors.append(f"operational_resources.{key} missing")

    # Check overall_execution_verdict
    verdict = data.get("overall_execution_verdict", {})
    if "can_execute_plan" not in verdict:
        errors.append("overall_execution_verdict.can_execute_plan missing")

    return len(errors) == 0, errors


# ── Internal: Output Schema Template ─────────────────────────────────────────
def _get_output_schema() -> dict:
    return {
        "financial_resources": {
            "is_sufficient": "true/false",
            "status": "Sufficient / Insufficient for full execution",
            "why": [
                "Projected burn rate increases by X%",
                "Cash runway drops to Y months",
                "Minimum safe runway is 9 months"
            ],
            "key_metrics": {
                "cash_balance": 0,
                "runway_after_plan_months": 0
            }
        },
        "human_resources": {
            "is_sufficient": "true/false",
            "status": "Sufficient with phased hiring / Insufficient",
            "why": [
                "Current team can absorb initial workload",
                "Only critical hires are required at later stages"
            ],
            "key_metrics": {
                "current_employees": 0,
                "required_new_hires": 0
            }
        },
        "operational_resources": {
            "is_sufficient": "true/false",
            "status": "Partially ready / Ready / Not ready",
            "why": [
                "New physical location required",
                "Inventory processes not yet scalable"
            ]
        },
        "overall_execution_verdict": {
            "can_execute_plan": "true/false",
            "blocking_factors": ["list of blocking reasons if any"]
        }
    }