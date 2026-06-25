
"""
schemas.py
==========
Pydantic models for input validation and output structure
of the Resource Simulator system.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# ─────────────────────────────────────────
#  ENUMS
# ─────────────────────────────────────────

class StrategyType(str, Enum):
    EXPANSION          = "Expansion"
    RESTRUCTURING      = "Restructuring"
    NEW_PRODUCT_LAUNCH = "New Product Launch"
    MARKET_ENTRY       = "Market Entry"
    COST_REDUCTION     = "Cost Reduction"


class ActionType(str, Enum):
    OPEN_BRANCH         = "Open Branch"
    HIRING              = "Hiring"
    MARKETING_CAMPAIGN  = "Marketing Campaign"
    PRODUCT_DEVELOPMENT = "Product Development"
    ACQUISITION         = "Acquire Company"
    ONLINE_CHANNEL      = "Open Online Channel"


class SupplyChainStatus(str, Enum):
    READY     = "ready"
    PARTIAL   = "partial"
    NOT_READY = "not_ready"


class RunwayStatus(str, Enum):
    SAFE     = "Safe"
    LOW      = "Low"
    CRITICAL = "Critical"


# ─────────────────────────────────────────
#  INPUT MODELS
# ─────────────────────────────────────────

class PlanRequirements(BaseModel):
    """Requirements of the proposed plan"""
    setup_cost:                float = Field(..., description="Setup cost in EGP")
    monthly_salaries_increase: float = Field(..., description="Required monthly salary increase")
    required_new_hires:        int   = Field(..., description="Number of new hires required")
    marketing_budget:          float = Field(0.0, description="Marketing budget")
    needs_physical_location:   bool  = Field(True, description="Does the plan require a new physical location?")


class PlanInput(BaseModel):
    """The complete strategic plan"""
    strategy_type: StrategyType
    industry:      str
    action_type:   ActionType
    location:      str
    time_horizon:  str
    requirements:  PlanRequirements


class FinancialSnapshot(BaseModel):
    """Current financial status of the company"""
    cash_available:        float = Field(..., description="Currently available cash in EGP")
    current_monthly_burn:  float = Field(..., description="Current monthly burn rate")
    monthly_revenue:       float = Field(0.0, description="Monthly revenue")
    profit_margin_percent: float = Field(0.0, description="Operating profit margin %")


class HumanResourcesSnapshot(BaseModel):
    """Current human resources of the company"""
    total_employees:              int   = Field(..., description="Total number of employees")
    capacity_utilization_percent: float = Field(..., description="Current utilization rate %")
    available_sales_staff:        int   = Field(0,     description="Available sales staff")
    has_funded_hiring_plan:       bool  = Field(False, description="Is there a funded hiring plan?")


class OperationalSnapshot(BaseModel):
    """Current operational assets of the company"""
    current_locations:              str                = Field(..., description="Current branches and offices")
    has_presence_in_target_location: bool              = Field(False, description="Does the company have presence in the target location?")
    supply_chain_readiness:          SupplyChainStatus = Field(SupplyChainStatus.PARTIAL)


class CompanyResourcesSnapshot(BaseModel):
    """Complete company resources snapshot"""
    financial:   FinancialSnapshot
    human:       HumanResourcesSnapshot
    operational: OperationalSnapshot


class SimulatorRequest(BaseModel):
    """Full request to the simulator"""
    plan:              PlanInput
    company_resources: CompanyResourcesSnapshot


# ─────────────────────────────────────────
#  OUTPUT MODELS
# ─────────────────────────────────────────

class FinancialKeyMetrics(BaseModel):
    cash_balance:              float
    runway_after_plan_months:  float


class FinancialResourcesResult(BaseModel):
    is_sufficient:  bool
    status:         str
    why:            List[str]
    key_metrics:    FinancialKeyMetrics


class HumanKeyMetrics(BaseModel):
    current_employees:  int
    required_new_hires: int


class HumanResourcesResult(BaseModel):
    is_sufficient: bool
    status:        str
    why:           List[str]
    key_metrics:   HumanKeyMetrics


class OperationalResourcesResult(BaseModel):
    is_sufficient:    bool
    status:           str
    why:              List[str]


class OverallVerdict(BaseModel):
    can_execute_plan:  bool
    blocking_factors:  List[str]


class SimulatorResponse(BaseModel):
    """Complete Readiness Report"""
    financial_resources:       FinancialResourcesResult
    human_resources:           HumanResourcesResult
    operational_resources:     OperationalResourcesResult
    overall_execution_verdict: OverallVerdict