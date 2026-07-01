"""
Pydantic Response Models
========================
API output models
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AsyncTaskResponse(BaseModel):
    """Response for async task submission (Celery)"""

    task_id: str = Field(..., description="Celery Task ID")
    status: str = Field(default="pending", description="Task status")
    message: str = Field(..., description="Informational message")


class TaskStatusResponse(BaseModel):
    """Response for checking async task status"""

    task_id: str = Field(..., description="Celery Task ID")
    status: str = Field(..., description="Task status")
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    result: Optional[Any] = Field(None, description="Final result")
    error: Optional[str] = Field(None, description="Error message if any")


class ErrorResponse(BaseModel):
    """Error message model"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional details")


class CompanyInfo(BaseModel):
    """Company information retrieved from the .NET API"""

    name: str = Field(..., description="Company name")
    industry: str = Field(..., description="Industry sector")
    size: str = Field(..., description="Company size")
    description: str = Field(default="", description="Company description")
    country: str = Field(default="", description="Company country")


class PrecedentSummary(BaseModel):
    """Summary of precedent analysis"""

    precedent_exists: bool = Field(..., description="Whether precedents were found")
    cases_analyzed: int = Field(..., description="Number of cases analyzed")
    context_match_level: str = Field(..., description="Match level: High, Medium, or Low")
    confidence_score: float = Field(..., description="Confidence score (0-100)")


class PrecedentOutcomes(BaseModel):
    """Outcome distribution of precedent cases"""

    success: int = Field(default=0, description="Number of success cases")
    partial_success: int = Field(default=0, description="Number of partial success cases")
    failure: int = Field(default=0, description="Number of failure cases")


class PrecedentCase(BaseModel):
    """A single precedent case"""

    company: str = Field(..., description="Company name")
    outcome: str = Field(..., description="Outcome: Success, Failure, or Partial")
    what_happened: str = Field(..., description="What happened in this case")
    reason: str = Field(..., description="Why it succeeded or failed")


class PrecedentResult(BaseModel):
    """Full precedent engine result"""

    precedent_summary: PrecedentSummary = Field(..., description="Summary of precedent analysis")
    outcomes: PrecedentOutcomes = Field(..., description="Outcome distribution")
    what_worked: List[str] = Field(default_factory=list, description="Patterns that worked")
    what_failed: List[str] = Field(default_factory=list, description="Patterns that failed")
    key_insights: Dict[str, List[str]] = Field(
        default_factory=dict, description="Key insights with success and failure factors"
    )
    cases: List[PrecedentCase] = Field(default_factory=list, description="List of precedent cases")


class ResourceResourceResult(BaseModel):
    """Resource analysis result for a single category"""

    is_sufficient: bool = Field(..., description="Whether resources are sufficient")
    status: str = Field(..., description="Status label")
    why: List[str] = Field(default_factory=list, description="Explanation bullet points")
    key_metrics: Optional[Any] = Field(None, description="Key metrics (dict or string)")


class OverallVerdict(BaseModel):
    """Overall execution verdict"""

    can_execute_plan: bool = Field(..., description="Whether the plan can be executed")
    blocking_factors: List[str] = Field(default_factory=list, description="Blocking factors if any")


class ResourceSimulationResult(BaseModel):
    """Full resource simulation result"""

    financial_resources: ResourceResourceResult = Field(..., description="Financial resources analysis")
    human_resources: ResourceResourceResult = Field(..., description="Human resources analysis")
    operational_resources: ResourceResourceResult = Field(..., description="Operational resources analysis")
    overall_execution_verdict: OverallVerdict = Field(..., description="Overall execution verdict")


class TrendSummary(BaseModel):
    """Market trend summary"""

    market_direction: str = Field(..., description="Growing / Declining / Stable / Volatile")
    growth_rate: str = Field(..., description="Growth rate or Unknown")
    trend_confidence: int = Field(..., description="Confidence score (0-100)")
    timing_assessment: str = Field(..., description="Timing recommendation")


class LocationInsights(BaseModel):
    """Location-specific market insights"""

    location: str = Field(..., description="Target location")
    market_maturity: str = Field(..., description="Emerging / Growing / Mature / Saturated")
    competition_level: str = Field(..., description="Low / Medium / High")


