"""
Internal Domain Entities
========================
Dataclass models for internal business logic
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PrimaryActionDetails:
    """Details of a primary action in the strategy"""

    location: str = ""
    channel: str = ""


@dataclass
class PrimaryAction:
    """Primary action extracted from user request"""

    action_type: str = ""
    details: PrimaryActionDetails = field(default_factory=PrimaryActionDetails)

    def to_dict(self) -> dict:
        return {
            "action_type": self.action_type,
            "details": {
                "location": self.details.location,
                "channel": self.details.channel,
            },
        }


@dataclass
class PrecedentEngineInput:
    """Input for the precedent engine"""

    strategy_type: str = ""
    decision_category: str = ""
    primary_action: PrimaryAction = field(default_factory=PrimaryAction)
    company_context: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "strategy_type": self.strategy_type,
            "decision_category": self.decision_category,
            "primary_action": self.primary_action.to_dict(),
            "company_context": self.company_context,
        }


@dataclass
class ActionItem:
    """An action item in the resource simulator input"""

    action_type: str = ""
    details: Optional[Dict[str, Any]] = None


@dataclass
class ResourceRequirements:
    """Resource requirements extracted from the plan"""

    financial: List[str] = field(default_factory=list)
    human: List[str] = field(default_factory=list)
    operational: List[str] = field(default_factory=list)


@dataclass
class ResourceSimulatorInput:
    """Input for the resource simulator"""

    all_actions: List[ActionItem] = field(default_factory=list)
    resource_requirements: ResourceRequirements = field(default_factory=ResourceRequirements)
    time_horizon: str = ""

    def to_dict(self) -> dict:
        return {
            "all_actions": [
                {"action_type": a.action_type, "details": a.details or {}} for a in self.all_actions
            ],
            "resource_requirements": {
                "financial": self.resource_requirements.financial,
                "human": self.resource_requirements.human,
                "operational": self.resource_requirements.operational,
            },
            "time_horizon": self.time_horizon,
        }


@dataclass
class StructuredPlan:
    """Structured plan from strategy structuring agent"""

    precedent_engine_input: PrecedentEngineInput = field(default_factory=PrecedentEngineInput)
    resource_simulator_input: ResourceSimulatorInput = field(default_factory=ResourceSimulatorInput)

    def to_dict(self) -> dict:
        return {
            "precedent_engine_input": self.precedent_engine_input.to_dict(),
            "resource_simulator_input": self.resource_simulator_input.to_dict(),
        }


@dataclass
class CompanyInfo:
    """Company information from the .NET API"""

    name: str = ""
    industry: str = ""
    size: str = ""
    description: str = ""
    country: str = ""


@dataclass
class PrecedentCase:
    """A single precedent case"""

    company: str = ""
    outcome: str = ""
    what_happened: str = ""
    reason: str = ""


@dataclass
class SearchResult:
    """A single search result"""

    title: str = ""
    snippet: str = ""
    link: str = ""
    source_tool: str = ""
