"""
Internal Pydantic Schemas
=========================
Used for CrewAI output_json parsing and LLM response validation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class PrimaryActionDetails(BaseModel):
    location: str = ""
    channel: str = ""


class PrimaryAction(BaseModel):
    action_type: str = ""
    details: PrimaryActionDetails = PrimaryActionDetails()


class PrecedentEngineInputSchema(BaseModel):
    strategy_type: str = ""
    decision_category: str = ""
    primary_action: PrimaryAction = PrimaryAction()


class ActionItemSchema(BaseModel):
    action_type: str = ""
    details: Optional[Dict[str, Any]] = None


class ResourceRequirementsSchema(BaseModel):
    financial: List[str] = []
    human: List[str] = []
    operational: List[str] = []


class ResourceSimulatorInputSchema(BaseModel):
    all_actions: List[ActionItemSchema] = []
    resource_requirements: ResourceRequirementsSchema = ResourceRequirementsSchema()
    time_horizon: str = ""


class StrategyOutput(BaseModel):
    """Top-level schema for the strategy structuring agent output."""

    precedent_engine_input: PrecedentEngineInputSchema
    resource_simulator_input: ResourceSimulatorInputSchema
