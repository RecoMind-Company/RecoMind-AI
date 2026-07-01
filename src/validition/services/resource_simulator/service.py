"""
Resource Simulator Agent - Service
"""
import json
import re
from typing import Any, Dict, List

from loguru import logger

from core.exceptions import ResourceSimulationException
from llm.client import llm_client
from models.entities import CompanyInfo, ResourceSimulatorInput
from .prompts import SYSTEM_PROMPT, OUTPUT_SCHEMA


class ResourceSimulatorService:
    """Adaptive resource analysis service."""

    async def simulate(
        self,
        plan_input: ResourceSimulatorInput,
        company_info: CompanyInfo,
        reports: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        logger.info("Resource simulator: starting adaptive simulation...")

        user_prompt = self._build_user_prompt(plan_input, company_info, reports)

        try:
            raw_output = await llm_client.generate(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.0,
            )
        except Exception as e:
            logger.error(f"Resource simulator LLM call failed: {e}")
            raise ResourceSimulationException(
                message=f"LLM simulation failed: {str(e)}",
            )

        result = self._parse_output(raw_output)
        result = self._normalize_booleans(result)
        logger.info("Resource simulator: completed successfully")
        return result

    @staticmethod
    def _build_user_prompt(
        plan_input: ResourceSimulatorInput,
        company_info: CompanyInfo,
        reports: List[Dict[str, Any]],
    ) -> str:
        plan_json = json.dumps(plan_input.to_dict(), ensure_ascii=False, indent=2)
        company_json = json.dumps(
            {
                "name": company_info.name,
                "industry": company_info.industry,
                "size": company_info.size,
                "description": company_info.description,
                "country": company_info.country,
            },
            ensure_ascii=False,
            indent=2,
        )
        reports_json = json.dumps(reports, ensure_ascii=False, indent=2) if reports else "No reports available."
        schema_json = json.dumps(OUTPUT_SCHEMA, ensure_ascii=False, indent=2)

        return f"""Here is the proposed strategic plan and its requirements:
---
{plan_json}
---

Here is the company's information:
---
{company_json}
---

Here are the company's recent reports (may contain various types of data):
---
{reports_json}
---

Analyze the available data and compare it against the plan's requirements.
If specific data categories are missing, make reasonable inferences based on \
company size, industry, and description.
Output the final Readiness Report as JSON following this structure:
{schema_json}"""

    @staticmethod
    def _parse_output(raw_text: str) -> Dict[str, Any]:
        cleaned = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ResourceSimulationException(
                message=f"Failed to parse JSON from LLM: {e}",
                details={"raw_output": raw_text[:500]},
            )

    @staticmethod
    def _normalize_booleans(data: Dict[str, Any]) -> Dict[str, Any]:
        for category in ["financial_resources", "human_resources", "operational_resources"]:
            if category in data and isinstance(data[category], dict):
                val = data[category].get("is_sufficient")
                if isinstance(val, str):
                    data[category]["is_sufficient"] = val.lower() == "true"

        verdict = data.get("overall_execution_verdict", {})
        if isinstance(verdict, dict):
            val = verdict.get("can_execute_plan")
            if isinstance(val, str):
                verdict["can_execute_plan"] = val.lower() == "true"

        return data


resource_simulator_service = ResourceSimulatorService()
