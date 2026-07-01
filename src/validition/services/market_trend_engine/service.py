"""
Market Trend Engine Agent - Service
"""
import asyncio
from typing import Any, Dict, List

from crewai import Agent, Crew, LLM, Task
from loguru import logger

from core.config import settings
from tools.search_tools import search_tools
from utils.helpers import safe_json_load
from .prompts import AGENT_ROLE, AGENT_GOAL, AGENT_BACKSTORY, TASK_DESCRIPTION


class MarketTrendEngineService:
    """Service for analyzing market trends relevant to the strategic decision."""

    def __init__(self):
        self._llm = LLM(
            model=f"groq/{settings.GROQ_MODEL}",
            api_key=settings.GROQ_API_KEY,
            temperature=0,
        )
        self._trend_agent = Agent(
            role=AGENT_ROLE,
            goal=AGENT_GOAL,
            backstory=AGENT_BACKSTORY,
            llm=self._llm,
            allow_delegation=False,
        )

    async def run(self, strategy_data: Dict[str, Any], company_context: Dict[str, str]) -> Dict[str, Any]:
        industry = company_context.get("industry", "")
        location = strategy_data.get("primary_action", {}).get("details", {}).get("location", "")
        strategy_type = strategy_data.get("strategy_type", "")
        action_type = strategy_data.get("primary_action", {}).get("action_type", "")

        logger.info(f"Market trend engine: analyzing trends for industry={industry}, location={location}")

        queries = self._build_queries(industry, location, strategy_type, action_type)
        if not queries:
            logger.warning("No queries generated for market trends")
            return self._empty_result(industry, location)

        try:
            results = await search_tools.search_all(queries)
            results = search_tools.deduplicate(results)

            high_value_kw = [industry.lower(), "market trend", "growth", "forecast", location.lower()]
            results = search_tools.filter_and_rank(results, high_value_keywords=high_value_kw)

            if not results:
                return self._empty_result(industry, location)

            context = search_tools.build_context(results, top_n=10)

            trend_analysis = await self._analyze_trends(
                industry, location, strategy_type, action_type, context
            )

            logger.info("Market trend engine: completed successfully")
            return trend_analysis

        except Exception as e:
            logger.error(f"Market trend engine failed: {e}")
            return self._empty_result(industry, location)

    @staticmethod
    def _build_queries(industry: str, location: str, strategy_type: str, action_type: str) -> List[str]:
        queries = []
        industry_lower = industry.lower() if industry else "business"
        location_lower = location.lower() if location else ""

        queries.append(f"{industry_lower} market trends 2025 2026 forecast")
        queries.append(f"{industry_lower} industry growth outlook report")
        queries.append(f"{industry_lower} market size trends analysis")

        if location_lower:
            queries.append(f"{location_lower} {industry_lower} market trends growth")
            queries.append(f"{location_lower} {industry_lower} investment opportunities")
            queries.append(f"{location_lower} market outlook {industry_lower} sector")

        if action_type:
            action_lower = action_type.lower()
            queries.append(f"{action_lower} {industry_lower} trend 2025")
            queries.append(f"{action_lower} market opportunity {industry_lower}")

        queries.append(f"{industry_lower} market news trends recent")

        return queries[:10]

    async def _analyze_trends(
        self, industry: str, location: str, strategy_type: str, action_type: str, context: str
    ) -> Dict[str, Any]:
        input_data = {
            "industry": industry,
            "location": location,
            "strategy_type": strategy_type,
            "action_type": action_type,
        }

        task = Task(
            description=TASK_DESCRIPTION,
            expected_output="Raw JSON object with market trend analysis",
            agent=self._trend_agent,
        )
        crew = Crew(tasks=[task], verbose=False)

        try:
            result = await asyncio.to_thread(
                crew.kickoff,
                inputs={"input": input_data, "context": context},
            )
            parsed = safe_json_load(result.raw)

            if isinstance(parsed, dict):
                return parsed
            elif isinstance(parsed, list) and parsed:
                return parsed[0] if isinstance(parsed[0], dict) else {}

            return self._empty_result(industry, location)

        except Exception as e:
            logger.error(f"Trend analysis LLM call failed: {e}")
            return self._empty_result(industry, location)

    @staticmethod
    def _empty_result(industry: str, location: str) -> Dict[str, Any]:
        return {
            "trend_summary": {
                "market_direction": "Unknown",
                "growth_rate": "Unknown",
                "trend_confidence": 0,
                "timing_assessment": "Unable to determine market timing due to insufficient data.",
            },
            "key_trends": [],
            "opportunities": [],
            "risks": [],
            "location_insights": {
                "location": location,
                "market_maturity": "Unknown",
                "competition_level": "Unknown",
            },
            "recommendation": "Gather more market data before making a strategic decision.",
        }


market_trend_engine_service = MarketTrendEngineService()