class MarketTrendResult(BaseModel):
    """Full market trend engine result"""

    trend_summary: TrendSummary = Field(..., description="Trend summary")
    key_trends: List[str] = Field(default_factory=list, description="Key market trends")
    opportunities: List[str] = Field(default_factory=list, description="Market opportunities")
    risks: List[str] = Field(default_factory=list, description="Market risks")
    location_insights: LocationInsights = Field(..., description="Location-specific insights")
    recommendation: str = Field(default="", description="Market timing recommendation")


class ValidationReport(BaseModel):
    """Final comprehensive validation report from the report generation agent"""

    executive_summary: str = Field(..., description="2-3 sentence summary")
    validation_decision: str = Field(..., description="Favorable / Conditional / Not Recommended / Risky")
    confidence_score: int = Field(..., description="Overall confidence score (0-100)")
    key_findings: Dict[str, Any] = Field(..., description="Key findings from each engine")
    recommendations: List[str] = Field(default_factory=list, description="Actionable recommendations")
    risk_factors: List[str] = Field(default_factory=list, description="Top risk factors")
    next_steps: List[str] = Field(default_factory=list, description="Clear next steps")


class StructuredPlan(BaseModel):
    """Structured plan output from the strategy structuring agent"""

    precedent_engine_input: Dict[str, Any] = Field(..., description="Input for precedent engine")
    resource_simulator_input: Dict[str, Any] = Field(..., description="Input for resource simulator")


class ValidationResponse(BaseModel):
    """
    Full validation response returned to the .NET backend.
    Contains all engine outputs and the final validation report.
    """

    status: str = Field(default="completed", description="Validation status")
    company_info: CompanyInfo = Field(..., description="Company information used for validation")
    structured_plan: StructuredPlan = Field(..., description="Structured plan from strategy structuring")
    precedent_result: PrecedentResult = Field(..., description="Precedent engine result")
    resource_simulation_result: ResourceSimulationResult = Field(
        ..., description="Resource simulator result"
    )
    market_trend_result: MarketTrendResult = Field(..., description="Market trend engine result")
    validation_report: ValidationReport = Field(..., description="Final validation report")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "completed",
                "company_info": {
                    "name": "Example Company",
                    "industry": "Retail",
                    "size": "Medium",
                    "description": "Retail company",
                    "country": "Egypt",
                },
                "structured_plan": {
                    "precedent_engine_input": {},
                    "resource_simulator_input": {},
                },
                "precedent_result": {
                    "precedent_summary": {
                        "precedent_exists": True,
                        "cases_analyzed": 5,
                        "context_match_level": "Medium",
                        "confidence_score": 65.5,
                    },
                    "outcomes": {"success": 3, "partial_success": 1, "failure": 1},
                    "what_worked": ["market research"],
                    "what_failed": ["rushed timeline"],
                    "key_insights": {},
                    "cases": [],
                },
                "resource_simulation_result": {
                    "financial_resources": {
                        "is_sufficient": False,
                        "status": "Insufficient",
                        "why": [],
                        "key_metrics": None,
                    },
                    "human_resources": {
                        "is_sufficient": False,
                        "status": "Insufficient",
                        "why": [],
                        "key_metrics": None,
                    },
                    "operational_resources": {
                        "is_sufficient": False,
                        "status": "Not ready",
                        "why": [],
                    },
                    "overall_execution_verdict": {
                        "can_execute_plan": False,
                        "blocking_factors": ["Insufficient resources"],
                    },
                },
                "market_trend_result": {
                    "trend_summary": {
                        "market_direction": "Growing",
                        "growth_rate": "8%",
                        "trend_confidence": 75,
                        "timing_assessment": "Favorable for expansion",
                    },
                    "key_trends": ["Digital transformation"],
                    "opportunities": ["Growing demand"],
                    "risks": ["Increasing competition"],
                    "location_insights": {
                        "location": "Cairo",
                        "market_maturity": "Growing",
                        "competition_level": "Medium",
                    },
                    "recommendation": "Proceed with careful planning",
                },
                "validation_report": {
                    "executive_summary": "The plan shows potential but has resource constraints.",
                    "validation_decision": "Conditional",
                    "confidence_score": 70,
                    "key_findings": {},
                    "recommendations": ["Address resource gaps first"],
                    "risk_factors": ["Insufficient runway"],
                    "next_steps": ["Secure additional funding"],
                },
            }
        }
