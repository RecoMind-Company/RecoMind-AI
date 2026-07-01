"""
Report Generation Agent - Service
"""
import asyncio
import json
from typing import Any, Dict

from crewai import Agent, Crew, LLM, Task
from loguru import logger

from core.config import settings
from utils.helpers import safe_json_load
from .prompts import AGENT_ROLE, AGENT_GOAL, AGENT_BACKSTORY, TASK_DESCRIPTION, OUTPUT_SCHEMA


class ReportGenerationService:
    """Service for generating a final comprehensive validation report."""

    def __init__(self):
        self._llm = LLM(
            model=f"groq/{settings.GROQ_MODEL}",
            api_key=settings.GROQ_API_KEY,
            temperature=0,
        )
        self._report_agent = Agent(
            role=AGENT_ROLE,
            goal=AGENT_GOAL,
            backstory=AGENT_BACKSTORY,
            llm=self._llm,
            allow_delegation=False,
        )

    async def generate(
        self,
        user_request: str,
        company_info: Dict[str, Any],
        structured_plan: Dict[str, Any],
        precedent_result: Dict[str, Any],
        resource_result: Dict[str, Any],
        market_trend_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        logger.info("Report generation: combining all engine outputs...")

        context = self._build_context(
            user_request, company_info, structured_plan,
            precedent_result, resource_result, market_trend_result,
        )

        task = Task(
            description=TASK_DESCRIPTION,
            expected_output="Raw JSON object with comprehensive validation report",
            agent=self._report_agent,
        )
        crew = Crew(tasks=[task], verbose=False)

        try:
            result = await asyncio.to_thread(
                crew.kickoff,
                inputs={
                    "context": context,
                    "schema": json.dumps(OUTPUT_SCHEMA, ensure_ascii=False, indent=2),
                },
            )
            parsed = safe_json_load(result.raw)

            if isinstance(parsed, dict):
                logger.info("Report generation: completed successfully")
                return parsed
            else:
                logger.warning("Report generation: unexpected output format, returning fallback")
                return self._fallback_report(
                    user_request, precedent_result, resource_result, market_trend_result
                )

        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            return self._fallback_report(
                user_request, precedent_result, resource_result, market_trend_result
            )

    @staticmethod
    def _build_context(
        user_request: str,
        company_info: Dict[str, Any],
        structured_plan: Dict[str, Any],
        precedent_result: Dict[str, Any],
        resource_result: Dict[str, Any],
        market_trend_result: Dict[str, Any],
    ) -> str:
        return f"""ORIGINAL USER REQUEST:
{user_request}

COMPANY INFORMATION:
{json.dumps(company_info, ensure_ascii=False, indent=2)}

STRUCTURED PLAN:
{json.dumps(structured_plan, ensure_ascii=False, indent=2)}

PRECEDENT ENGINE RESULTS:
{json.dumps(precedent_result, ensure_ascii=False, indent=2)}

RESOURCE SIMULATION RESULTS:
{json.dumps(resource_result, ensure_ascii=False, indent=2)}

MARKET TREND ANALYSIS:
{json.dumps(market_trend_result, ensure_ascii=False, indent=2)}"""

    @staticmethod
    def _fallback_report(
        user_request: str,
        precedent_result: Dict[str, Any],
        resource_result: Dict[str, Any],
        market_trend_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        resource_verdict = resource_result.get("overall_execution_verdict", {})
        precedent_summary = precedent_result.get("precedent_summary", {})
        trend_summary = market_trend_result.get("trend_summary", {})

        can_execute = resource_verdict.get("can_execute_plan", False)
        confidence = precedent_summary.get("confidence_score", 0)

        if can_execute and confidence > 50:
            decision = "Favorable"
        elif not can_execute:
            decision = "Not Recommended"
        else:
            decision = "Conditional"

        return {
            "executive_summary": f"Validation analysis for the proposed plan has been completed. "
            f"Based on resource assessment, precedent analysis, and market trends, "
            f"the recommendation is: {decision}.",
            "validation_decision": decision,
            "confidence_score": confidence,
            "key_findings": {
                "precedent_analysis": f"{precedent_summary.get('cases_analyzed', 0)} cases analyzed "
                f"with {confidence}% confidence.",
                "resource_assessment": resource_verdict.get("blocking_factors", []),
                "market_trends": trend_summary.get("timing_assessment", "Unknown"),
            },
            "recommendations": [
                "Review the detailed engine outputs for more information.",
                "Consider addressing blocking factors before proceeding." if not can_execute else
                "Proceed with careful monitoring of key metrics.",
            ],
            "risk_factors": resource_verdict.get("blocking_factors", []),
            "next_steps": [
                "Address identified blocking factors" if not can_execute else "Begin phased implementation",
                "Monitor market trends continuously",
                "Review resource allocation periodically",
            ],
        }


report_generation_service = ReportGenerationService()
