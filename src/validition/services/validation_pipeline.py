"""
Validation Pipeline Service
===========================
Main orchestrator for the validation feature.
Runs the full pipeline:
  Phase 1: Strategy structuring + company info + reports (concurrent)
  Phase 2: Precedent engine + resource simulator + market trend engine (concurrent)
  Phase 3: Report generation (combines all outputs)
"""

import asyncio
from typing import Any, Dict

from loguru import logger

from clients.company_client import company_client
from clients.reports_client import reports_client
from models.entities import CompanyInfo, StructuredPlan
from models.responses import (
    CompanyInfo as CompanyInfoResponse,
    PrecedentResult,
    PrecedentSummary,
    PrecedentOutcomes,
    PrecedentCase as PrecedentCaseResponse,
    ResourceResourceResult,
    OverallVerdict,
    ResourceSimulationResult,
    StructuredPlan as StructuredPlanResponse,
    MarketTrendResult,
    TrendSummary,
    LocationInsights,
    ValidationReport,
    ValidationResponse,
)
from services.strategy_structuring import strategy_structuring_service
from services.precedent_engine import precedent_engine_service
from services.resource_simulator import resource_simulator_service
from services.market_trend_engine import market_trend_engine_service
from services.report_generation import report_generation_service


class ValidationPipelineService:
    """Main orchestrator that runs the full validation pipeline."""

    async def run(self, company_id: str, team_id: str, user_request: str) -> ValidationResponse:
        """
        Run the full validation pipeline in three phases.
        """
        logger.info(f"Starting validation pipeline for company_id: {company_id}, team_id: {team_id}")

        # Phase 1: Run independent tasks concurrently
        structuring_task = asyncio.create_task(
            strategy_structuring_service.structure(user_request)
        )
        company_task = asyncio.create_task(
            company_client.get_company(company_id)
        )
        reports_task = asyncio.create_task(
            reports_client.get_reports(team_id)
        )

        structured_plan, company_info, reports = await asyncio.gather(
            structuring_task, company_task, reports_task
        )

        logger.info("Phase 1 complete: structuring, company info, and reports retrieved")

        # Build shared context
        precedent_input = structured_plan.precedent_engine_input.to_dict()
        company_context = {
            "industry": company_info.industry,
            "size": company_info.size,
            "location": structured_plan.precedent_engine_input.primary_action.details.location,
        }

        resource_plan = structured_plan.resource_simulator_input
        market_trend_input = precedent_input

        # Phase 2: Run three engines concurrently
        precedent_task = asyncio.create_task(
            precedent_engine_service.run(precedent_input, company_context)
        )
        resource_task = asyncio.create_task(
            resource_simulator_service.simulate(resource_plan, company_info, reports)
        )
        market_trend_task = asyncio.create_task(
            market_trend_engine_service.run(market_trend_input, company_context)
        )

        precedent_result, resource_result, market_trend_result = await asyncio.gather(
            precedent_task, resource_task, market_trend_task
        )

        logger.info("Phase 2 complete: precedent, resource, and market trend engines finished")

        # Phase 3: Report generation (combines all outputs)
        company_info_dict = {
            "name": company_info.name,
            "industry": company_info.industry,
            "size": company_info.size,
            "description": company_info.description,
            "country": company_info.country,
        }

        report_result = await report_generation_service.generate(
            user_request=user_request,
            company_info=company_info_dict,
            structured_plan=structured_plan.to_dict(),
            precedent_result=precedent_result,
            resource_result=resource_result,
            market_trend_result=market_trend_result,
        )

        logger.info("Phase 3 complete: report generation finished")

        return self._build_response(
            company_info=company_info,
            structured_plan=structured_plan,
            precedent_result=precedent_result,
            resource_result=resource_result,
            market_trend_result=market_trend_result,
            report_result=report_result,
        )

    @staticmethod
    def _build_response(
        company_info: CompanyInfo,
        structured_plan: StructuredPlan,
        precedent_result: Dict[str, Any],
        resource_result: Dict[str, Any],
        market_trend_result: Dict[str, Any],
        report_result: Dict[str, Any],
    ) -> ValidationResponse:
        """Build the final ValidationResponse from all component results."""

        # Company info
        company_response = CompanyInfoResponse(
            name=company_info.name,
            industry=company_info.industry,
            size=company_info.size,
            description=company_info.description,
            country=company_info.country,
        )

        # Structured plan
        plan_response = StructuredPlanResponse(
            precedent_engine_input=structured_plan.precedent_engine_input.to_dict(),
            resource_simulator_input=structured_plan.resource_simulator_input.to_dict(),
        )

        # Precedent result
        ps = precedent_result.get("precedent_summary", {})
        outcomes = precedent_result.get("outcomes", {})
        precedent_response = PrecedentResult(
            precedent_summary=PrecedentSummary(
                precedent_exists=ps.get("precedent_exists", False),
                cases_analyzed=ps.get("cases_analyzed", 0),
                context_match_level=ps.get("context_match_level", "Low"),
                confidence_score=ps.get("confidence_score", 0),
            ),
            outcomes=PrecedentOutcomes(
                success=outcomes.get("success", 0),
                partial_success=outcomes.get("partial_success", 0),
                failure=outcomes.get("failure", 0),
            ),
            what_worked=precedent_result.get("what_worked", []),
            what_failed=precedent_result.get("what_failed", []),
            key_insights=precedent_result.get("key_insights", {}),
            cases=[
                PrecedentCaseResponse(
                    company=c.get("company", ""),
                    outcome=c.get("outcome", ""),
                    what_happened=c.get("what_happened", ""),
                    reason=c.get("reason", ""),
                )
                for c in precedent_result.get("cases", [])
            ],
        )

        # Resource simulation result
        fin = resource_result.get("financial_resources", {})
        hum = resource_result.get("human_resources", {})
        ops = resource_result.get("operational_resources", {})
        verdict = resource_result.get("overall_execution_verdict", {})

        resource_response = ResourceSimulationResult(
            financial_resources=ResourceResourceResult(
                is_sufficient=fin.get("is_sufficient", False),
                status=fin.get("status", ""),
                why=fin.get("why", []),
                key_metrics=fin.get("key_metrics"),
            ),
            human_resources=ResourceResourceResult(
                is_sufficient=hum.get("is_sufficient", False),
                status=hum.get("status", ""),
                why=hum.get("why", []),
                key_metrics=hum.get("key_metrics"),
            ),
            operational_resources=ResourceResourceResult(
                is_sufficient=ops.get("is_sufficient", False),
                status=ops.get("status", ""),
                why=ops.get("why", []),
            ),
            overall_execution_verdict=OverallVerdict(
                can_execute_plan=verdict.get("can_execute_plan", False),
                blocking_factors=verdict.get("blocking_factors", []),
            ),
        )

        # Market trend result
        ts = market_trend_result.get("trend_summary", {})
        li = market_trend_result.get("location_insights", {})
        market_trend_response = MarketTrendResult(
            trend_summary=TrendSummary(
                market_direction=ts.get("market_direction", "Unknown"),
                growth_rate=ts.get("growth_rate", "Unknown"),
                trend_confidence=ts.get("trend_confidence", 0),
                timing_assessment=ts.get("timing_assessment", ""),
            ),
            key_trends=market_trend_result.get("key_trends", []),
            opportunities=market_trend_result.get("opportunities", []),
            risks=market_trend_result.get("risks", []),
            location_insights=LocationInsights(
                location=li.get("location", ""),
                market_maturity=li.get("market_maturity", "Unknown"),
                competition_level=li.get("competition_level", "Unknown"),
            ),
            recommendation=market_trend_result.get("recommendation", ""),
        )

        # Report
        report_response = ValidationReport(
            executive_summary=report_result.get("executive_summary", ""),
            validation_decision=report_result.get("validation_decision", ""),
            confidence_score=report_result.get("confidence_score", 0),
            key_findings=report_result.get("key_findings", {}),
            recommendations=report_result.get("recommendations", []),
            risk_factors=report_result.get("risk_factors", []),
            next_steps=report_result.get("next_steps", []),
        )

        return ValidationResponse(
            status="completed",
            company_info=company_response,
            structured_plan=plan_response,
            precedent_result=precedent_response,
            resource_simulation_result=resource_response,
            market_trend_result=market_trend_response,
            validation_report=report_response,
        )


# Singleton instance
validation_pipeline_service = ValidationPipelineService()
