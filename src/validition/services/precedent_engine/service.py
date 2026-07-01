"""
Precedent Engine Agent - Service
"""
import asyncio
from typing import Any, Dict, List

from crewai import Agent, Crew, LLM, Task
from loguru import logger

from core.config import settings
from core.exceptions import PrecedentEngineException
from tools.search_tools import search_tools
from utils.helpers import safe_json_load
from .prompts import (
    QUERY_AGENT_ROLE, QUERY_AGENT_GOAL, QUERY_AGENT_BACKSTORY,
    PRECEDENT_AGENT_ROLE, PRECEDENT_AGENT_GOAL, PRECEDENT_AGENT_BACKSTORY,
    QUERY_TASK_DESCRIPTION, PRECEDENT_TASK_DESCRIPTION,
)
from .analyzer import precedent_analyzer


VAGUE_PHRASES = [
    "source does not", "not indicated", "not quantified", "no evidence",
    "outcome uncertain", "unclear", "not provided", "does not specify",
    "cannot determine", "not mentioned", "no information", "no data",
    "not clear", "hard to say", "difficult to determine", "insufficient information",
]


class PrecedentEngineService:
    """Service for finding and extracting business case precedents."""

    def __init__(self):
        self._llm = LLM(
            model=f"groq/{settings.GROQ_MODEL}",
            api_key=settings.GROQ_API_KEY,
            temperature=0,
        )
        self._query_agent = Agent(
            role=QUERY_AGENT_ROLE,
            goal=QUERY_AGENT_GOAL,
            backstory=QUERY_AGENT_BACKSTORY,
            llm=self._llm,
            allow_delegation=False,
        )
        self._precedent_agent = Agent(
            role=PRECEDENT_AGENT_ROLE,
            goal=PRECEDENT_AGENT_GOAL,
            backstory=PRECEDENT_AGENT_BACKSTORY,
            llm=self._llm,
            allow_delegation=False,
        )

    async def run(self, precedent_input: Dict[str, Any], company_context: Dict[str, str]) -> Dict[str, Any]:
        input_data = {
            "strategy_type": precedent_input.get("strategy_type", ""),
            "decision_category": precedent_input.get("decision_category", ""),
            "primary_action": precedent_input.get("primary_action", {}),
            "company_context": company_context,
        }

        try:
            logger.info("Precedent engine: generating search queries...")
            queries = await self._generate_queries(input_data)
            if not queries:
                logger.warning("No queries generated, returning empty result")
                return precedent_analyzer.empty_result()

            logger.info(f"Precedent engine: searching with {len(queries)} queries...")
            results = await self._run_search_pipeline(queries)
            logger.info(f"Precedent engine: {len(results)} ranked results")

            if not results:
                return precedent_analyzer.empty_result()

            context = search_tools.build_context(results, top_n=10)

            logger.info("Precedent engine: extracting cases (round 1)...")
            valid_cases = await self._extract_cases(input_data, context)
            logger.info(f"Precedent engine: {len(valid_cases)} valid cases")

            should_retry, missing = self._needs_retry(valid_cases)
            if should_retry:
                reason = f"count={len(valid_cases)}/{settings.MIN_PRECEDENT_CASES}"
                if missing:
                    reason += f", missing={missing}"
                logger.info(f"Precedent engine: retry ({reason})...")

                followup = self._build_followup_queries(input_data, missing)
                extra_results = await self._run_search_pipeline(followup)
                merged = search_tools.deduplicate(results + extra_results)
                merged = search_tools.filter_and_rank(merged)
                context2 = search_tools.build_context(merged, top_n=12)

                extra_cases = await self._extract_cases(input_data, context2)
                existing = {c["company"].lower() for c in valid_cases}
                for c in extra_cases:
                    if c["company"].lower() not in existing:
                        valid_cases.append(c)
                        existing.add(c["company"].lower())

                logger.info(f"Precedent engine: {len(valid_cases)} cases after retry")

            logger.info(f"Precedent engine: completed with {len(valid_cases)} cases")
            return precedent_analyzer.build_output(valid_cases)

        except PrecedentEngineException:
            raise
        except Exception as e:
            logger.error(f"Precedent engine failed: {e}")
            raise PrecedentEngineException(
                message=f"Precedent engine failed: {str(e)}",
            )

    async def _generate_queries(self, input_data: Dict[str, Any]) -> List[str]:
        task = Task(
            description=QUERY_TASK_DESCRIPTION,
            expected_output="Raw JSON array of 10 targeted search query strings",
            agent=self._query_agent,
        )
        crew = Crew(tasks=[task], verbose=False)

        try:
            result = await asyncio.to_thread(
                crew.kickoff, inputs={"input": input_data}
            )
            queries = safe_json_load(result.raw)
            if not isinstance(queries, list):
                return []
            return [q for q in queries if isinstance(q, str) and len(q) > 5][:10]
        except Exception as e:
            logger.error(f"Query generation failed: {e}")
            raise PrecedentEngineException(message=f"Query generation failed: {str(e)}")

    async def _extract_cases(self, input_data: Dict[str, Any], context: str) -> List[Dict[str, Any]]:
        task = Task(
            description=PRECEDENT_TASK_DESCRIPTION,
            expected_output="Raw JSON array of business cases",
            agent=self._precedent_agent,
        )
        crew = Crew(tasks=[task], verbose=False)

        try:
            result = await asyncio.to_thread(
                crew.kickoff,
                inputs={"input": input_data, "context": context},
            )
            cases = safe_json_load(result.raw)
            return self._validate_cases(cases)
        except Exception as e:
            logger.error(f"Case extraction failed: {e}")
            raise PrecedentEngineException(message=f"Case extraction failed: {str(e)}")

    async def _run_search_pipeline(self, queries: List[str]) -> List[Dict[str, Any]]:
        try:
            search_results = await search_tools.search_all(queries)
            enriched = await search_tools.enrich_with_wikipedia(list(search_results))
        except Exception as e:
            logger.warning(f"Search pipeline error, falling back to sequential: {e}")
            search_results = await search_tools.search_all(queries)
            enriched = await search_tools.enrich_with_wikipedia(search_results)

        enriched = search_tools.deduplicate(enriched)
        return search_tools.filter_and_rank(enriched)

    @staticmethod
    def _validate_cases(cases: Any) -> List[Dict[str, Any]]:
        if not isinstance(cases, list):
            return []

        required_keys = {"company", "outcome", "reason", "what_happened"}
        valid = []

        for c in cases:
            if not isinstance(c, dict):
                continue
            if not required_keys.issubset(c.keys()):
                continue
            if any(not isinstance(c[k], str) for k in required_keys):
                continue
            if c["outcome"] not in ["Success", "Failure", "Partial"]:
                continue
            if len(c["what_happened"].strip()) < 10:
                continue
            if len(c["reason"].strip()) < 25:
                continue
            if any(p in c["reason"].lower() for p in VAGUE_PHRASES):
                continue
            valid.append(c)

        return valid

    @staticmethod
    def _needs_retry(valid_cases: List[Dict[str, Any]]) -> tuple:
        count = len(valid_cases)
        has_success = any(c["outcome"] == "Success" for c in valid_cases)
        has_failure = any(c["outcome"] in ["Failure", "Partial"] for c in valid_cases)

        missing = []
        if not has_success:
            missing.append("success")
        if not has_failure:
            missing.append("failure")

        should_retry = (count < settings.MIN_PRECEDENT_CASES) or bool(missing)
        return should_retry, missing

    @staticmethod
    def _build_followup_queries(input_data: Dict[str, Any], missing: List[str]) -> List[str]:
        industry = input_data.get("company_context", {}).get("industry", "retail")
        size = input_data.get("company_context", {}).get("size", "")
        action = input_data.get("primary_action", {}).get("action_type", "expansion")
        location = input_data.get("primary_action", {}).get("details", {}).get("location", "")

        size_label = "small business" if size and any(s in str(size).lower() for s in ["small", "sme", "1", "2"]) else \
                     "medium company" if size and any(s in str(size).lower() for s in ["medium", "mid", "50", "100", "200"]) else \
                     "company"

        queries = []
        if "success" in missing or not missing:
            queries += [
                f"{size_label} {industry} {action} success case study",
                f"successful {size_label} {industry} growth profitable",
                f"{industry} {action} small company wins growth story",
            ]
        if "failure" in missing or not missing:
            queries += [
                f"{size_label} {industry} {action} failure lessons learned",
                f"{industry} {action} small company failed what went wrong",
            ]
        if location:
            queries.append(f"{size_label} {industry} {location} {action} success failure results")

        return queries[:5]


precedent_engine_service = PrecedentEngineService()
