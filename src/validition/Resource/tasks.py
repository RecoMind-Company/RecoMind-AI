
"""
tasks.py
========
Defines the Tasks that the simulation process passes through as clean dataclasses.
Each Task contains its own input + output, making the pipeline easily extensible.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing      import Any


# ── Base Task ─────────────────────────────────────────────────────────────────
@dataclass
class BaseTask:
    name:        str
    description: str
    status:      str = "pending"   # pending | running | done | failed
    error:       str = ""


# ── Task 1: Input Aggregation ─────────────────────────────────────────────────
@dataclass
class AggregationTask(BaseTask):
    """
    Aggregates the plan and company data into a unified structure
    ready to be sent to the LLM.
    """
    name:              str = "aggregation"
    description:       str = "Merge plan inputs and company resources"
    plan_input:        str = ""
    company_resources: str = ""
    combined_prompt:   str = ""


# ── Task 2: LLM Call ──────────────────────────────────────────────────────────
@dataclass
class SimulationTask(BaseTask):
    """
    Sends the prompt to the LLM and receives the raw response.
    """
    name:         str = "simulation"
    description:  str = "Run resource simulation via Claude"
    raw_response: str = ""


# ── Task 3: Output Parsing and Validation ─────────────────────────────────────
@dataclass
class ValidationTask(BaseTask):
    """
    Converts the raw response into a dict and validates the structure.
    """
    name:        str            = "validation"
    description: str            = "Parse and validate the output JSON"
    report:      dict[str, Any] = field(default_factory=dict)
    is_valid:    bool           = False
    errors:      list[str]      = field(default_factory=list)


# ── Task 4: Final Verdict ─────────────────────────────────────────────────────
@dataclass
class VerdictTask(BaseTask):
    """
    Extracts the overall verdict and prepares the final output.
    """
    name:             str            = "verdict"
    description:      str            = "Extract the final execution decision"
    can_execute_plan: bool           = False
    blocking_factors: list[str]      = field(default_factory=list)
    final_report:     dict[str, Any] = field(default_factory=dict)


# ── Pipeline Builder ──────────────────────────────────────────────────────────
def build_pipeline() -> list[BaseTask]:
    """Creates and returns the list of tasks in the correct order."""
    return [
        AggregationTask(),
        SimulationTask(),
        ValidationTask(),
        VerdictTask(),
    ]
